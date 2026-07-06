"""Catálogo de las tablas crudas del esquema estrella para el explorador."""

import pandas as pd
import streamlit as st

from dashboard.data.rutas import RUTA_PROCESSED

# Metadatos de cada tabla: tipo dentro del modelo dimensional, grano y descripción.
_CATALOGO = {
    "fact_rendimiento": {
        "tipo": "Hecho",
        "grano": "país × cultivo × año",
        "descripcion": (
            "Rendimiento agrícola (ton/ha) con clima y pesticidas asociados. "
            "Fuente: FAOSTAT + CCKP Banco Mundial."
        ),
    },
    "fact_compras": {
        "tipo": "Hecho",
        "grano": "orden de compra",
        "descripcion": (
            "Órdenes de compra internas: volúmenes, precios, márgenes y merma. "
            "Fuente interna simulada, sin PII."
        ),
    },
    "dim_cultivo": {
        "tipo": "Dimensión",
        "grano": "cultivo",
        "descripcion": "Cultivos con nombre en inglés/español y categoría agronómica.",
    },
    "dim_geografia": {
        "tipo": "Dimensión",
        "grano": "país",
        "descripcion": "Países con su región comercial para la empresa.",
    },
    "dim_tiempo": {
        "tipo": "Dimensión",
        "grano": "año",
        "descripcion": "Calendario anual con década y período.",
    },
    "dim_proveedor": {
        "tipo": "Dimensión",
        "grano": "proveedor",
        "descripcion": "Proveedores anonimizados (solo código) con región de origen.",
    },
    "api_worldbank": {
        "tipo": "Fuente externa",
        "grano": "país × año",
        "descripcion": (
            "Indicadores agrícolas del Banco Mundial (fertilizantes, lluvia, "
            "cereales, tierra agrícola) usados como contexto."
        ),
    },
}


@st.cache_data
def cargar_tablas_estrella() -> dict[str, dict]:
    """Devuelve {nombre: {"df", "tipo", "grano", "descripcion"}} por cada CSV."""
    tablas = {}
    for nombre, meta in _CATALOGO.items():
        df = pd.read_csv(RUTA_PROCESSED / f"{nombre}.csv")
        tablas[nombre] = {"df": df, **meta}
    return tablas
