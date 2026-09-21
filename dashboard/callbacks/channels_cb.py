"""Callbacks para la sección Descubrir Canales — Versión completa y corregida."""
import threading
import logging
from dash import Input, Output, State, html, no_update, ctx
import dash_bootstrap_components as dbc

from core.discovery import DiscoveryEngine
from core.database import get_session
from core.models import Channel, Video
from core.outliers import OutlierEngine
from core.youtube_api import YouTubeAPI
from dashboard.layout import COLORS
from utils_app import fmt_number, fmt_duration

logger = logging.getLogger(__name__)

_channel_state = {
    "running":  False,
    "progress": 0,
    "message":  "Listo para buscar canales.",
    "results":  None,
}


def register_callbacks(app):

    # ════════════════════════════════════════════════════════════════════
    #  1. INICIAR BÚSQUEDA DE CANALES (API)
    # ════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("ch-store",     "data"),
        Output("ch-poll",      "disabled"),
        Output("ch-start-btn", "disabled"),
        Input("ch-start-btn",  "n_clicks"),
        State("ch-keywords",   "value"),
        State("ch-region",     "value"),
        State("ch-language",   "value"),
        State("ch-category",   "value"),
        State("ch-min-subs",   "value"),
        State("ch-max-subs",   "value"),
        State("ch-min-videos", "value"),
        State("ch-min-total-views", "value"),
        State("ch-max-results","value"),
        prevent_initial_call=True,
    )
    def start_channel_discovery(
        n, keywords, region, language, category,
        min_subs, max_subs, min_videos, min_views, max_results
    ):
        if not n or _channel_state["running"]:
            return no_update, no_update, no_update

        _channel_state["running"]  = True
        _channel_state["progress"] = 0
        _channel_state["message"]  = "🚀 Iniciando búsqueda de canales..."
        _channel_state["results"]  = None

        def progress_cb(pct, msg):
            _channel_state["progress"] = pct
            _channel_state["message"]  = msg

        def run():
            try:
                engine = DiscoveryEngine()
                results = engine.discover_channels(
                    keywords=keywords or "",
                    region_code=region if region is not None else "US",
                    language=language or "es",
                    category_name=category or "",
                    min_subs=int(min_subs or 0),
                    max_subs=int(max_subs or 0),
                    min_videos=int(min_videos or 0),
                    min_total_views=int(min_views or 0),
                    max_results=int(max_results or 25),
                    progress_callback=progress_cb,
                )
                _channel_state["results"] = results
            except Exception as e:
                logger.error(f"Error descubriendo canales: {e}")
                _channel_state["message"] = f"❌ Error: {e}"
            finally:
                _channel_state["running"]  = False
                _channel_state["progress"] = 100

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return {"running": True}, False, True
    # ════════════════════════════════════════════════════════════════════
    #  2. POLLING DE BÚSQUEDA DE CANALES
    # ════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("ch-status",       "children"),
        Output("ch-progress",     "value"),
        Output("ch-results-list", "children"),
        Output("ch-poll",         "disabled",  allow_duplicate=True),
        Output("ch-start-btn",    "disabled",  allow_duplicate=True),
        Input("ch-poll",          "n_intervals"),
        prevent_initial_call=True,
    )
    def poll_channels(n):
        state   = _channel_state
        running = state["running"]
        pct     = state["progress"]
        msg     = state["message"]

        results_el = html.Div()

        try:
            session = get_session()
            channels = (
                session.query(Channel)
                .order_by(Channel.subscriber_count.desc())
                .limit(50)
                .all()
            )
            if channels:
                rows = []
                for ch in channels:
                    cat_badge = html.Span(
                        ch.category or "Sin categoría",
                        style={"background": f"{COLORS['primary']}20",
                               "color": COLORS["primary"],
                               "padding": "1px 7px", "borderRadius": "6px",
                               "fontSize": "0.68rem", "marginTop": "2px",
                               "display": "inline-block"},
                    ) if ch.category else html.Div()

                    rows.append(html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Img(
                                    src=ch.thumbnail_url or "",
                                    style={"width": "50px", "height": "50px",
                                           "borderRadius": "50%", "objectFit": "cover"},
                                ) if ch.thumbnail_url else html.Div(
                                    "📺", style={"width": "50px", "height": "50px",
                                                  "background": COLORS["surface2"],
                                                  "borderRadius": "50%", "display": "flex",
                                                  "alignItems": "center",
                                                  "justifyContent": "center",
                                                  "fontSize": "1.3rem"}
                                ),
                            ], width=1),
                            dbc.Col([
                                html.P(ch.title or "Sin nombre",
                                       style={"color": COLORS["text"], "fontWeight": "700",
                                              "margin": "0", "fontSize": "0.9rem"}),
                                html.P(
                                    f"@{ch.handle}" if ch.handle else ch.id,
                                    style={"color": COLORS["muted"], "margin": "0",
                                           "fontSize": "0.75rem"}),
                                cat_badge,
                            ], width=4),
                            dbc.Col([
                                html.Span(fmt_number(ch.subscriber_count or 0),
                                          style={"color": COLORS["primary"],
                                                 "fontWeight": "700"}),
                                html.P("subs",
                                       style={"color": COLORS["muted"],
                                              "fontSize": "0.7rem", "margin": "0"}),
                            ], width=2, style={"textAlign": "center"}),
                            dbc.Col([
                                html.Span(fmt_number(ch.video_count or 0),
                                          style={"color": COLORS["success"],
                                                 "fontWeight": "700"}),
                                html.P("videos",
                                       style={"color": COLORS["muted"],
                                              "fontSize": "0.7rem", "margin": "0"}),
                            ], width=2, style={"textAlign": "center"}),
                            dbc.Col([
                                html.Span(fmt_number(ch.view_count or 0),
                                          style={"color": COLORS["warning"],
                                                 "fontWeight": "700"}),
                                html.P("views",
                                       style={"color": COLORS["muted"],
                                              "fontSize": "0.7rem", "margin": "0"}),
                            ], width=2, style={"textAlign": "center"}),
                            dbc.Col([
                                html.Span(ch.country or "—",
                                          style={"color": COLORS["muted"],
                                                 "fontSize": "0.8rem"}),
                            ], width=1, style={"textAlign": "center"}),
                        ], className="g-2", style={"alignItems": "center"}),
                    ], style={"padding": "12px",
                              "borderBottom": f"1px solid {COLORS['border']}"}))

                summary = ""
                if state["results"]:
                    r = state["results"]
                    summary = (
                        f"✅ {r.get('channels_found', 0)} nuevos · "
                        f"⏭️ {r.get('channels_skipped', 0)} filtrados · "
                        f"📊 {r.get('quota_used', 0)} cuota"
                    )

                results_el = html.Div([
                    html.P(summary, style={"color": COLORS["success"],
                                           "fontWeight": "600",
                                           "marginBottom": "12px"})
                    if summary else html.Div(),
                    html.P(f"📺 {len(channels)} canales en tu base de datos",
                           style={"color": COLORS["muted"], "marginBottom": "12px",
                                  "fontSize": "0.85rem"}),
                    *rows,
                ])
            session.close()
        except Exception as e:
            logger.error(f"Error en poll_channels: {e}")
            results_el = html.P(str(e), style={"color": COLORS["danger"]})

        return msg, pct, results_el, not running, running

    # ════════════════════════════════════════════════════════════════════
    #  3. CARGAR VIDEOS DE CANALES (API)
    # ════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("ch-actions-feedback", "children"),
        Input("ch-load-videos-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def load_channel_videos(n_clicks):
        if not n_clicks:
            return no_update

        session = get_session()
        try:
            channels = session.query(Channel).order_by(
                Channel.subscriber_count.desc()
            ).limit(20).all()

            if not channels:
                return dbc.Alert(
                    "No hay canales en la base de datos.",
                    color="warning",
                )

            api = YouTubeAPI()
            total_videos = 0

            for ch in channels:
                try:
                    ch_videos = api.get_channel_videos(ch.id, max_results=20)
                    subs = ch.subscriber_count or 0

                    for v_raw in ch_videos:
                        parsed = YouTubeAPI.parse_video(
                            v_raw, subs, category_label=ch.category or ""
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
                        total_videos += 1

                except Exception as e:
                    logger.warning(f"Error cargando videos de {ch.title}: {e}")

            session.commit()

            from core.outliers import OutlierEngine
            OutlierEngine().run(session)
            session.commit()

            return dbc.Alert(
                f"✅ {total_videos} videos cargados y outliers recalculados.",
                color="success", dismissable=True,
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error en load_channel_videos: {e}")
            return dbc.Alert(f"❌ Error: {e}", color="danger")
        finally:
            session.close()

    # ════════════════════════════════════════════════════════════════════
    #  4. MOSTRAR OUTLIERS DE CANALES (sección)
    # ════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("ch-outliers-section", "children"),
        Input("ch-analyze-outliers-btn", "n_clicks"),
        Input("ch-poll", "n_intervals"),
        prevent_initial_call=True,
    )
    def show_channel_outliers(n_clicks, _poll):
        triggered = ctx.triggered_id
        session = get_session()
        try:
            if triggered == "ch-analyze-outliers-btn" and n_clicks:
                engine = OutlierEngine()
                engine.run(session)
                session.commit()

            videos = (
                session.query(Video)
                .filter(Video.outlier_score >= 1.0)
                .order_by(Video.outlier_score.desc())
                .limit(20)
                .all()
            )

            if not videos:
                return html.P(
                    "Sin outliers detectados aún.",
                    style={"color": COLORS["muted"]},
                )

            items = []
            for v in videos:
                sc = v.outlier_score or 0
                sc_col = (
                    COLORS["viral"]   if sc >= 5 else
                    COLORS["success"] if sc >= 2 else
                    COLORS["warning"] if sc >= 1 else
                    COLORS["muted"]
                )
                items.append(html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Img(
                                src=v.thumbnail_url or "",
                                style={"width": "100%", "borderRadius": "6px",
                                       "maxHeight": "65px", "objectFit": "cover"},
                            ) if v.thumbnail_url else html.Div(
                                style={"height": "60px",
                                       "background": COLORS["surface2"],
                                       "borderRadius": "6px"}
                            ),
                        ], width=2),
                        dbc.Col([
                            html.A(
                                (v.title or "")[:60] + ("..." if len(v.title or "") > 60 else ""),
                                href=f"https://youtube.com/watch?v={v.id}",
                                target="_blank",
                                style={"color": COLORS["text"], "fontWeight": "600",
                                       "fontSize": "0.82rem", "textDecoration": "none"},
                            ),
                            html.P(
                                f"📺 {v.channel_title or ''}  ·  "
                                f"👁️ {fmt_number(v.view_count or 0)}  ·  "
                                f"⏱️ {fmt_duration(v.duration_seconds or 0)}",
                                style={"color": COLORS["muted"],
                                       "fontSize": "0.72rem",
                                       "margin": "2px 0 0"},
                            ),
                        ], width=8),
                        dbc.Col([
                            html.Span(
                                f"{sc:.1f}x",
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
                    "padding": "10px",
                    "borderBottom": f"1px solid {COLORS['border']}",
                }))

            return html.Div([
                html.P(f"🔥 Top {len(videos)} outliers:",
                       style={"color": COLORS["text"], "fontWeight": "600",
                              "marginBottom": "12px"}),
                *items
            ])

        except Exception as e:
            logger.error(f"Error en show_channel_outliers: {e}")
            return dbc.Alert(f"Error: {e}", color="danger")
        finally:
            session.close()

    # ════════════════════════════════════════════════════════════════════
    #  5. TOGGLE MODO: API ↔ BASE DE DATOS
    # ════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("ch-api-controls", "style"),
        Output("ch-db-controls",  "style"),
        Input("ch-mode",          "value"),
    )
    def toggle_channel_mode(mode):
        if mode == "db":
            return {"display": "none"}, {"display": "block"}
        return {"display": "block"}, {"display": "none"}

    # ════════════════════════════════════════════════════════════════════
    #  6. EXPLORAR CANALES DE LA BASE DE DATOS (filtros completos)
    # ════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("ch-results-list", "children", allow_duplicate=True),
        Output("ch-status",       "children", allow_duplicate=True),
        Input("ch-db-explore-btn", "n_clicks"),
        State("ch-db-search",      "value"),
        State("ch-db-category",    "value"),
        State("ch-db-region",      "value"),
        State("ch-db-language",    "value"),
        State("ch-db-min-subs",    "value"),
        State("ch-db-max-subs",    "value"),
        State("ch-db-min-videos",  "value"),
        State("ch-db-min-views",   "value"),
        State("ch-db-sort",        "value"),
        State("ch-db-limit",       "value"),
        prevent_initial_call=True,
    )
    def explore_db_channels(
        n_clicks, search_text, category, region, language,
        min_subs, max_subs, min_videos, min_views, sort_by, limit
    ):
        if not n_clicks:
            return no_update, no_update

        session = get_session()
        try:
            q = session.query(Channel)

            if search_text and search_text.strip():
                search_term = f"%{search_text.strip()}%"
                q = q.filter(Channel.title.ilike(search_term))

            if category and category != "all":
                q = q.filter(Channel.category == category)

            if region and region != "all":
                q = q.filter(Channel.country == region)

            if language and language != "all":
                q = q.filter(Channel.language == language)

            if min_subs and int(min_subs) > 0:
                q = q.filter(Channel.subscriber_count >= int(min_subs))

            if max_subs and int(max_subs) > 0:
                q = q.filter(Channel.subscriber_count <= int(max_subs))

            if min_videos and int(min_videos) > 0:
                q = q.filter(Channel.video_count >= int(min_videos))

            if min_views and int(min_views) > 0:
                q = q.filter(Channel.view_count >= int(min_views))

            if sort_by == "subs_desc":
                q = q.order_by(Channel.subscriber_count.desc())
            elif sort_by == "subs_asc":
                q = q.order_by(Channel.subscriber_count.asc())
            elif sort_by == "videos_desc":
                q = q.order_by(Channel.video_count.desc())
            elif sort_by == "views_desc":
                q = q.order_by(Channel.view_count.desc())
            elif sort_by == "name_asc":
                q = q.order_by(Channel.title.asc())

            channels = q.limit(int(limit or 50)).all()

            # ── Resumen de filtros aplicados ──────────────────────────
            filters_applied = []
            if category and category != "all":
                filters_applied.append(f"🏷️ {category}")
            if region and region != "all":
                filters_applied.append(f"🌍 {region}")
            if language and language != "all":
                filters_applied.append(f"🗣️ {language}")
            if min_subs and int(min_subs) > 0:
                filters_applied.append(f"📊 ≥{fmt_number(min_subs)} subs")
            if max_subs and int(max_subs) > 0:
                filters_applied.append(f"📊 ≤{fmt_number(max_subs)} subs")
            if min_videos and int(min_videos) > 0:
                filters_applied.append(f"🎬 ≥{min_videos} videos")
            if min_views and int(min_views) > 0:
                filters_applied.append(f"👁️ ≥{fmt_number(min_views)} views")

            if not channels:
                filter_hint = " con filtros: " + ", ".join(filters_applied) if filters_applied else ""
                status = f"Sin canales que coincidan{filter_hint}."
                results = html.Div([
                    html.P(status, style={"color": COLORS["muted"]}),
                    html.P("💡 Intenta ampliar los rangos o eliminar algunos filtros.",
                           style={"color": COLORS["muted"], "fontSize": "0.8rem",
                                  "fontStyle": "italic", "marginTop": "8px"}),
                ])
                return results, status

            # ── Construir lista de resultados ─────────────────────────
            rows = []
            for ch in channels:
                # Badges
                cat_badge = html.Span(
                    ch.category or "Sin categoría",
                    style={"background": f"{COLORS['primary']}20",
                           "color": COLORS["primary"],
                           "padding": "1px 7px", "borderRadius": "6px",
                           "fontSize": "0.68rem", "marginTop": "2px",
                           "display": "inline-block"},
                ) if ch.category else html.Div()

                lang_badge = html.Span(
                    f"🗣️ {ch.language.upper()}" if ch.language else "",
                    style={"background": f"{COLORS['success']}20",
                           "color": COLORS["success"],
                           "padding": "1px 7px", "borderRadius": "6px",
                           "fontSize": "0.68rem", "marginLeft": "4px",
                           "display": "inline-block"},
                ) if ch.language else html.Div()

                country_badge = html.Span(
                    f"🌍 {ch.country}" if ch.country else "",
                    style={"background": f"{COLORS['warning']}20",
                           "color": COLORS["warning"],
                           "padding": "1px 7px", "borderRadius": "6px",
                           "fontSize": "0.68rem", "marginLeft": "4px",
                           "display": "inline-block"},
                ) if ch.country else html.Div()

                # Botón Outliers con clase para JS
                outliers_btn = html.Button(
                    "🔥 Outliers",
                    className="ch-view-outliers-btn btn btn-sm btn-outline-warning",
                    **{"data-channel-id": ch.id,
                       "data-channel-name": ch.title or "Sin nombre"},
                    style={
                        "borderRadius": "6px",
                        "fontSize": "0.72rem",
                        "padding": "4px 10px",
                        "whiteSpace": "nowrap",
                        "cursor": "pointer",
                        "fontWeight": "600",
                    },
                )

                rows.append(html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Img(
                                src=ch.thumbnail_url or "",
                                style={"width": "50px", "height": "50px",
                                       "borderRadius": "50%", "objectFit": "cover"},
                            ) if ch.thumbnail_url else html.Div(
                                "📺", style={"width": "50px", "height": "50px",
                                              "background": COLORS["surface2"],
                                              "borderRadius": "50%", "display": "flex",
                                              "alignItems": "center",
                                              "justifyContent": "center",
                                              "fontSize": "1.3rem"}
                            ),
                        ], width=1),
                        dbc.Col([
                            html.P(ch.title or "Sin nombre",
                                   style={"color": COLORS["text"], "fontWeight": "700",
                                          "margin": "0", "fontSize": "0.9rem"}),
                            html.P(
                                f"@{ch.handle}" if ch.handle else ch.id,
                                style={"color": COLORS["muted"], "margin": "0",
                                       "fontSize": "0.75rem"}),
                            html.Div([cat_badge, lang_badge, country_badge],
                                     style={"marginTop": "4px"}),
                        ], width=4),
                        dbc.Col([
                            html.Span(fmt_number(ch.subscriber_count or 0),
                                      style={"color": COLORS["primary"],
                                             "fontWeight": "700"}),
                            html.P("subs",
                                   style={"color": COLORS["muted"],
                                          "fontSize": "0.7rem", "margin": "0"}),
                        ], width=2, style={"textAlign": "center"}),
                        dbc.Col([
                            html.Span(fmt_number(ch.video_count or 0),
                                      style={"color": COLORS["success"],
                                             "fontWeight": "700"}),
                            html.P("videos",
                                   style={"color": COLORS["muted"],
                                          "fontSize": "0.7rem", "margin": "0"}),
                        ], width=2, style={"textAlign": "center"}),
                        dbc.Col([
                            html.Span(fmt_number(ch.view_count or 0),
                                      style={"color": COLORS["warning"],
                                             "fontWeight": "700"}),
                            html.P("views",
                                   style={"color": COLORS["muted"],
                                          "fontSize": "0.7rem", "margin": "0"}),
                        ], width=2, style={"textAlign": "center"}),
                        dbc.Col(
                            outliers_btn,
                            width=1,
                            style={"textAlign": "center",
                                   "display": "flex",
                                   "alignItems": "center",
                                   "justifyContent": "center"}
                        ),
                    ], className="g-2", style={"alignItems": "center"}),
                ], style={"padding": "12px",
                          "borderBottom": f"1px solid {COLORS['border']}"}))

            filter_summary = ""
            if filters_applied:
                filter_summary = html.P(
                    "🎯 Filtros: " + " · ".join(filters_applied),
                    style={"color": COLORS["primary"], "fontSize": "0.8rem",
                           "marginBottom": "8px"},
                )

            status = f"✅ {len(channels)} canales encontrados en la base de datos."
            results = html.Div([
                html.P(status, style={"color": COLORS["success"],
                                       "fontWeight": "600",
                                       "marginBottom": "8px"}),
                filter_summary,
                *rows,
            ])

            return results, status

        except Exception as e:
            logger.error(f"Error en explore_db_channels: {e}")
            return dbc.Alert(f"Error: {e}", color="danger"), f"❌ Error: {e}"
        finally:
            session.close()