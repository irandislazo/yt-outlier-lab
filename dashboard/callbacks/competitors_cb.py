# dashboard/callbacks/competitors_cb.py
"""Callbacks del Radar de Competidores."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dash import Input, Output, html, no_update
import dash_bootstrap_components as dbc

from core.database import get_session
from core.models import Channel, Video
from dashboard.layout import COLORS
from utils_app import fmt_number, fmt_duration


def register_callbacks(app):

    # ── Poblar selector de canales ────────────────────────────────────
    @app.callback(
        Output("comp-channel-select", "options"),
        Output("comp-channel-select", "value"),
        Input("comp-refresh",         "n_intervals"),
    )
    def populate_channels(_):
        session = get_session()
        try:
            channels = (
                session.query(Channel)
                .order_by(Channel.subscriber_count.desc())
                .limit(50)
                .all()
            )
            opts = [{"label": f"📺 {c.title}", "value": c.id} for c in channels]
            default = [c.id for c in channels[:5]]
            return opts, default
        finally:
            session.close()

    # ── Actualizar todo ───────────────────────────────────────────────
    @app.callback(
        Output("comp-table",        "children"),
        Output("comp-views-chart",  "figure"),
        Output("comp-outlier-chart","figure"),
        Output("comp-radar-chart",  "figure"),
        Output("comp-recent-posts", "children"),
        Input("comp-channel-select","value"),
        Input("comp-days",          "value"),
        Input("comp-refresh",       "n_intervals"),
    )
    def update_competitors(channel_ids, days, _):
        if not channel_ids:
            empty = html.P("Selecciona al menos un canal.",
                           style={"color": COLORS["muted"]})
            ef = _empty_fig()
            return empty, ef, ef, ef, empty

        session = get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=int(days or 30))
            stats  = []

            for ch_id in channel_ids:
                ch = session.get(Channel, ch_id)
                if not ch:
                    continue

                videos = (
                    session.query(Video)
                    .filter(Video.channel_id == ch_id)
                    .filter(Video.published_at >= cutoff)
                    .all()
                )
                if not videos:
                    continue

                views_list = [v.view_count or 0 for v in videos]
                scores     = [v.outlier_score or 0 for v in videos]
                likes      = [v.like_count or 0 for v in videos]
                comments   = [v.comment_count or 0 for v in videos]

                total_v   = sum(views_list)
                avg_v     = int(total_v / len(videos)) if videos else 0
                out_count = sum(1 for s in scores if s >= 1.0)
                avg_score = sum(scores) / len(scores) if scores else 0
                eng       = (
                    round((sum(likes) + sum(comments)) / total_v * 100, 2)
                    if total_v > 0 else 0
                )
                freq      = round(len(videos) / int(days or 30) * 7, 1)

                stats.append({
                    "Canal":        ch.title,
                    "Subs":         ch.subscriber_count or 0,
                    "Videos":       len(videos),
                    "Vid/semana":   freq,
                    "Views prom":   avg_v,
                    "Views total":  total_v,
                    "Engagement %": eng,
                    "Outliers":     out_count,
                    "Score prom":   round(avg_score, 2),
                    "_id":          ch_id,
                })

            if not stats:
                empty = html.P("Sin datos para el período.",
                               style={"color": COLORS["muted"]})
                ef = _empty_fig()
                return empty, ef, ef, ef, empty

            df = pd.DataFrame(stats)

            # ── Tabla ────────────────────────────────────────────────
            table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th(col, style={"color": COLORS["muted"],
                                        "fontSize": "0.78rem",
                                        "fontWeight": "700",
                                        "textTransform": "uppercase",
                                        "borderBottom": f"2px solid {COLORS['border']}",
                                        "background": COLORS["surface2"],
                                        "padding": "10px 12px"})
                    for col in ["Canal", "Subs", "Vid/sem", "Views prom",
                                "Engagement", "Outliers", "Score prom"]
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(row["Canal"],
                                style={"color": COLORS["text"], "fontWeight": "600",
                                       "padding": "10px 12px"}),
                        html.Td(fmt_number(row["Subs"]),
                                style={"color": COLORS["muted"], "padding": "10px 12px"}),
                        html.Td(f'{row["Vid/semana"]}',
                                style={"color": COLORS["muted"], "padding": "10px 12px"}),
                        html.Td(fmt_number(row["Views prom"]),
                                style={"color": COLORS["primary"], "fontWeight": "600",
                                       "padding": "10px 12px"}),
                        html.Td(f'{row["Engagement %"]}%',
                                style={"color": COLORS["success"], "padding": "10px 12px"}),
                        html.Td(
                            html.Span(str(row["Outliers"]), style={
                                "background":   f"{COLORS['viral']}20",
                                "color":        COLORS["viral"],
                                "borderRadius": "10px",
                                "padding":      "2px 8px",
                                "fontWeight":   "700",
                            }),
                            style={"padding": "10px 12px"},
                        ),
                        html.Td(f'{row["Score prom"]}x',
                                style={"color": COLORS["warning"], "fontWeight": "600",
                                       "padding": "10px 12px"}),
                    ], style={"borderBottom": f"1px solid {COLORS['border']}"})
                    for _, row in df.iterrows()
                ]),
            ], style={"width": "100%", "borderCollapse": "collapse"})

            # ── Gráfico views ─────────────────────────────────────────
            fig_views = px.bar(
                df, x="Canal", y="Views prom",
                color="Views prom",
                color_continuous_scale="Blues",
                template="plotly_dark",
            )
            fig_views.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=40),
                showlegend=False,
            )

            # ── Gráfico outliers ──────────────────────────────────────
            fig_out = px.bar(
                df, x="Canal", y="Outliers",
                color="Outliers",
                color_continuous_scale="Reds",
                template="plotly_dark",
            )
            fig_out.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=40),
            )

            # ── Radar ─────────────────────────────────────────────────
            radar_metrics = ["Vid/semana", "Views prom", "Engagement %",
                             "Score prom", "Outliers"]
            fig_radar = go.Figure()
            for _, row in df.iterrows():
                vals = [row[m] for m in radar_metrics]
                max_vals = [df[m].max() or 1 for m in radar_metrics]
                norm_vals = [v / m for v, m in zip(vals, max_vals)]
                norm_vals.append(norm_vals[0])
                cats = radar_metrics + [radar_metrics[0]]

                fig_radar.add_trace(go.Scatterpolar(
                    r=norm_vals, theta=cats,
                    fill="toself", name=row["Canal"], opacity=0.7,
                ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1],
                                           gridcolor=COLORS["border"],
                                           linecolor=COLORS["border"])),
                paper_bgcolor="rgba(0,0,0,0)",
                font_color=COLORS["text"],
                legend=dict(font=dict(size=10)),
                margin=dict(l=20, r=20, t=20, b=20),
            )

            # ── Últimas publicaciones ─────────────────────────────────
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_cards  = []

            for ch_id in channel_ids[:5]:
                ch = session.get(Channel, ch_id)
                if not ch:
                    continue
                recent_vids = (
                    session.query(Video)
                    .filter(Video.channel_id == ch_id)
                    .filter(Video.published_at >= recent_cutoff)
                    .order_by(Video.published_at.desc())
                    .limit(3)
                    .all()
                )
                if not recent_vids:
                    continue

                for v in recent_vids:
                    sc_col = (
                        COLORS["viral"]   if (v.outlier_score or 0) >= 5 else
                        COLORS["success"] if (v.outlier_score or 0) >= 2 else
                        COLORS["warning"] if (v.outlier_score or 0) >= 1 else
                        COLORS["muted"]
                    )
                    recent_cards.append(
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Img(
                                        src=v.thumbnail_url or "",
                                        style={"width": "100%", "borderRadius": "6px",
                                               "maxHeight": "60px", "objectFit": "cover"},
                                    ) if v.thumbnail_url else html.Div(
                                        style={"height": "60px",
                                               "background": COLORS["surface2"],
                                               "borderRadius": "6px"}
                                    ),
                                ], width=2),
                                dbc.Col([
                                    html.A(
                                        v.title[:65],
                                        href=f"https://youtube.com/watch?v={v.id}",
                                        target="_blank",
                                        style={"color": COLORS["text"],
                                               "fontWeight": "600",
                                               "fontSize":   "0.85rem",
                                               "textDecoration": "none"},
                                    ),
                                    html.P(
                                        f"📺 {ch.title}  ·  "
                                        f"👁️ {fmt_number(v.view_count or 0)}  ·  "
                                        f"📅 {v.published_at.strftime('%d %b') if v.published_at else ''}",
                                        style={"color": COLORS["muted"],
                                               "fontSize": "0.75rem",
                                               "margin":   "2px 0 0"},
                                    ),
                                ], width=8),
                                dbc.Col([
                                    html.Span(
                                        f"{v.outlier_score:.1f}x",
                                        style={
                                            "background":   f"{sc_col}20",
                                            "color":        sc_col,
                                            "border":       f"1px solid {sc_col}",
                                            "borderRadius": "12px",
                                            "padding":      "2px 8px",
                                            "fontSize":     "0.78rem",
                                            "fontWeight":   "700",
                                        },
                                    ),
                                ], width=2, style={"textAlign": "right",
                                                   "display": "flex",
                                                   "alignItems": "center",
                                                   "justifyContent": "flex-end"}),
                            ], className="g-2"),
                        ], style={
                            "padding":      "10px",
                            "borderBottom": f"1px solid {COLORS['border']}",
                        })
                    )

            recent_el = html.Div(recent_cards) if recent_cards else \
                html.P("Sin publicaciones en los últimos 7 días.",
                       style={"color": COLORS["muted"]})

            return table, fig_views, fig_out, fig_radar, recent_el

        except Exception as e:
            err = dbc.Alert(f"Error: {e}", color="danger")
            ef  = _empty_fig()
            return err, ef, ef, ef, html.Div()
        finally:
            session.close()


def _empty_fig():
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False}, yaxis={"visible": False},
        annotations=[{"text": "Sin datos", "xref": "paper",
                       "yref": "paper", "x": 0.5, "y": 0.5,
                       "showarrow": False,
                       "font": {"color": "#718096"}}],
    )
    return fig