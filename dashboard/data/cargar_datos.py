"""Carga del esquema estrella ya unido para las vistas analíticas."""

import pandas as pd
import streamlit as st

from dashboard.data.rutas import RUTA_PROCESSED, RUTA_REPORTES


@st.cache_data
def cargar_datos() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Devuelve (rendimiento, compras, recomendaciones) con dimensiones unidas."""
    fact_rend = pd.read_csv(RUTA_PROCESSED / "fact_rendimiento.csv")
    fact_compras = pd.read_csv(RUTA_PROCESSED / "fact_compras.csv")
    dim_geo = pd.read_csv(RUTA_PROCESSED / "dim_geografia.csv")
    dim_cultivo = pd.read_csv(RUTA_PROCESSED / "dim_cultivo.csv")
    recomendaciones = pd.read_csv(RUTA_REPORTES / "recomendaciones_compra.csv")

    rendimiento = (
        fact_rend.merge(dim_geo, on="id_geografia")
        .merge(dim_cultivo, on="id_cultivo")
        .rename(columns={"id_tiempo": "anio"})
    )
    compras = fact_compras.merge(dim_cultivo, on="id_cultivo").rename(
        columns={"id_tiempo": "anio"}
    )
    return rendimiento, compras, recomendaciones
