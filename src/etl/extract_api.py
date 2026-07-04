"""
Fase 2.2 — Extracción (E de ETL): API pública del Banco Mundial.

AgroComercial del Litoral S.A. — Proyecto Integrador de Analítica de Negocios.

Este módulo consume la API pública del Banco Mundial (World Bank Open Data,
https://api.worldbank.org/v2) para obtener indicadores agroclimáticos oficiales
de Ecuador y países de referencia. Cumple el requisito de la Fase 1.4:
"al menos utilizar una API pública".

Indicadores extraídos:
  - AG.YLD.CREL.KG : Rendimiento de cereales (kg por hectárea)
  - AG.LND.PRCP.MM : Precipitación media anual (mm)
  - AG.LND.AGRI.ZS : Tierra agrícola (% del territorio)
  - AG.CON.FERT.ZS : Consumo de fertilizantes (kg por ha de tierra cultivable)

Salida: data/external/worldbank_indicadores.csv
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_SALIDA = RUTA_PROYECTO / "data" / "external" / "worldbank_indicadores.csv"

URL_BASE = "https://api.worldbank.org/v2/country/{pais}/indicator/{indicador}"

INDICADORES = {
    "AG.YLD.CREL.KG": "rendimiento_cereales_kg_ha",
    "AG.LND.PRCP.MM": "precipitacion_media_mm",
    "AG.LND.AGRI.ZS": "tierra_agricola_pct",
    "AG.CON.FERT.ZS": "consumo_fertilizantes_kg_ha",
}

# Ecuador (mercado principal) + países andinos de referencia comercial
PAISES = ["ECU", "COL", "PER", "BRA", "MEX"]

RANGO_ANIOS = "1990:2023"


def extraer_indicador(codigo_pais: str, codigo_indicador: str) -> list[dict]:
    """Descarga todas las observaciones de un indicador para un país.

    La API pública ocasionalmente devuelve errores transitorios (400/5xx),
    por lo que se reintenta hasta 4 veces con espera incremental.
    """
    url = URL_BASE.format(pais=codigo_pais, indicador=codigo_indicador)
    parametros = {"format": "json", "date": RANGO_ANIOS, "per_page": 200}

    respuesta = None
    for intento in range(4):
        respuesta = requests.get(url, params=parametros, timeout=60)
        if respuesta.status_code == 200:
            break
        time.sleep(1.5 * (intento + 1))
    else:
        print(f"    AVISO: {codigo_indicador}/{codigo_pais} falló tras 4 intentos; se omite")
        return []
    cuerpo = respuesta.json()

    # La API devuelve [metadata, observaciones]
    if len(cuerpo) < 2 or cuerpo[1] is None:
        return []

    observaciones = []
    for registro in cuerpo[1]:
        if registro["value"] is None:
            continue
        observaciones.append(
            {
                "codigo_pais": registro["countryiso3code"],
                "pais": registro["country"]["value"],
                "anio": int(registro["date"]),
                "indicador": INDICADORES[codigo_indicador],
                "valor": float(registro["value"]),
            }
        )
    return observaciones


def ejecutar_extraccion() -> pd.DataFrame:
    """Extrae todos los indicadores para todos los países configurados."""
    todas: list[dict] = []
    for pais in PAISES:
        for indicador in INDICADORES:
            print(f"  Extrayendo {indicador} para {pais}...")
            todas.extend(extraer_indicador(pais, indicador))
            time.sleep(0.3)  # cortesía con la API pública

    tabla_larga = pd.DataFrame(todas)
    tabla = tabla_larga.pivot_table(
        index=["codigo_pais", "pais", "anio"],
        columns="indicador",
        values="valor",
    ).reset_index()
    tabla.columns.name = None
    return tabla.sort_values(["codigo_pais", "anio"])


if __name__ == "__main__":
    print("Extracción desde la API pública del Banco Mundial")
    datos = ejecutar_extraccion()
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    datos.to_csv(RUTA_SALIDA, index=False)
    print(f"OK — {len(datos)} filas guardadas en {RUTA_SALIDA}")
