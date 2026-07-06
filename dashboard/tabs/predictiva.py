"""Pestaña Predictiva: simulador de escenarios con el modelo entrenado."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.data import cargar_modelo
from dashboard.theme import AMBAR, FONDO, TINTA_SUAVE, VERDE

# Malla del optimizador: lluvia y pesticidas cubren el rango de los sliders.
_LLUVIAS_MALLA = list(range(200, 4001, 200))
_PESTICIDAS_MALLA = list(range(0, 20001, 1000))


@st.cache_data
def _malla_rendimiento(cultivo_en: str, temp: float, anio: int) -> pd.DataFrame:
    """Predice el rendimiento sobre la malla pesticidas × lluvia (una sola pasada)."""
    escenarios = pd.DataFrame(
        [{
            "anio": anio,
            "precipitacion_mm": lluvia,
            "pesticidas_ton": pesticidas,
            "temperatura_media_c": temp,
            "pais": "Ecuador",
            "cultivo": cultivo_en,
        } for pesticidas in _PESTICIDAS_MALLA for lluvia in _LLUVIAS_MALLA]
    )
    escenarios["rendimiento"] = cargar_modelo().predict(
        escenarios[["anio", "precipitacion_mm", "pesticidas_ton",
                    "temperatura_media_c", "pais", "cultivo"]]
    )
    return escenarios


def _renderizar_optimizador(
    cultivo_sim: str, cultivo_en: str, anio: int,
    lluvia_sim: int, temp_sim: float, pest_sim: int, prediccion_actual: float,
) -> None:
    """Heatmap pesticidas × lluvia con el óptimo del modelo y recomendación."""
    malla = _malla_rendimiento(cultivo_en, temp_sim, anio)

    optimo_global = malla.loc[malla["rendimiento"].idxmax()]
    lluvia_cercana = min(_LLUVIAS_MALLA, key=lambda ll: abs(ll - lluvia_sim))
    franja = malla[malla["precipitacion_mm"] == lluvia_cercana]
    optimo_local = franja.loc[franja["rendimiento"].idxmax()]
    delta = (optimo_local["rendimiento"] / max(prediccion_actual, 1e-9) - 1) * 100

    st.markdown(
        f"""
<div class="section-note">
<b>🧪 ¿Qué combinación de insumos conviene? (según el modelo)</b> — con la lluvia
(~{lluvia_cercana:,} mm) y temperatura ({temp_sim:.1f} °C) de tu escenario, el nivel de
pesticidas que maximiza el rendimiento predicho de {cultivo_sim.lower()} es
<b>{optimo_local["pesticidas_ton"]:,.0f} ton</b> →
<b>{optimo_local["rendimiento"]:.2f} ton/ha</b> ({delta:+.1f} % vs tu escenario actual).
Pesticidas es la única palanca controlable: la lluvia y la temperatura son supuestos del
ciclo. El modelo es correlacional (ver pestaña Diagnóstica), por lo que esta cifra orienta,
no establece causalidad.
</div>
""",
        unsafe_allow_html=True,
    )

    matriz = malla.pivot(
        index="pesticidas_ton", columns="precipitacion_mm", values="rendimiento"
    )
    fig = go.Figure(
        go.Heatmap(
            z=matriz.values, x=matriz.columns, y=matriz.index,
            colorscale=[[0, FONDO], [1, VERDE]],
            colorbar=dict(title="ton/ha", thickness=12),
            hovertemplate=(
                "Lluvia: %{x:,} mm<br>Pesticidas: %{y:,} ton<br>"
                "Rendimiento predicho: %{z:.2f} ton/ha<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[optimo_global["precipitacion_mm"]], y=[optimo_global["pesticidas_ton"]],
            mode="markers+text", text=["⭐"], textfont=dict(size=16),
            marker=dict(size=1, color=VERDE),
            name="máximo del modelo", hovertemplate=(
                "⭐ Máximo del modelo<br>Lluvia: %{x:,} mm<br>"
                "Pesticidas: %{y:,} ton<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[lluvia_sim], y=[pest_sim],
            mode="markers+text", text=["✕"], textfont=dict(size=14, color=AMBAR),
            marker=dict(size=1, color=AMBAR),
            name="escenario actual", hovertemplate=(
                "✕ Escenario actual<br>Lluvia: %{x:,} mm<br>"
                "Pesticidas: %{y:,} ton<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=f"Rendimiento predicho · pesticidas × lluvia · {cultivo_sim} (temperatura fija {temp_sim:.1f} °C)",
        xaxis_title="Lluvia anual (mm)", yaxis_title="Pesticidas (ton)",
        height=430, showlegend=False, margin=dict(t=60, b=10),
    )
    with st.container(border=False):
        st.plotly_chart(fig, width='stretch')


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

    _renderizar_optimizador(
        cultivo_sim, cultivo_map[cultivo_sim], int(ecuador["anio"].max()) + 1,
        lluvia_sim, temp_sim, pest_sim, prediccion,
    )
