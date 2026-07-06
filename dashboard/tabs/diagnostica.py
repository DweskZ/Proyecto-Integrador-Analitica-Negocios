"""Pestaña Diagnóstica: correlaciones y dispersión clima-rendimiento."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.theme import ROJO, VERDE


def renderizar_diagnostica(rendimiento: pd.DataFrame, ecuador_f: pd.DataFrame) -> None:
    """Dibuja la matriz de correlación global y la dispersión para Ecuador."""
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
