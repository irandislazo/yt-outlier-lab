"""Callbacks de Favoritos — Versión con Flask API."""
import logging
from dash import Input, Output, html, no_update
import dash_bootstrap_components as dbc

from core.database import get_session
from core.models import Video
from dashboard.layout import COLORS
from utils_app import fmt_number, fmt_duration

logger = logging.getLogger(__name__)


def register_callbacks(app):

    # ── MOSTRAR LISTA DE FAVORITOS ───────────────────────────────────
    @app.callback(
        Output("fav-metrics",     "children"),
        Output("fav-videos-list", "children"),
        Input("fav-refresh",      "n_intervals"),
        Input("fav-category",     "value"),
        Input("fav-min-score",    "value"),
        Input("fav-sort",         "value"),
        Input("fav-limit",        "value"),
    )
    def update_favorites(_, category, min_score, sort_col, limit):
        session = get_session()
        try:
            q = session.query(Video).filter(Video.is_favorite == True)

            if category and category != "all":
                q = q.filter(Video.category_label == category)

            if min_score and float(min_score) > 0:
                q = q.filter(Video.outlier_score >= float(min_score))

            if sort_col == "outlier_score":
                q = q.order_by(Video.outlier_score.desc())
            elif sort_col == "view_count":
                q = q.order_by(Video.view_count.desc())
            else:
                q = q.order_by(Video.created_at.desc())

            videos = q.limit(int(limit or 50)).all()
            logger.info(f"⭐ Favoritos encontrados: {len(videos)}")

            if not videos:
                empty = html.Div([
                    html.H1("⭐", style={"textAlign": "center",
                                          "margin": "20px 0", "fontSize": "3rem"}),
                    html.P("No tienes videos favoritos aún.",
                           style={"color": COLORS["text"], "textAlign": "center",
                                  "fontWeight": "600", "marginBottom": "8px"}),
                    html.P("Ve a Outliers y haz clic en ☆ para agregar videos.",
                           style={"color": COLORS["muted"], "textAlign": "center"}),
                ], style={"padding": "40px 20px"})
                return html.Div(), empty

            total = len(videos)
            avg_score = sum(v.outlier_score or 0 for v in videos) / total if total else 0
            total_views = sum(v.view_count or 0 for v in videos)

            metrics = dbc.Row([
                dbc.Col(_fav_metric("⭐ Favoritos", str(total), COLORS["warning"]), width=4),
                dbc.Col(_fav_metric("📈 Score prom", f"{avg_score:.2f}x", COLORS["success"]), width=4),
                dbc.Col(_fav_metric("👁️ Views", fmt_number(total_views), COLORS["primary"]), width=4),
            ], className="g-2 mb-3")

            cards = []
            for v in videos:
                sc = v.outlier_score or 0
                sc_col = (COLORS["viral"] if sc >= 5 else
                          COLORS["success"] if sc >= 2 else
                          COLORS["warning"] if sc >= 1 else COLORS["muted"])
                yt_url = f"https://youtube.com/watch?v={v.id}"

                cards.append(html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Img(src=v.thumbnail_url or "",
                                     style={"width": "100%", "borderRadius": "8px",
                                            "maxHeight": "90px", "objectFit": "cover"},
                            ) if v.thumbnail_url else html.Div(
                                style={"height": "80px", "background": COLORS["surface2"],
                                       "borderRadius": "8px"}),
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.A(v.title or "Sin título", href=yt_url, target="_blank",
                                       style={"color": COLORS["text"], "fontWeight": "700",
                                              "fontSize": "0.92rem", "textDecoration": "none"}),
                                html.Span(f"  {sc:.1f}x",
                                          style={"background": f"{sc_col}20", "color": sc_col,
                                                 "border": f"1px solid {sc_col}",
                                                 "borderRadius": "20px", "padding": "1px 8px",
                                                 "fontSize": "0.72rem", "fontWeight": "700",
                                                 "marginLeft": "8px"}),
                            ]),
                            html.P(f"📺 {v.channel_title or ''}  ·  "
                                   f"📅 {v.published_at.strftime('%Y-%m-%d') if v.published_at else ''}  ·  "
                                   f"⏱️ {fmt_duration(v.duration_seconds or 0)}",
                                   style={"color": COLORS["muted"], "fontSize": "0.78rem",
                                          "margin": "4px 0 8px"}),
                        ], width=8),
                        dbc.Col([
                            html.Button(
                                "🗑️",
                                className="fav-remove-btn btn btn-sm btn-outline-danger",
                                **{"data-video-id": v.id},
                                style={"borderRadius": "6px"},
                            ),
                        ], width=2, style={"display": "flex", "alignItems": "center",
                                           "justifyContent": "center"}),
                    ], className="g-2"),
                ], style={"padding": "14px",
                          "borderBottom": f"1px solid {COLORS['border']}"}))

            return metrics, html.Div(cards)

        except Exception as e:
            logger.error(f"Error update_favorites: {e}")
            return html.Div(), dbc.Alert(f"Error: {e}", color="danger")
        finally:
            session.close()


def _fav_metric(label, value, color):
    return html.Div([
        html.P(label, style={"color": COLORS["muted"], "margin": "0",
                              "fontSize": "0.75rem", "fontWeight": "600",
                              "textTransform": "uppercase"}),
        html.H4(value, style={"color": color, "margin": "2px 0 0", "fontWeight": "800"}),
    ], style={"background": COLORS["surface"],
              "border": f"1px solid {COLORS['border']}",
              "borderRadius": "10px", "padding": "12px 16px"})


def _stat_chip(label, value):
    return html.Div(f"{label}: {value}",
                    style={"background": COLORS["surface2"], "borderRadius": "6px",
                           "padding": "2px 8px", "fontSize": "0.75rem",
                           "color": COLORS["muted"]})