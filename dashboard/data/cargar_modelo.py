"""Carga del modelo predictivo entrenado."""

import joblib
import streamlit as st

from dashboard.data.rutas import RUTA_MODELO


@st.cache_resource
def cargar_modelo():
    """Devuelve el pipeline de sklearn serializado con joblib.

    Seguridad: el .joblib es un artefacto propio, generado por
    src/models/entrenar_modelo.py dentro de este mismo repositorio
    (no proviene de una fuente externa), por lo que su deserialización
    es confiable.
    """
    return joblib.load(RUTA_MODELO)
