"""
Fase 2.2 — Fuente interna simulada: registros de compras de AgroComercial del Litoral S.A.

Genera el Excel de compras históricas de la empresa (fuente "Excel/interno" de la
Fase 1.4). Los volúmenes y precios se simulan de forma coherente con el
rendimiento real de Ecuador del dataset FAO/Banco Mundial, para que el análisis
descriptivo y prescriptivo tenga consistencia interna.

Cumplimiento normativo (Fase 2.3): los proveedores se registran únicamente con
códigos anónimos (PROV-001, PROV-002, ...). No se almacena ningún dato personal
(PII): ni nombres, ni cédulas/RUC, ni teléfonos, ni ubicaciones exactas de fincas.

Salida: data/raw/compras_internas.xlsx
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_YIELD = RUTA_PROYECTO / "data" / "raw" / "rendimiento_actualizado.csv"
RUTA_SALIDA = RUTA_PROYECTO / "data" / "raw" / "compras_internas.xlsx"

SEMILLA = 2026

# Precios de referencia USD/tonelada (aproximados al mercado ecuatoriano,
# declarados como supuesto del escenario simulado)
PRECIO_COMPRA_BASE_USD_TON = {
    "Rice, paddy": 380.0,
    "Maize": 310.0,
    "Potatoes": 350.0,
    "Cassava": 260.0,
    "Plantains and others": 300.0,
    "Soybeans": 480.0,
    "Wheat": 340.0,
    "Sweet potatoes": 320.0,
    "Sorghum": 280.0,
}

# Margen bruto objetivo de reventa por cultivo (supuesto del escenario)
MARGEN_REVENTA_OBJETIVO = {
    "Rice, paddy": 0.22,
    "Maize": 0.18,
    "Potatoes": 0.25,
    "Cassava": 0.20,
    "Plantains and others": 0.24,
    "Soybeans": 0.15,
    "Wheat": 0.14,
    "Sweet potatoes": 0.21,
    "Sorghum": 0.16,
}

REGIONES_ECUADOR = ["Costa", "Sierra", "Amazonía"]

CANALES_REVENTA = [
    "Industria procesadora",
    "Supermercados",
    "Mercado de exportación",
    "Mayoristas locales",
]


def generar_compras() -> pd.DataFrame:
    rng = np.random.default_rng(SEMILLA)

    rendimiento = pd.read_csv(RUTA_YIELD)
    ecuador = rendimiento[rendimiento["Area"] == "Ecuador"].copy()
    ecuador["ton_ha"] = ecuador["hg/ha_yield"] / 10_000.0

    # Rendimiento promedio anual por cultivo (para modular volúmenes comprados)
    base = (
        ecuador.groupby(["Item", "Year"], as_index=False)["ton_ha"].mean()
    )

    proveedores = [f"PROV-{i:03d}" for i in range(1, 41)]

    registros: list[dict] = []
    numero_orden = 0
    for _, fila in base.iterrows():
        cultivo, anio, ton_ha = fila["Item"], int(fila["Year"]), fila["ton_ha"]
        # Entre 3 y 7 órdenes de compra por cultivo-año
        for _ in range(int(rng.integers(3, 8))):
            numero_orden += 1
            hectareas_contratadas = float(rng.uniform(15, 220))
            merma = float(rng.uniform(0.02, 0.09))
            volumen_ton = hectareas_contratadas * ton_ha * (1 - merma)

            precio_base = PRECIO_COMPRA_BASE_USD_TON[cultivo]
            # Los precios suben cuando el rendimiento del año es bajo (escasez)
            factor_escasez = float(np.clip(1.6 - ton_ha / base[base["Item"] == cultivo]["ton_ha"].mean(), 0.85, 1.35))
            precio_compra = precio_base * factor_escasez * float(rng.uniform(0.93, 1.07))

            margen = MARGEN_REVENTA_OBJETIVO[cultivo] * float(rng.uniform(0.7, 1.25))
            precio_reventa = precio_compra * (1 + margen)

            registros.append(
                {
                    "orden_compra": f"OC-{anio}-{numero_orden:05d}",
                    "anio": anio,
                    "mes": int(rng.integers(1, 13)),
                    "codigo_proveedor": str(rng.choice(proveedores)),
                    "region": str(rng.choice(REGIONES_ECUADOR, p=[0.55, 0.35, 0.10])),
                    "cultivo": cultivo,
                    "hectareas_contratadas": round(hectareas_contratadas, 1),
                    "volumen_comprado_ton": round(volumen_ton, 2),
                    "precio_compra_usd_ton": round(precio_compra, 2),
                    "precio_reventa_usd_ton": round(precio_reventa, 2),
                    "canal_reventa": str(rng.choice(CANALES_REVENTA, p=[0.35, 0.30, 0.15, 0.20])),
                    "merma_pct": round(merma * 100, 1),
                }
            )

    compras = pd.DataFrame(registros)
    compras["costo_total_usd"] = (
        compras["volumen_comprado_ton"] * compras["precio_compra_usd_ton"]
    ).round(2)
    compras["ingreso_reventa_usd"] = (
        compras["volumen_comprado_ton"] * compras["precio_reventa_usd_ton"]
    ).round(2)
    compras["margen_bruto_usd"] = (
        compras["ingreso_reventa_usd"] - compras["costo_total_usd"]
    ).round(2)
    return compras


if __name__ == "__main__":
    print("Generando registros internos de compras (simulados, sin PII)...")
    compras = generar_compras()
    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    compras.to_excel(RUTA_SALIDA, index=False, sheet_name="compras_historicas")
    print(f"OK — {len(compras)} órdenes de compra guardadas en {RUTA_SALIDA}")
