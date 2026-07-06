"""
Fase 3.3 — Dashboard Estratégico de AgroComercial del Litoral S.A.

Dashboard interactivo (Streamlit + Plotly) que acompaña al archivo de Power BI.
Sirve como entregable interactivo desplegado y como demo para la defensa.

Diseño (justificación en el informe, sección 3.3):
  - Principios de percepción visual (Gestalt): proximidad (KPIs agrupados
    arriba), jerarquía visual (KPIs -> tendencia -> detalle) y canales de
    posición/longitud (barras y líneas) para comparaciones precisas.
  - Psicología del color: verde (#2E7D32) = agro/crecimiento/positivo;
    rojo (#C62828) reservado exclusivamente para alertas (reducir compra);
    neutros tierra para contexto. Máximo 4 colores semánticos por vista.
  - Tipografía: una sola familia sans-serif (Inter), jerarquía por tamaño/peso.

Ejecutar:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --- Silenciar traceback benigno de asyncio en Windows -----------------------
# En Windows, cuando el navegador cierra su conexión con el servidor Tornado de
# Streamlit, el bucle asyncio (ProactorEventLoop) lanza un ConnectionResetError
# no capturado (WinError 10054) dentro de
# _ProactorBasePipeTransport._call_connection_lost y vuelca ese traceback a la
# consola. Es inofensivo. Envolvemos ese método UNA sola vez (Streamlit reejecuta
# el script en cada interacción) para descartar solo ese error concreto.
if sys.platform == "win32":
    from asyncio.proactor_events import _ProactorBasePipeTransport

    if not getattr(
        _ProactorBasePipeTransport._call_connection_lost, "_conn_reset_silenciado", False
    ):
        _call_connection_lost_original = _ProactorBasePipeTransport._call_connection_lost

        def _call_connection_lost(self, exc):
            if isinstance(exc, ConnectionResetError):
                return None
            return _call_connection_lost_original(self, exc)

        _call_connection_lost._conn_reset_silenciado = True
        _ProactorBasePipeTransport._call_connection_lost = _call_connection_lost

RUTA_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_PROCESSED = RUTA_PROYECTO / "data" / "processed"
RUTA_REPORTES = RUTA_PROYECTO / "reports"
RUTA_MODELO = RUTA_PROYECTO / "models" / "modelo_rendimiento.joblib"

VERDE = "#2E7D32"
VERDE_OSCURO = "#1B4332"
VERDE_CLARO = "#66BB6A"
TIERRA = "#8D6E63"
AMBAR = "#F9A825"
ROJO = "#C62828"
FONDO = "#F6F8F4"
TINTA = "#1C2B21"
TINTA_SUAVE = "#5C6F62"

SECUENCIA_CULTIVOS = [
    "#2E7D32", "#66BB6A", "#A5D6A7", "#8D6E63", "#F9A825",
    "#1565C0", "#6D4C41", "#00897B", "#7CB342",
]

st.set_page_config(
    page_title="AgroComercial del Litoral — Analítica de Compras",
    page_icon="🌾",
    layout="wide",
)

# ------------------------- Tema global de Plotly -----------------------------
pio.templates["agro"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, 'Segoe UI', sans-serif", size=13, color=TINTA),
        title=dict(font=dict(size=15, color=TINTA), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=SECUENCIA_CULTIVOS,
        xaxis=dict(gridcolor="#E3EAE0", zerolinecolor="#E3EAE0", linecolor="#CBD8C6"),
        yaxis=dict(gridcolor="#E3EAE0", zerolinecolor="#E3EAE0", linecolor="#CBD8C6"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11)),
        margin=dict(l=10, r=10, t=60, b=10),
        hoverlabel=dict(font_family="Inter, 'Segoe UI', sans-serif"),
    )
)
pio.templates.default = "agro"

# ------------------------------- CSS ----------------------------------------
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

footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def cargar_datos():
    fact_rend = pd.read_csv(RUTA_PROCESSED / "fact_rendimiento.csv")
    fact_compras = pd.read_csv(RUTA_PROCESSED / "fact_compras.csv")
    dim_geo = pd.read_csv(RUTA_PROCESSED / "dim_geografia.csv")
    dim_cultivo = pd.read_csv(RUTA_PROCESSED / "dim_cultivo.csv")
    recomendaciones = pd.read_csv(RUTA_REPORTES / "recomendaciones_compra.csv")

    rendimiento = (
        fact_rend.merge(dim_geo, on="id_geografia")
        .merge(dim_cultivo, on="id_cultivo")
        .rename(columns={"id_tiempo": "anio"})
    )
    compras = fact_compras.merge(dim_cultivo, on="id_cultivo").rename(
        columns={"id_tiempo": "anio"}
    )
    return rendimiento, compras, recomendaciones


@st.cache_resource
def cargar_modelo():
    return joblib.load(RUTA_MODELO)


rendimiento, compras, recomendaciones = cargar_datos()
ecuador = rendimiento[rendimiento["pais"] == "Ecuador"]

# ----------------------------- Encabezado -----------------------------------
st.markdown(
    """
<div class="hero">
  <h1>🌾 AgroComercial del Litoral S.A.</h1>
  <p>Dashboard estratégico · Predicción del rendimiento de cosechas y planificación de compras</p>
  <div class="badges">
    <span class="badge">📡 FAOSTAT + Banco Mundial (API pública)</span>
    <span class="badge">🇪🇨 Ecuador · 1990–2023</span>
    <span class="badge">🤖 Random Forest · R² 0.96</span>
    <span class="badge">🔒 Datos sin PII</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------------------- Filtros ---------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Filtros")
    cultivos_sel = st.multiselect(
        "Cultivos",
        sorted(ecuador["cultivo_es"].unique()),
        default=sorted(ecuador["cultivo_es"].unique()),
    )
    rango_anios = st.slider(
        "Rango de años",
        int(ecuador["anio"].min()),
        int(ecuador["anio"].max()),
        (int(ecuador["anio"].min()), int(ecuador["anio"].max())),
    )
    st.divider()
    st.markdown(
        "<small>El rendimiento y el clima son <b>datos reales</b> (FAO / Banco Mundial). "
        "Las compras internas son <b>simuladas</b> para el escenario académico.</small>",
        unsafe_allow_html=True,
    )

ecuador_f = ecuador[
    ecuador["cultivo_es"].isin(cultivos_sel) & ecuador["anio"].between(*rango_anios)
]
compras_f = compras[
    compras["cultivo_es"].isin(cultivos_sel) & compras["anio"].between(*rango_anios)
]

if ecuador_f.empty or compras_f.empty:
    st.warning("Selecciona al menos un cultivo y un rango de años válido.")
    st.stop()

# ----------------------------- Fila de KPIs ---------------------------------
ultimo_lustro = ecuador_f[ecuador_f["anio"] >= ecuador_f["anio"].max() - 4]
cv_prom = (
    ecuador_f.groupby("cultivo_es")["rendimiento_ton_ha"]
    .agg(lambda s: s.std() / s.mean() * 100)
    .mean()
)
margen_pct = compras_f["margen_bruto_usd"].sum() / max(compras_f["costo_total_usd"].sum(), 1) * 100
merma = compras_f["merma_pct"].mean()
vol_cultivo = compras_f.groupby("cultivo_es")["volumen_comprado_ton"].sum()
concentracion = vol_cultivo.nlargest(3).sum() / max(vol_cultivo.sum(), 1) * 100


def tarjeta_kpi(columna, etiqueta: str, valor: str, unidad: str, pilar: str, clase: str = "") -> None:
    columna.markdown(
        f"""
<div class="kpi {clase}">
  <div class="etiqueta">{etiqueta}</div>
  <div class="valor">{valor} <span class="unidad">{unidad}</span></div>
  <span class="pilar">{pilar}</span>
</div>
""",
        unsafe_allow_html=True,
    )


k1, k2, k3, k4, k5 = st.columns(5)
tarjeta_kpi(k1, "Rendimiento prom. (últ. 5 años)", f"{ultimo_lustro['rendimiento_ton_ha'].mean():.2f}", "ton/ha", "DESCRIPTIVO")
tarjeta_kpi(k2, "Variabilidad interanual (CV)", f"{cv_prom:.1f}", "%", "DIAGNÓSTICO", "ambar")
tarjeta_kpi(k3, "Margen bruto de reventa", f"{margen_pct:.1f}", "%", "DESCRIPTIVO")
tarjeta_kpi(k4, "Merma promedio", f"{merma:.1f}", "%", "DIAGNÓSTICO", "tierra")
tarjeta_kpi(k5, "Concentración top 3 cultivos", f"{concentracion:.1f}", "%", "PRESCRIPTIVO", "ambar")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ------------------- Pestañas: 4 pilares de analítica ------------------------
tab_desc, tab_diag, tab_pred, tab_presc = st.tabs(
    ["📊  Descriptiva", "🔍  Diagnóstica", "🤖  Predictiva", "🎯  Prescriptiva"]
)

with tab_desc:
    col_izq, col_der = st.columns((11, 9))

    serie = (
        ecuador_f.groupby(["anio", "cultivo_es"], as_index=False)["rendimiento_ton_ha"].mean()
    )
    fig = px.line(
        serie, x="anio", y="rendimiento_ton_ha", color="cultivo_es",
        title="Evolución del rendimiento por cultivo · Ecuador",
        labels={"anio": "", "rendimiento_ton_ha": "ton/ha", "cultivo_es": ""},
    )
    fig.update_traces(line_width=2.4)
    fig.update_layout(
        height=400,
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0),
        margin=dict(t=50, b=10),
    )
    with col_izq.container(border=False):
        st.plotly_chart(fig, width='stretch')

    ranking = (
        ecuador_f.groupby("cultivo_es", as_index=False)["rendimiento_ton_ha"].mean()
        .sort_values("rendimiento_ton_ha")
    )
    fig = px.bar(
        ranking, x="rendimiento_ton_ha", y="cultivo_es", orientation="h",
        title="Rendimiento promedio por cultivo · Ecuador",
        labels={"rendimiento_ton_ha": "ton/ha", "cultivo_es": ""},
        color_discrete_sequence=[VERDE], text_auto=".2f",
    )
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(height=380, showlegend=False)
    with col_der.container(border=False):
        st.plotly_chart(fig, width='stretch')

    col_a, col_b = st.columns(2)
    margen_anual = compras_f.groupby("anio", as_index=False)["margen_bruto_usd"].sum()
    fig = px.bar(
        margen_anual, x="anio", y="margen_bruto_usd",
        title="Margen bruto anual de reventa (USD)",
        labels={"anio": "", "margen_bruto_usd": "USD"},
        color_discrete_sequence=[VERDE_CLARO],
    )
    fig.update_layout(height=330)
    with col_a.container(border=False):
        st.plotly_chart(fig, width='stretch')

    vol = vol_cultivo.sort_values().reset_index()
    fig = px.bar(
        vol, x="volumen_comprado_ton", y="cultivo_es", orientation="h",
        title="Volumen histórico comprado por cultivo (ton)",
        labels={"volumen_comprado_ton": "toneladas", "cultivo_es": ""},
        color_discrete_sequence=[TIERRA],
    )
    fig.update_layout(height=330, showlegend=False)
    with col_b.container(border=False):
        st.plotly_chart(fig, width='stretch')

with tab_diag:
    st.markdown(
        """
<div class="section-note">
<b>Pregunta diagnóstica:</b> ¿el rendimiento se mueve con la lluvia, la temperatura o los
pesticidas? La correlación global es débil: el factor dominante es el <b>tipo de cultivo</b> y el
<b>país</b> (suelo, tecnología, variedades). <i>Correlación no implica causalidad</i>: los países con
más pesticidas suelen tener agricultura más tecnificada, y esa tecnificación —no el pesticida en
sí— explica gran parte del mayor rendimiento.
</div>
""",
        unsafe_allow_html=True,
    )
    col_izq, col_der = st.columns(2)

    variables = ["rendimiento_ton_ha", "precipitacion_mm", "temperatura_media_c", "pesticidas_ton"]
    etiquetas = ["Rendimiento", "Lluvia", "Temperatura", "Pesticidas"]
    correlacion = rendimiento[variables].corr()
    fig = go.Figure(
        go.Heatmap(
            z=correlacion.values, x=etiquetas, y=etiquetas,
            colorscale=[[0, ROJO], [0.5, "#FFFDF5"], [1, VERDE]], zmin=-1, zmax=1,
            text=correlacion.round(2).values, texttemplate="%{text}",
            textfont=dict(size=13),
        )
    )
    fig.update_layout(title="Correlación de Pearson (todas las geografías)", height=380)
    with col_izq.container(border=False):
        st.plotly_chart(fig, width='stretch')

    dispersion = ecuador_f.groupby(["anio", "cultivo_es"], as_index=False).agg(
        rendimiento=("rendimiento_ton_ha", "mean"),
        temperatura=("temperatura_media_c", "mean"),
    )
    fig = px.scatter(
        dispersion, x="temperatura", y="rendimiento", color="cultivo_es",
        title="Rendimiento vs temperatura media · Ecuador",
        labels={"temperatura": "Temperatura media (°C)", "rendimiento": "ton/ha", "cultivo_es": ""},
    )
    fig.update_traces(marker=dict(size=9, opacity=0.75, line=dict(width=1, color="white")))
    fig.update_layout(
        height=400,
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0),
    )
    with col_der.container(border=False):
        st.plotly_chart(fig, width='stretch')

with tab_pred:
    st.markdown(
        """
<div class="section-note">
<b>Modelo ganador: Random Forest</b> — R² = 0.96, RMSE = 1.64 ton/ha en datos nunca vistos
(en Ecuador el error baja a 0.73 ton/ha).
Ajusta las condiciones del próximo ciclo y observa el rendimiento esperado al instante.
</div>
""",
        unsafe_allow_html=True,
    )
    modelo = cargar_modelo()

    col_controles, col_resultado = st.columns((11, 7))
    with col_controles:
        cultivo_map = dict(ecuador[["cultivo_es", "cultivo"]].drop_duplicates().itertuples(index=False))
        cultivo_sim = st.selectbox("Cultivo", sorted(cultivo_map))
        c1, c2 = st.columns(2)
        lluvia_sim = c1.slider("🌧️ Lluvia anual (mm)", 200, 4000, int(ecuador["precipitacion_mm"].mean()))
        temp_sim = c2.slider("🌡️ Temperatura media (°C)", 5.0, 35.0, float(round(ecuador["temperatura_media_c"].mean(), 1)))
        pest_sim = st.slider("🧪 Pesticidas (ton)", 0, 20000, int(ecuador["pesticidas_ton"].mean()))

    escenario = pd.DataFrame(
        [{
            "anio": int(ecuador["anio"].max()) + 1,
            "precipitacion_mm": lluvia_sim,
            "pesticidas_ton": pest_sim,
            "temperatura_media_c": temp_sim,
            "pais": "Ecuador",
            "cultivo": cultivo_map[cultivo_sim],
        }]
    )
    prediccion = float(modelo.predict(escenario)[0])
    historico_cultivo = float(ecuador[ecuador["cultivo_es"] == cultivo_sim]["rendimiento_ton_ha"].mean())
    delta = (prediccion / historico_cultivo - 1) * 100
    color_delta = "#B9F6CA" if delta >= 0 else "#FFCDD2"
    flecha = "▲" if delta >= 0 else "▼"

    with col_resultado:
        st.markdown(
            f"""
<div class="pred-box">
  <div class="titulo">Rendimiento predicho · {cultivo_sim}</div>
  <div class="numero">{prediccion:.2f} <span style="font-size:1.2rem">ton/ha</span></div>
  <div class="sub">Histórico: {historico_cultivo:.2f} ton/ha ·
  <b style="color:{color_delta}">{flecha} {abs(delta):.1f} %</b> vs histórico</div>
  <div class="sub" style="margin-top:8px; font-size:.75rem; opacity:.8">
  ± 0.73 ton/ha (RMSE Ecuador) · La predicción apoya la decisión, no reemplaza al comité
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # Curva de sensibilidad: cómo cambia la predicción si varía la lluvia
    lluvias = list(range(200, 4001, 200))
    escenarios = pd.DataFrame(
        [{
            "anio": int(ecuador["anio"].max()) + 1,
            "precipitacion_mm": ll,
            "pesticidas_ton": pest_sim,
            "temperatura_media_c": temp_sim,
            "pais": "Ecuador",
            "cultivo": cultivo_map[cultivo_sim],
        } for ll in lluvias]
    )
    sensibilidad = pd.DataFrame({"lluvia": lluvias, "prediccion": modelo.predict(escenarios)})
    fig = px.area(
        sensibilidad, x="lluvia", y="prediccion",
        title=f"Sensibilidad a la lluvia · {cultivo_sim} (temperatura y pesticidas fijos)",
        labels={"lluvia": "Lluvia anual (mm)", "prediccion": "Rendimiento predicho (ton/ha)"},
        color_discrete_sequence=[VERDE],
    )
    fig.add_vline(x=lluvia_sim, line_dash="dash", line_color=AMBAR,
                  annotation_text="escenario actual", annotation_font_color=TINTA_SUAVE)
    fig.update_traces(line_width=2.5)
    fig.update_layout(height=320)
    with st.container(border=False):
        st.plotly_chart(fig, width='stretch')

with tab_presc:
    anio_objetivo = int(recomendaciones["anio_objetivo"].iloc[0])
    st.markdown(
        f"""
<div class="section-note">
<b>Plan de compras recomendado · ciclo {anio_objetivo}</b> — regla de decisión sobre el
<b>índice de oferta</b> (rendimiento predicho ÷ promedio histórico):
≥ 1.05 aumentar +15 % · 0.95–1.05 mantener · &lt; 0.95 reducir −15 % y asegurar contratos.
</div>
""",
        unsafe_allow_html=True,
    )

    col_grafico, col_cards = st.columns((10, 8))

    tabla = recomendaciones.copy()
    fig = px.bar(
        tabla.sort_values("indice_oferta"),
        x="indice_oferta", y="cultivo", orientation="h",
        color="decision",
        color_discrete_map={
            "AUMENTAR compra": VERDE,
            "MANTENER volumen": AMBAR,
            "REDUCIR compra": ROJO,
        },
        title="Índice de oferta esperada (1.0 = igual al histórico)",
        labels={"indice_oferta": "Índice de oferta", "cultivo": "", "decision": ""},
        text_auto=".2f",
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color=TINTA_SUAVE)
    fig.update_traces(textposition="outside", textfont_size=11)
    fig.update_layout(
        height=470,
        legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0),
        margin=dict(t=60, b=10),
    )
    with col_grafico.container(border=False):
        st.plotly_chart(fig, width='stretch')

    with col_cards:
        clases = {"AUMENTAR compra": "up", "MANTENER volumen": "keep", "REDUCIR compra": "down"}
        iconos = {"AUMENTAR compra": "▲ AUMENTAR +15 %", "MANTENER volumen": "● MANTENER", "REDUCIR compra": "▼ REDUCIR −15 %"}
        for _, fila in tabla.iterrows():
            volumen = (
                f"{fila['volumen_historico_ton']:,.0f} → <b>{fila['volumen_recomendado_ton']:,.0f} ton</b>"
                if pd.notna(fila["volumen_historico_ton"]) else "sin histórico de compra"
            )
            st.markdown(
                f"""
<div class="decision-card {clases[fila['decision']]}">
  <span class="accion">{iconos[fila['decision']]}</span>
  <div class="cultivo">{fila['cultivo']}</div>
  <div class="detalle">Predicho {fila['rendimiento_predicho_ton_ha']} ton/ha ·
  índice {fila['indice_oferta']} · {volumen}</div>
</div>
""",
                unsafe_allow_html=True,
            )

st.markdown(
    f"""
<div style="text-align:center; color:{TINTA_SUAVE}; font-size:.75rem; padding:18px 0 6px 0;">
Proyecto Integrador · Analítica de Negocios 7A · Universidad Laica Eloy Alfaro de Manabí ·
Fuentes: FAO, Banco Mundial (API pública) y registros internos anonimizados
</div>
""",
    unsafe_allow_html=True,
)
