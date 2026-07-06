"""Encabezado hero del dashboard."""

import streamlit as st


def renderizar_hero(resultados_modelo: dict) -> None:
    """Dibuja el encabezado con badges; las métricas salen del JSON real."""
    ganador = resultados_modelo["modelo_ganador"]
    r2 = resultados_modelo["metricas_por_modelo"][ganador]["r2"]
    st.markdown(
        f"""
<div class="hero">
  <h1><span class="icono-material">agriculture</span> AgroComercial del Litoral S.A.</h1>
  <p>Dashboard estratégico · Predicción del rendimiento de cosechas y planificación de compras</p>
  <div class="badges">
    <span class="badge"><span class="icono-material">satellite_alt</span> FAOSTAT + Banco Mundial (API pública)</span>
    <span class="badge"><span class="icono-material">flag</span> Ecuador · 1990–2023</span>
    <span class="badge"><span class="icono-material">smart_toy</span> {ganador} · R² {r2:.2f}</span>
    <span class="badge"><span class="icono-material">lock</span> Datos sin PII</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
