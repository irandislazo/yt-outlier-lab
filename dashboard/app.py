"""
Aplicación Dash principal.
Registra todos los callbacks y el routing de páginas.
"""
import os
import sys

# ── Path fix (permite imports desde la raíz) ──────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Salida UTF-8 (evita errores al imprimir emojis en consolas Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html

from core.database import init_db
from dashboard.layout import (
    build_layout,
    page_dashboard,
    page_discovery,
    page_channels,
    page_outliers,
    page_favorites,
    page_ideas,
    page_competitors,
    page_thumbnails,
    page_analytics,
    page_settings,
    COLORS,
)

# ── Inicializar DB ────────────────────────────────────────────────────────
init_db()

# ── Crear app ─────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="YT Outlier Lab 🚀",
    update_title="Cargando...",
    assets_folder="../assets",  # ← AGREGAR ESTA LÍNEA
)

app.layout = build_layout()

# ── API Route para toggle de favoritos ────────────────────────────────
from flask import jsonify

@app.server.route('/api/toggle-favorite/<video_id>')
def toggle_favorite_api(video_id):
    """Endpoint REST para toggle de favoritos. No depende de callbacks de Dash."""
    session = get_session()
    try:
        video = session.get(Video, video_id)
        if not video:
            return jsonify({"success": False, "error": "Video no encontrado"})

        current = bool(video.is_favorite) if video.is_favorite is not None else False
        video.is_favorite = not current
        session.commit()

        return jsonify({
            "success": True,
            "video_id": video_id,
            "is_favorite": video.is_favorite,
        })
    except Exception as e:
        session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        session.close()

# ── API Route: Outliers de un canal específico ────────────────────────
@app.server.route('/api/channel-outliers/<channel_id>')
def channel_outliers_api(channel_id):
    """Retorna los outliers de un canal en formato JSON."""
    session = get_session()
    try:
        ch = session.get(Channel, channel_id)
        if not ch:
            return jsonify({"success": False, "error": "Canal no encontrado"})

        videos = (
            session.query(Video)
            .filter(Video.channel_id == channel_id)
            .filter(Video.outlier_score > 0)
            .order_by(Video.outlier_score.desc())
            .limit(50)
            .all()
        )

        videos_data = []
        for v in videos:
            videos_data.append({
                "id": v.id,
                "title": v.title or "",
                "thumbnail_url": v.thumbnail_url or "",
                "outlier_score": round(v.outlier_score or 0, 2),
                "view_count": v.view_count or 0,
                "like_count": v.like_count or 0,
                "published_at": v.published_at.strftime("%Y-%m-%d") if v.published_at else "",
                "duration_seconds": v.duration_seconds or 0,
                "category_label": v.category_label or "",
                "is_favorite": bool(v.is_favorite) if v.is_favorite is not None else False,
            })

        return jsonify({
            "success": True,
            "channel_id": channel_id,
            "channel_title": ch.title or "",
            "subscriber_count": ch.subscriber_count or 0,
            "videos": videos_data,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        session.close()

# ── API Route: Calcular outliers de un canal específico ──────────────
@app.server.route('/api/compute-channel-outliers/<channel_id>')
def compute_channel_outliers_api(channel_id):
    """
    Calcula los outlier scores de un canal específico bajo demanda.
    Si el canal no tiene videos en la DB, los descarga primero.
    """
    session = get_session()
    try:
        ch = session.get(Channel, channel_id)
        if not ch:
            return jsonify({"success": False, "error": "Canal no encontrado"})

        # Verificar cuántos videos tiene el canal en la DB
        from sqlalchemy import func
        video_count = session.query(func.count(Video.id)).filter(
            Video.channel_id == channel_id
        ).scalar() or 0

        videos_downloaded = 0

        # Si tiene menos de 2 videos, descargar desde la API
        if video_count < 2:
            from core.youtube_api import YouTubeAPI
            api = YouTubeAPI()

            try:
                ch_videos = api.get_channel_videos(channel_id, max_results=30)
                subs = ch.subscriber_count or 0

                for v_raw in ch_videos:
                    parsed = YouTubeAPI.parse_video(
                        v_raw, subs,
                        category_label=ch.category or ""
                    )
                    v_id = parsed.get("id", "")
                    if not v_id:
                        continue

                    existing = session.get(Video, v_id)
                    if not existing:
                        video = Video(id=v_id)
                        session.add(video)
                    else:
                        video = existing

                    for key, value in parsed.items():
                        if hasattr(video, key) and key not in (
                            "default_language", "default_audio_language"
                        ):
                            setattr(video, key, value)

                    # Asignar idioma si no lo tiene
                    if not video.language and ch.language:
                        video.language = ch.language

                    videos_downloaded += 1

                session.commit()

            except Exception as e:
                logger.error(f"Error descargando videos de {ch.title}: {e}")
                # Continuar con los videos existentes si los hay

        # Calcular outliers
        from core.outliers import OutlierEngine
        engine = OutlierEngine()
        count = engine._compute_for_channel(channel_id, session)
        session.commit()

        return jsonify({
            "success": True,
            "channel_id": channel_id,
            "channel_title": ch.title or "",
            "videos_computed": count,
            "videos_downloaded": videos_downloaded,
        })
    except Exception as e:
        session.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        session.close()
        
# ── Routing de páginas ────────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def render_page(pathname):
    routes = {
        "/":            page_dashboard,
        "/discovery":   page_discovery,
        "/channels":    page_channels,
        "/outliers":    page_outliers,
        "/favorites":   page_favorites,
        "/competitors": page_competitors,
        "/thumbnails":  page_thumbnails,
        "/analytics":   page_analytics,
        "/settings":    page_settings,
    }
    page_fn = routes.get(pathname or "/", page_dashboard)
    return page_fn()


# ── NUEVO: Sincronizar filtro global entre sidebar y store ───────────────
@app.callback(
    Output("global-category-store", "data"),
    Input("global-category-filter", "value"),
    prevent_initial_call=True,
)
def update_global_category(category):
    return category or "Todos"


@app.callback(
    Output("global-category-filter", "value", allow_duplicate=True),
    Input("global-category-store", "data"),
    prevent_initial_call=True,
)
def sync_global_filter_ui(stored_value):
    return stored_value or "Todos"


# ── Dashboard callbacks ───────────────────────────────────────────────────
from core.database import get_session
from core.models import Channel, Video, TopicCluster, QuotaLog
from sqlalchemy import func
from utils_app import fmt_number
from dashboard.layout import metric_card


@app.callback(
    Output("dashboard-metrics",      "children"),
    Output("dashboard-top-outliers", "children"),
    Output("dashboard-top-channels", "children"),
    Output("dashboard-score-dist",   "figure"),
    Output("dashboard-category-pie", "figure"),
    Input("dashboard-refresh",       "n_intervals"),
    Input("global-category-store",   "data"),
)
def update_dashboard(_, global_category):
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd

    session = get_session()
    try:
        # ── Filtro global por categoría ──────────────────────────────
        cat_filter = (global_category or "Todos").strip()
        apply_cat = cat_filter and cat_filter != "Todos"

        # Conteos generales (respetando filtro global)
        q_channels = session.query(func.count(Channel.id))
        q_videos   = session.query(func.count(Video.id))
        q_outliers = session.query(func.count(Video.id)).filter(Video.outlier_score >= 1.0)

        if apply_cat:
            q_channels = q_channels.filter(Channel.category == cat_filter)
            q_videos   = q_videos.filter(Video.category == cat_filter)
            q_outliers = q_outliers.filter(Video.category == cat_filter)

        n_channels = q_channels.scalar() or 0
        n_videos   = q_videos.scalar() or 0
        n_outliers = q_outliers.scalar() or 0
        n_clusters = session.query(func.count(TopicCluster.id)).scalar() or 0
        quota_used = QuotaLog.get_used_today(session)

        # Indicador de filtro activo
        filter_note = f"  ·  🎯 Filtro: {cat_filter}" if apply_cat else ""

        metrics = dbc.Row([
            dbc.Col(metric_card("Canales",   fmt_number(n_channels), "📺",
                                COLORS["primary"],
                                subtitle=filter_note if apply_cat else ""),
                    width=12//5),
            dbc.Col(metric_card("Videos",    fmt_number(n_videos),   "🎬",
                                COLORS["success"]), width=12//5),
            dbc.Col(metric_card("Outliers",  fmt_number(n_outliers), "🔥",
                                COLORS["viral"]),   width=12//5),
            dbc.Col(metric_card("Clusters",  str(n_clusters),        "🏷️",
                                COLORS["warning"]), width=12//5),
            dbc.Col(metric_card("Cuota hoy",
                                f"{quota_used:,}/10K",               "📊",
                                COLORS["danger"] if quota_used > 8000 else COLORS["muted"],
                                f"{round(quota_used/10000*100,1)}% usado"),
                    width=12//5),
        ], className="g-3 mb-3")

        # Top outliers (respetando filtro global)
        q_top = session.query(Video).filter(Video.outlier_score >= 1.0)
        if apply_cat:
            q_top = q_top.filter(Video.category == cat_filter)
        top_vids = q_top.order_by(Video.outlier_score.desc()).limit(10).all()

        outlier_rows = []
        for i, v in enumerate(top_vids, 1):
            sc  = v.outlier_score or 0
            col = COLORS["viral"] if sc >= 5 else COLORS["success"] if sc >= 2 else COLORS["warning"]
            outlier_rows.append(html.Div([
                html.Div([
                    html.Span(f"#{i}", style={"color": COLORS["muted"],
                                               "fontSize": "0.75rem",
                                               "width":    "24px",
                                               "display":  "inline-block"}),
                    html.A(
                        (v.title or "")[:50] + ("..." if len(v.title or "") > 50 else ""),
                        href=f"https://youtube.com/watch?v={v.id}",
                        target="_blank",
                        style={"color": COLORS["text"], "fontSize": "0.82rem",
                               "fontWeight": "600", "textDecoration": "none",
                               "flex": 1},
                    ),
                    html.Span(
                        f"{sc:.1f}x",
                        style={
                            "background":   f"{col}20",
                            "color":        col,
                            "border":       f"1px solid {col}",
                            "borderRadius": "10px",
                            "padding":      "1px 7px",
                            "fontSize":     "0.72rem",
                            "fontWeight":   "700",
                            "whiteSpace":   "nowrap",
                        },
                    ),
                ], style={"display": "flex", "gap": "8px",
                           "alignItems": "center", "flex": 1}),
                html.P(
                    f"📺 {v.channel_title or ''}  ·  👁️ {fmt_number(v.view_count or 0)}",
                    style={"color": COLORS["muted"], "fontSize": "0.72rem",
                           "margin": "2px 0 0 32px"},
                ),
            ], style={"padding": "8px 0",
                       "borderBottom": f"1px solid {COLORS['border']}"}))

        top_outliers_el = html.Div(outlier_rows) if outlier_rows else \
            html.P("Sin outliers aún. Ejecuta el Auto-Descubrimiento." + filter_note,
                   style={"color": COLORS["muted"]})

        # Top canales (respetando filtro global)
        q_ch = session.query(Channel)
        if apply_cat:
            q_ch = q_ch.filter(Channel.category == cat_filter)
        top_chs = q_ch.order_by(Channel.subscriber_count.desc()).limit(8).all()

        ch_rows = []
        for ch in top_chs:
            ch_rows.append(html.Div([
                html.Div([
                    html.Img(
                        src=ch.thumbnail_url or "",
                        style={"width": "30px", "height": "30px",
                               "borderRadius": "50%", "objectFit": "cover"},
                    ) if ch.thumbnail_url else html.Div(
                        "📺",
                        style={"width": "30px", "height": "30px",
                               "background": COLORS["surface2"],
                               "borderRadius": "50%",
                               "display": "flex", "alignItems": "center",
                               "justifyContent": "center"}
                    ),
                    html.Div([
                        html.P(ch.title[:28], style={"color": COLORS["text"],
                                                      "margin": "0",
                                                      "fontSize": "0.82rem",
                                                      "fontWeight": "600"}),
                        html.P(fmt_number(ch.subscriber_count or 0) + " subs",
                               style={"color": COLORS["muted"], "margin": "0",
                                      "fontSize": "0.72rem"}),
                    ]),
                ], style={"display": "flex", "gap": "8px", "alignItems": "center"}),
            ], style={"padding": "8px 0",
                       "borderBottom": f"1px solid {COLORS['border']}"}))

        top_channels_el = html.Div(ch_rows) if ch_rows else \
            html.P("Sin canales aún.", style={"color": COLORS["muted"]})

        # Gráfico distribución de scores (con filtro)
        q_scores = session.query(Video.outlier_score).filter(Video.outlier_score > 0)
        if apply_cat:
            q_scores = q_scores.filter(Video.category == cat_filter)
        scores = q_scores.limit(500).all()

        if scores:
            df_s = pd.DataFrame([{"Score": s[0]} for s in scores])
            fig_dist = px.histogram(
                df_s, x="Score", nbins=30,
                color_discrete_sequence=[COLORS["primary"]],
                template="plotly_dark",
            )
        else:
            fig_dist = go.Figure()

        fig_dist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=10, t=10, b=30),
        )

        # Gráfico categorías (siempre muestra todas)
        cats = session.query(Video.category, func.count(Video.id)) \
            .filter(Video.category.isnot(None)) \
            .group_by(Video.category).all()

        if cats:
            df_c = pd.DataFrame(cats, columns=["Categoría", "Videos"])
            fig_cat = px.pie(
                df_c, names="Categoría", values="Videos",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                template="plotly_dark",
            )
        else:
            fig_cat = go.Figure()

        fig_cat.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
        )

        return metrics, top_outliers_el, top_channels_el, fig_dist, fig_cat

    except Exception as e:
        err = dbc.Alert(f"Error: {e}", color="danger")
        ef  = go.Figure()
        ef.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        return err, html.Div(), html.Div(), ef, ef
    finally:
        session.close()


# ── Sidebar: cuota y stats ────────────────────────────────────────────────
@app.callback(
    Output("sidebar-quota-display", "children"),
    Output("sidebar-db-stats",      "children"),
    Input("dashboard-refresh",      "n_intervals"),
    Input("global-category-store",  "data"),
)
def update_sidebar_stats(_, global_category):
    session = get_session()
    try:
        used  = QuotaLog.get_used_today(session)
        pct   = round(used / 10000 * 100, 1)

        cat_filter = (global_category or "Todos").strip()
        apply_cat = cat_filter and cat_filter != "Todos"

        q_ch  = session.query(func.count(Channel.id))
        q_vid = session.query(func.count(Video.id))
        if apply_cat:
            q_ch  = q_ch.filter(Channel.category == cat_filter)
            q_vid = q_vid.filter(Video.category == cat_filter)

        n_ch  = q_ch.scalar() or 0
        n_vid = q_vid.scalar() or 0

        quota_el = html.Div([
            html.P("📊 Cuota API",
                   style={"color": COLORS["muted"], "fontSize": "0.72rem",
                          "fontWeight": "700", "textTransform": "uppercase",
                          "margin": "0 0 4px"}),
            dbc.Progress(
                value=pct,
                color="danger" if pct > 80 else "warning" if pct > 50 else "success",
                style={"height": "5px", "borderRadius": "3px", "marginBottom": "4px"},
            ),
            html.P(f"{used:,} / 10,000 unidades",
                   style={"color": COLORS["muted"], "fontSize": "0.7rem", "margin": "0"}),
        ])

        filter_hint = f"  ·  🎯 {cat_filter}" if apply_cat else ""
        db_el = html.Div([
            html.P(
                f"📺 {n_ch} canales  ·  🎬 {fmt_number(n_vid)} videos{filter_hint}",
                style={"color": COLORS["muted"], "fontSize": "0.7rem",
                       "margin": "8px 0 0"},
            ),
        ])

        return quota_el, db_el

    except Exception:
        return html.Div(), html.Div()
    finally:
        session.close()


# ── Thumbnails callbacks ──────────────────────────────────────────────────
@app.callback(
    Output("thumb-brightness-chart", "figure"),
    Output("thumb-face-chart",       "figure"),
    Output("thumb-text-chart",       "figure"),
    Output("thumb-gallery",          "children"),
    Output("thumb-metrics",          "children"),
    Input("thumb-refresh",           "n_intervals"),
    Input("thumb-min-score",         "value"),
    Input("thumb-filter",            "value"),
    Input("thumb-category",          "value"),
    Input("thumb-language",          "value"),
    Input("thumb-limit",             "value"),
    Input("thumb-sort",              "value"),
)
def update_thumbnails(_, min_score, filt, category, language, thumb_limit, sort_by):
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd

    session = get_session()
    try:
        q = session.query(Video).filter(
            Video.outlier_score >= (min_score or 0),
            Video.thumbnail_url.isnot(None),
            Video.thumb_brightness.isnot(None),
        )

        # Filtro por categoría
        if category and category != "all":
            q = q.filter(Video.category_label == category)

        # Filtro por idioma
        if language and language != "all":
            q = q.filter(Video.language == language)

        # Filtro especial
        if filt == "outliers":
            q = q.filter(Video.outlier_score >= 1.0)
        elif filt == "face":
            q = q.filter(Video.thumb_has_face == True)
        elif filt == "text":
            q = q.filter(Video.thumb_text_detected == True)
        elif filt == "no_face":
            q = q.filter(Video.thumb_has_face == False)
        elif filt == "no_text":
            q = q.filter(Video.thumb_text_detected == False)
        elif filt == "bright":
            q = q.filter(Video.thumb_brightness > 150)
        elif filt == "dark":
            q = q.filter(Video.thumb_brightness < 80)

        # Ordenar
        if sort_by == "view_count":
            q = q.order_by(Video.view_count.desc())
        elif sort_by == "thumb_brightness":
            q = q.order_by(Video.thumb_brightness.desc())
        else:
            q = q.order_by(Video.outlier_score.desc())

        videos = q.limit(int(thumb_limit or 100)).all()

        if not videos:
            ef = _empty_fig_simple()
            gallery = html.P(
                "Sin thumbnails analizados. Usa el panel de análisis de arriba.",
                style={"color": COLORS["muted"]},
            )
            empty_metrics = html.Div()
            return ef, ef, ef, gallery, empty_metrics

        df = pd.DataFrame([{
            "Score":   v.outlier_score or 0,
            "Brillo":  v.thumb_brightness or 0,
            "Cara":    "Con cara" if v.thumb_has_face else "Sin cara",
            "Texto":   "Con texto" if v.thumb_text_detected else "Sin texto",
            "Tipo":    "Outlier" if (v.outlier_score or 0) >= 1 else "Normal",
            "Views":   v.view_count or 0,
        } for v in videos])

        # ── Métricas ─────────────────────────────────────────────────
        total = len(videos)
        avg_brightness = df["Brillo"].mean() if total else 0
        face_pct = (df["Cara"] == "Con cara").sum() / total * 100 if total else 0
        text_pct = (df["Texto"] == "Con texto").sum() / total * 100 if total else 0
        outlier_avg_score = df[df["Tipo"] == "Outlier"]["Score"].mean() if total else 0
        normal_avg_score = df[df["Tipo"] == "Normal"]["Score"].mean() if total else 0

        metrics = dbc.Row([
            dbc.Col(_thumb_metric("🖼️ Analizados", str(total), COLORS["primary"]), width=2),
            dbc.Col(_thumb_metric("☀️ Brillo prom", f"{avg_brightness:.0f}", COLORS["warning"]), width=2),
            dbc.Col(_thumb_metric("👤 Con cara", f"{face_pct:.1f}%", COLORS["success"]), width=2),
            dbc.Col(_thumb_metric("📝 Con texto", f"{text_pct:.1f}%", COLORS["viral"]), width=2),
            dbc.Col(_thumb_metric("🔥 Score outliers", f"{outlier_avg_score:.2f}x", COLORS["viral"]), width=2),
            dbc.Col(_thumb_metric("📊 Score normales", f"{normal_avg_score:.2f}x", COLORS["muted"]), width=2),
        ], className="g-2 mb-3")

        # ── Gráficos ─────────────────────────────────────────────────
        def mini_fig(data, x, y, title, colors_map):
            fig = px.bar(
                data.groupby(x)[y].mean().reset_index(),
                x=x, y=y, color=x,
                color_discrete_map=colors_map,
                template="plotly_dark",
                title=title,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            return fig

        fig_br = px.scatter(
            df, x="Brillo", y="Score", color="Tipo",
            color_discrete_map={"Outlier": COLORS["success"],
                                 "Normal":  COLORS["muted"]},
            template="plotly_dark", title="Brillo vs Score",
        )
        fig_br.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=40, b=10),
        )

        fig_face = mini_fig(
            df, "Cara", "Score", "Cara → Score promedio",
            {"Con cara": COLORS["success"], "Sin cara": COLORS["danger"]},
        )
        fig_text = mini_fig(
            df, "Texto", "Score", "Texto → Score promedio",
            {"Con texto": COLORS["warning"], "Sin texto": COLORS["muted"]},
        )

        # ── Galería ──────────────────────────────────────────────────
        gallery_videos = videos[:48]
        grid_cols = 6
        gallery_rows = []
        for i in range(0, len(gallery_videos), grid_cols):
            row_vids = gallery_videos[i: i + grid_cols]
            row_cols  = []
            for v in row_vids:
                sc     = v.outlier_score or 0
                sc_col = (
                    COLORS["viral"]   if sc >= 5 else
                    COLORS["success"] if sc >= 2 else
                    COLORS["warning"] if sc >= 1 else
                    COLORS["muted"]
                )
                row_cols.append(
                    dbc.Col([
                        html.A([
                            html.Img(
                                src=v.thumbnail_url or "",
                                style={"width": "100%", "borderRadius": "6px",
                                       "display": "block"},
                            ),
                            html.Div([
                                html.Span(
                                    f"{sc:.1f}x",
                                    style={
                                        "background":   f"{sc_col}CC",
                                        "color":        "white",
                                        "borderRadius": "4px",
                                        "padding":      "1px 6px",
                                        "fontSize":     "0.7rem",
                                        "fontWeight":   "700",
                                    },
                                ),
                                html.Span(
                                    "👤" if v.thumb_has_face else "",
                                    style={"marginLeft": "4px", "fontSize": "0.7rem"},
                                ),
                                html.Span(
                                    "📝" if v.thumb_text_detected else "",
                                    style={"marginLeft": "2px", "fontSize": "0.7rem"},
                                ),
                            ], style={
                                "position":   "absolute",
                                "bottom":     "4px",
                                "left":       "4px",
                                "display":    "flex",
                                "alignItems": "center",
                                "gap":        "2px",
                            }),
                        ], href=f"https://youtube.com/watch?v={v.id}",
                           target="_blank",
                           style={"position": "relative", "display": "block"}),
                        html.P(
                            (v.title or "")[:30] + ("..." if len(v.title or "") > 30 else ""),
                            style={"color": COLORS["muted"],
                                   "fontSize": "0.68rem",
                                   "margin":   "4px 0 8px",
                                   "overflow": "hidden",
                                   "textOverflow": "ellipsis",
                                   "whiteSpace": "nowrap"},
                        ),
                    ], width=2)
                )
            gallery_rows.append(dbc.Row(row_cols, className="g-2 mb-1"))

        return fig_br, fig_face, fig_text, html.Div(gallery_rows), metrics

    except Exception as e:
        ef = _empty_fig_simple()
        return ef, ef, ef, dbc.Alert(f"Error: {e}", color="danger"), html.Div()
    finally:
        session.close()


def _thumb_metric(label, value, color):
    return html.Div([
        html.P(label, style={"color": COLORS["muted"], "margin": "0",
                              "fontSize": "0.75rem", "fontWeight": "600",
                              "textTransform": "uppercase"}),
        html.H4(value, style={"color": color, "margin": "2px 0 0",
                               "fontWeight": "800"}),
    ], style={
        "background": COLORS["surface"],
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "10px",
        "padding": "12px 16px",
    })


def _empty_fig_simple():
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False}, yaxis={"visible": False},
        annotations=[{"text": "Sin datos", "xref": "paper", "yref": "paper",
                       "x": 0.5, "y": 0.5, "showarrow": False,
                       "font": {"color": "#718096"}}],
    )
    return fig


# ── Settings callbacks ────────────────────────────────────────────────────
@app.callback(
    Output("settings-key-status",    "children"),
    Output("settings-system-status", "children"),
    Input("settings-verify-key",     "n_clicks"),
    Input("url",                     "pathname"),
    State("settings-api-key", "value"),
    prevent_initial_call=True,
)
def settings_callbacks(n_verify, pathname, api_key_input):
    from dash import ctx
    import requests as req
    session = get_session()

    triggered = ctx.triggered_id
    key_status = html.Div()

    if triggered == "settings-verify-key" and api_key_input:
        try:
            r = req.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"key": api_key_input, "part": "id",
                        "chart": "mostPopular", "maxResults": "1"},
                timeout=8,
            )
            if r.status_code == 200:
                key_status = dbc.Alert("✅ API Key válida.", color="success")
            elif r.status_code == 400:
                key_status = dbc.Alert("❌ API Key inválida.", color="danger")
            else:
                key_status = dbc.Alert(f"⚠️ HTTP {r.status_code}", color="warning")
        except Exception as e:
            key_status = dbc.Alert(f"Error: {e}", color="danger")

    # Estado del sistema
    try:
        from sqlalchemy import func
        n_ch  = session.query(func.count(Channel.id)).scalar() or 0
        n_vid = session.query(func.count(Video.id)).scalar() or 0
        n_cl  = session.query(func.count(TopicCluster.id)).scalar() or 0
        quot  = QuotaLog.get_used_today(session)
        import os
        from pathlib import Path
        db_size = Path("yt_outlier_lab.db").stat().st_size / 1024 if Path("yt_outlier_lab.db").exists() else 0

        sys_status = html.Div([
            _sys_row("📺 Canales en DB",      str(n_ch)),
            _sys_row("🎬 Videos en DB",       fmt_number(n_vid)),
            _sys_row("🏷️ Clusters de temas",  str(n_cl)),
            _sys_row("📊 Cuota usada hoy",    f"{quot:,} / 10,000"),
            _sys_row("💾 Tamaño de DB",       f"{db_size:.1f} KB"),
            _sys_row("🐍 Python",             sys.version.split()[0]),
        ])
    except Exception as e:
        sys_status = dbc.Alert(f"Error: {e}", color="danger")
    finally:
        session.close()

    return key_status, sys_status


@app.callback(
    Output("settings-action-result", "children"),
    Input("settings-clean-btn",      "n_clicks"),
    Input("settings-reset-btn",      "n_clicks"),
    prevent_initial_call=True,
)
def settings_actions(clean, reset):
    from dash import ctx
    triggered = ctx.triggered_id
    session   = get_session()

    try:
        if triggered == "settings-clean-btn":
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=30)
            n = session.query(Video).filter(Video.created_at < cutoff).delete()
            session.commit()
            return dbc.Alert(f"✅ {n} videos eliminados.", color="success")

        elif triggered == "settings-reset-btn":
            session.query(Video).delete()
            session.query(Channel).delete()
            session.query(TopicCluster).delete()
            session.commit()
            return dbc.Alert("✅ Base de datos limpiada.", color="warning")

    except Exception as e:
        session.rollback()
        return dbc.Alert(f"❌ {e}", color="danger")
    finally:
        session.close()

    return html.Div()


def _sys_row(label, value):
    return html.Div([
        html.Span(label, style={"color": COLORS["muted"], "fontSize": "0.82rem"}),
        html.Span(value, style={"color": COLORS["text"], "fontWeight": "600",
                                 "fontSize": "0.82rem"}),
    ], style={"display": "flex", "justifyContent": "space-between",
               "padding": "8px 0",
               "borderBottom": f"1px solid {COLORS['border']}"})



# ── Análisis de Thumbnails (nuevo) ──────────────────────────────────────
import threading

_thumb_analyze_state = {
    "running": False,
    "progress": 0,
    "message": "Listo para analizar.",
    "results": None,
}

@app.callback(
    Output("thumb-analyze-store", "data"),
    Output("thumb-analyze-poll",  "disabled"),
    Output("thumb-analyze-btn",   "disabled"),
    Input("thumb-analyze-btn",    "n_clicks"),
    State("thumb-analyze-min-score", "value"),
    State("thumb-analyze-category",  "value"),
    State("thumb-analyze-limit",     "value"),
    State("thumb-analyze-options",   "value"),
    prevent_initial_call=True,
)
def start_thumb_analysis(n_clicks, min_score, category, limit, options):
    if not n_clicks or _thumb_analyze_state["running"]:
        return no_update, no_update, no_update

    _thumb_analyze_state["running"]  = True
    _thumb_analyze_state["progress"] = 0
    _thumb_analyze_state["message"]  = "🚀 Iniciando análisis de thumbnails..."
    _thumb_analyze_state["results"]  = None

    def progress_cb(pct, msg):
        _thumb_analyze_state["progress"] = pct
        _thumb_analyze_state["message"]  = msg

    def run():
        try:
            from core.thumbnails import ThumbnailEngine
            session = get_session()
            engine = ThumbnailEngine()

            cat_filter = None
            if category and category != "all":
                cat_filter = category

            results = engine.run_filtered(
                session,
                limit=int(limit or 50),
                min_score=float(min_score or 0),
                category_label=cat_filter,
                only_outliers="only_outliers" in (options or []),
                progress_callback=progress_cb,
            )
            _thumb_analyze_state["results"] = results
            session.close()
        except Exception as e:
            _thumb_analyze_state["message"] = f"❌ Error: {e}"
        finally:
            _thumb_analyze_state["running"]  = False
            _thumb_analyze_state["progress"] = 100

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return {"running": True}, False, True


@app.callback(
    Output("thumb-analyze-status",   "children"),
    Output("thumb-analyze-progress", "value"),
    Output("thumb-analyze-results",  "children"),
    Output("thumb-analyze-poll",     "disabled",  allow_duplicate=True),
    Output("thumb-analyze-btn",      "disabled",  allow_duplicate=True),
    Input("thumb-analyze-poll",      "n_intervals"),
    prevent_initial_call=True,
)
def poll_thumb_analysis(n):
    state   = _thumb_analyze_state
    running = state["running"]
    pct     = state["progress"]
    msg     = state["message"]

    results_el = html.Div()

    if state["results"]:
        r = state["results"]
        results_el = dbc.Alert([
            html.Strong("✅ Análisis completado: "),
            html.Span(f"{r['analyzed']} analizados · "
                      f"📊 {r['total_selected']} en total · "
                      f"⏭️ {r['skipped_already_done']} ya tenían análisis · "
                      f"❌ {r['errors']} errores"),
        ], color="success", dismissable=True)

    return msg, pct, results_el, not running, running

# ── Registrar callbacks de módulos ────────────────────────────────────────
from dashboard.callbacks import (
    discovery_cb, outliers_cb, ideas_cb, competitors_cb, analytics_cb, channels_cb,favorites_cb,
)

discovery_cb.register_callbacks(app)
outliers_cb.register_callbacks(app)
favorites_cb.register_callbacks(app)
competitors_cb.register_callbacks(app)
analytics_cb.register_callbacks(app)
channels_cb.register_callbacks(app)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)