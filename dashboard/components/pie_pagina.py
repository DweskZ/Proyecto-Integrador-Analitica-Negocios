"""Pie de página del dashboard."""

import streamlit as st

from dashboard.theme import TINTA_SUAVE


def renderizar_pie() -> None:
    """Dibuja el pie de página institucional."""
    st.markdown(
        f"""
<div style="text-align:center; color:{TINTA_SUAVE}; font-size:.75rem; padding:18px 0 6px 0;">
Proyecto Integrador · Analítica de Negocios 7A · Universidad Laica Eloy Alfaro de Manabí ·
Fuentes: FAO, Banco Mundial (API pública) y registros internos anonimizados
</div>
""",
        unsafe_allow_html=True,
    )
