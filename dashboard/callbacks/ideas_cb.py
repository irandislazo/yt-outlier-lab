# dashboard/callbacks/ideas_cb.py
"""Callbacks de la página Ideas."""
import json
import plotly.express as px
from dash import Input, Output, State, html, dcc, no_update, ctx
import dash_bootstrap_components as dbc

from core.database import get_session
from core.models import Video, TopicCluster, IdeaNote
from dashboard.layout import COLORS
from utils_app import fmt_number


def register_callbacks(app):

    # ── Poblar selector de videos outliers ───────────────────────────
    @app.callback(
        Output("idea-video-select", "options"),
        Input("idea-video-select",  "search_value"),
    )
    def populate_video_options(search):
        session = get_session()
        try:
            q = (
                session.query(Video)
                .filter(Video.outlier_score >= 1.0)
                .order_by(Video.outlier_score.desc())
                .limit(100)
            )
            if search:
                q = q.filter(Video.title.ilike(f"%{search}%"))
            videos = q.all()
            return [
                {
                    "label": f"[{v.outlier_score:.1f}x] {v.title[:60]}",
                    "value": v.id,
                }
                for v in videos
            ]
        finally:
            session.close()

    # ── Preview del video seleccionado ───────────────────────────────
    @app.callback(
        Output("idea-source-preview", "children"),
        Input("idea-video-select",    "value"),
    )
    def show_source_preview(video_id):
        if not video_id:
            return html.P("Selecciona un video arriba para ver su preview.",
                          style={"color": COLORS["muted"], "fontSize": "0.85rem"})
        session = get_session()
        try:
            v = session.get(Video, video_id)
            if not v:
                return html.Div()
            return html.Div([
                html.Img(
                    src=v.thumbnail_url or "",
                    style={"width": "100%", "borderRadius": "8px", "marginBottom": "10px"},
                ) if v.thumbnail_url else html.Div(),
                html.P(v.title, style={"color": COLORS["text"], "fontWeight": "700",
                                        "fontSize": "0.85rem", "margin": "0 0 4px"}),
                html.P(
                    f"👁️ {fmt_number(v.view_count or 0)} · 📈 {v.outlier_score:.1f}x · "
                    f"📺 {v.channel_title or ''}",
                    style={"color": COLORS["muted"], "fontSize": "0.75rem"},
                ),
            ])
        finally:
            session.close()

    # ── Generar ideas ─────────────────────────────────────────────────
    @app.callback(
        Output("idea-generated-list", "children"),
        Input("idea-generate-btn",    "n_clicks"),
        State("idea-video-select",    "value"),
        prevent_initial_call=True,
    )
    def generate_ideas(n_clicks, video_id):
        if not video_id:
            return dbc.Alert("Selecciona un video primero.", color="warning")

        session = get_session()
        try:
            v = session.get(Video, video_id)
            if not v:
                return dbc.Alert("Video no encontrado.", color="danger")

            ideas = _generate_ideas_for_video(v)
            cards = []
            for idea in ideas:
                cards.append(
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Span(idea["icon"],
                                              style={"fontSize": "1.3rem",
                                                     "marginRight": "8px"}),
                                    html.Span(idea["tipo"],
                                              style={"color": COLORS["primary"],
                                                     "fontWeight": "700",
                                                     "fontSize":   "0.85rem"}),
                                ]),
                                html.P(
                                    f"📌 {idea['titulo']}",
                                    style={"color": COLORS["text"],
                                           "fontWeight": "600",
                                           "margin":     "6px 0 4px",
                                           "fontSize":   "0.88rem"},
                                ),
                                html.P(
                                    f"🎤 Hook: {idea['hook']}",
                                    style={"color": COLORS["muted"],
                                           "fontSize": "0.8rem",
                                           "fontStyle": "italic",
                                           "margin":    "0"},
                                ),
                            ], width=9),
                            dbc.Col([
                                dbc.Button(
                                    "💾 Guardar",
                                    id={"type": "save-idea-btn", "index": idea["tipo"]},
                                    size="sm",
                                    color="success",
                                    outline=True,
                                    style={"width": "100%", "borderRadius": "6px"},
                                    n_clicks=0,
                                ),
                                dcc.Store(
                                    id={"type": "idea-data", "index": idea["tipo"]},
                                    data={
                                        "title":    idea["titulo"],
                                        "angle":    idea["tipo"] + " — " + idea["hook"],
                                        "video_id": video_id,
                                    },
                                ),
                                html.Div(
                                    id={"type": "save-feedback", "index": idea["tipo"]},
                                ),
                            ], width=3, style={"display": "flex", "flexDirection": "column",
                                               "gap": "4px", "justifyContent": "center"}),
                        ], className="g-2"),
                    ], style={
                        "padding":      "14px",
                        "borderBottom": f"1px solid {COLORS['border']}",
                    })
                )
            return html.Div(cards) if cards else html.P("Sin ideas generadas.",
                                                         style={"color": COLORS["muted"]})
        finally:
            session.close()

    # ── Guardar idea ──────────────────────────────────────────────────
    @app.callback(
        Output({"type": "save-feedback", "index": "__match__"}, "children"),
        Input({"type":  "save-idea-btn", "index": "__match__"}, "n_clicks"),
        State({"type":  "idea-data",     "index": "__match__"}, "data"),
        prevent_initial_call=True,
    )
    def save_idea(n_clicks, idea_data):
        if not n_clicks or not idea_data:
            return no_update
        session = get_session()
        try:
            note = IdeaNote(
                title=idea_data.get("title", ""),
                angle=idea_data.get("angle", ""),
                inspired_by_video_id=idea_data.get("video_id"),
                status="idea",
                priority=0,
            )
            session.add(note)
            session.commit()
            return html.Span("✅", style={"color": COLORS["success"], "fontSize": "1.1rem"})
        except Exception as e:
            return html.Span("❌", style={"color": COLORS["danger"]})
        finally:
            session.close()

    # ── Chart de oportunidad ──────────────────────────────────────────
    @app.callback(
        Output("idea-opportunity-chart", "figure"),
        Input("idea-generate-btn",       "n_clicks"),
    )
    def update_opportunity_chart(_):
        session = get_session()
        try:
            clusters = (
                session.query(TopicCluster)
                .order_by(TopicCluster.opportunity_score.desc())
                .limit(12)
                .all()
            )
            if not clusters:
                return _empty_opportunity_fig()

            labels = [c.label[:25] for c in clusters]
            opps   = [c.opportunity_score for c in clusters]

            fig = px.bar(
                x=opps, y=labels,
                orientation="h",
                color=opps,
                color_continuous_scale="RdYlGn",
                template="plotly_dark",
                labels={"x": "Oportunidad", "y": ""},
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis={"autorange": "reversed"},
            )
            return fig
        finally:
            session.close()

    # ── Ideas guardadas ───────────────────────────────────────────────
    @app.callback(
        Output("idea-saved-list", "children"),
        Input("idea-generate-btn", "n_clicks"),
    )
    def show_saved_ideas(_):
        session = get_session()
        try:
            ideas = (
                session.query(IdeaNote)
                .order_by(IdeaNote.priority.desc(), IdeaNote.created_at.desc())
                .limit(20)
                .all()
            )
            if not ideas:
                return html.P("No tienes ideas guardadas aún.",
                              style={"color": COLORS["muted"], "fontSize": "0.85rem"})

            rows = []
            for idea in ideas:
                status_color = {
                    "idea":          COLORS["primary"],
                    "en_produccion": COLORS["warning"],
                    "publicado":     COLORS["success"],
                }.get(idea.status, COLORS["muted"])

                rows.append(html.Div([
                    html.Div([
                        html.Span(
                            idea.status.replace("_", " ").title(),
                            style={
                                "background":   f"{status_color}20",
                                "color":        status_color,
                                "borderRadius": "10px",
                                "padding":      "2px 8px",
                                "fontSize":     "0.72rem",
                                "fontWeight":   "700",
                                "marginRight":  "8px",
                            },
                        ),
                        html.Span(
                            idea.title[:60],
                            style={"color": COLORS["text"],
                                   "fontSize": "0.85rem",
                                   "fontWeight": "600"},
                        ),
                    ]),
                    html.P(
                        idea.created_at.strftime("%Y-%m-%d") if idea.created_at else "",
                        style={"color": COLORS["muted"], "fontSize": "0.72rem",
                               "margin": "2px 0 0"},
                    ),
                ], style={
                    "padding":      "10px",
                    "borderBottom": f"1px solid {COLORS['border']}",
                }))

            return html.Div(rows)
        finally:
            session.close()


def _generate_ideas_for_video(v) -> list[dict]:
    title = v.title or ""
    return [
        {"icon": "🔄", "tipo": "Ángulo Opuesto",
         "titulo": f"Por qué lo que dicen de '{title[:35]}' está EQUIVOCADO",
         "hook": "Todo lo que escuchaste sobre esto es mentira. Aquí la verdad..."},
        {"icon": "📈", "tipo": "Versión Extrema",
         "titulo": f"Hice {title[:35]} durante 30 DÍAS SEGUIDOS y esto ocurrió",
         "hook": "Nadie lleva esto al extremo. Yo sí. Los resultados me sorprendieron..."},
        {"icon": "🎯", "tipo": "Guía Definitiva",
         "titulo": f"La Guía COMPLETA de {title[:35]} (lo que nadie te explica)",
         "hook": "Busqué por horas y no encontré nada bueno. Así que lo hice yo mismo..."},
        {"icon": "❓", "tipo": "Pregunta Viral",
         "titulo": f"¿Realmente funciona {title[:35]}? Lo probé durante 2 semanas",
         "hook": "Me prometieron resultados increíbles. Lo que encontré fue muy diferente..."},
        {"icon": "🏆", "tipo": "Comparativa",
         "titulo": f"Comparé 5 formas de {title[:35]}. Solo UNA funciona de verdad",
         "hook": "Gasté tiempo y dinero en todo esto para que tú no tengas que hacerlo..."},
        {"icon": "📖", "tipo": "Historia Personal",
         "titulo": f"Cómo {title[:35]} cambió mi vida completamente en 60 días",
         "hook": "Hace 2 meses era escéptico. Hoy no puedo imaginar mi vida sin esto..."},
        {"icon": "🚫", "tipo": "Errores Comunes",
         "titulo": f"Los 7 errores que todos cometen con {title[:35]} (y cómo evitarlos)",
         "hook": "El 95% de la gente lo hace mal. Yo también lo hacía hasta que descubrí esto..."},
        {"icon": "⚡", "tipo": "Lista Accionable",
         "titulo": f"10 secretos de {title[:35]} que los expertos no quieren que sepas",
         "hook": "Llevo años investigando esto. Estas son las 10 verdades que cambiaron todo..."},
    ]


def _empty_opportunity_fig():
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{"text": "Sin clusters. Ejecuta descubrimiento primero.",
                       "xref": "paper", "yref": "paper",
                       "x": 0.5, "y": 0.5, "showarrow": False,
                       "font": {"color": "#718096"}}],
    )
    return fig