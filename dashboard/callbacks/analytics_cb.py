# dashboard/callbacks/analytics_cb.py
"""Callbacks de Mi Canal (Analytics OAuth)."""
from dash import Input, Output, html, no_update
import dash_bootstrap_components as dbc
from dashboard.layout import COLORS


def register_callbacks(app):

    @app.callback(
        Output("analytics-content", "children"),
        Input("url", "pathname"),
    )
    def render_analytics(pathname):
        if pathname != "/analytics":
            return no_update

        try:
            from connectors.youtube_analytics import YouTubeAnalyticsConnector
            conn = YouTubeAnalyticsConnector()

            if not conn.is_authenticated():
                return html.Div([
                    html.Div([
                        html.H1("🔐", style={"fontSize": "3rem", "textAlign": "center"}),
                        html.H4("Autenticación requerida",
                                style={"color": COLORS["text"], "textAlign": "center"}),
                        html.P(
                            "Para ver los analytics de tu canal necesitas autenticarte "
                            "con tu cuenta de Google/YouTube.",
                            style={"color": COLORS["muted"], "textAlign": "center",
                                   "marginBottom": "24px"},
                        ),
                        html.Div([
                            html.P("📋 Pasos para activar:", style={"color": COLORS["text"],
                                                                     "fontWeight": "700"}),
                            html.Ol([
                                html.Li("Crea un proyecto en Google Cloud Console",
                                        style={"color": COLORS["muted"]}),
                                html.Li("Activa YouTube Data API v3 y YouTube Analytics API",
                                        style={"color": COLORS["muted"]}),
                                html.Li("Crea credenciales OAuth 2.0 → Aplicación de escritorio",
                                        style={"color": COLORS["muted"]}),
                                html.Li("Descarga client_secret.json a la raíz del proyecto",
                                        style={"color": COLORS["muted"]}),
                                html.Li("Agrega tu correo como usuario de prueba en la pantalla de consentimiento",
                                        style={"color": COLORS["muted"]}),
                            ], style={"paddingLeft": "20px"}),
                        ], style={
                            "background":   COLORS["surface2"],
                            "borderRadius": "10px",
                            "padding":      "16px 20px",
                            "marginBottom": "20px",
                        }),
                        dbc.Button(
                            "🔐 Autenticar con YouTube",
                            id="analytics-auth-btn",
                            color="primary",
                            style={
                                "display":      "block",
                                "margin":       "0 auto",
                                "background":   COLORS["primary"],
                                "border":       "none",
                                "borderRadius": "10px",
                                "padding":      "12px 32px",
                                "fontWeight":   "700",
                            },
                        ),
                        html.Div(id="analytics-auth-result", style={"marginTop": "16px",
                                                                      "textAlign": "center"}),
                    ], style={
                        "maxWidth":     "500px",
                        "margin":       "60px auto",
                        "background":   COLORS["surface"],
                        "borderRadius": "16px",
                        "padding":      "40px",
                        "border":       f"1px solid {COLORS['border']}",
                    }),
                ])

            # Autenticado → mostrar métricas básicas
            return html.Div([
                dbc.Alert(
                    "✅ Conectado con YouTube Analytics API. "
                    "Las métricas avanzadas de tu canal están disponibles.",
                    color="success",
                ),
                html.P(
                    "Los datos de retención, CTR e impresiones solo están disponibles "
                    "para tu propio canal y requieren autenticación OAuth.",
                    style={"color": COLORS["muted"]},
                ),
            ])

        except ImportError:
            return dbc.Alert(
                "El módulo de Analytics no está disponible. "
                "Verifica que google-auth-oauthlib está instalado.",
                color="warning",
            )

    @app.callback(
        Output("analytics-auth-result", "children"),
        Input("analytics-auth-btn",     "n_clicks"),
        prevent_initial_call=True,
    )
    def do_auth(n_clicks):
        if not n_clicks:
            return no_update
        try:
            from connectors.youtube_analytics import YouTubeAnalyticsConnector
            conn    = YouTubeAnalyticsConnector()
            success = conn.authenticate()
            if success:
                return dbc.Alert("✅ Autenticación exitosa. Recarga la página.",
                                 color="success")
            return dbc.Alert("❌ Error en la autenticación.", color="danger")
        except Exception as e:
            return dbc.Alert(f"❌ {e}", color="danger")