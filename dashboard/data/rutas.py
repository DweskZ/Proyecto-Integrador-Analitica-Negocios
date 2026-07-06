"""Rutas del proyecto usadas por el dashboard."""

from pathlib import Path

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_PROCESSED = RUTA_PROYECTO / "data" / "processed"
RUTA_REPORTES = RUTA_PROYECTO / "reports"
RUTA_MODELO = RUTA_PROYECTO / "models" / "modelo_rendimiento.joblib"
