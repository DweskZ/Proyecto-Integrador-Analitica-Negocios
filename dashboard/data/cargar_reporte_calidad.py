"""Carga del reporte de calidad del pipeline ETL."""

import json

import streamlit as st

from dashboard.data.rutas import RUTA_PROCESSED


@st.cache_data
def cargar_reporte_calidad() -> dict:
    """Devuelve el JSON con los pasos de calidad aplicados en el ETL."""
    with open(RUTA_PROCESSED / "reporte_calidad.json", encoding="utf-8") as archivo:
        return json.load(archivo)
