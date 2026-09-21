# core/discovery.py
"""
Motor de auto-descubrimiento — Versión definitiva.
- Filtra Shorts por duración
- Respeta idioma con validación estricta
- No repite canales/videos ya encontrados
- Usa paginación para encontrar contenido nuevo
- Soporta descubrimiento dedicado de canales
- Asigna category_label para filtrado por nicho
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select

from core.youtube_api import YouTubeAPI, YOUTUBE_CATEGORIES
from core.database import get_session
from core.models import Channel, Video, QuotaLog

logger = logging.getLogger(__name__)

# Duración mínima por defecto para excluir Shorts (en segundos)
DEFAULT_MIN_DURATION = 61  # > 1 minuto = NO es Short


class DiscoveryEngine:

    def __init__(self):
        self.api = YouTubeAPI()

 
    # ================================================================== #
    #  DESCUBRIMIENTO DE VIDEOS                                           #
    # ================================================================== #
    def run_discovery(
        self,
        category_name: str    = "Todos",
        region_code: str      = "US",
        language: str         = "es",
        keywords: str         = "",
        days_back: int        = 30,
        max_channels: int     = 50,
        min_subs: int         = 1000,
        max_subs: int         = 0,
        use_trending: bool    = True,
        use_search: bool      = True,
        videos_per_channel: int = 30,
        min_duration: int     = DEFAULT_MIN_DURATION,
        max_duration: int     = 0,
        duration_api_filter: str = "medium",
        min_views: int        = 0,
        progress_callback     = None,
    ) -> dict:
        """
        Descubrimiento completo con todos los filtros respetados.
        Los videos se guardan con category_label para filtrado por nicho.
        """
        session = get_session()
        results = {
            "channels_found":  0,
            "videos_found":    0,
            "videos_skipped_lang": 0,
            "videos_skipped_duration": 0,
            "videos_skipped_duplicate": 0,
            "quota_used": 0,
            "errors":     [],
        }

        try:
            category_id = YOUTUBE_CATEGORIES.get(category_name, "0")
            published_after = (
                datetime.utcnow() - timedelta(days=days_back)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")

            # Obtener IDs ya existentes para no repetir
            existing_video_ids = set(
                row[0] for row in
                session.execute(select(Video.id)).all()
            )
            existing_channel_ids = set(
                row[0] for row in
                session.execute(select(Channel.id)).all()
            )

            self._report(progress_callback, 2,
                         f"📊 Ya tienes {len(existing_video_ids)} videos y "
                         f"{len(existing_channel_ids)} canales en tu base de datos.")

            raw_videos_pool = []

            # ── CAPA 1: Trending ──────────────────────────────────────
            if use_trending:
                self._report(progress_callback, 5,
                             "🔥 Buscando videos en tendencia...")
                trending = self.api.get_trending_videos(
                    region_code=region_code,
                    category_id=category_id,
                    max_results=50,
                )
                raw_videos_pool.extend(trending)
                results["quota_used"] += 1
                self._log_quota(session, "videos", 1)
                self._report(progress_callback, 10,
                             f"✅ {len(trending)} videos en tendencia encontrados.")

            # ── CAPA 2: Keyword Search ────────────────────────────────
            if use_search:
                search_queries = self._build_queries(
                    keywords, category_name, language
                )
                total_queries = len(search_queries)

                for i, query in enumerate(search_queries):
                    pct = 10 + int((i / max(total_queries, 1)) * 25)
                    self._report(progress_callback, pct,
                                 f"🔍 Buscando: '{query}' ({i+1}/{total_queries})...")

                    found, next_token = self.api.search_videos(
                        query=query,
                        category_id=category_id,
                        region_code=region_code,
                        language=language,
                        order="viewCount",
                        max_results=50,
                        published_after=published_after,
                        duration_filter=duration_api_filter,
                    )
                    raw_videos_pool.extend(found)
                    results["quota_used"] += 101

                    # Segunda página para encontrar más variedad
                    if next_token:
                        found2, _ = self.api.search_videos(
                            query=query,
                            category_id=category_id,
                            region_code=region_code,
                            language=language,
                            order="date",
                            max_results=50,
                            published_after=published_after,
                            duration_filter=duration_api_filter,
                            page_token=next_token,
                        )
                        raw_videos_pool.extend(found2)
                        results["quota_used"] += 101

                    self._log_quota(session, "search", 100)
                    self._log_quota(session, "videos", 1)

            # ── Filtrar y UPSERTEAR videos con category_label ────────
            channel_ids_set = set()
            new_video_count = 0

            self._report(progress_callback, 38,
                         "🔧 Aplicando filtros y guardando videos...")

            for v in raw_videos_pool:
                vid = v.get("id", "")
                if isinstance(vid, dict):
                    vid = vid.get("videoId", "")
                if not vid:
                    continue

                # Deduplicar
                if vid in existing_video_ids:
                    results["videos_skipped_duplicate"] += 1
                    continue

                # Parsear para obtener duración
                parsed = YouTubeAPI.parse_video(v)

                # Filtro de duración (excluir Shorts)
                dur = parsed.get("duration_seconds", 0)
                if min_duration > 0 and dur < min_duration:
                    results["videos_skipped_duration"] += 1
                    continue
                if max_duration > 0 and dur > max_duration:
                    results["videos_skipped_duration"] += 1
                    continue

                # Filtro de idioma estricto
                if language:
                    title = parsed.get("title", "")
                    desc = parsed.get("description", "")
                    audio_lang = parsed.get("default_audio_language", "")
                    video_lang = parsed.get("default_language", "")

                    lang_match = False
                    if audio_lang and audio_lang.startswith(language):
                        lang_match = True
                    elif video_lang and video_lang.startswith(language):
                        lang_match = True
                    else:
                        lang_match = YouTubeAPI.validate_language(
                            title, desc, language
                        )

                    if not lang_match:
                        results["videos_skipped_lang"] += 1
                        continue

                # Filtro de views mínimas
                if min_views > 0 and parsed.get("view_count", 0) < min_views:
                    continue

                # ── UPSERTEAR video CON category_label ────────────────
                video = self._upsert_video(
                    v, session, channel_subs=0,
                    category_label=category_name,
                    video_language=language,  # ← NUEVO
                )
                if video:
                    existing_video_ids.add(vid)
                    new_video_count += 1

                # Registrar canal para expansión posterior
                ch_id = parsed.get("channel_id", "")
                if ch_id and ch_id not in existing_channel_ids:
                    channel_ids_set.add(ch_id)

            self._report(progress_callback, 42,
                         f"📊 {new_video_count} videos nuevos guardados / "
                         f"{len(channel_ids_set)} canales nuevos descubiertos. "
                         f"({results['videos_skipped_duration']} excluidos por duración, "
                         f"{results['videos_skipped_lang']} por idioma, "
                         f"{results['videos_skipped_duplicate']} duplicados)")

            # ── CAPA 3: Expansión de canales ──────────────────────────
            channel_ids = list(channel_ids_set)
            random.shuffle(channel_ids)
            channel_ids = channel_ids[:max_channels]
            total_ch = len(channel_ids)

            channels_saved = 0
            videos_saved = 0

            for i, ch_id in enumerate(channel_ids):
                pct = 42 + int((i / max(total_ch, 1)) * 50)
                self._report(progress_callback, pct,
                             f"📺 Analizando canal {i+1}/{total_ch}...")

                ch_raw = self.api.get_channel_info(ch_id)
                if not ch_raw:
                    continue
                results["quota_used"] += 1
                self._log_quota(session, "channels", 1)

                subs = int(
                    ch_raw.get("statistics", {}).get("subscriberCount", 0) or 0
                )
                if subs < min_subs:
                    continue
                if max_subs > 0 and subs > max_subs:
                    continue

                channel = self._upsert_channel(
                    ch_raw, session, category=category_name, language=language
                )
                if channel:
                    channels_saved += 1
                    existing_channel_ids.add(ch_id)

                ch_videos = self.api.get_channel_videos(
                    ch_id, max_results=videos_per_channel
                )
                results["quota_used"] += 2
                self._log_quota(session, "playlistItems", 1)
                self._log_quota(session, "videos", 1)

                for v_raw in ch_videos:
                    parsed = YouTubeAPI.parse_video(v_raw, subs)
                    v_id = parsed.get("id", "")

                    if v_id in existing_video_ids:
                        continue

                    dur = parsed.get("duration_seconds", 0)
                    if min_duration > 0 and dur < min_duration:
                        results["videos_skipped_duration"] += 1
                        continue
                    if max_duration > 0 and dur > max_duration:
                        results["videos_skipped_duration"] += 1
                        continue

                    if language:
                        title = parsed.get("title", "")
                        desc = parsed.get("description", "")
                        audio_lang = parsed.get("default_audio_language", "")
                        video_lang = parsed.get("default_language", "")

                        lang_match = False
                        if audio_lang and audio_lang.startswith(language):
                            lang_match = True
                        elif video_lang and video_lang.startswith(language):
                            lang_match = True
                        else:
                            lang_match = YouTubeAPI.validate_language(
                                title, desc, language
                            )
                        if not lang_match:
                            results["videos_skipped_lang"] += 1
                            continue

                    if min_views > 0 and parsed.get("view_count", 0) < min_views:
                        continue

                    # ── UPSERTEAR video CON category_label ────────────
                    video = self._upsert_video(
                        v_raw, session, subs,
                        category_label=category_name,
                        video_language=language,  # ← NUEVO
                    )
                    if video:
                        videos_saved += 1
                        existing_video_ids.add(v_id)

            session.commit()
            results["channels_found"] = channels_saved
            results["videos_found"] = new_video_count + videos_saved

            self._report(progress_callback, 94, "🧮 Calculando outlier scores...")
            from core.outliers import OutlierEngine
            OutlierEngine().run(session)
            session.commit()

            self._report(progress_callback, 100,
                         f"✅ Descubrimiento completado: {channels_saved} canales, "
                         f"{results['videos_found']} videos nuevos.")

        except Exception as e:
            logger.error(f"Error en discovery: {e}")
            results["errors"].append(str(e))
            session.rollback()
        finally:
            session.close()

        return results
    
    # ================================================================== #
    #  DESCUBRIMIENTO DEDICADO DE CANALES                                 #
    # ================================================================== #
    def discover_channels(
        self,
        keywords: str           = "",
        region_code: str        = "US",
        language: str           = "es",
        category_name: str      = "",
        min_subs: int           = 1000,
        max_subs: int           = 0,
        min_videos: int         = 0,
        min_total_views: int    = 0,
        max_results: int        = 50,
        progress_callback       = None,
    ) -> dict:
        """
        Descubrimiento dedicado de CANALES con filtros avanzados.
        category_name: Nicho asignado a los canales descubiertos.
        """
        session = get_session()
        results = {
            "channels_found": 0,
            "channels_skipped": 0,
            "quota_used": 0,
            "errors": [],
        }

        try:
            existing_ids = set(
                row[0] for row in session.execute(select(Channel.id)).all()
            )

            queries = []
            if keywords:
                for kw in keywords.split(","):
                    kw = kw.strip()
                    if kw:
                        queries.append(kw)

            if not queries:
                queries = self._build_channel_queries(language)

            channels_found = 0
            total_queries = len(queries)

            for qi, query in enumerate(queries):
                if channels_found >= max_results:
                    break

                pct = int((qi / max(total_queries, 1)) * 80) + 5
                self._report(progress_callback, pct,
                             f"🔍 Buscando canales: '{query}' ({qi+1}/{total_queries})...")

                raw_channels, next_token = self.api.search_channels(
                    query=query,
                    region_code=region_code,
                    language=language,
                    max_results=min(50, max_results - channels_found),
                )
                results["quota_used"] += 101
                self._log_quota(session, "search", 100)
                self._log_quota(session, "channels", 1)

                for ch_raw in raw_channels:
                    ch_id = ch_raw.get("id", "")
                    if ch_id in existing_ids:
                        results["channels_skipped"] += 1
                        continue

                    stats = ch_raw.get("statistics", {})
                    subs = int(stats.get("subscriberCount", 0) or 0)
                    vids = int(stats.get("videoCount", 0) or 0)
                    total_views = int(stats.get("viewCount", 0) or 0)

                    if subs < min_subs:
                        results["channels_skipped"] += 1
                        continue
                    if max_subs > 0 and subs > max_subs:
                        results["channels_skipped"] += 1
                        continue
                    if min_videos > 0 and vids < min_videos:
                        results["channels_skipped"] += 1
                        continue
                    if min_total_views > 0 and total_views < min_total_views:
                        results["channels_skipped"] += 1
                        continue

                    snippet = ch_raw.get("snippet", {})
                    ch_title = snippet.get("title", "")
                    ch_desc = snippet.get("description", "")
                    if language and not YouTubeAPI.validate_language(
                        ch_title, ch_desc, language
                    ):
                        ch_country = snippet.get("country", "")
                        lang_countries = {
                            "es": {"ES","MX","AR","CO","CL","PE","EC","VE","BO","PY",
                                   "UY","DO","GT","HN","SV","CR","PA","CU","NI"},
                            "pt": {"BR","PT","AO","MZ"},
                            "fr": {"FR","BE","CA","CH","SN","CI","CM","ML"},
                            "de": {"DE","AT","CH"},
                            "it": {"IT"},
                        }
                        valid_countries = lang_countries.get(language, set())
                        if ch_country and ch_country not in valid_countries:
                            results["channels_skipped"] += 1
                            continue

                    # ── CORRECCIÓN: Pasar category_name en lugar de "" ──
                    channel = self._upsert_channel(
                        ch_raw, session,
                        category=category_name,
                        language=language,
                    )
                    if channel:
                        channels_found += 1
                        existing_ids.add(ch_id)

                if next_token and channels_found < max_results:
                    raw2, _ = self.api.search_channels(
                        query=query,
                        region_code=region_code,
                        language=language,
                        max_results=min(50, max_results - channels_found),
                        page_token=next_token,
                    )
                    results["quota_used"] += 101
                    self._log_quota(session, "search", 100)
                    self._log_quota(session, "channels", 1)

                    for ch_raw in raw2:
                        ch_id = ch_raw.get("id", "")
                        if ch_id in existing_ids:
                            continue

                        stats = ch_raw.get("statistics", {})
                        subs = int(stats.get("subscriberCount", 0) or 0)
                        vids = int(stats.get("videoCount", 0) or 0)
                        total_views = int(stats.get("viewCount", 0) or 0)

                        if subs < min_subs:
                            continue
                        if max_subs > 0 and subs > max_subs:
                            continue
                        if min_videos > 0 and vids < min_videos:
                            continue
                        if min_total_views > 0 and total_views < min_total_views:
                            continue

                        # ── CORRECCIÓN: Pasar category_name ──────────
                        channel = self._upsert_channel(
                            ch_raw, session,
                            category=category_name,
                            language=language,
                        )
                        if channel:
                            channels_found += 1
                            existing_ids.add(ch_id)

            session.commit()
            results["channels_found"] = channels_found
            self._report(progress_callback, 100,
                         f"✅ {channels_found} canales nuevos descubiertos.")

        except Exception as e:
            logger.error(f"Error descubriendo canales: {e}")
            results["errors"].append(str(e))
            session.rollback()
        finally:
            session.close()

        return results

    # ================================================================== #
    #  HELPERS                                                            #
    # ================================================================== #
    def _build_queries(
        self, keywords: str, category_name: str, language: str
    ) -> list:
        queries = []
        if keywords:
            for kw in keywords.split(","):
                kw = kw.strip()
                if kw:
                    queries.append(kw)

        category_queries_by_lang = {
            "es": {
                "Gaming":              ["gameplay español", "juegos en español", "gaming"],
                "Educación":           ["tutorial español", "aprende", "explicado fácil"],
                "Finanzas":            ["finanzas personales", "invertir", "dinero"],
                "Ciencia y Tecnología":["tecnología", "review español", "análisis tech"],
                "Salud y Fitness":     ["rutina ejercicio", "fitness español", "salud"],
                "Cocina":              ["recetas fáciles", "cocina casera", "receta"],
                "Entretenimiento":     ["viral español", "reacción", "challenge"],
                "Música":              ["música nueva", "cover español", "canción"],
                "Vlogs/Gente":         ["vlog español", "día a día", "rutina"],
                "Viajes":              ["viaje", "destinos", "turismo"],
                "Moda y Belleza":      ["maquillaje", "outfit", "skincare español"],
                "Noticias":            ["noticias hoy", "actualidad", "última hora"],
                "Comedia":             ["comedia español", "humor", "gracioso"],
                "Deportes":            ["goles", "resumen partido", "deporte"],
            },
            "en": {
                "Gaming":              ["gaming highlights", "gameplay", "let's play"],
                "Educación":           ["tutorial", "explained", "how to"],
                "Finanzas":            ["personal finance", "investing", "money"],
                "Ciencia y Tecnología":["tech review", "unboxing", "technology"],
                "Entretenimiento":     ["viral", "challenge", "reaction"],
            },
            "fr": {
                "Gaming":              ["gameplay français", "jeux vidéo", "gaming fr"],
                "Educación":           ["tutoriel", "apprendre", "expliqué"],
                "Entretenimiento":     ["viral français", "réaction", "challenge"],
                "Cocina":              ["recette facile", "cuisine française", "recette"],
            },
            "pt": {
                "Gaming":              ["gameplay português", "jogos", "gaming br"],
                "Educación":           ["tutorial português", "aprenda", "explicado"],
                "Entretenimiento":     ["viral brasileiro", "reação", "desafio"],
                "Cocina":              ["receita fácil", "cozinha", "receita"],
            },
            "de": {
                "Gaming":              ["gameplay deutsch", "spiele", "gaming"],
                "Educación":           ["tutorial deutsch", "erklärt", "anleitung"],
                "Entretenimiento":     ["viral deutsch", "reaktion", "challenge"],
            },
        }

        lang_queries = category_queries_by_lang.get(language, {})
        auto = lang_queries.get(category_name, [])

        if not auto:
            fallback = {
                "es": ["tendencia español", "viral español"],
                "en": ["trending", "viral"],
                "fr": ["tendance français", "viral français"],
                "pt": ["tendência brasileiro", "viral brasileiro"],
                "de": ["trending deutsch", "viral deutsch"],
            }
            auto = fallback.get(language, ["trending", "viral"])

        queries.extend(auto)
        return queries[:5]

    def _build_channel_queries(self, language: str) -> list:
        channel_queries = {
            "es": [
                "canal español youtube",
                "youtuber español",
                "canal en español",
                "youtuber latino",
                "creador contenido español",
            ],
            "en": [
                "youtube channel",
                "youtuber",
                "content creator",
            ],
            "fr": [
                "chaîne youtube français",
                "youtubeur français",
                "créateur contenu français",
            ],
            "pt": [
                "canal youtube brasileiro",
                "youtuber brasileiro",
                "canal português",
            ],
            "de": [
                "youtube kanal deutsch",
                "youtuber deutsch",
            ],
        }
        return channel_queries.get(language, ["youtube channel"])[:3]

    def _upsert_channel(self, raw, session, category, language):
        try:
            ch_id = raw.get("id", "")
            snippet = raw.get("snippet", {})
            stats = raw.get("statistics", {})
            if not ch_id:
                return None

            channel = session.get(Channel, ch_id)
            if not channel:
                channel = Channel(id=ch_id)
                session.add(channel)

            thumbs = snippet.get("thumbnails", {})
            channel.title            = snippet.get("title", "")
            channel.description      = (snippet.get("description") or "")[:500]
            channel.thumbnail_url    = thumbs.get("default", {}).get("url", "")
            channel.subscriber_count = int(stats.get("subscriberCount", 0) or 0)
            channel.video_count      = int(stats.get("videoCount", 0) or 0)
            channel.view_count       = int(stats.get("viewCount", 0) or 0)
            channel.country          = snippet.get("country", "")
            channel.category         = category
            channel.language         = language
            channel.updated_at       = datetime.utcnow()
            channel.last_ingested_at = datetime.utcnow()
            custom = snippet.get("customUrl", "")
            channel.handle = custom.lstrip("@") if custom else ""
            session.flush()
            return channel
        except Exception as e:
            logger.error(f"Error canal: {e}")
            return None

    def _upsert_video(self, raw, session, channel_subs=0, category_label="", video_language=""):
        """Inserta o actualiza un video. Acepta category_label y video_language."""
        try:
            parsed = YouTubeAPI.parse_video(
                raw, channel_subs, category_label=category_label
            )
            vid_id = parsed.get("id", "")
            if not vid_id:
                return None
            video = session.get(Video, vid_id)
            if not video:
                video = Video(id=vid_id)
                session.add(video)
            for key, value in parsed.items():
                if hasattr(video, key) and key not in (
                    "default_language", "default_audio_language"
                ):
                    setattr(video, key, value)

            # ── Asignar idioma si el video no lo tiene ────────────────
            if not video.language and video_language:
                video.language = video_language

            video.updated_at = datetime.utcnow()
            session.flush()
            return video
        except Exception as e:
            logger.error(f"Error video: {e}")
            return None

    # ================================================================== #
    #  MÉTODOS ESTÁTICOS (report y quota) — NO ELIMINAR                 #
    # ================================================================== #
    @staticmethod
    def _report(callback, pct, msg):
        """Reporta progreso al callback si existe y loguea."""
        if callback:
            try:
                callback(pct, msg)
            except Exception:
                pass
        logger.info(f"[{pct}%] {msg}")

    @staticmethod
    def _log_quota(session, endpoint, units):
        """Registra el uso de cuota API en la base de datos."""
        try:
            log = QuotaLog(endpoint=endpoint, units_used=units, success=True)
            session.add(log)
        except Exception:
            pass