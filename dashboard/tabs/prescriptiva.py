"""Pestaña Prescriptiva: plan de compras recomendado por la regla de decisión."""

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.theme import AMBAR, ROJO, TINTA_SUAVE, VERDE


def renderizar_prescriptiva(recomendaciones: pd.DataFrame) -> None:
    """Dibuja el índice de oferta y las tarjetas de decisión por cultivo."""
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
