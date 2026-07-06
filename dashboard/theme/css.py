"""Hoja de estilos del dashboard (inyectada vía st.markdown)."""

import streamlit as st

from dashboard.theme.colores import (
    AMBAR,
    FONDO,
    ROJO,
    TIERRA,
    TINTA,
    TINTA_SUAVE,
    VERDE,
    VERDE_OSCURO,
)


def inyectar_css() -> None:
    """Inyecta la hoja de estilos global del dashboard."""
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] * {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}
/* restaurar la fuente de iconos: el selector universal de arriba la pisaba y
   los iconos se veían como texto crudo (p. ej. "keyboard_double_arrow_left") */
[data-testid="stIconMaterial"],
span[class*="material-icons"],
span[class*="material-symbols"] {{
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined',
                 'Material Icons' !important;
}}
[data-testid="stAppViewContainer"] {{
    background: {FONDO};
}}
[data-testid="stHeader"] {{
    background: transparent;
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {VERDE_OSCURO} 0%, #123021 100%);
}}
[data-testid="stSidebar"] * {{
    color: #E8F2EA !important;
}}
/* control del multiselect: fondo translúcido oscuro para que el texto claro se lea */
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background-color: rgba(255,255,255,.07) !important;
    border-color: rgba(255,255,255,.22) !important;
    border-radius: 8px;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div:hover {{
    border-color: rgba(255,255,255,.4) !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] input {{
    color: #E8F2EA !important;
}}
/* chips de cultivos seleccionados: verde legible con texto blanco */
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
    background: {VERDE} !important;
    border-radius: 6px;
}}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span,
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] svg {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}}
/* iconos de flecha y limpiar del selector */
[data-testid="stSidebar"] [data-baseweb="select"] svg {{
    fill: #C7D8CB !important;
}}
/* menú desplegable (portal en el cuerpo): texto oscuro sobre blanco */
[data-baseweb="popover"] [role="option"] {{
    color: {TINTA} !important;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,.15);
}}

/* ---------------- encabezado hero ---------------- */
.hero {{
    background: linear-gradient(120deg, {VERDE_OSCURO} 0%, {VERDE} 62%, #43A047 100%);
    border-radius: 18px;
    padding: 28px 34px 26px 34px;
    color: white;
    margin-bottom: 6px;
    box-shadow: 0 8px 24px rgba(27, 67, 50, .25);
}}
.hero h1 {{
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -.02em;
    margin: 0 0 4px 0;
    color: white;
}}
.hero p {{
    margin: 0;
    font-size: .92rem;
    color: rgba(255,255,255,.85);
    font-weight: 400;
}}
.hero .badges {{ margin-top: 14px; }}
.hero .badge {{
    display: inline-block;
    background: rgba(255,255,255,.16);
    border: 1px solid rgba(255,255,255,.25);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: .74rem;
    font-weight: 600;
    margin-right: 8px;
    letter-spacing: .02em;
}}

/* ---------------- tarjetas KPI ---------------- */
.kpi {{
    background: white;
    border-radius: 14px;
    padding: 18px 20px 16px 20px;
    border: 1px solid #E4ECE2;
    border-top: 4px solid {VERDE};
    box-shadow: 0 2px 10px rgba(28, 43, 33, .06);
    height: 100%;
}}
.kpi .etiqueta {{
    font-size: .72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: {TINTA_SUAVE};
    margin-bottom: 6px;
}}
.kpi .valor {{
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -.03em;
    color: {TINTA};
    line-height: 1.1;
}}
.kpi .unidad {{
    font-size: .95rem;
    font-weight: 600;
    color: {TINTA_SUAVE};
}}
.kpi .pilar {{
    display: inline-block;
    margin-top: 10px;
    font-size: .68rem;
    font-weight: 700;
    color: {VERDE};
    background: #E8F3EA;
    border-radius: 6px;
    padding: 3px 9px;
}}
.kpi.ambar {{ border-top-color: {AMBAR}; }}
.kpi.ambar .pilar {{ color: #8A6D00; background: #FDF3D5; }}
.kpi.tierra {{ border-top-color: {TIERRA}; }}
.kpi.tierra .pilar {{ color: {TIERRA}; background: #F1EAE7; }}

/* ---------------- contenedores de gráficos ---------------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(.js-plotly-plot),
div[data-testid="stDataFrame"] {{
    background: white;
    border-radius: 14px;
    border: 1px solid #E4ECE2;
    box-shadow: 0 2px 10px rgba(28, 43, 33, .05);
    padding: 6px;
}}

/* ---------------- pestañas ---------------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    background: transparent;
    border-bottom: none;
    margin-top: 8px;
}}
.stTabs [data-baseweb="tab"] {{
    background: white;
    border: 1px solid #E4ECE2;
    border-radius: 10px 10px 0 0;
    padding: 10px 22px;
    font-weight: 600;
    color: {TINTA_SUAVE};
}}
.stTabs [aria-selected="true"] {{
    background: {VERDE} !important;
    color: white !important;
    border-color: {VERDE} !important;
}}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{
    display: none;
}}

/* ---------------- tarjetas de decisión (prescriptiva) ---------------- */
.decision-card {{
    background: white;
    border-radius: 12px;
    border: 1px solid #E4ECE2;
    border-left: 6px solid {AMBAR};
    padding: 14px 16px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(28,43,33,.05);
}}
.decision-card .cultivo {{
    font-weight: 700;
    font-size: 1rem;
    color: {TINTA};
}}
.decision-card .detalle {{
    font-size: .8rem;
    color: {TINTA_SUAVE};
    margin-top: 2px;
}}
.decision-card .accion {{
    float: right;
    font-size: .74rem;
    font-weight: 700;
    border-radius: 999px;
    padding: 5px 14px;
    letter-spacing: .03em;
}}
.decision-card.up {{ border-left-color: {VERDE}; }}
.decision-card.up .accion {{ background: #E8F3EA; color: {VERDE}; }}
.decision-card.keep .accion {{ background: #FDF3D5; color: #8A6D00; }}
.decision-card.down {{ border-left-color: {ROJO}; }}
.decision-card.down .accion {{ background: #FBE4E4; color: {ROJO}; }}

/* ---------------- caja de predicción ---------------- */
.pred-box {{
    background: linear-gradient(120deg, {VERDE_OSCURO}, {VERDE});
    color: white;
    border-radius: 14px;
    padding: 22px 26px;
    text-align: center;
    box-shadow: 0 6px 18px rgba(27,67,50,.28);
}}
.pred-box .titulo {{ font-size: .75rem; font-weight: 600; text-transform: uppercase;
                     letter-spacing: .08em; color: rgba(255,255,255,.75); }}
.pred-box .numero {{ font-size: 2.6rem; font-weight: 800; letter-spacing: -.03em; line-height: 1.15; }}
.pred-box .sub {{ font-size: .85rem; color: rgba(255,255,255,.85); }}

.section-note {{
    background: white;
    border: 1px solid #E4ECE2;
    border-left: 5px solid {VERDE};
    border-radius: 10px;
    padding: 14px 18px;
    font-size: .9rem;
    color: {TINTA};
    margin: 4px 0 14px 0;
}}

/* ---------------- explorador de datos (pestaña Datos) ---------------- */
.tabla-meta {{
    background: white;
    border: 1px solid #E4ECE2;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(28,43,33,.05);
}}
.tabla-meta .nombre {{
    font-weight: 700;
    font-size: 1.05rem;
    color: {TINTA};
}}
.tabla-meta .tipo {{
    display: inline-block;
    margin-left: 10px;
    font-size: .68rem;
    font-weight: 700;
    border-radius: 999px;
    padding: 3px 12px;
    letter-spacing: .04em;
    vertical-align: middle;
}}
.tabla-meta .tipo.hecho {{ background: #E8F3EA; color: {VERDE}; }}
.tabla-meta .tipo.dimension {{ background: #FDF3D5; color: #8A6D00; }}
.tabla-meta .tipo.externa {{ background: #F1EAE7; color: {TIERRA}; }}
.tabla-meta .descripcion {{
    font-size: .82rem;
    color: {TINTA_SUAVE};
    margin-top: 4px;
}}

.quality-card {{
    background: white;
    border: 1px solid #E4ECE2;
    border-left: 5px solid {VERDE};
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(28,43,33,.05);
    height: 100%;
}}
.quality-card .titulo {{
    font-weight: 700;
    font-size: .86rem;
    color: {TINTA};
    margin-bottom: 4px;
}}
.quality-card .detalle {{
    font-size: .8rem;
    color: {TINTA_SUAVE};
}}
.quality-card .ok {{
    display: inline-block;
    margin-top: 8px;
    font-size: .7rem;
    font-weight: 700;
    color: {VERDE};
    background: #E8F3EA;
    border-radius: 6px;
    padding: 3px 9px;
}}

footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
</style>
""",
        unsafe_allow_html=True,
    )
