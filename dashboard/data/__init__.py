"""Acceso a datos del dashboard: rutas y cargadores cacheados."""

from dashboard.data.cargar_datos import cargar_datos
from dashboard.data.cargar_modelo import cargar_modelo
from dashboard.data.cargar_reporte_calidad import cargar_reporte_calidad
from dashboard.data.cargar_resultados_modelo import cargar_resultados_modelo
from dashboard.data.cargar_tablas_estrella import cargar_tablas_estrella
from dashboard.data.rutas import (
    RUTA_MODELO,
    RUTA_PROCESSED,
    RUTA_PROYECTO,
    RUTA_REPORTES,
)

__all__ = [
    "RUTA_MODELO",
    "RUTA_PROCESSED",
    "RUTA_PROYECTO",
    "RUTA_REPORTES",
    "cargar_datos",
    "cargar_modelo",
    "cargar_reporte_calidad",
    "cargar_resultados_modelo",
    "cargar_tablas_estrella",
]
