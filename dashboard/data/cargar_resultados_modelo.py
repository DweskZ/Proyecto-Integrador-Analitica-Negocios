"""Carga de las métricas reales del modelo (reports/modelo_resultados.json)."""

import json

import streamlit as st

from dashboard.data.rutas import RUTA_REPORTES


@st.cache_data
def cargar_resultados_modelo() -> dict:
    """Devuelve el JSON de resultados del entrenamiento (métricas, XAI, sesgos)."""
    with open(RUTA_REPORTES / "modelo_resultados.json", encoding="utf-8") as archivo:
        return json.load(archivo)
