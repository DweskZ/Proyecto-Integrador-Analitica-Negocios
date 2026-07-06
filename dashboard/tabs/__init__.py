"""Pestañas del dashboard: los cuatro pilares analíticos + datos crudos."""

from dashboard.tabs.datos import renderizar_datos
from dashboard.tabs.descriptiva import renderizar_descriptiva
from dashboard.tabs.diagnostica import renderizar_diagnostica
from dashboard.tabs.predictiva import renderizar_predictiva
from dashboard.tabs.prescriptiva import renderizar_prescriptiva

__all__ = [
    "renderizar_datos",
    "renderizar_descriptiva",
    "renderizar_diagnostica",
    "renderizar_predictiva",
    "renderizar_prescriptiva",
]
