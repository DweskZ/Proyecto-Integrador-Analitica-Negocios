"""Pestaña Descriptiva: evolución, ranking, margen y volumen."""

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.theme import TIERRA, VERDE, VERDE_CLARO


def renderizar_descriptiva(
    ecuador_f: pd.DataFrame, compras_f: pd.DataFrame, vol_cultivo: pd.Series
) -> None:
    """Dibuja los cuatro gráficos descriptivos con los datos ya filtrados."""
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
