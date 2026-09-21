"""
Funciones utilitarias compartidas por toda la app.
Importar SOLO desde aquí para evitar dependencias circulares.
"""
import re


def fmt_number(n) -> str:
    """Formatea número grande: 1234567 → '1.2M'."""
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        return "0"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_duration(seconds: int) -> str:
    """Formatea segundos → MM:SS o HH:MM:SS."""
    try:
        s = int(seconds or 0)
    except (TypeError, ValueError):
        return "0:00"
    if s <= 0:
        return "0:00"
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def score_badge(score: float) -> str:
    """Retorna emoji + etiqueta según el score."""
    if score >= 5:  return "🔥🔥 VIRAL"
    if score >= 3:  return "🔥 OUTLIER FUERTE"
    if score >= 1:  return "⬆️ OUTLIER"
    return "📊 NORMAL"


def score_color(score: float) -> str:
    """Retorna color hex según el score."""
    if score >= 5:  return "#ff6b35"
    if score >= 3:  return "#00d4aa"
    if score >= 1:  return "#ffd166"
    return "#718096"

# ═══════════════════════════════════════════════════════════
# MAPEO DE CATEGORÍAS (nombre ↔ ID)
# ═══════════════════════════════════════════════════════════

# Mismo mapeo que en youtube_api.py
_CATEGORY_NAME_TO_ID = {
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

# Mapeo inverso: ID → Nombre
_CATEGORY_ID_TO_NAME = {v: k for k, v in _CATEGORY_NAME_TO_ID.items()}


def category_name_to_id(name: str) -> str:
    """Convierte nombre de categoría a ID de YouTube."""
    return _CATEGORY_NAME_TO_ID.get(name, "0")


def category_id_to_name(cat_id: str) -> str:
    """Convierte ID de categoría de YouTube a nombre legible."""
    return _CATEGORY_ID_TO_NAME.get(str(cat_id), "Otro")


def migrate_category_labels(session) -> int:
    """
    Migra videos existentes: asigna category_label basado en Channel.category.
    Ejecutar una vez para datos antiguos.
    """
    from core.models import Video, Channel
    from sqlalchemy import select

    videos = session.execute(
        select(Video).where(Video.category_label.is_(None))
    ).scalars().all()

    count = 0
    for v in videos:
        ch = session.get(Channel, v.channel_id)
        if ch and ch.category:
            v.category_label = ch.category
            count += 1

    session.commit()
    return count