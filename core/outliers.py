# core/outliers.py
"""
Motor de cálculo de Outlier Scores — Versión mejorada.
Score = log2( (views+1) / (median_canal+1) )

Mejoras aplicadas:
- El video evaluado se excluye de su propio baseline
- Score ponderado por antigüedad (método adicional)
- Método extendido de ranking con múltiples factores
"""
import math
import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from sqlalchemy import select

from core.database import get_session
from core.models import Channel, Video

logger = logging.getLogger(__name__)

OUTLIER_THRESHOLD = 1.0   # 2x el baseline
BASELINE_WINDOW   = 30    # últimos N videos para calcular mediana
MIN_AGE_HOURS     = 24    # ignorar videos muy nuevos
MAX_VIDEOS_PER_CHANNEL = 200  # límite de videos a analizar por canal


class OutlierEngine:

    def run(self, session=None) -> int:
        """Recalcula scores para todos los canales. Retorna total actualizado."""
        close_after = session is None
        if session is None:
            session = get_session()

        try:
            channels = session.execute(select(Channel)).scalars().all()
            total = 0
            for ch in channels:
                total += self._compute_for_channel(ch.id, session)
            session.commit()
            return total
        except Exception as e:
            logger.error(f"Error calculando outliers: {e}")
            session.rollback()
            return 0
        finally:
            if close_after:
                session.close()

    def _compute_for_channel(self, channel_id: str, session) -> int:
        """
        Calcula outlier scores para todos los videos de un canal.
        
        Mejora: El video evaluado se excluye de su propio baseline
        para evitar subestimar scores de videos que están en la ventana.
        """
        videos = (
            session.execute(
                select(Video)
                .where(Video.channel_id == channel_id)
                .where(Video.view_count > 0)
                .order_by(Video.published_at.desc())
                .limit(MAX_VIDEOS_PER_CHANNEL)
            ).scalars().all()
        )

        if len(videos) < 2:
            return 0

        now = datetime.utcnow()
        mature = [
            v for v in videos
            if v.published_at and
            (now - v.published_at).total_seconds() / 3600 >= MIN_AGE_HOURS
        ]

        if not mature:
            return 0

        # Obtener subs del canal
        ch = session.get(Channel, channel_id)
        subs = ch.subscriber_count if ch else 0

        count = 0
        for v in mature:
            # ── MEJORA: Excluir el video actual del baseline ──────────
            others = [
                x.view_count for x in mature
                if x.id != v.id
            ][:BASELINE_WINDOW]

            baseline = float(np.median(others)) if others else 1.0
            baseline = max(baseline, 1.0)

            # Score estándar (misma fórmula, baseline más preciso)
            score = math.log2((v.view_count + 1) / (baseline + 1))
            v.outlier_score = round(score, 3)

            # Views por suscriptor
            if subs > 0:
                v.views_per_sub = round(v.view_count / subs, 4)

            # Velocidad aproximada (promedio histórico)
            if v.published_at:
                age_h = max(
                    0.1,
                    (now - v.published_at).total_seconds() / 3600
                )
                v.views_per_hour = round(v.view_count / age_h, 2)

            count += 1

        return count

    def get_top_outliers(
        self,
        session,
        limit: int = 50,
        min_score: float = 0.0,
        min_views: int = 0,
        channel_id: Optional[str] = None,
        category: Optional[str] = None,
        category_label: Optional[str] = None,
        language: Optional[str] = None,
    ) -> list:
        """
        Obtiene los mejores outliers con filtros aplicados en SQL.
        """
        q = (
            select(Video)
            .where(Video.outlier_score >= min_score)
            .where(Video.view_count >= min_views)
        )
        if channel_id:
            q = q.where(Video.channel_id == channel_id)
        if category:
            q = q.where(Video.category == category)
        if category_label:
            q = q.where(Video.category_label == category_label)
        if language:
            q = q.where(Video.language == language)

        q = q.order_by(Video.outlier_score.desc()).limit(limit)
        return session.execute(q).scalars().all()

    def get_top_outliers_weighted(
        self,
        session,
        limit: int = 50,
        min_score: float = 0.0,
        min_views: int = 0,
        channel_id: Optional[str] = None,
        category_label: Optional[str] = None,
        language: Optional[str] = None,
        max_age_days: int = 0,
        sort_by: str = "weighted_score",
    ) -> list:
        """
        Método EXTENDIDO: Obtiene outliers con score ponderado por antigüedad.
        
        El score ponderado reduce el peso de videos muy antiguos que
        acumularon views durante mucho tiempo, priorizando videos
        con crecimiento reciente.
        
        No modifica outlier_score existente. Retorna lista de tuplas
        (video, weighted_score) ordenadas.
        """
        q = (
            select(Video)
            .where(Video.outlier_score >= min_score)
            .where(Video.view_count >= min_views)
        )
        if channel_id:
            q = q.where(Video.channel_id == channel_id)
        if category_label:
            q = q.where(Video.category_label == category_label)
        if language:
            q = q.where(Video.language == language)

        videos = session.execute(q).scalars().all()

        if not videos:
            return []

        now = datetime.utcnow()
        results = []

        for v in videos:
            # Filtrar por antigüedad máxima si se especifica
            if max_age_days > 0 and v.published_at:
                age_days = (now - v.published_at).days
                if age_days > max_age_days:
                    continue

            # Calcular score ponderado por antigüedad
            weighted = self._age_weighted_score(v, now)
            results.append((v, weighted))

        # Ordenar según el criterio solicitado
        if sort_by == "weighted_score":
            results.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == "outlier_score":
            results.sort(key=lambda x: x[0].outlier_score or 0, reverse=True)
        elif sort_by == "view_count":
            results.sort(key=lambda x: x[0].view_count or 0, reverse=True)
        elif sort_by == "views_per_hour":
            results.sort(key=lambda x: x[0].views_per_hour or 0, reverse=True)
        elif sort_by == "recent":
            results.sort(
                key=lambda x: x[0].published_at or datetime.min,
                reverse=True,
            )

        return results[:limit]

    def _age_weighted_score(self, video: Video, now: datetime) -> float:
        """
        Calcula un score ponderado por antigüedad.
        
        Videos recientes (≤7 días) mantienen su score completo.
        Videos más antiguos reciben un decaimiento suave.
        
        Fórmula: score * weight
        weight = 1.0 si age ≤ 7 días
        weight = 1 / (1 + 0.15 * log2(age_days / 7)) si age > 7 días
        
        Esto asegura que:
        - 7 días:  weight = 1.00 (sin cambio)
        - 14 días: weight = 0.87
        - 30 días: weight = 0.77
        - 90 días: weight = 0.64
        - 365 días: weight = 0.53
        """
        base_score = video.outlier_score or 0.0

        if not video.published_at:
            return base_score

        age_days = max(0, (now - video.published_at).days)

        if age_days <= 7:
            return base_score

        # Decaimiento suave logarítmico
        decay = 1.0 / (1.0 + 0.15 * math.log2(age_days / 7.0))
        return round(base_score * decay, 3)

    def get_channel_outlier_stats(self, session, channel_id: str) -> dict:
        """
        Método NUEVO: Estadísticas completas de outliers de un canal.
        Útil para análisis comparativo entre canales.
        """
        videos = (
            session.execute(
                select(Video)
                .where(Video.channel_id == channel_id)
                .where(Video.view_count > 0)
                .order_by(Video.published_at.desc())
                .limit(MAX_VIDEOS_PER_CHANNEL)
            ).scalars().all()
        )

        if not videos:
            return {
                "total_videos": 0,
                "outlier_count": 0,
                "outlier_rate": 0.0,
                "avg_score": 0.0,
                "max_score": 0.0,
                "avg_views": 0,
                "median_views": 0,
            }

        scores = [v.outlier_score or 0 for v in videos]
        views_list = [v.view_count or 0 for v in videos]
        outlier_count = sum(1 for s in scores if s >= OUTLIER_THRESHOLD)

        return {
            "total_videos": len(videos),
            "outlier_count": outlier_count,
            "outlier_rate": round(outlier_count / len(videos), 3) if videos else 0,
            "avg_score": round(float(np.mean(scores)), 3) if scores else 0,
            "max_score": round(float(np.max(scores)), 3) if scores else 0,
            "avg_views": int(np.mean(views_list)) if views_list else 0,
            "median_views": int(np.median(views_list)) if views_list else 0,
        }