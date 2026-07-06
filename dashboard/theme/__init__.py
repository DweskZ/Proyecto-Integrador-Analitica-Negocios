"""Tema visual del dashboard: paleta, template de Plotly y CSS."""

from dashboard.theme.colores import (
    AMBAR,
    FONDO,
    ROJO,
    SECUENCIA_CULTIVOS,
    TIERRA,
    TINTA,
    TINTA_SUAVE,
    VERDE,
    VERDE_CLARO,
    VERDE_OSCURO,
)
from dashboard.theme.css import inyectar_css
from dashboard.theme.plotly_template import registrar_tema_plotly

__all__ = [
    "AMBAR",
    "FONDO",
    "ROJO",
    "SECUENCIA_CULTIVOS",
    "TIERRA",
    "TINTA",
    "TINTA_SUAVE",
    "VERDE",
    "VERDE_CLARO",
    "VERDE_OSCURO",
    "inyectar_css",
    "registrar_tema_plotly",
]
