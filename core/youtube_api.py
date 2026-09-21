# core/youtube_api.py
"""
Conector YouTube Data API v3 — Versión definitiva.
Soporta filtros de duración, idioma estricto y deduplicación.
"""
import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

import requests
from dotenv import load_dotenv

# ── NUEVO: Import de langdetect (opcional) ──────────────────────────
try:
    from langdetect import detect, LangDetectException
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://www.googleapis.com/youtube/v3"

YOUTUBE_CATEGORIES = {
    "Todos":           "0",
    "Cine y Animación":"1",
    "Autos":           "2",
    "Música":          "10",
    "Mascotas":        "15",
    "Deportes":        "17",
    "Viajes":          "19",
    "Gaming":          "20",
    "Vlogs/Gente":     "22",
    "Comedia":         "23",
    "Entretenimiento": "24",
    "Noticias":        "25",
    "Cómo hacer":      "26",
    "Educación":       "27",
    "Ciencia y Tecnología": "28",
    "ONGs":            "29",
    "Finanzas":        "27",
    "Salud y Fitness": "17",
    "Cocina":          "26",
    "Moda y Belleza":  "22",
}

REGIONS = {
    "🌍 Global (Todo el mundo)": "",
    "🇺🇸 Estados Unidos": "US",
    "🇪🇸 España":          "ES",
    "🇲🇽 México":          "MX",
    "🇦🇷 Argentina":       "AR",
    "🇨🇴 Colombia":        "CO",
    "🇨🇱 Chile":           "CL",
    "🇵🇪 Perú":            "PE",
    "🇪🇨 Ecuador":         "EC",
    "🇻🇪 Venezuela":       "VE",
    "🇧🇴 Bolivia":         "BO",
    "🇵🇾 Paraguay":        "PY",
    "🇺🇾 Uruguay":         "UY",
    "🇩🇴 Rep. Dominicana": "DO",
    "🇬🇹 Guatemala":       "GT",
    "🇭🇳 Honduras":        "HN",
    "🇸🇻 El Salvador":     "SV",
    "🇨🇷 Costa Rica":      "CR",
    "🇵🇦 Panamá":          "PA",
    "🇧🇷 Brasil":          "BR",
    "🇬🇧 Reino Unido":     "GB",
    "🇫🇷 Francia":         "FR",
    "🇩🇪 Alemania":        "DE",
    "🇮🇹 Italia":          "IT",
    "🇵🇹 Portugal":        "PT",
    "🇯🇵 Japón":           "JP",
    "🇰🇷 Corea del Sur":   "KR",
    "🇮🇳 India":           "IN",
    "🇮🇩 Indonesia":       "ID",
    "🇹🇷 Turquía":         "TR",
    "🇷🇺 Rusia":           "RU",
    "🇸🇦 Arabia Saudita":  "SA",
    "🇪🇬 Egipto":          "EG",
    "🇳🇬 Nigeria":         "NG",
    "🇿🇦 Sudáfrica":       "ZA",
    "🇦🇺 Australia":       "AU",
    "🇨🇦 Canadá":          "CA",
}

LANGUAGES = {
    "Español":    "es",
    "Inglés":     "en",
    "Portugués":  "pt",
    "Francés":    "fr",
    "Alemán":     "de",
    "Italiano":   "it",
    "Japonés":    "ja",
    "Coreano":    "ko",
    "Hindi":      "hi",
    "Árabe":      "ar",
    "Ruso":       "ru",
    "Turco":      "tr",
    "Indonesio":  "id",
    "Tailandés":  "th",
    "Vietnamita": "vi",
    "Polaco":     "pl",
    "Neerlandés": "nl",
    "Sueco":      "sv",
    "Chino":      "zh",
}

# Mapeo de códigos de idioma a patrones de caracteres para detección
LANGUAGE_CHAR_PATTERNS = {
    "es": r"[áéíóúñ¿¡]",
    "pt": r"[ãõçê]",
    "fr": r"[àâéèêëîïôùûüÿç]",
    "de": r"[äöüß]",
    "ja": r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]",
    "ko": r"[\uAC00-\uD7AF\u1100-\u11FF]",
    "ar": r"[\u0600-\u06FF]",
    "ru": r"[\u0400-\u04FF]",
    "zh": r"[\u4E00-\u9FFF]",
    "hi": r"[\u0900-\u097F]",
    "th": r"[\u0E00-\u0E7F]",
}

# Palabras comunes por idioma para validar
LANGUAGE_COMMON_WORDS = {
    "es": {"como", "para", "que", "con", "los", "las", "del", "por", "una",
           "más", "pero", "este", "esta", "todo", "mejor", "hacer", "tiene",
           "son", "muy", "sin", "hoy", "día", "mi", "te", "yo", "nuevo",
           "porque", "solo", "aquí", "cuando", "puede", "entre", "cada"},
    "en": {"the", "and", "for", "you", "that", "with", "this", "are", "from",
           "your", "how", "was", "but", "not", "what", "all", "were", "when",
           "can", "said", "there", "each", "which", "their", "will", "about"},
    "pt": {"como", "para", "que", "com", "uma", "mais", "por", "são", "tem",
           "mas", "este", "esta", "muito", "fazer", "novo", "hoje", "dia"},
    "fr": {"les", "des", "pour", "que", "avec", "dans", "une", "sur", "pas",
           "plus", "est", "sont", "mais", "fait", "tout", "très", "cette",
           "comment", "comme", "aussi", "jour", "nouveau"},
    "de": {"und", "der", "die", "das", "ist", "ein", "eine", "mit", "für",
           "auf", "nicht", "sich", "von", "den", "auch", "wie", "noch"},
    "it": {"che", "per", "con", "una", "sono", "del", "della", "più", "come",
           "questo", "questa", "tutto", "anche", "fare", "molto", "nuovo"},
    "ja": set(),
    "ko": set(),
    "ar": set(),
    "ru": set(),
    "zh": set(),
    "hi": set(),
}

# videoDuration mapping para la API
DURATION_FILTER_MAP = {
    "any":    None,           # Sin filtro
    "short":  "short",        # < 4 minutos
    "medium": "medium",       # 4-20 minutos
    "long":   "long",         # > 20 minutos
}

ENDPOINT_COSTS = {
    "search":        100,
    "videos":          1,
    "channels":        1,
    "playlistItems":   1,
}


class YouTubeAPI:

    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        if not self.api_key or self.api_key == "TU_API_KEY_AQUI":
            raise ValueError(
                "YOUTUBE_API_KEY no configurada. Edita el archivo .env."
            )
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ================================================================== #
    #  BÚSQUEDA DE VIDEOS                                                 #
    # ================================================================== #
    def search_videos(
        self,
        query: str = "",
        category_id: str = "0",
        region_code: str = "US",
        language: str = "es",
        order: str = "viewCount",
        max_results: int = 50,
        published_after: Optional[str] = None,
        duration_filter: str = "any",
        page_token: Optional[str] = None,
    ) -> tuple[list[dict], Optional[str]]:
        """
        Busca videos. Retorna (lista_de_videos, next_page_token).
        """
        params = {
            "key":             self.api_key,
            "part":            "snippet",
            "type":            "video",
            "maxResults":      min(max_results, 50),
            "order":           order,
            "relevanceLanguage": language,
        }
        if region_code:
            params["regionCode"] = region_code
        if query:
            params["q"] = query
        if category_id and category_id != "0":
            params["videoCategoryId"] = category_id
        if published_after:
            params["publishedAfter"] = published_after
        if page_token:
            params["pageToken"] = page_token

        # Filtro de duración en la API
        api_duration = DURATION_FILTER_MAP.get(duration_filter)
        if api_duration:
            params["videoDuration"] = api_duration

        data = self._get("search", params)
        items = data.get("items", [])
        next_token = data.get("nextPageToken")

        video_ids = [
            item["id"]["videoId"]
            for item in items
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return [], next_token

        videos = self.get_videos_by_ids(video_ids)
        return videos, next_token

    def get_trending_videos(
        self,
        region_code: str = "US",
        category_id: str = "0",
        max_results: int = 50,
    ) -> list[dict]:
        params = {
            "key":             self.api_key,
            "part":            "snippet,statistics,contentDetails",
            "chart":           "mostPopular",
            "maxResults":      min(max_results, 50),
        }
        if region_code:
            params["regionCode"] = region_code
        if category_id and category_id != "0":
            params["videoCategoryId"] = category_id
        data = self._get("videos", params)
        return data.get("items", [])

    def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 50,
    ) -> list[dict]:
        ch_data = self._get("channels", {
            "key":  self.api_key,
            "part": "contentDetails",
            "id":   channel_id,
        })
        items = ch_data.get("items", [])
        if not items:
            return []

        playlist_id = (
            items[0].get("contentDetails", {})
            .get("relatedPlaylists", {}).get("uploads", "")
        )
        if not playlist_id:
            return []

        video_ids = []
        pt = None
        while len(video_ids) < max_results:
            params = {
                "key":        self.api_key,
                "part":       "contentDetails",
                "playlistId": playlist_id,
                "maxResults": min(50, max_results - len(video_ids)),
            }
            if pt:
                params["pageToken"] = pt
            pl_data = self._get("playlistItems", params)
            for item in pl_data.get("items", []):
                vid = item.get("contentDetails", {}).get("videoId")
                if vid:
                    video_ids.append(vid)
            pt = pl_data.get("nextPageToken")
            if not pt:
                break

        return self.get_videos_by_ids(video_ids)

    def get_videos_by_ids(self, video_ids: list[str]) -> list[dict]:
        results = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i: i + 50]
            data = self._get("videos", {
                "key":  self.api_key,
                "part": "snippet,statistics,contentDetails",
                "id":   ",".join(batch),
            })
            results.extend(data.get("items", []))
            time.sleep(0.05)
        return results

    def get_channel_info(self, channel_id: str) -> Optional[dict]:
        data = self._get("channels", {
            "key":  self.api_key,
            "part": "snippet,statistics,contentDetails",
            "id":   channel_id,
        })
        items = data.get("items", [])
        return items[0] if items else None

    # ================================================================== #
    #  BÚSQUEDA DE CANALES                                                #
    # ================================================================== #
    def search_channels(
        self,
        query: str = "",
        region_code: str = "US",
        language: str = "es",
        max_results: int = 25,
        order: str = "relevance",
        page_token: Optional[str] = None,
    ) -> tuple[list[dict], Optional[str]]:
        """
        Busca CANALES por keyword. Retorna (lista_canales_raw, next_token).
        Costo: 100 unidades (search.list con type=channel).
        """
        params = {
            "key":               self.api_key,
            "part":              "snippet",
            "type":              "channel",
            "maxResults":        min(max_results, 50),
            "order":             order,
            "relevanceLanguage": language,
        }
        if region_code:
            params["regionCode"] = region_code
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token

        data = self._get("search", params)
        items = data.get("items", [])
        next_token = data.get("nextPageToken")

        channel_ids = [
            item["id"]["channelId"]
            for item in items
            if item.get("id", {}).get("channelId")
        ]
        if not channel_ids:
            return [], next_token

        details = self.get_channels_by_ids(channel_ids)
        return details, next_token

    def get_channels_by_ids(self, channel_ids: list[str]) -> list[dict]:
        results = []
        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i: i + 50]
            data = self._get("channels", {
                "key":  self.api_key,
                "part": "snippet,statistics,contentDetails",
                "id":   ",".join(batch),
            })
            results.extend(data.get("items", []))
            time.sleep(0.05)
        return results

    # ================================================================== #
    #  VALIDACIÓN DE IDIOMA (MEJORADA)                                    #
    # ================================================================== #
    @staticmethod
    def validate_language(title: str, description: str, target_lang: str) -> bool:
        """
        Valida si un texto está en el idioma objetivo.
        
        Estrategia en 3 capas:
        1. Detección automática con langdetect (si está disponible)
        2. Detección por scripts únicos (japonés, árabe, etc.)
        3. Heurística de palabras comunes (fallback)
        """
        if not target_lang:
            return True

        text = (title + " " + (description or "")).lower().strip()
        if not text:
            return True

        # ── CAPA 1: Detección automática con langdetect ──────────────
        if HAS_LANGDETECT and len(text) >= 20:
            try:
                detected = detect(text)
                detected_base = detected.split("-")[0]
                target_base = target_lang.split("-")[0]

                if detected_base == target_base:
                    return True

                known_langs = {"es", "en", "pt", "fr", "de", "it",
                               "ja", "ko", "ar", "ru", "zh", "hi",
                               "th", "vi", "pl", "nl", "sv", "tr"}
                if detected_base in known_langs:
                    return False
            except LangDetectException:
                pass
            except Exception:
                pass

        # ── CAPA 2: Scripts únicos ───────────────────────────────────
        pattern = LANGUAGE_CHAR_PATTERNS.get(target_lang)
        if pattern and target_lang in ("ja", "ko", "ar", "ru", "zh", "hi", "th"):
            return bool(re.search(pattern, text))

        # ── CAPA 3: Heurística de palabras comunes ───────────────────
        common = LANGUAGE_COMMON_WORDS.get(target_lang, set())
        if not common:
            return True

        words = set(re.findall(r'\b\w+\b', text))
        target_hits = len(words & common)

        other_langs = {"es", "en", "pt", "fr", "de", "it"} - {target_lang}
        other_hits = 0
        for other in other_langs:
            other_common = LANGUAGE_COMMON_WORDS.get(other, set())
            other_hits = max(other_hits, len(words & other_common))

        if target_hits >= 2 and target_hits >= other_hits:
            return True

        if pattern and re.search(pattern, text):
            return True

        if target_hits == 0 and other_hits == 0:
            return True

        return target_hits >= other_hits

    # ================================================================== #
    #  PARSERS                                                            #
    # ================================================================== #
    @staticmethod
    def parse_video(raw: dict, channel_subs: int = 0, category_label: str = "") -> dict:
        snippet = raw.get("snippet", {})
        stats   = raw.get("statistics", {})
        content = raw.get("contentDetails", {})

        duration = YouTubeAPI._parse_duration(content.get("duration", ""))

        pub_at_str = snippet.get("publishedAt", "")
        pub_at = None
        if pub_at_str:
            try:
                pub_at = datetime.fromisoformat(
                    pub_at_str.replace("Z", "+00:00")
                ).replace(tzinfo=None)
            except Exception:
                pub_at = datetime.utcnow()

        thumbs = snippet.get("thumbnails", {})
        thumb = (
            thumbs.get("maxres", {}).get("url")
            or thumbs.get("high", {}).get("url")
            or thumbs.get("medium", {}).get("url")
            or ""
        )

        views    = int(stats.get("viewCount",    0) or 0)
        likes    = int(stats.get("likeCount",    0) or 0)
        comments = int(stats.get("commentCount", 0) or 0)
        vps      = round(views / channel_subs, 4) if channel_subs > 0 else 0.0

        return {
            "id":               raw.get("id", ""),
            "channel_id":       snippet.get("channelId", ""),
            "channel_title":    snippet.get("channelTitle", ""),
            "title":            snippet.get("title", ""),
            "description":      (snippet.get("description") or "")[:1000],
            "published_at":     pub_at,
            "thumbnail_url":    thumb,
            "duration_seconds": duration,
            "tags":             ",".join(snippet.get("tags", []))[:500],
            "view_count":       views,
            "like_count":       likes,
            "comment_count":    comments,
            "views_per_sub":    vps,
            "category":         snippet.get("categoryId", ""),
            "category_label":   category_label,
            "language":         snippet.get("defaultLanguage", "") or snippet.get("defaultAudioLanguage", ""),  # ← NUEVO
            "default_language": snippet.get("defaultLanguage", ""),
            "default_audio_language": snippet.get("defaultAudioLanguage", ""),
        }


    @staticmethod
    def _parse_duration(iso: str) -> int:
        if not iso:
            return 0
        match = re.match(
            r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso
        )
        if not match:
            return 0
        d, h, m, s = (int(x or 0) for x in match.groups())
        return d * 86400 + h * 3600 + m * 60 + s

    # ================================================================== #
    #  HTTP                                                               #
    # ================================================================== #
    def _get(self, endpoint: str, params: dict, retries: int = 3) -> dict:
        url = f"{BASE_URL}/{endpoint}"
        for attempt in range(retries):
            try:
                resp = self.session.get(url, params=params, timeout=15)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 403:
                    err = resp.json().get("error", {})
                    reason = (err.get("errors") or [{}])[0].get("reason", "")
                    if reason == "quotaExceeded":
                        logger.error("CUOTA DIARIA AGOTADA.")
                        return {}
                    logger.error(f"403: {err.get('message', '')}")
                    return {}
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                logger.error(f"HTTP {resp.status_code}")
                return {}
            except requests.RequestException as e:
                logger.error(f"Red (intento {attempt+1}): {e}")
                time.sleep(1)
        return {}
