"""
Layout UI — Versión definitiva en español.
Tema oscuro profesional con CSS corregido para dropdowns/sliders.
+ Filtro global por categoría
"""
import dash_bootstrap_components as dbc
from dash import dcc, html
from core.youtube_api import YOUTUBE_CATEGORIES, REGIONS, LANGUAGES

# ─────────────────────────────────────────────────────────────────────────
#  COLORES
# ─────────────────────────────────────────────────────────────────────────
COLORS = {
    "bg":      "#0f1117",
    "surface": "#1a1d2e",
    "surface2":"#22263a",
    "border":  "#2d3250",
    "primary": "#6c63ff",
    "success": "#00d4aa",
    "warning": "#ffd166",
    "danger":  "#ef476f",
    "text":    "#e2e8f0",
    "muted":   "#94a3b8",
    "viral":   "#ff6b35",
}

CARD = {
    "background":   COLORS["surface"],
    "border":       f"1px solid {COLORS['border']}",
    "borderRadius": "12px",
    "padding":      "20px",
    "marginBottom": "16px",
}

SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0,
    "width": "260px", "background": COLORS["surface"],
    "borderRight": f"1px solid {COLORS['border']}",
    "padding": "0", "overflowY": "auto", "zIndex": 1000,
}

CONTENT_STYLE = {
    "marginLeft": "260px", "background": COLORS["bg"],
    "minHeight": "100vh", "padding": "24px",
}

# CSS global AGRESIVO para forzar tema oscuro en TODOS los componentes
GLOBAL_CSS = """
/* ── Dropdowns oscuros (Dash V1 + V2) ────────────────────── */
.Select-control, .Select-menu-outer,
.dash-dropdown .Select-control,
.dash-dropdown .Select-menu-outer {
    background-color: #22263a !important;
    border-color: #2d3250 !important;
    color: #e2e8f0 !important;
}
.Select-value-label, .Select-placeholder,
.Select-input > input,
.Select--single > .Select-control .Select-value .Select-value-label {
    color: #e2e8f0 !important;
}
.Select-option {
    background-color: #22263a !important;
    color: #e2e8f0 !important;
}
.Select-option.is-focused {
    background-color: #6c63ff !important;
    color: white !important;
}
.Select-option.is-selected {
    background-color: #3d3a70 !important;
}
.Select-arrow { border-color: #94a3b8 transparent transparent !important; }
.Select.is-open > .Select-control { border-color: #6c63ff !important; }

/* Dash Dropdown V2 (react-select nuevo) */
.dash-dropdown .VirtualizedSelectOption {
    background-color: #22263a !important;
    color: #e2e8f0 !important;
}
.dash-dropdown .VirtualizedSelectFocusedOption {
    background-color: #6c63ff !important;
    color: white !important;
}
.dash-dropdown .Select-menu {
    background-color: #22263a !important;
}
.css-1fdsij3-ValueContainer,
.css-13cymwt-control,
.css-1nmdiq5-menu,
.css-t3ipsp-control,
.css-qbdosj-Input,
.css-1dimb5e-singleValue,
.css-1pndypt-ValueContainer,
.css-wsp2cs-ValueContainer,
div[class*="-control"],
div[class*="-menu"],
div[class*="-singleValue"],
div[class*="-placeholder"],
div[class*="-input"] {
    background-color: #22263a !important;
    color: #e2e8f0 !important;
    border-color: #2d3250 !important;
}
div[class*="-menu"] > div {
    background-color: #22263a !important;
    color: #e2e8f0 !important;
}
div[class*="-option"]:hover,
div[class*="-option"][class*="focused"] {
    background-color: #6c63ff !important;
    color: white !important;
}

/* ── Inputs ─────────────────────────────────────────────── */
input.form-control, .form-control,
input[type="text"], input[type="number"], input[type="password"],
input[type="search"] {
    background-color: #22263a !important;
    border-color: #2d3250 !important;
    color: #e2e8f0 !important;
}
input.form-control:focus, .form-control:focus,
input:focus {
    border-color: #6c63ff !important;
    box-shadow: 0 0 0 0.2rem rgba(108,99,255,0.25) !important;
    background-color: #22263a !important;
    color: #e2e8f0 !important;
}
input::placeholder { color: #64748b !important; }

/* ── SLIDERS 100% OSCUROS (el fix crítico) ─────────────── */
.rc-slider { background-color: transparent !important; }
.rc-slider-rail {
    background-color: #2d3250 !important;
    border-color: #2d3250 !important;
}
.rc-slider-track {
    background-color: #6c63ff !important;
}
.rc-slider-handle {
    border-color: #6c63ff !important;
    background-color: #6c63ff !important;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.3) !important;
}
.rc-slider-handle:hover,
.rc-slider-handle:focus,
.rc-slider-handle:active {
    border-color: #847dff !important;
    background-color: #847dff !important;
    box-shadow: 0 0 0 5px rgba(108,99,255,0.4) !important;
}
.rc-slider-dot {
    background-color: #2d3250 !important;
    border-color: #2d3250 !important;
}
.rc-slider-dot-active {
    border-color: #6c63ff !important;
    background-color: #6c63ff !important;
}
.rc-slider-mark-text {
    color: #94a3b8 !important;
    font-size: 0.72rem !important;
}
.rc-slider-mark-text-active { color: #e2e8f0 !important; }

/* Tooltip del slider — FORZAR OSCURO */
.rc-slider-tooltip,
.rc-slider-tooltip *,
.rc-slider-tooltip-content,
.rc-slider-tooltip-content * {
    background-color: #1a1d2e !important;
    color: #e2e8f0 !important;
    border-color: #6c63ff !important;
}
.rc-slider-tooltip-inner,
.rc-slider-tooltip-inner * {
    background-color: #1a1d2e !important;
    color: #e2e8f0 !important;
    border: 1px solid #6c63ff !important;
    border-radius: 6px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    padding: 4px 10px !important;
    text-align: center !important;
    min-width: 40px !important;
}
.rc-slider-tooltip-placement-bottom .rc-slider-tooltip-arrow {
    border-bottom-color: #6c63ff !important;
    border-top-color: transparent !important;
}
.rc-slider-tooltip-placement-top .rc-slider-tooltip-arrow {
    border-top-color: #6c63ff !important;
    border-bottom-color: transparent !important;
}

/* Inputs dentro de tooltips (para editar valores) */
.rc-slider-tooltip input,
.rc-slider-tooltip-content input {
    background-color: #1a1d2e !important;
    color: #e2e8f0 !important;
    border: 1px solid #6c63ff !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
    width: 60px !important;
    text-align: center !important;
    font-weight: 700 !important;
}

/* ── Checklists ─────────────────────────────────────────── */
.form-check-input {
    background-color: #22263a !important;
    border-color: #2d3250 !important;
}
.form-check-input:checked {
    background-color: #6c63ff !important;
    border-color: #6c63ff !important;
}
.form-check-label { color: #e2e8f0 !important; }

/* ── Tabs ───────────────────────────────────────────────── */
.nav-link { color: #94a3b8 !important; }
.nav-link.active {
    color: #6c63ff !important;
    border-bottom: 2px solid #6c63ff !important;
    background: transparent !important;
}

/* ── Sidebar ────────────────────────────────────────────── */
.sidebar-link:hover { background: #22263a !important; }
a.nav-link.active.sidebar-link {
    background: #6c63ff20 !important;
    color: #6c63ff !important;
}

/* ── Progress bar ───────────────────────────────────────── */
.progress { background-color: #22263a !important; }
.progress-bar { background-color: #6c63ff !important; }

/* ── Scrollbar ──────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2d3250; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #6c63ff; }

/* ── Alerts ─────────────────────────────────────────────── */
.alert { border-radius: 10px !important; }
.alert-success { background-color: #00d4aa20 !important; border-color: #00d4aa !important; color: #00d4aa !important; }
.alert-danger  { background-color: #ef476f20 !important; border-color: #ef476f !important; color: #ef476f !important; }
.alert-warning { background-color: #ffd16620 !important; border-color: #ffd166 !important; color: #ffd166 !important; }

/* ── Botones ────────────────────────────────────────────── */
.btn-outline-secondary {
    color: #e2e8f0 !important;
    border-color: #2d3250 !important;
    background: transparent !important;
}
.btn-outline-secondary:hover {
    background-color: #22263a !important;
    color: #e2e8f0 !important;
    border-color: #6c63ff !important;
}

/* ── Tablas ─────────────────────────────────────────────── */
.table { color: #e2e8f0 !important; }
.table th { background-color: #22263a !important; color: #e2e8f0 !important; }

/* ── General ────────────────────────────────────────────── */
body { background-color: #0f1117 !important; color: #e2e8f0 !important; }
* { box-sizing: border-box; }
"""


# ─────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────
def metric_card(title, value, icon, color, subtitle=""):
    return html.Div([
        html.Div([
            html.Div([html.Span(icon, style={"fontSize": "1.5rem"})],
                     style={"background": f"{color}20", "borderRadius": "10px",
                            "padding": "10px", "display": "flex", "alignItems": "center"}),
            html.Div([
                html.P(title, style={"color": COLORS["muted"], "fontSize": "0.78rem",
                                     "margin": "0", "fontWeight": "500",
                                     "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.H3(value, style={"color": COLORS["text"], "margin": "2px 0 0",
                                      "fontSize": "1.6rem", "fontWeight": "700"}),
                html.P(subtitle, style={"color": COLORS["muted"], "fontSize": "0.72rem",
                                        "margin": "0"}) if subtitle else html.Div(),
            ]),
        ], style={"display": "flex", "gap": "14px", "alignItems": "center"}),
    ], style={**CARD, "padding": "16px 20px"})


def label(text):
    return html.Label(text, style={
        "color": COLORS["muted"], "fontSize": "0.82rem",
        "fontWeight": "600", "textTransform": "uppercase",
        "marginBottom": "4px", "display": "block",
    })


def dropdown(id, options, value, **kwargs):
    return dcc.Dropdown(
        id=id, options=options, value=value, clearable=False,
        style={"marginBottom": "14px",
               "backgroundColor": COLORS["surface2"],
               "color": COLORS["text"]},
        **kwargs,
    )


# ─────────────────────────────────────────────────────────────────────────
#  SIDEBAR (con filtro global por categoría)
# ─────────────────────────────────────────────────────────────────────────
def build_sidebar():
    items = [
        ("🏠", "Panel Principal",       "/"),
        ("🔍", "Descubrir Videos",      "/discovery"),
        ("📺", "Descubrir Canales",     "/channels"),
        ("🔥", "Outliers",              "/outliers"),
        ("⭐", "Favoritos",             "/favorites"),
        ("📡", "Competidores",          "/competitors"),
        ("🖼️", "Thumbnails",            "/thumbnails"),
        ("📊", "Mi Canal",              "/analytics"),
        ("⚙️", "Configuración",         "/settings"),
    ]
    links = [
        dbc.NavLink(
            [html.Span(i, style={"marginRight": "10px", "fontSize": "1.1rem"}), l],
            href=h, active="exact",
            style={"color": COLORS["text"], "padding": "10px 20px",
                   "borderRadius": "8px", "margin": "2px 10px",
                   "fontSize": "0.88rem", "fontWeight": "500"},
            className="sidebar-link",
        ) for i, l, h in items
    ]

    return html.Div([
        html.Div([
            html.Div("🚀", style={"fontSize": "2rem"}),
            html.Div([
                html.H6("YT Outlier Lab", style={"color": COLORS["text"], "margin": 0,
                                                  "fontWeight": "700"}),
                html.P("Pro Analytics", style={"color": COLORS["primary"], "margin": 0,
                                               "fontSize": "0.72rem", "fontWeight": "600"}),
            ]),
        ], style={"display": "flex", "alignItems": "center", "gap": "12px",
                  "padding": "20px", "borderBottom": f"1px solid {COLORS['border']}",
                  "marginBottom": "10px"}),

        dbc.Nav(links, vertical=True, pills=True),

        html.Div([
            html.Div(id="sidebar-quota-display"),
            html.Div(id="sidebar-db-stats"),
        ], style={"position": "absolute", "bottom": 0, "left": 0, "right": 0,
                  "padding": "16px", "borderTop": f"1px solid {COLORS['border']}",
                  "background": COLORS["surface"]}),
    ], style=SIDEBAR_STYLE)


# ─────────────────────────────────────────────────────────────────────────
#  PÁGINAS
# ─────────────────────────────────────────────────────────────────────────
def page_dashboard():
    return html.Div([
        html.H2("📊 Panel Principal", style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Visión general de toda tu base de datos de YouTube.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),
        html.Div([
            html.P("💡 Tip: Usa el filtro global del sidebar para enfocar todos los datos en un nicho específico.",
                   style={"color": COLORS["primary"], "margin": "0 0 12px",
                          "fontSize": "0.85rem", "fontStyle": "italic"}),
        ], style={**CARD, "padding": "12px 20px"}),
        html.Div(id="dashboard-metrics"),
        dbc.Row([
            dbc.Col([html.Div([
                html.H5("🔥 Top 10 Outliers", style={"color": COLORS["text"], "marginBottom": "16px"}),
                html.Div(id="dashboard-top-outliers"),
            ], style=CARD)], width=8),
            dbc.Col([html.Div([
                html.H5("🏆 Top Canales", style={"color": COLORS["text"], "marginBottom": "16px"}),
                html.Div(id="dashboard-top-channels"),
            ], style=CARD)], width=4),
        ]),
        dbc.Row([
            dbc.Col([html.Div([
                html.H5("📈 Distribución de Outlier Scores",
                        style={"color": COLORS["text"], "marginBottom": "12px"}),
                dcc.Graph(id="dashboard-score-dist", config={"displayModeBar": False}),
            ], style=CARD)], width=6),
            dbc.Col([html.Div([
                html.H5("🏷️ Videos por Categoría",
                        style={"color": COLORS["text"], "marginBottom": "12px"}),
                dcc.Graph(id="dashboard-category-pie", config={"displayModeBar": False}),
            ], style=CARD)], width=6),
        ]),
        dcc.Interval(id="dashboard-refresh", interval=30000, n_intervals=0),
    ])


def page_discovery():
    return html.Div([
        html.H2("🔍 Descubrir Videos", style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Busca automáticamente entre miles de videos. Solo configura los parámetros.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),
        dbc.Row([
            dbc.Col([html.Div([
                html.H5("⚙️ Parámetros de búsqueda",
                        style={"color": COLORS["text"], "marginBottom": "20px"}),

                label("🎯 Nicho / Categoría"),
                dropdown("disc-category",
                         [{"label": k, "value": k} for k in YOUTUBE_CATEGORIES],
                         "Entretenimiento"),

                label("🌍 Región / País"),
                dropdown("disc-region",
                         [{"label": k, "value": v} for k, v in REGIONS.items()],
                         "US"),

                label("🗣️ Idioma"),
                dropdown("disc-language",
                         [{"label": k, "value": v} for k, v in LANGUAGES.items()],
                         "es"),

                label("🔑 Palabras clave adicionales (separar con coma)"),
                dbc.Input(
                    id="disc-keywords", type="text",
                    placeholder="ej: minecraft, fortnite, gameplay...",
                    style={"background": COLORS["surface2"],
                           "border": f"1px solid {COLORS['border']}",
                           "color": COLORS["text"], "borderRadius": "8px",
                           "marginBottom": "14px"},
                ),

                html.Hr(style={"borderColor": COLORS["border"]}),

                # ── FILTROS DE DURACIÓN ──────────────────────────────
                html.H6("⏱️ Filtro de Duración",
                        style={"color": COLORS["text"], "marginBottom": "10px",
                               "marginTop": "8px"}),

                label("Tipo de contenido"),
                dropdown("disc-duration-type", [
                    {"label": "🎬 Solo videos largos (> 20 min)",      "value": "long"},
                    {"label": "📹 Videos medios (4-20 min)",           "value": "medium"},
                    {"label": "📱 Solo Shorts (< 4 min)",             "value": "short"},
                    {"label": "🔄 Todos (incluye Shorts)",            "value": "any"},
                ], "medium"),

                label("Duración mínima (segundos)"),
                dcc.Slider(
                    id="disc-min-duration",
                    min=0, max=3600, step=30, value=240,
                    marks={
                        0:    {"label": "0s",     "style": {"color": COLORS["muted"]}},
                        60:   {"label": "1 min",  "style": {"color": COLORS["muted"]}},
                        240:  {"label": "4 min",  "style": {"color": COLORS["muted"]}},
                        600:  {"label": "10 min", "style": {"color": COLORS["muted"]}},
                        1200: {"label": "20 min", "style": {"color": COLORS["muted"]}},
                        3600: {"label": "1 hora", "style": {"color": COLORS["muted"]}},
                    },
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Div(style={"height": "12px"}),

                label("Duración máxima (segundos) — 0 = sin límite"),
                dcc.Slider(
                    id="disc-max-duration",
                    min=0, max=7200, step=60, value=0,
                    marks={
                        0:    {"label": "∞",       "style": {"color": COLORS["muted"]}},
                        600:  {"label": "10 min",  "style": {"color": COLORS["muted"]}},
                        1200: {"label": "20 min",  "style": {"color": COLORS["muted"]}},
                        3600: {"label": "1 hora",  "style": {"color": COLORS["muted"]}},
                        7200: {"label": "2 horas", "style": {"color": COLORS["muted"]}},
                    },
                    tooltip={"placement": "bottom", "always_visible": True},
                ),

                html.Hr(style={"borderColor": COLORS["border"]}),

                # ── FILTROS DE CANAL ─────────────────────────────────
                label("📊 Suscriptores mínimos del canal"),
                dcc.Slider(
                    id="disc-min-subs",
                    min=0, max=1000000, step=1000, value=5000,
                    marks={
                        0:       {"label": "0",    "style": {"color": COLORS["muted"]}},
                        10000:   {"label": "10K",  "style": {"color": COLORS["muted"]}},
                        100000:  {"label": "100K", "style": {"color": COLORS["muted"]}},
                        500000:  {"label": "500K", "style": {"color": COLORS["muted"]}},
                        1000000: {"label": "1M",   "style": {"color": COLORS["muted"]}},
                    },
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Div(style={"height": "12px"}),

                label("📊 Suscriptores máximos del canal (0 = sin límite)"),
                dcc.Slider(
                    id="disc-max-subs",
                    min=0, max=10000000, step=10000, value=0,
                    marks={
                        0:        {"label": "∞",    "style": {"color": COLORS["muted"]}},
                        100000:   {"label": "100K", "style": {"color": COLORS["muted"]}},
                        1000000:  {"label": "1M",   "style": {"color": COLORS["muted"]}},
                        5000000:  {"label": "5M",   "style": {"color": COLORS["muted"]}},
                        10000000: {"label": "10M",  "style": {"color": COLORS["muted"]}},
                    },
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Div(style={"height": "12px"}),

                label("👁️ Views mínimas por video"),
                dcc.Slider(
                    id="disc-min-views",
                    min=0, max=1000000, step=1000, value=0,
                    marks={
                        0:       {"label": "0",    "style": {"color": COLORS["muted"]}},
                        1000:    {"label": "1K",   "style": {"color": COLORS["muted"]}},
                        10000:   {"label": "10K",  "style": {"color": COLORS["muted"]}},
                        100000:  {"label": "100K", "style": {"color": COLORS["muted"]}},
                        1000000: {"label": "1M",   "style": {"color": COLORS["muted"]}},
                    },
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Div(style={"height": "12px"}),

                label("📅 Videos de los últimos N días"),
                dcc.Slider(
                    id="disc-days-back",
                    min=7, max=365, step=7, value=30,
                    marks={
                        7:   {"label": "7d",    "style": {"color": COLORS["muted"]}},
                        30:  {"label": "30d",   "style": {"color": COLORS["muted"]}},
                        90:  {"label": "90d",   "style": {"color": COLORS["muted"]}},
                        180: {"label": "6 meses","style": {"color": COLORS["muted"]}},
                        365: {"label": "1 año", "style": {"color": COLORS["muted"]}},
                    },
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Div(style={"height": "12px"}),

                label("📺 Máximo de canales a analizar"),
                dcc.Slider(
                    id="disc-max-channels",
                    min=5, max=100, step=5, value=30,
                    marks={
                        5:   {"label": "5",   "style": {"color": COLORS["muted"]}},
                        25:  {"label": "25",  "style": {"color": COLORS["muted"]}},
                        50:  {"label": "50",  "style": {"color": COLORS["muted"]}},
                        100: {"label": "100", "style": {"color": COLORS["muted"]}},
                    },
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Div(style={"height": "12px"}),

                label("🔧 Fuentes de búsqueda"),
                dbc.Checklist(
                    id="disc-options",
                    options=[
                        {"label": " 🔥 Incluir tendencias (gratis, 1 unidad)",
                         "value": "trending"},
                        {"label": " 🔍 Búsqueda por palabras clave (100 unidades c/u)",
                         "value": "search"},
                    ],
                    value=["trending", "search"],
                    style={"color": COLORS["text"], "marginBottom": "16px"},
                ),

                html.Hr(style={"borderColor": COLORS["border"]}),

                dbc.Button(
                    [html.Span("🚀"), " Iniciar Descubrimiento"],
                    id="disc-start-btn", color="primary", size="lg",
                    style={"width": "100%", "background": COLORS["primary"],
                           "border": "none", "borderRadius": "10px",
                           "fontWeight": "700", "padding": "14px"},
                    className="mb-2",
                ),
                dbc.Button(
                    [html.Span("🧮"), " Re-calcular Outliers"],
                    id="disc-recalc-btn", color="secondary", outline=True,
                    size="sm", style={"width": "100%", "borderRadius": "8px"},
                    className="mb-1",
                ),
                dbc.Button(
                    [html.Span("🏷️"), " Re-clusterizar Temas"],
                    id="disc-cluster-btn", color="secondary", outline=True,
                    size="sm", style={"width": "100%", "borderRadius": "8px"},
                    className="mb-1",
                ),
                dbc.Button(
                    [html.Span("🖼️"), " Analizar Thumbnails"],
                    id="disc-thumb-btn", color="secondary", outline=True,
                    size="sm", style={"width": "100%", "borderRadius": "8px"},
                ),
                html.Div(id="disc-action-feedback", style={"marginTop": "12px"}),
            ], style=CARD)], width=4),

            dbc.Col([
                html.Div([
                    html.H5("📡 Estado del Descubrimiento",
                            style={"color": COLORS["text"], "marginBottom": "16px"}),
                    html.Div(id="disc-status-text",
                             style={"color": COLORS["muted"], "marginBottom": "10px",
                                    "fontSize": "0.9rem"}),
                    dbc.Progress(id="disc-progress-bar", value=0,
                                 style={"height": "8px", "borderRadius": "4px"}, color="primary"),
                    html.Div(id="disc-results-summary", style={"marginTop": "20px"}),
                ], style=CARD),

                html.Div([
                    html.H5("📋 Últimos videos descubiertos",
                            style={"color": COLORS["text"], "marginBottom": "16px"}),
                    html.Div(id="disc-recent-videos"),
                ], style=CARD),

                html.Div([
                    html.H5("📊 Uso de Cuota API (hoy)",
                            style={"color": COLORS["text"], "marginBottom": "12px"}),
                    html.Div(id="disc-quota-detail"),
                ], style=CARD),
            ], width=8),
        ]),
        dcc.Store(id="disc-store", data={"running": False}),
        dcc.Interval(id="disc-poll", interval=2000, n_intervals=0, disabled=True),
    ])


def page_channels():
    """Página dedicada para descubrir CANALES."""
    return html.Div([
        html.H2("📺 Descubrir Canales", style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Encuentra canales por nicho o explora los que ya tienes en tu base de datos.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),

        # ── NUEVO: Selector de modo ──────────────────────────────────
        html.Div([
            dbc.RadioItems(
                id="ch-mode",
                options=[
                    {"label": " 🔍 Buscar canales nuevos (API)",  "value": "api"},
                    {"label": " 📂 Explorar canales de la base de datos", "value": "db"},
                ],
                value="api",
                inline=True,
                style={"color": COLORS["text"], "fontSize": "0.95rem"},
            ),
        ], style={**CARD, "padding": "16px 20px", "marginBottom": "20px"}),

        dbc.Row([
            dbc.Col([html.Div([
                # ── MODO API (existente) ─────────────────────────────
                html.Div(id="ch-api-controls", children=[
                    html.H5("⚙️ Filtros de búsqueda de canales",
                            style={"color": COLORS["text"], "marginBottom": "20px"}),

                    label("🔑 Palabras clave (separar con coma)"),
                    dbc.Input(
                        id="ch-keywords", type="text",
                        placeholder="ej: recetas, cocina mexicana, comida...",
                        style={"background": COLORS["surface2"],
                               "border": f"1px solid {COLORS['border']}",
                               "color": COLORS["text"], "borderRadius": "8px",
                               "marginBottom": "14px"},
                    ),

                    label("🌍 Región / País"),
                    dropdown("ch-region",
                             [{"label": k, "value": v} for k, v in REGIONS.items()],
                             "US"),

                    label("🗣️ Idioma"),
                    dropdown("ch-language",
                             [{"label": k, "value": v} for k, v in LANGUAGES.items()],
                             "es"),

                    # ── NUEVO: Selector de categoría para búsqueda API ──
                    label("🏷️ Nicho / Categoría"),
                    dropdown("ch-category",
                             [{"label": k, "value": k} for k in YOUTUBE_CATEGORIES],
                             "Entretenimiento"),

                    html.Hr(style={"borderColor": COLORS["border"]}),

                    label("📊 Suscriptores MÍNIMOS"),
                    dcc.Slider(
                        id="ch-min-subs",
                        min=0, max=1000000, step=1000, value=5000,
                        marks={
                            0:       {"label": "0",    "style": {"color": COLORS["muted"]}},
                            10000:   {"label": "10K",  "style": {"color": COLORS["muted"]}},
                            100000:  {"label": "100K", "style": {"color": COLORS["muted"]}},
                            500000:  {"label": "500K", "style": {"color": COLORS["muted"]}},
                            1000000: {"label": "1M",   "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"height": "12px"}),

                    label("📊 Suscriptores MÁXIMOS (0 = sin límite)"),
                    dcc.Slider(
                        id="ch-max-subs",
                        min=0, max=10000000, step=10000, value=0,
                        marks={
                            0:        {"label": "∞",    "style": {"color": COLORS["muted"]}},
                            100000:   {"label": "100K", "style": {"color": COLORS["muted"]}},
                            1000000:  {"label": "1M",   "style": {"color": COLORS["muted"]}},
                            5000000:  {"label": "5M",   "style": {"color": COLORS["muted"]}},
                            10000000: {"label": "10M",  "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"height": "12px"}),

                    label("🎬 Cantidad mínima de videos del canal"),
                    dcc.Slider(
                        id="ch-min-videos",
                        min=0, max=1000, step=10, value=20,
                        marks={
                            0:    {"label": "0",    "style": {"color": COLORS["muted"]}},
                            50:   {"label": "50",   "style": {"color": COLORS["muted"]}},
                            100:  {"label": "100",  "style": {"color": COLORS["muted"]}},
                            500:  {"label": "500",  "style": {"color": COLORS["muted"]}},
                            1000: {"label": "1000", "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"height": "12px"}),

                    label("👁️ Views totales mínimas del canal"),
                    dcc.Slider(
                        id="ch-min-total-views",
                        min=0, max=100000000, step=100000, value=0,
                        marks={
                            0:         {"label": "0",    "style": {"color": COLORS["muted"]}},
                            100000:    {"label": "100K", "style": {"color": COLORS["muted"]}},
                            1000000:   {"label": "1M",   "style": {"color": COLORS["muted"]}},
                            10000000:  {"label": "10M",  "style": {"color": COLORS["muted"]}},
                            100000000: {"label": "100M", "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"height": "12px"}),

                    label("🔢 Máximo de canales a buscar"),
                    dcc.Slider(
                        id="ch-max-results",
                        min=5, max=100, step=5, value=25,
                        marks={
                            5:   {"label": "5",   "style": {"color": COLORS["muted"]}},
                            25:  {"label": "25",  "style": {"color": COLORS["muted"]}},
                            50:  {"label": "50",  "style": {"color": COLORS["muted"]}},
                            100: {"label": "100", "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),

                    html.Hr(style={"borderColor": COLORS["border"]}),

                    dbc.Button(
                        [html.Span("🚀"), " Buscar Canales"],
                        id="ch-start-btn", color="primary", size="lg",
                        style={"width": "100%", "background": COLORS["primary"],
                               "border": "none", "borderRadius": "10px",
                               "fontWeight": "700", "padding": "14px"},
                        className="mb-2",
                    ),
                    html.H6("⚡ Acciones sobre canales encontrados",
                            style={"color": COLORS["text"], "marginTop": "16px",
                                   "marginBottom": "10px"}),
                    dbc.Button(
                        [html.Span("🔥"), " Analizar Outliers de estos canales"],
                        id="ch-analyze-outliers-btn", color="warning", outline=True,
                        style={"width": "100%", "borderRadius": "8px", "marginBottom": "6px"},
                    ),
                    dbc.Button(
                        [html.Span("📥"), " Cargar videos de estos canales"],
                        id="ch-load-videos-btn", color="success", outline=True,
                        style={"width": "100%", "borderRadius": "8px"},
                    ),
                    html.Div(id="ch-actions-feedback", style={"marginTop": "10px"}),
                ]),

                # ── MODO DB (nuevo) ──────────────────────────────────
                html.Div(id="ch-db-controls", style={"display": "none"}, children=[
                    html.H5("📂 Explorar canales de la base de datos",
                            style={"color": COLORS["text"], "marginBottom": "20px"}),

                    label("🔍 Buscar por nombre"),
                    dbc.Input(
                        id="ch-db-search", type="text",
                        placeholder="Escribe para filtrar canales...",
                        style={"background": COLORS["surface2"],
                               "border": f"1px solid {COLORS['border']}",
                               "color": COLORS["text"], "borderRadius": "8px",
                               "marginBottom": "14px"},
                    ),

                    label("🏷️ Categoría / Nicho"),
                    dcc.Dropdown(
                        id="ch-db-category",
                        options=[{"label": "🌐 Todas las categorías", "value": "all"}] + [
                            {"label": k, "value": k}
                            for k in YOUTUBE_CATEGORIES.keys() if k != "Todos"
                        ],
                        value="all",
                        clearable=False,
                        style={"marginBottom": "14px"},
                    ),

                    label("🌍 Región / País"),
                    dcc.Dropdown(
                        id="ch-db-region",
                        options=[{"label": "🌐 Todos los países", "value": "all"}] + [
                            {"label": k, "value": v} for k, v in REGIONS.items() if v
                        ],
                        value="all",
                        clearable=False,
                        style={"marginBottom": "14px"},
                    ),

                    label("🗣️ Idioma"),
                    dcc.Dropdown(
                        id="ch-db-language",
                        options=[{"label": "🌐 Todos los idiomas", "value": "all"}] + [
                            {"label": k, "value": v} for k, v in LANGUAGES.items()
                        ],
                        value="all",
                        clearable=False,
                        style={"marginBottom": "14px"},
                    ),

                    html.Hr(style={"borderColor": COLORS["border"]}),

                    label("📊 Suscriptores MÍNIMOS"),
                    dcc.Slider(
                        id="ch-db-min-subs",
                        min=0, max=1000000, step=1000, value=0,
                        marks={
                            0:       {"label": "0",    "style": {"color": COLORS["muted"]}},
                            10000:   {"label": "10K",  "style": {"color": COLORS["muted"]}},
                            100000:  {"label": "100K", "style": {"color": COLORS["muted"]}},
                            500000:  {"label": "500K", "style": {"color": COLORS["muted"]}},
                            1000000: {"label": "1M",   "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"height": "12px"}),

                    label("📊 Suscriptores MÁXIMOS (0 = sin límite)"),
                    dcc.Slider(
                        id="ch-db-max-subs",
                        min=0, max=10000000, step=10000, value=0,
                        marks={
                            0:        {"label": "∞",    "style": {"color": COLORS["muted"]}},
                            100000:   {"label": "100K", "style": {"color": COLORS["muted"]}},
                            1000000:  {"label": "1M",   "style": {"color": COLORS["muted"]}},
                            5000000:  {"label": "5M",   "style": {"color": COLORS["muted"]}},
                            10000000: {"label": "10M",  "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"height": "12px"}),

                    label("🎬 Videos MÍNIMOS del canal"),
                    dcc.Slider(
                        id="ch-db-min-videos",
                        min=0, max=1000, step=10, value=0,
                        marks={
                            0:    {"label": "0",    "style": {"color": COLORS["muted"]}},
                            50:   {"label": "50",   "style": {"color": COLORS["muted"]}},
                            100:  {"label": "100",  "style": {"color": COLORS["muted"]}},
                            500:  {"label": "500",  "style": {"color": COLORS["muted"]}},
                            1000: {"label": "1000", "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"height": "12px"}),

                    label("👁️ Views totales MÍNIMAS"),
                    dcc.Slider(
                        id="ch-db-min-views",
                        min=0, max=100000000, step=100000, value=0,
                        marks={
                            0:         {"label": "0",    "style": {"color": COLORS["muted"]}},
                            100000:    {"label": "100K", "style": {"color": COLORS["muted"]}},
                            1000000:   {"label": "1M",   "style": {"color": COLORS["muted"]}},
                            10000000:  {"label": "10M",  "style": {"color": COLORS["muted"]}},
                            100000000: {"label": "100M", "style": {"color": COLORS["muted"]}},
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"height": "12px"}),

                    html.Hr(style={"borderColor": COLORS["border"]}),

                    label("📊 Ordenar por"),
                    dropdown("ch-db-sort", [
                        {"label": "Suscriptores (mayor a menor)", "value": "subs_desc"},
                        {"label": "Suscriptores (menor a mayor)", "value": "subs_asc"},
                        {"label": "Videos (mayor a menor)",       "value": "videos_desc"},
                        {"label": "Views totales",                "value": "views_desc"},
                        {"label": "Nombre (A-Z)",                 "value": "name_asc"},
                    ], "subs_desc"),

                    label("🔢 Máximo de resultados"),
                    dropdown("ch-db-limit", [
                        {"label": "25 canales",  "value": 25},
                        {"label": "50 canales",  "value": 50},
                        {"label": "100 canales", "value": 100},
                        {"label": "200 canales", "value": 200},
                        {"label": "500 canales", "value": 500},
                    ], 50),

                    html.Hr(style={"borderColor": COLORS["border"]}),

                    dbc.Button(
                        [html.Span("📂"), " Explorar Base de Datos"],
                        id="ch-db-explore-btn", color="success", size="lg",
                        style={"width": "100%", "background": COLORS["success"],
                               "border": "none", "borderRadius": "10px",
                               "fontWeight": "700", "padding": "14px",
                               "color": "#0f1117"},
                    ),
                ]),

            ], style=CARD)], width=4),

            dbc.Col([
                html.Div([
                    html.H5("📡 Estado", style={"color": COLORS["text"], "marginBottom": "12px"}),
                    html.Div(id="ch-status",
                             style={"color": COLORS["muted"], "fontSize": "0.9rem"}),
                    dbc.Progress(id="ch-progress", value=0,
                                 style={"height": "8px", "borderRadius": "4px",
                                        "marginTop": "10px"}, color="primary"),
                ], style=CARD),

                html.Div([
                    html.H5("📺 Canales Descubiertos",
                            style={"color": COLORS["text"], "marginBottom": "16px"}),
                    html.Div(id="ch-results-list"),
                ], style=CARD),

                html.Div([
                    html.H5("🔥 Top Outliers de canales descubiertos",
                            style={"color": COLORS["text"], "marginBottom": "16px"}),
                    html.P("Los mejores videos encontrados en los canales que descubriste.",
                           style={"color": COLORS["muted"], "fontSize": "0.8rem",
                                  "marginBottom": "12px"}),
                    html.Div(id="ch-outliers-section"),
                ], style=CARD),
            ], width=8),
        ]),

        dcc.Store(id="ch-store", data={}),
        dcc.Interval(id="ch-poll", interval=2000, n_intervals=0, disabled=True),
        # ── Modal de Outliers por Canal ──────────────────────────────
        html.Div(id="ch-outliers-modal", style={
            "display": "none",
            "position": "fixed",
            "top": "0", "left": "0", "right": "0", "bottom": "0",
            "backgroundColor": "rgba(0,0,0,0.75)",
            "zIndex": 10000,
            "overflowY": "auto",
            "padding": "40px 20px",
        }, children=[
            html.Div(id="ch-outliers-modal-content", style={
                "maxWidth": "1000px",
                "margin": "0 auto",
                "background": COLORS["surface"],
                "borderRadius": "16px",
                "border": f"1px solid {COLORS['border']}",
                "padding": "24px",
                "position": "relative",
            }),
        ]),
    ])

def page_outliers():
    return html.Div([
        html.H2("🔥 Detector de Outliers",
                style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Videos que superan el rendimiento habitual de su canal. "
               "Score 1.0x = 2x, 2.0x = 4x, 3.0x = 8x el promedio.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),

        # ── FILA 1: Categoría, Score, Views, Duración ────────────────
        html.Div([dbc.Row([
            dbc.Col([
                label("🎯 Categoría / Nicho"),
                dcc.Dropdown(
                    id="out-category",
                    options=[{"label": "🌐 Todas las categorías", "value": "all"}] + [
                        {"label": k, "value": k}
                        for k in YOUTUBE_CATEGORIES.keys() if k != "Todos"
                    ],
                    value="all",
                    clearable=False,
                ),
            ], width=3),
            dbc.Col([
                label("📈 Score mínimo"),
                dcc.Slider(
                    id="out-min-score", min=0, max=6, step=0.5, value=1.0,
                    marks={i: {"label": f"{i}x", "style": {"color": COLORS["muted"]}}
                           for i in range(7)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ], width=3),
            dbc.Col([
                label("👁️ Views mínimas"),
                dropdown("out-min-views", [
                    {"label": "Sin mínimo",     "value": 0},
                    {"label": "1,000+",         "value": 1000},
                    {"label": "5,000+",         "value": 5000},
                    {"label": "10,000+",        "value": 10000},
                    {"label": "15,000+",        "value": 15000},
                    {"label": "20,000+",        "value": 20000},
                    {"label": "30,000+",        "value": 30000},
                    {"label": "50,000+",        "value": 50000},
                    {"label": "100,000+",       "value": 100000},
                    {"label": "250,000+",       "value": 250000},
                    {"label": "500,000+",       "value": 500000},
                    {"label": "1,000,000+",     "value": 1000000},
                    {"label": "5,000,000+",     "value": 5000000},
                ], 1000),
            ], width=3),
            dbc.Col([
                label("⏱️ Duración"),
                dropdown("out-duration", [
                    {"label": "Todos",               "value": "all"},
                    {"label": "Shorts (<1 min)",     "value": "short"},
                    {"label": "Cortos (1-5 min)",    "value": "medium"},
                    {"label": "Medio-cortos (3-8 min)", "value": "mid_short"},
                    {"label": "Medios (5-20 min)",   "value": "long"},
                    {"label": "Largos (>20 min)",    "value": "vlong"},
                ], "all"),
            ], width=3),
        ], className="g-3")], style={**CARD, "padding": "16px 20px", "marginBottom": "16px"}),

        # ── FILA 2: Idioma, País, Subs máx, Orden, Límite ────────────
        html.Div([dbc.Row([
            dbc.Col([
                label("🗣️ Idioma del video"),
                dcc.Dropdown(
                    id="out-language",
                    options=[{"label": "🌐 Todos los idiomas", "value": "all"}] + [
                        {"label": k, "value": v} for k, v in LANGUAGES.items()
                    ],
                    value="all",
                    clearable=False,
                ),
            ], width=2),
            dbc.Col([
                label("🌍 País del canal"),
                dcc.Dropdown(
                    id="out-region",
                    options=[{"label": "🌐 Todos los países", "value": "all"}] + [
                        {"label": k, "value": v} for k, v in REGIONS.items() if v
                    ],
                    value="all",
                    clearable=False,
                ),
            ], width=2),
            dbc.Col([
                label("👥 Subs máximos del canal"),
                dropdown("out-max-subs", [
                    {"label": "Sin límite",       "value": 0},
                    {"label": "≤ 1,000",          "value": 1000},
                    {"label": "≤ 5,000",          "value": 5000},
                    {"label": "≤ 10,000",         "value": 10000},
                    {"label": "≤ 50,000",         "value": 50000},
                    {"label": "≤ 100,000",        "value": 100000},
                    {"label": "≤ 500,000",        "value": 500000},
                    {"label": "≤ 1,000,000",      "value": 1000000},
                    {"label": "≤ 5,000,000",      "value": 5000000},
                    {"label": "≤ 10,000,000",     "value": 10000000},
                ], 0),
            ], width=3),
            dbc.Col([
                label("📊 Ordenar por"),
                dropdown("out-sort", [
                    {"label": "Outlier Score",  "value": "outlier_score"},
                    {"label": "Views totales",  "value": "view_count"},
                    {"label": "Views/hora",     "value": "views_per_hour"},
                    {"label": "Views/Sub",      "value": "views_per_sub"},
                    {"label": "Fecha (recientes)", "value": "published_at"},
                ], "outlier_score"),
            ], width=3),
            dbc.Col([
                label("🔢 Resultados"),
                dropdown("out-limit", [
                    {"label": "25 videos",   "value": 25},
                    {"label": "50 videos",   "value": 50},
                    {"label": "100 videos",  "value": 100},
                    {"label": "150 videos",  "value": 150},
                    {"label": "200 videos",  "value": 200},
                    {"label": "250 videos",  "value": 250},
                    {"label": "300 videos",  "value": 300},
                    {"label": "350 videos",  "value": 350},
                    {"label": "400 videos",  "value": 400},
                    {"label": "450 videos",  "value": 450},
                    {"label": "500 videos",  "value": 500},
                ], 25),
            ], width=2),
        ], className="g-3")], style={**CARD, "padding": "16px 20px"}),

        html.Div(id="out-metrics"),
        dbc.Row([
            dbc.Col([html.Div([
                html.H6("Score vs Views", style={"color": COLORS["text"]}),
                dcc.Graph(id="out-scatter", config={"displayModeBar": False},
                          style={"height": "300px"}),
            ], style=CARD)], width=6),
            dbc.Col([html.Div([
                html.H6("Distribución de Scores", style={"color": COLORS["text"]}),
                dcc.Graph(id="out-histogram", config={"displayModeBar": False},
                          style={"height": "300px"}),
            ], style=CARD)], width=6),
        ]),
        html.Div([
            html.H5("🎬 Videos Outliers", style={"color": COLORS["text"], "marginBottom": "16px"}),
            html.Div(id="out-videos-list"),
        ], style=CARD),
        dcc.Interval(id="out-refresh", interval=60000, n_intervals=0),
        # ── Toast de favoritos ──────────────────────────────────────
        html.Div(
            id="fav-toast",
            children="",
            style={
                "position": "fixed",
                "bottom": "30px",
                "right": "30px",
                "background": COLORS["surface"],
                "color": COLORS["text"],
                "padding": "14px 24px",
                "borderRadius": "10px",
                "border": f"1px solid {COLORS['primary']}",
                "boxShadow": "0 8px 24px rgba(0,0,0,0.4)",
                "zIndex": 99999,
                "fontWeight": "600",
                "fontSize": "0.9rem",
                "opacity": "0",
                "transform": "translateY(20px)",
                "transition": "all 0.3s ease",
                "pointerEvents": "none",
            },
        ),
    ])

def page_ideas():
    return html.Div([
        html.H2("💡 Ideas de Contenido", style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Genera ideas basadas en outliers y clusters de oportunidad.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H5("🎯 Selecciona un Outlier como inspiración",
                            style={"color": COLORS["text"], "marginBottom": "16px"}),
                    dcc.Dropdown(id="idea-video-select",
                                placeholder="Busca un video outlier...",
                                style={"marginBottom": "16px"}),
                    html.Div(id="idea-source-preview"),
                    html.Hr(style={"borderColor": COLORS["border"]}),
                    dbc.Button("✨ Generar Ideas", id="idea-generate-btn",
                               color="primary",
                               style={"width": "100%", "background": COLORS["primary"],
                                      "border": "none", "borderRadius": "10px",
                                      "fontWeight": "700", "padding": "12px"}),
                ], style=CARD),
                html.Div([
                    html.H5("🏆 Clusters de Oportunidad",
                            style={"color": COLORS["text"], "marginBottom": "12px"}),
                    dcc.Graph(id="idea-opportunity-chart",
                              config={"displayModeBar": False},
                              style={"height": "300px"}),
                ], style=CARD),
            ], width=4),
            dbc.Col([
                html.Div([
                    html.H5("💡 Ideas Generadas",
                            style={"color": COLORS["text"], "marginBottom": "16px"}),
                    html.Div(id="idea-generated-list"),
                ], style=CARD),
                html.Div([
                    html.H5("📋 Mis Ideas Guardadas",
                            style={"color": COLORS["text"], "marginBottom": "16px"}),
                    html.Div(id="idea-saved-list"),
                ], style=CARD),
            ], width=8),
        ]),
        dcc.Store(id="idea-store", data={}),
    ])


def page_competitors():
    return html.Div([
        html.H2("📡 Radar de Competidores", style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Compara canales por métricas clave, frecuencia de publicación y engagement.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),
        html.Div([
            label("📺 Selecciona canales a comparar"),
            dcc.Dropdown(id="comp-channel-select", multi=True,
                         placeholder="Selecciona canales...",
                         style={"marginBottom": "16px"}),
            dbc.Row([dbc.Col([
                label("📅 Período (días)"),
                dcc.Slider(
                    id="comp-days", min=7, max=180, step=7, value=30,
                    marks={7: {"label": "7d", "style": {"color": COLORS["muted"]}},
                           30: {"label": "30d", "style": {"color": COLORS["muted"]}},
                           90: {"label": "90d", "style": {"color": COLORS["muted"]}},
                           180: {"label": "180d", "style": {"color": COLORS["muted"]}}},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ], width=6)]),
        ], style=CARD),
        html.Div([
            html.H5("📊 Comparativa", style={"color": COLORS["text"], "marginBottom": "16px"}),
            html.Div(id="comp-table"),
        ], style=CARD),
        dbc.Row([
            dbc.Col([html.Div([
                html.H6("Views promedio", style={"color": COLORS["text"]}),
                dcc.Graph(id="comp-views-chart", config={"displayModeBar": False},
                          style={"height": "280px"}),
            ], style=CARD)], width=4),
            dbc.Col([html.Div([
                html.H6("Outliers por canal", style={"color": COLORS["text"]}),
                dcc.Graph(id="comp-outlier-chart", config={"displayModeBar": False},
                          style={"height": "280px"}),
            ], style=CARD)], width=4),
            dbc.Col([html.Div([
                html.H6("Radar comparativo", style={"color": COLORS["text"]}),
                dcc.Graph(id="comp-radar-chart", config={"displayModeBar": False},
                          style={"height": "280px"}),
            ], style=CARD)], width=4),
        ]),
        html.Div([
            html.H5("🔔 Últimas publicaciones",
                    style={"color": COLORS["text"], "marginBottom": "16px"}),
            html.Div(id="comp-recent-posts"),
        ], style=CARD),
        dcc.Interval(id="comp-refresh", interval=60000, n_intervals=0),
    ])


def page_thumbnails():
    return html.Div([
        html.H2("🖼️ Análisis de Thumbnails",
                style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Descubre qué patrones visuales correlacionan con videos virales. "
               "Analiza, filtra y encuentra tendencias.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),

        # ── PANEL DE ANÁLISIS ─────────────────────────────────────────
        html.Div([
            html.H5("⚙️ Analizar nuevos thumbnails",
                    style={"color": COLORS["text"], "marginBottom": "16px"}),

            dbc.Row([
                dbc.Col([
                    label("📈 Score mínimo"),
                    dcc.Slider(
                        id="thumb-analyze-min-score",
                        min=0, max=6, step=0.5, value=0.0,
                        marks={i: {"label": f"{i}x", "style": {"color": COLORS["muted"]}}
                               for i in range(7)},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ], width=3),
                dbc.Col([
                    label("🎯 Categoría"),
                    dcc.Dropdown(
                        id="thumb-analyze-category",
                        options=[{"label": "🌐 Todas las categorías", "value": "all"}] + [
                            {"label": k, "value": k}
                            for k in YOUTUBE_CATEGORIES.keys() if k != "Todos"
                        ],
                        value="all",
                        clearable=False,
                    ),
                ], width=3),
                dbc.Col([
                    label("🔢 Cantidad a analizar"),
                    dropdown("thumb-analyze-limit", [
                        {"label": "25 videos (rápido)", "value": 25},
                        {"label": "50 videos",          "value": 50},
                        {"label": "100 videos",         "value": 100},
                        {"label": "200 videos",         "value": 200},
                    ], 50),
                ], width=2),
                dbc.Col([
                    label("⚡ Opciones"),
                    dbc.Checklist(
                        id="thumb-analyze-options",
                        options=[
                            {"label": " Solo outliers (≥1.0x)", "value": "only_outliers"},
                        ],
                        value=[],
                        style={"color": COLORS["text"]},
                    ),
                ], width=2),
                dbc.Col([
                    html.Div(style={"height": "28px"}),
                    dbc.Button(
                        [html.Span("🖼️"), " Analizar Thumbnails"],
                        id="thumb-analyze-btn", color="primary",
                        style={"width": "100%", "background": COLORS["primary"],
                               "border": "none", "borderRadius": "10px",
                               "fontWeight": "700", "padding": "10px"},
                    ),
                ], width=2),
            ], className="g-3"),

            html.Div(id="thumb-analyze-progress-container", style={"marginTop": "16px"}, children=[
                html.Div(id="thumb-analyze-status",
                         style={"color": COLORS["muted"], "fontSize": "0.85rem",
                                "marginBottom": "8px"}),
                dbc.Progress(id="thumb-analyze-progress", value=0,
                             style={"height": "8px", "borderRadius": "4px"}, color="primary"),
                html.Div(id="thumb-analyze-results", style={"marginTop": "12px"}),
            ]),
        ], style={**CARD, "padding": "20px"}),

        # ── FILTROS DE VISUALIZACIÓN ──────────────────────────────────
        html.Div([
            html.H5("🔍 Filtros de visualización",
                    style={"color": COLORS["text"], "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col([
                    label("📈 Score mínimo"),
                    dcc.Slider(
                        id="thumb-min-score", min=0, max=6, step=0.5, value=0.0,
                        marks={i: {"label": f"{i}x", "style": {"color": COLORS["muted"]}}
                               for i in range(7)},
                    ),
                ], width=2),
                dbc.Col([
                    label("🎯 Categoría"),
                    dcc.Dropdown(
                        id="thumb-category",
                        options=[{"label": "🌐 Todas", "value": "all"}] + [
                            {"label": k, "value": k}
                            for k in YOUTUBE_CATEGORIES.keys() if k != "Todos"
                        ],
                        value="all",
                        clearable=False,
                    ),
                ], width=2),
                dbc.Col([
                    label("🗣️ Idioma"),
                    dcc.Dropdown(
                        id="thumb-language",
                        options=[{"label": "🌐 Todos", "value": "all"}] + [
                            {"label": k, "value": v} for k, v in LANGUAGES.items()
                        ],
                        value="all",
                        clearable=False,
                    ),
                ], width=2),
                dbc.Col([
                    label("🔧 Filtrar por"),
                    dropdown("thumb-filter", [
                        {"label": "Todos",                   "value": "all"},
                        {"label": "Solo outliers (≥1.0x)",  "value": "outliers"},
                        {"label": "Con cara detectada",      "value": "face"},
                        {"label": "Con texto detectado",     "value": "text"},
                        {"label": "Sin cara",               "value": "no_face"},
                        {"label": "Sin texto",              "value": "no_text"},
                        {"label": "Alto brillo (>150)",     "value": "bright"},
                        {"label": "Bajo brillo (<80)",      "value": "dark"},
                    ], "all"),
                ], width=2),
                dbc.Col([
                    label("🔢 Resultados"),
                    dropdown("thumb-limit", [
                        {"label": "50 videos",   "value": 50},
                        {"label": "100 videos",  "value": 100},
                        {"label": "200 videos",  "value": 200},
                        {"label": "300 videos",  "value": 300},
                    ], 100),
                ], width=2),
                dbc.Col([
                    label("📊 Ordenar por"),
                    dropdown("thumb-sort", [
                        {"label": "Outlier Score",  "value": "outlier_score"},
                        {"label": "Views",          "value": "view_count"},
                        {"label": "Brillo",         "value": "thumb_brightness"},
                    ], "outlier_score"),
                ], width=2),
            ], className="g-3"),
        ], style={**CARD, "padding": "20px"}),

        # ── MÉTRICAS ──────────────────────────────────────────────────
        html.Div(id="thumb-metrics"),

        # ── GRÁFICOS DE CORRELACIÓN ───────────────────────────────────
        html.Div([
            html.H5("🔬 Correlación Features vs Score",
                    style={"color": COLORS["text"], "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col([dcc.Graph(id="thumb-brightness-chart",
                                   config={"displayModeBar": False},
                                   style={"height": "260px"})], width=4),
                dbc.Col([dcc.Graph(id="thumb-face-chart",
                                   config={"displayModeBar": False},
                                   style={"height": "260px"})], width=4),
                dbc.Col([dcc.Graph(id="thumb-text-chart",
                                   config={"displayModeBar": False},
                                   style={"height": "260px"})], width=4),
            ]),
        ], style=CARD),

        # ── GALERÍA ───────────────────────────────────────────────────
        html.Div([
            html.H5("🖼️ Galería de Thumbnails",
                    style={"color": COLORS["text"], "marginBottom": "16px"}),
            html.Div(id="thumb-gallery"),
        ], style=CARD),

        dcc.Interval(id="thumb-refresh", interval=60000, n_intervals=0),
        dcc.Store(id="thumb-analyze-store", data={"running": False}),
        dcc.Interval(id="thumb-analyze-poll", interval=1500, n_intervals=0, disabled=True),
    ])


def page_analytics():
    return html.Div([
        html.H2("📊 Mi Canal — Analytics",
                style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Métricas avanzadas de TU canal con YouTube Analytics API (OAuth).",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),
        html.Div(id="analytics-content"),
    ])


def page_settings():
    return html.Div([
        html.H2("⚙️ Configuración", style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Configura tu API Key y gestiona tu base de datos.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),
        dbc.Row([
            dbc.Col([html.Div([
                html.H5("🔑 Claves de API",
                        style={"color": COLORS["text"], "marginBottom": "20px"}),
                label("YouTube Data API Key"),
                dbc.InputGroup([
                    dbc.Input(id="settings-api-key", type="password",
                              placeholder="AIzaSy...",
                              style={"background": COLORS["surface2"],
                                     "border": f"1px solid {COLORS['border']}",
                                     "color": COLORS["text"]}),
                    dbc.Button("✅ Verificar", id="settings-verify-key",
                               color="success", outline=True),
                ], style={"marginBottom": "16px"}),
                html.Div(id="settings-key-status"),
                html.Hr(style={"borderColor": COLORS["border"]}),
                html.H5("🗄️ Base de Datos",
                        style={"color": COLORS["text"], "marginBottom": "16px"}),
                dbc.Row([
                    dbc.Col([dbc.Button("🗑️ Limpiar videos (>30 días)",
                                        id="settings-clean-btn", color="warning",
                                        outline=True,
                                        style={"width": "100%", "borderRadius": "8px"})],
                            width=6),
                    dbc.Col([dbc.Button("💥 Borrar Todo", id="settings-reset-btn",
                                        color="danger", outline=True,
                                        style={"width": "100%", "borderRadius": "8px"})],
                            width=6),
                ], className="g-2"),
                html.Div(id="settings-action-result", style={"marginTop": "12px"}),
            ], style=CARD)], width=6),
            dbc.Col([html.Div([
                html.H5("📊 Estado del Sistema",
                        style={"color": COLORS["text"], "marginBottom": "16px"}),
                html.Div(id="settings-system-status"),
            ], style=CARD)], width=6),
        ]),
    ])


def page_favorites():
    return html.Div([
        html.H2("⭐ Videos Favoritos", style={"color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Tu colección personal de videos para estudiar más tarde.",
               style={"color": COLORS["muted"], "marginBottom": "24px"}),

        html.Div([dbc.Row([
            dbc.Col([
                label("🎯 Categoría"),
                dcc.Dropdown(
                    id="fav-category",
                    options=[{"label": "🌐 Todas las categorías", "value": "all"}] + [
                        {"label": k, "value": k}
                        for k in YOUTUBE_CATEGORIES.keys() if k != "Todos"
                    ],
                    value="all",
                    clearable=False,
                ),
            ], width=3),
            dbc.Col([
                label("📈 Score mínimo"),
                dcc.Slider(
                    id="fav-min-score", min=0, max=6, step=0.5, value=0.0,
                    marks={i: {"label": f"{i}x", "style": {"color": COLORS["muted"]}}
                           for i in range(7)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ], width=4),
            dbc.Col([
                label("📊 Ordenar por"),
                dropdown("fav-sort", [
                    {"label": "Fecha agregado",    "value": "created_at"},
                    {"label": "Outlier Score",    "value": "outlier_score"},
                    {"label": "Views",            "value": "view_count"},
                ], "created_at"),
            ], width=3),
            dbc.Col([
                label("🔢 Resultados"),
                dropdown("fav-limit", [
                    {"label": "25 videos",  "value": 25},
                    {"label": "50 videos",  "value": 50},
                    {"label": "100 videos", "value": 100},
                ], 50),
            ], width=2),
        ], className="g-3")], style={**CARD, "padding": "16px 20px"}),

        html.Div(id="fav-metrics"),
        html.Div([
            html.H5("⭐ Lista de Favoritos", style={"color": COLORS["text"], "marginBottom": "16px"}),
            html.Div(id="fav-videos-list"),
        ], style=CARD),
        dcc.Interval(id="fav-refresh", interval=60000, n_intervals=0),
    ])

# ─────────────────────────────────────────────────────────────────────────
#  LAYOUT PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────

def build_layout():
    return html.Div([
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="app-store", data={}),
        build_sidebar(),
        html.Div(id="page-content", style=CONTENT_STYLE),
    ], style={"background": COLORS["bg"],
              "fontFamily": "'Inter', 'Segoe UI', sans-serif"})