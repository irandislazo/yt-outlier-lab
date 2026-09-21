# core/thumbnails.py
"""
Análisis de thumbnails: brillo, color dominante, cara proxy, texto proxy.
Sin almacenar imágenes (solo features numéricas).
"""
import io
import logging

import numpy as np
import requests
from PIL import Image, ImageStat
from sqlalchemy import select

from core.models import Video

logger = logging.getLogger(__name__)
SIZE = (240, 135)


class ThumbnailEngine:

    def run(self, session, limit: int = 100) -> int:
        videos = (
            session.execute(
                select(Video)
                .where(Video.thumbnail_url.isnot(None))
                .where(Video.thumb_brightness.is_(None))
                .order_by(Video.outlier_score.desc())
                .limit(limit)
            ).scalars().all()
        )

        count = 0
        for v in videos:
            feats = self._analyze(v.thumbnail_url)
            if feats:
                v.thumb_dominant_color  = feats["dominant_color"]
                v.thumb_brightness      = feats["brightness"]
                v.thumb_has_face        = feats["has_face"]
                v.thumb_text_detected   = feats["has_text"]
                count += 1

        session.commit()
        return count

    def _analyze(self, url: str):
        try:
            r = requests.get(url, timeout=8)
            if r.status_code != 200:
                return None

            img  = Image.open(io.BytesIO(r.content)).convert("RGB")
            img  = img.resize(SIZE, Image.LANCZOS)
            stat = ImageStat.Stat(img)

            brightness = sum(stat.mean) / 3
            dominant   = self._dominant_color(img)
            has_face   = self._proxy_face(img)
            has_text   = bool(sum(stat.stddev) / 3 > 55)

            return {
                "brightness":    round(brightness, 2),
                "dominant_color": dominant,
                "has_face":      has_face,
                "has_text":      has_text,
            }
        except Exception as e:
            logger.debug(f"Thumb error {url}: {e}")
            return None

    def _dominant_color(self, img: Image.Image) -> str:
        small = img.resize((30, 17), Image.LANCZOS)
        arr   = np.array(small).mean(axis=(0, 1)).astype(int)
        return f"#{arr[0]:02x}{arr[1]:02x}{arr[2]:02x}"

    def _proxy_face(self, img: Image.Image) -> bool:
        w, h = img.size
        cx, cy = w // 4, h // 4
        crop = img.crop((cx, cy, w - cx, h - cy))
        return bool(np.array(crop).astype(float).var() > 700)


    def run_filtered(
        self,
        session,
        limit: int = 50,
        min_score: float = 0.0,
        category_label: str = None,
        language: str = None,
        only_outliers: bool = False,
        progress_callback=None,
    ) -> dict:
        """
        Análisis de thumbnails con filtros y progreso.
        
        Solo analiza videos que AÚN no tienen análisis de thumbnail,
        lo que hace que las ejecuciones posteriores sean casi instantáneas.
        
        Retorna dict con estadísticas del análisis.
        """
        results = {
            "analyzed": 0,
            "skipped_already_done": 0,
            "errors": 0,
            "total_selected": 0,
        }

        q = (
            select(Video)
            .where(Video.thumbnail_url.isnot(None))
            .where(Video.thumbnail_url != "")
        )

        # Solo videos sin análisis previo
        q = q.where(Video.thumb_brightness.is_(None))

        # Filtro de score mínimo
        if min_score > 0:
            q = q.where(Video.outlier_score >= min_score)

        # Solo outliers
        if only_outliers:
            q = q.where(Video.outlier_score >= 1.0)

        # Filtro por categoría
        if category_label:
            q = q.where(Video.category_label == category_label)

        # Filtro por idioma
        if language:
            q = q.where(Video.language == language)

        # Ordenar por score descendente (analizar los mejores primero)
        q = q.order_by(Video.outlier_score.desc())

        # Contar total antes de limitar
        all_videos = session.execute(q).scalars().all()
        results["total_selected"] = len(all_videos)

        # Limitar la cantidad a procesar
        videos = all_videos[:limit]

        for i, v in enumerate(videos):
            try:
                feats = self._analyze(v.thumbnail_url)
                if feats:
                    v.thumb_dominant_color = feats["dominant_color"]
                    v.thumb_brightness     = feats["brightness"]
                    v.thumb_has_face       = feats["has_face"]
                    v.thumb_text_detected  = feats["has_text"]
                    results["analyzed"] += 1
                else:
                    results["errors"] += 1

                # Reportar progreso
                if progress_callback:
                    pct = int((i + 1) / len(videos) * 100)
                    progress_callback(pct, f"Analizando {i+1}/{len(videos)}...")

            except Exception as e:
                logger.warning(f"Error analizando thumb {v.id}: {e}")
                results["errors"] += 1

        session.commit()
        return results