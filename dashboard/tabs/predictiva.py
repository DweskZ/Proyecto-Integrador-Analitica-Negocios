"""Pestaña Predictiva: simulador de escenarios con el modelo entrenado."""

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.data import cargar_modelo
from dashboard.theme import AMBAR, TINTA_SUAVE, VERDE


def renderizar_predictiva(ecuador: pd.DataFrame, resultados_modelo: dict) -> None:
    """Dibuja el simulador; las métricas mostradas salen del JSON real."""
    ganador = resultados_modelo["modelo_ganador"]
    metricas = resultados_modelo["metricas_por_modelo"][ganador]
    rmse_ecuador = resultados_modelo["error_por_grupo"]["rmse_ecuador"]

    st.markdown(
        f"""
<div class="section-note">
<b>Modelo ganador: {ganador}</b> — R² = {metricas["r2"]:.2f}, RMSE = {metricas["rmse_ton_ha"]:.2f} ton/ha
en datos nunca vistos (en Ecuador el error baja a {rmse_ecuador:.2f} ton/ha).
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
  ± {rmse_ecuador:.2f} ton/ha (RMSE Ecuador) · La predicción apoya la decisión, no reemplaza al comité
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
