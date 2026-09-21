# dashboard/callbacks/discovery_cb.py
"""Callbacks del Auto-Descubrimiento — Versión definitiva."""
import threading
from dash import Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from dash import html

from core.discovery import DiscoveryEngine
from core.database import get_session
from core.models import Video, Channel, QuotaLog
from dashboard.layout import COLORS
from utils_app import fmt_number

_discovery_state = {
    "running":  False,
    "progress": 0,
    "message":  "Listo para iniciar.",
    "results":  None,
}


def register_callbacks(app):

    @app.callback(
        Output("disc-store",     "data"),
        Output("disc-poll",      "disabled"),
        Output("disc-start-btn", "disabled"),
        Input("disc-start-btn",  "n_clicks"),
        State("disc-category",   "value"),
        State("disc-region",     "value"),
        State("disc-language",   "value"),
        State("disc-keywords",   "value"),
        State("disc-min-subs",   "value"),
        State("disc-max-subs",   "value"),
        State("disc-min-views",  "value"),
        State("disc-days-back",  "value"),
        State("disc-max-channels","value"),
        State("disc-options",    "value"),
        State("disc-duration-type", "value"),
        State("disc-min-duration",  "value"),
        State("disc-max-duration",  "value"),
        prevent_initial_call=True,
    )
    def start_discovery(
        n_clicks, category, region, language, keywords,
        min_subs, max_subs, min_views, days_back, max_channels, options,
        duration_type, min_duration, max_duration,
    ):
        if not n_clicks or _discovery_state["running"]:
            return no_update, no_update, no_update

        _discovery_state["running"]  = True
        _discovery_state["progress"] = 0
        _discovery_state["message"]  = "🚀 Iniciando descubrimiento..."
        _discovery_state["results"]  = None

        def progress_cb(pct, msg):
            _discovery_state["progress"] = pct
            _discovery_state["message"]  = msg

        def run():
            try:
                engine  = DiscoveryEngine()
                results = engine.run_discovery(
                    category_name      = category or "Entretenimiento",
                    region_code        = region if region is not None else "US",
                    language           = language or "es",
                    keywords           = keywords or "",
                    days_back          = int(days_back or 30),
                    max_channels       = int(max_channels or 30),
                    min_subs           = int(min_subs or 1000),
                    max_subs           = int(max_subs or 0),
                    use_trending       = "trending" in (options or []),
                    use_search         = "search"   in (options or []),
                    videos_per_channel = 30,
                    min_duration       = int(min_duration or 0),
                    max_duration       = int(max_duration or 0),
                    duration_api_filter= duration_type or "medium",
                    min_views          = int(min_views or 0),
                    progress_callback  = progress_cb,
                )
                _discovery_state["results"] = results
            except Exception as e:
                _discovery_state["message"] = f"❌ Error: {e}"
            finally:
                _discovery_state["running"]  = False
                _discovery_state["progress"] = 100

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return {"running": True}, False, True

    @app.callback(
        Output("disc-status-text",    "children"),
        Output("disc-progress-bar",   "value"),
        Output("disc-results-summary","children"),
        Output("disc-recent-videos",  "children"),
        Output("disc-quota-detail",   "children"),
        Output("disc-poll",           "disabled",  allow_duplicate=True),
        Output("disc-start-btn",      "disabled",  allow_duplicate=True),
        Input("disc-poll",            "n_intervals"),
        prevent_initial_call=True,
    )
    def poll_discovery(n):
        state   = _discovery_state
        running = state["running"]
        pct     = state["progress"]
        msg     = state["message"]

        summary_el = html.Div()
        recent_el  = html.Div()
        quota_el   = html.Div()

        if state["results"]:
            r = state["results"]
            summary_el = html.Div([
                dbc.Row([
                    dbc.Col(_metric_box(
                        fmt_number(r.get("channels_found", 0)),
                        "Canales", COLORS["success"]), width=2),
                    dbc.Col(_metric_box(
                        fmt_number(r.get("videos_found", 0)),
                        "Videos nuevos", COLORS["primary"]), width=2),
                    dbc.Col(_metric_box(
                        str(r.get("videos_skipped_duration", 0)),
                        "Filtrados duración", COLORS["warning"]), width=2),
                    dbc.Col(_metric_box(
                        str(r.get("videos_skipped_lang", 0)),
                        "Filtrados idioma", COLORS["warning"]), width=2),
                    dbc.Col(_metric_box(
                        str(r.get("videos_skipped_duplicate", 0)),
                        "Duplicados omitidos", COLORS["muted"]), width=2),
                    dbc.Col(_metric_box(
                        fmt_number(r.get("quota_used", 0)),
                        "Cuota usada", COLORS["danger"]), width=2),
                ], className="g-2"),
                html.Div([
                    html.P(f"❌ Errores: {', '.join(r.get('errors', []))}",
                           style={"color": COLORS["danger"], "fontSize": "0.8rem",
                                  "marginTop": "8px"})
                ]) if r.get("errors") else html.Div(),
            ])

        try:
            session = get_session()
            videos = (
                session.query(Video)
                .order_by(Video.created_at.desc())
                .limit(10)
                .all()
            )
            if videos:
                cards = []
                for v in videos:
                    sc = v.outlier_score or 0
                    sc_col = _score_color(sc)
                    from utils_app import fmt_duration
                    cards.append(html.Div([
                        html.Div([
                            html.Img(
                                src=v.thumbnail_url or "",
                                style={"width": "90px", "height": "50px",
                                       "objectFit": "cover", "borderRadius": "4px"},
                            ) if v.thumbnail_url else html.Div(
                                style={"width": "90px", "height": "50px",
                                       "background": COLORS["surface2"],
                                       "borderRadius": "4px"}
                            ),
                            html.Div([
                                html.P(
                                    (v.title or "")[:55] + ("..." if len(v.title or "") > 55 else ""),
                                    style={"color": COLORS["text"], "margin": "0",
                                           "fontSize": "0.82rem", "fontWeight": "600"}),
                                html.P(
                                    f"📺 {v.channel_title or ''} · "
                                    f"👁️ {fmt_number(v.view_count or 0)} · "
                                    f"⏱️ {fmt_duration(v.duration_seconds or 0)}",
                                    style={"color": COLORS["muted"], "margin": "0",
                                           "fontSize": "0.72rem"}),
                            ], style={"flex": 1}),
                            html.Span(
                                f"{sc:.1f}x",
                                style={"background": f"{sc_col}20", "color": sc_col,
                                       "border": f"1px solid {sc_col}",
                                       "borderRadius": "20px", "padding": "2px 10px",
                                       "fontSize": "0.78rem", "fontWeight": "700",
                                       "whiteSpace": "nowrap"},
                            ),
                        ], style={"display": "flex", "gap": "10px",
                                  "alignItems": "center"}),
                    ], style={"padding": "10px",
                              "borderBottom": f"1px solid {COLORS['border']}"}))
                recent_el = html.Div(cards)
            session.close()
        except Exception as e:
            recent_el = html.P(str(e), style={"color": COLORS["danger"]})

        try:
            session = get_session()
            used = QuotaLog.get_used_today(session)
            remaining = max(0, 10000 - used)
            pct_used = round(used / 10000 * 100, 1)
            quota_el = html.Div([
                dbc.Progress(
                    value=pct_used,
                    color="danger" if pct_used > 80 else "warning" if pct_used > 50 else "success",
                    style={"height": "8px", "borderRadius": "4px", "marginBottom": "8px"},
                    label=f"{pct_used}%",
                ),
                html.Div([
                    html.Span(f"✅ Usadas: {fmt_number(used)}",
                              style={"color": COLORS["muted"], "fontSize": "0.82rem"}),
                    html.Span(f"🕐 Restantes: {fmt_number(remaining)}",
                              style={"color": COLORS["muted"], "fontSize": "0.82rem",
                                     "marginLeft": "16px"}),
                ]),
            ])
            session.close()
        except Exception:
            pass

        return msg, pct, summary_el, recent_el, quota_el, not running, running

    @app.callback(
        Output("disc-action-feedback", "children"),
        Input("disc-recalc-btn",  "n_clicks"),
        Input("disc-cluster-btn", "n_clicks"),
        Input("disc-thumb-btn",   "n_clicks"),
        prevent_initial_call=True,
    )
    def secondary_actions(recalc, cluster, thumb):
        from dash import ctx
        triggered = ctx.triggered_id

        if triggered == "disc-recalc-btn":
            try:
                from core.outliers import OutlierEngine
                session = get_session()
                n = OutlierEngine().run(session)
                session.close()
                return dbc.Alert(f"✅ {n} outlier scores recalculados.", color="success",
                                 dismissable=True)
            except Exception as e:
                return dbc.Alert(f"❌ {e}", color="danger", dismissable=True)

        elif triggered == "disc-cluster-btn":
            try:
                from core.topics import TopicsEngine
                session = get_session()
                n = TopicsEngine().run(session)
                session.close()
                return dbc.Alert(f"✅ {n} clusters de temas generados.", color="success",
                                 dismissable=True)
            except Exception as e:
                return dbc.Alert(f"❌ {e}", color="danger", dismissable=True)

        elif triggered == "disc-thumb-btn":
            try:
                from core.thumbnails import ThumbnailEngine
                session = get_session()
                n = ThumbnailEngine().run(session, limit=100)
                session.close()
                return dbc.Alert(f"✅ {n} thumbnails analizados.", color="success",
                                 dismissable=True)
            except Exception as e:
                return dbc.Alert(f"❌ {e}", color="danger", dismissable=True)

        return no_update


def _metric_box(value, label_text, color):
    return html.Div([
        html.H5(value, style={"color": color, "margin": 0, "fontWeight": "700"}),
        html.P(label_text, style={"color": COLORS["muted"], "margin": 0,
                                  "fontSize": "0.72rem"}),
    ], style={"textAlign": "center", "padding": "10px",
              "background": COLORS["surface2"], "borderRadius": "8px"})


def _score_color(score):
    if score >= 5:  return "#ff6b35"
    if score >= 3:  return "#00d4aa"
    if score >= 1:  return "#ffd166"
    return "#718096"
