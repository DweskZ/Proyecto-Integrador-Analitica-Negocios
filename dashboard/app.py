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

# Streamlit ejecuta este archivo como script (sys.path[0] = dashboard/), así que
# añadimos la raíz del proyecto para poder importar el paquete `dashboard`.
_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st

from dashboard.components import (
    renderizar_hero,
    renderizar_pie,
    silenciar_conn_reset_windows,
    tarjeta_kpi,
)
from dashboard.data import (
    cargar_datos,
    cargar_reporte_calidad,
    cargar_resultados_modelo,
    cargar_tablas_estrella,
)
from dashboard.tabs import (
    renderizar_datos,
    renderizar_descriptiva,
    renderizar_diagnostica,
    renderizar_predictiva,
    renderizar_prescriptiva,
    renderizar_rentabilidad,
)
from dashboard.theme import inyectar_css, registrar_tema_plotly

silenciar_conn_reset_windows()

st.set_page_config(
    page_title="AgroComercial del Litoral — Analítica de Compras",
    page_icon=":material/agriculture:",
    layout="wide",
)
registrar_tema_plotly()
inyectar_css()

rendimiento, compras, recomendaciones = cargar_datos()
resultados_modelo = cargar_resultados_modelo()
ecuador = rendimiento[rendimiento["pais"] == "Ecuador"]

renderizar_hero(resultados_modelo)

# ----------------------------- Filtros ---------------------------------------
with st.sidebar:
    st.markdown("### :material/tune: Filtros")
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

k1, k2, k3, k4, k5 = st.columns(5)
tarjeta_kpi(k1, "Rendimiento prom. (últ. 5 años)", f"{ultimo_lustro['rendimiento_ton_ha'].mean():.2f}", "ton/ha", "DESCRIPTIVO")
tarjeta_kpi(k2, "Variabilidad interanual (CV)", f"{cv_prom:.1f}", "%", "DIAGNÓSTICO", "ambar")
tarjeta_kpi(k3, "Margen bruto de reventa", f"{margen_pct:.1f}", "%", "DESCRIPTIVO")
tarjeta_kpi(k4, "Merma promedio", f"{merma:.1f}", "%", "DIAGNÓSTICO", "tierra")
tarjeta_kpi(k5, "Concentración top 3 cultivos", f"{concentracion:.1f}", "%", "PRESCRIPTIVO", "ambar")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ------------- Pestañas: 4 pilares + rentabilidad + datos crudos -------------
tab_desc, tab_diag, tab_pred, tab_presc, tab_rent, tab_datos = st.tabs(
    [":material/bar_chart: Descriptiva", ":material/query_stats: Diagnóstica",
     ":material/smart_toy: Predictiva", ":material/track_changes: Prescriptiva",
     ":material/payments: Rentabilidad", ":material/database: Datos"]
)

with tab_desc:
    renderizar_descriptiva(ecuador_f, compras_f, vol_cultivo)

with tab_diag:
    renderizar_diagnostica(rendimiento, ecuador_f)

with tab_pred:
    renderizar_predictiva(ecuador, resultados_modelo)

with tab_presc:
    renderizar_prescriptiva(recomendaciones)

with tab_rent:
    renderizar_rentabilidad(compras_f)

with tab_datos:
    renderizar_datos(cargar_tablas_estrella(), cargar_reporte_calidad())

renderizar_pie()
