"""Callbacks de la página Outliers."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, html, dcc, no_update
import dash_bootstrap_components as dbc
from datetime import datetime  # ← AGREGAR

from core.database import get_session
from core.models import Video, Channel
from core.outliers import OutlierEngine
from core.youtube_api import YOUTUBE_CATEGORIES, LANGUAGES, REGIONS  # ← ACTUALIZAR
from dashboard.layout import COLORS, CARD
from utils_app import fmt_number, fmt_duration, score_badge, category_name_to_id


def register_callbacks(app):

    @app.callback(
        Output("out-metrics",      "children"),
        Output("out-scatter",      "figure"),
        Output("out-histogram",    "figure"),
        Output("out-videos-list",  "children"),
        Input("out-refresh",       "n_intervals"),
        Input("out-min-score",     "value"),
        Input("out-min-views",     "value"),
        Input("out-duration",      "value"),
        Input("out-sort",          "value"),
        Input("out-limit",         "value"),
        Input("out-category",      "value"),
        Input("out-language",      "value"),
        Input("out-region",        "value"),
        Input("out-max-subs",      "value"),
    )
    def update_outliers(_, min_score, min_views, duration, sort_col, limit,
                        category, video_language, channel_region, max_subs):
        session = get_session()
        try:
            from core.models import Channel

            selected_limit = int(limit or 25)

            # ── Construir parámetros de consulta SQL ──────────────────
            query_params = {
                "limit": selected_limit,
                "min_score": float(min_score or 0),
                "min_views": int(min_views or 0),
            }

            if category and category != "all":
                query_params["category_label"] = category

            if video_language and video_language != "all":
                query_params["language"] = video_language

            engine = OutlierEngine()
            videos = engine.get_top_outliers(session, **query_params)

            # ── Cache de canales para evitar queries repetidas ────────
            channel_cache = {}

            def get_channel(ch_id):
                if ch_id not in channel_cache:
                    channel_cache[ch_id] = session.get(Channel, ch_id)
                return channel_cache[ch_id]

            # ── Filtrar por país del canal ────────────────────────────
            if channel_region and channel_region != "all":
                videos = [
                    v for v in videos
                    if (lambda ch: ch and (ch.country or "") == channel_region)(
                        get_channel(v.channel_id)
                    )
                ]

            # ── NUEVO: Filtrar por suscriptores máximos del canal ─────
            if max_subs and int(max_subs) > 0:
                max_subs_val = int(max_subs)
                videos = [
                    v for v in videos
                    if (lambda ch: ch and (ch.subscriber_count or 0) <= max_subs_val)(
                        get_channel(v.channel_id)
                    )
                ]

            # ── Filtro duración ───────────────────────────────────────
            if duration == "short":
                videos = [v for v in videos if (v.duration_seconds or 0) <= 60]
            elif duration == "medium":
                videos = [v for v in videos if 60 < (v.duration_seconds or 0) <= 300]
            elif duration == "mid_short":
                videos = [v for v in videos if 180 <= (v.duration_seconds or 0) <= 480]
            elif duration == "long":
                videos = [v for v in videos if 300 < (v.duration_seconds or 0) <= 1200]
            elif duration == "vlong":
                videos = [v for v in videos if (v.duration_seconds or 0) > 1200]

            # ── Ordenar ───────────────────────────────────────────────
            if sort_col == "published_at":
                videos = sorted(
                    videos,
                    key=lambda v: v.published_at or datetime.min,
                    reverse=True,
                )
            else:
                videos = sorted(
                    videos,
                    key=lambda v: getattr(v, sort_col, 0) or 0,
                    reverse=True,
                )

            # Limitar al resultado final
            videos = videos[:selected_limit]

            if not videos:
                empty_msg = "No hay outliers con estos filtros."
                if category and category != "all":
                    empty_msg += f" (Categoría: {category})"
                if video_language and video_language != "all":
                    empty_msg += f" (Idioma: {video_language})"
                if channel_region and channel_region != "all":
                    empty_msg += f" (País: {channel_region})"
                if max_subs and int(max_subs) > 0:
                    empty_msg += f" (Subs ≤ {fmt_number(max_subs)})"
                empty_msg += " Intenta ampliar los filtros o el Auto-Descubrimiento."
                empty = html.Div(
                    empty_msg,
                    style={"color": COLORS["muted"], "padding": "40px",
                           "textAlign": "center"},
                )
                return html.Div(), _empty_fig(), _empty_fig(), empty

            # ── Métricas rápidas ──────────────────────────────────────
            total_views = sum(v.view_count or 0 for v in videos)
            avg_score   = sum(v.outlier_score or 0 for v in videos) / len(videos)
            max_score   = max(v.outlier_score or 0 for v in videos)

            filter_badges = []
            if category and category != "all":
                filter_badges.append(f"🎯 {category}")
            if video_language and video_language != "all":
                filter_badges.append(f"🗣️ {video_language}")
            if channel_region and channel_region != "all":
                filter_badges.append(f"🌍 {channel_region}")
            if max_subs and int(max_subs) > 0:
                filter_badges.append(f"👥 ≤{fmt_number(max_subs)} subs")

            filter_summary = html.Div()
            if filter_badges:
                filter_summary = html.Div([
                    html.Span(badge, style={
                        "background": f"{COLORS['primary']}20",
                        "color": COLORS["primary"],
                        "padding": "4px 10px", "borderRadius": "10px",
                        "fontSize": "0.78rem", "fontWeight": "700",
                        "marginLeft": "8px",
                    }) for badge in filter_badges
                ], style={"display": "inline-block"})

            metrics = html.Div([
                html.Div([
                    html.H6("Resumen de Outliers",
                            style={"color": COLORS["text"], "margin": "0",
                                   "display": "inline-block"}),
                    filter_summary,
                ], style={"marginBottom": "12px"}),
                dbc.Row([
                    dbc.Col(_mini_metric("🎬 Videos",     str(len(videos)),        COLORS["primary"]), width=3),
                    dbc.Col(_mini_metric("📈 Score prom", f"{avg_score:.2f}x",     COLORS["success"]), width=3),
                    dbc.Col(_mini_metric("🏆 Score máx",  f"{max_score:.2f}x",     COLORS["viral"]),   width=3),
                    dbc.Col(_mini_metric("👁️ Views total", fmt_number(total_views), COLORS["warning"]), width=3),
                ], className="g-2 mb-3"),
            ])

            # ── DataFrame para gráficos ──────────────────────────────
            chart_limit = min(len(videos), 200)
            df = pd.DataFrame([{
                "Título":   v.title[:45] + "..." if len(v.title or "") > 45 else v.title,
                "Score":    round(v.outlier_score or 0, 2),
                "Views":    v.view_count or 0,
                "V/hora":   round(v.views_per_hour or 0, 1),
                "Canal":    v.channel_title or v.channel_id,
                "Duración": fmt_duration(v.duration_seconds or 0),
                "Idioma":   v.language or "—",
            } for v in videos[:chart_limit]])

            # Scatter
            fig_scatter = px.scatter(
                df, x="Views", y="Score",
                color="Score", size="Views",
                hover_name="Título", hover_data=["Canal", "V/hora", "Idioma"],
                color_continuous_scale="RdYlGn",
                log_x=True,
                template="plotly_dark",
            )
            fig_scatter.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(l=30, r=10, t=10, b=30),
            )

            # Histograma
            fig_hist = px.histogram(
                df, x="Score", nbins=20,
                color_discrete_sequence=[COLORS["primary"]],
                template="plotly_dark",
            )
            fig_hist.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=30, r=10, t=10, b=30),
            )

            # ── Advertencia de rendimiento ───────────────────────────
            perf_warning = html.Div()
            if selected_limit >= 200:
                perf_warning = html.Div([
                    html.Span("⚠️ ", style={"fontSize": "1rem"}),
                    html.Span(
                        f"Mostrando {selected_limit} videos. "
                        "La carga puede ser más lenta de lo habitual.",
                        style={"color": COLORS["warning"], "fontSize": "0.8rem"},
                    ),
                ], style={
                    "background": f"{COLORS['warning']}15",
                    "border": f"1px solid {COLORS['warning']}",
                    "borderRadius": "8px",
                    "padding": "8px 14px",
                    "marginBottom": "14px",
                })

            # ── Cards de videos ──────────────────────────────────────
            cards = []
            for v in videos:
                sc     = v.outlier_score or 0
                sc_col = _score_col(sc)
                sc_lbl = (
                    "🔥🔥 VIRAL"    if sc >= 5 else
                    "🔥 OUTLIER"   if sc >= 2 else
                    "⬆️ BUENO"     if sc >= 1 else
                    "📊 NORMAL"
                )
                yt_url = f"https://youtube.com/watch?v={v.id}"

                # Obtener info del canal para badge de suscriptores
                ch = get_channel(v.channel_id)
                ch_subs = ch.subscriber_count if ch else 0

                extra_badges = []
                if v.category_label:
                    extra_badges.append(html.Span(
                        f"🏷️ {v.category_label}",
                        style={"background": f"{COLORS['primary']}20",
                               "color": COLORS["primary"],
                               "borderRadius": "8px",
                               "padding": "1px 7px",
                               "fontSize": "0.68rem",
                               "marginLeft": "8px"},
                    ))
                if v.language:
                    extra_badges.append(html.Span(
                        f"🗣️ {v.language.upper()}",
                        style={"background": f"{COLORS['success']}20",
                               "color": COLORS["success"],
                               "borderRadius": "8px",
                               "padding": "1px 7px",
                               "fontSize": "0.68rem",
                               "marginLeft": "8px"},
                    ))
                if ch_subs > 0:
                    extra_badges.append(html.Span(
                        f"👥 {fmt_number(ch_subs)} subs",
                        style={"background": f"{COLORS['warning']}20",
                               "color": COLORS["warning"],
                               "borderRadius": "8px",
                               "padding": "1px 7px",
                               "fontSize": "0.68rem",
                               "marginLeft": "8px"},
                    ))

                cards.append(html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Img(
                                src=v.thumbnail_url or "",
                                style={"width": "100%", "borderRadius": "8px",
                                       "maxHeight": "90px", "objectFit": "cover"},
                            ) if v.thumbnail_url else html.Div(
                                style={"height": "80px", "background": COLORS["surface2"],
                                       "borderRadius": "8px"}
                            ),
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.A(
                                    v.title or "Sin título",
                                    href=yt_url, target="_blank",
                                    style={"color": COLORS["text"],
                                           "fontWeight": "700",
                                           "fontSize":   "0.92rem",
                                           "textDecoration": "none"},
                                ),
                                html.Span(
                                    f"  {sc_lbl}",
                                    style={
                                        "background":   f"{sc_col}20",
                                        "color":        sc_col,
                                        "border":       f"1px solid {sc_col}",
                                        "borderRadius": "20px",
                                        "padding":      "1px 8px",
                                        "fontSize":     "0.72rem",
                                        "fontWeight":   "700",
                                        "marginLeft":   "8px",
                                    },
                                ),
                                *extra_badges,
                            ]),
                            html.P(
                                f"📺 {v.channel_title or ''}  ·  "
                                f"📅 {v.published_at.strftime('%Y-%m-%d') if v.published_at else ''}  ·  "
                                f"⏱️ {fmt_duration(v.duration_seconds or 0)}",
                                style={"color": COLORS["muted"], "fontSize": "0.78rem",
                                       "margin": "4px 0 8px"},
                            ),
                            dbc.Row([
                                dbc.Col(_stat_chip("👁️ Views",     fmt_number(v.view_count or 0)),    width="auto"),
                                dbc.Col(_stat_chip("📈 Score",     f"{sc:.2f}x"),                     width="auto"),
                                dbc.Col(_stat_chip("⚡ V/hora",    fmt_number(int(v.views_per_hour or 0))), width="auto"),
                                dbc.Col(_stat_chip("📊 Views/Sub", f"{(v.views_per_sub or 0):.1%}"),  width="auto"),
                                dbc.Col(_stat_chip("👍 Likes",     fmt_number(v.like_count or 0)),    width="auto"),
                            ], className="g-1"),
                        ], width=8),
                        dbc.Col([
                            html.Button(
                                "⭐" if v.is_favorite else "☆",
                                className="fav-toggle-btn btn btn-sm "
                                          + ("btn-warning" if v.is_favorite else "btn-outline-secondary"),
                                **{"data-video-id": v.id},
                                style={
                                    "borderRadius": "50%",
                                    "width": "40px",
                                    "height": "40px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "fontSize": "1.1rem",
                                    "padding": "0",
                                    "border": "2px solid",
                                    "cursor": "pointer",
                                    "transition": "all 0.2s ease",
                                },
                            ),
                        ], width=2, style={"display": "flex", "alignItems": "center",
                                           "justifyContent": "center"}),
                    ], className="g-2"),
                ], style={
                    "padding":      "14px",
                    "borderBottom": f"1px solid {COLORS['border']}",
                    "transition":   "background 0.2s",
                }))

            return metrics, fig_scatter, fig_hist, html.Div([
                perf_warning,
                html.Div(cards),
            ])

        except Exception as e:
            err = dbc.Alert(f"Error: {e}", color="danger")
            return html.Div(), _empty_fig(), _empty_fig(), err
        finally:
            session.close()
            
# ── Helpers ──────────────────────────────────────────────────────────────────
def _mini_metric(label, value, color):
    return html.Div([
        html.P(label, style={"color": COLORS["muted"], "margin": "0",
                              "fontSize": "0.75rem", "fontWeight": "600",
                              "textTransform": "uppercase"}),
        html.H4(value, style={"color": color, "margin": "2px 0 0",
                               "fontWeight": "800"}),
    ], style={
        "background":   COLORS["surface"],
        "border":       f"1px solid {COLORS['border']}",
        "borderRadius": "10px",
        "padding":      "12px 16px",
    })


def _stat_chip(label, value):
    return html.Div(
        f"{label}: {value}",
        style={
            "background":   COLORS["surface2"],
            "borderRadius": "6px",
            "padding":      "2px 8px",
            "fontSize":     "0.75rem",
            "color":        COLORS["muted"],
        },
    )


def _empty_fig():
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{
            "text": "Sin datos. Ejecuta el descubrimiento primero.",
            "xref": "paper", "yref": "paper",
            "x": 0.5, "y": 0.5,
            "showarrow": False,
            "font": {"color": "#718096", "size": 13},
        }],
    )
    return fig


def _score_col(score: float) -> str:
    if score >= 5:  return "#ff6b35"
    if score >= 3:  return "#00d4aa"
    if score >= 1:  return "#ffd166"
    return "#718096"