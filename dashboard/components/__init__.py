"""Componentes visuales reutilizables del dashboard."""

from dashboard.components.hero import renderizar_hero
from dashboard.components.pie_pagina import renderizar_pie
from dashboard.components.silenciar_asyncio import silenciar_conn_reset_windows
from dashboard.components.tarjeta_kpi import tarjeta_kpi

__all__ = [
    "renderizar_hero",
    "renderizar_pie",
    "silenciar_conn_reset_windows",
    "tarjeta_kpi",
]
