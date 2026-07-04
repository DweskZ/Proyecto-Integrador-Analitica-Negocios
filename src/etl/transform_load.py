"""
Fase 2.1 y 2.2 — Transformación y Carga (T y L de ETL): esquema estrella.

Integra las tres fuentes de la Fase 1.4 (versión actualizada a 1990-2023):
  1. Dataset consolidado FAO + clima CCKP: rendimiento_actualizado.csv
     (construido por extraer_datos_actualizados.py desde FAOSTAT bulk y la
     API pública del Banco Mundial/CCKP; reemplaza al dataset de Kaggle que
     llegaba solo hasta 2013)
  2. API pública del Banco Mundial: worldbank_indicadores.csv
  3. Excel interno de compras (simulado, anonimizado): compras_internas.xlsx

y produce un MODELO DIMENSIONAL EN ESTRELLA (data/processed/):

  Tablas de dimensiones:
    - dim_tiempo     (id_tiempo, anio, decada, periodo)
    - dim_geografia  (id_geografia, pais, codigo_iso3, region_comercial)
    - dim_cultivo    (id_cultivo, cultivo, cultivo_es, categoria)
    - dim_proveedor  (id_proveedor, codigo_proveedor, region_origen)

  Tablas de hechos:
    - fact_rendimiento (métricas: rendimiento_ton_ha, precipitacion_mm,
                        pesticidas_ton, temperatura_media_c)
    - fact_compras     (métricas: volumen_ton, precios, costo, ingreso, margen)

Calidad de datos (documentada en data/processed/reporte_calidad.json):
  - Eliminación de duplicados exactos.
  - Tipado explícito de columnas (numéricas y categóricas).
  - Manejo de nulos: descarte en variables críticas del hecho (no se imputan
    métricas de negocio); registro de cuántas filas se pierden y por qué.
  - Validación de rangos físicos (rendimiento > 0, temperatura entre -10 y 45 °C,
    lluvia entre 0 y 12000 mm).
  - Consistencia referencial: toda fila de hechos referencia una clave existente
    en cada dimensión.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_RAW = RUTA_PROYECTO / "data" / "raw"
RUTA_EXTERNAL = RUTA_PROYECTO / "data" / "external"
RUTA_PROCESSED = RUTA_PROYECTO / "data" / "processed"

TRADUCCION_CULTIVOS = {
    "Cassava": ("Yuca", "Tubérculo"),
    "Maize": ("Maíz", "Cereal"),
    "Plantains and others": ("Plátano y otros", "Fruta/Musácea"),
    "Potatoes": ("Papa", "Tubérculo"),
    "Rice, paddy": ("Arroz en cáscara", "Cereal"),
    "Sorghum": ("Sorgo", "Cereal"),
    "Soybeans": ("Soya", "Oleaginosa"),
    "Sweet potatoes": ("Camote", "Tubérculo"),
    "Wheat": ("Trigo", "Cereal"),
    "Yams": ("Ñame", "Tubérculo"),
}

PAISES_ANDINOS = {"Colombia", "Peru", "Brazil", "Mexico", "Argentina", "Chile"}

reporte_calidad: dict = {"pasos": []}


def registrar_paso(nombre: str, detalle: dict) -> None:
    reporte_calidad["pasos"].append({"paso": nombre, **detalle})
    print(f"  [calidad] {nombre}: {detalle}")


def limpiar_rendimiento() -> pd.DataFrame:
    """Limpieza y tipado del dataset consolidado FAO + Banco Mundial."""
    crudo = pd.read_csv(RUTA_RAW / "rendimiento_actualizado.csv")
    filas_iniciales = len(crudo)

    crudo = crudo.rename(
        columns={
            "Area": "pais",
            "Item": "cultivo",
            "Year": "anio",
            "hg/ha_yield": "rendimiento_hg_ha",
            "average_rain_fall_mm_per_year": "precipitacion_mm",
            "pesticides_tonnes": "pesticidas_ton",
            "avg_temp": "temperatura_media_c",
        }
    )

    duplicados = int(crudo.duplicated().sum())
    crudo = crudo.drop_duplicates()
    registrar_paso("eliminacion_duplicados", {"duplicados_eliminados": duplicados})

    # Tipado explícito: la columna de lluvia llega como texto en la fuente original
    for col in ["rendimiento_hg_ha", "precipitacion_mm", "pesticidas_ton", "temperatura_media_c"]:
        crudo[col] = pd.to_numeric(crudo[col], errors="coerce")
    crudo["anio"] = crudo["anio"].astype(int)

    nulos_por_columna = crudo.isna().sum().to_dict()
    filas_con_nulos = int(crudo.isna().any(axis=1).sum())
    crudo = crudo.dropna()
    registrar_paso(
        "manejo_nulos",
        {
            "politica": "descartar filas con nulos en métricas críticas (sin imputación)",
            "nulos_por_columna": {k: int(v) for k, v in nulos_por_columna.items()},
            "filas_descartadas": filas_con_nulos,
        },
    )

    # Validación de rangos físicos
    validas = (
        (crudo["rendimiento_hg_ha"] > 0)
        & crudo["temperatura_media_c"].between(-10, 45)
        & crudo["precipitacion_mm"].between(0, 12_000)
        & (crudo["pesticidas_ton"] >= 0)
    )
    fuera_rango = int((~validas).sum())
    crudo = crudo[validas]
    registrar_paso("validacion_rangos_fisicos", {"filas_fuera_de_rango": fuera_rango})

    # Conversión de unidades a la métrica de negocio: toneladas por hectárea
    crudo["rendimiento_ton_ha"] = (crudo["rendimiento_hg_ha"] / 10_000).round(3)

    registrar_paso(
        "resumen_rendimiento",
        {"filas_iniciales": filas_iniciales, "filas_finales": len(crudo)},
    )
    return crudo.reset_index(drop=True)


def construir_dimensiones(rendimiento: pd.DataFrame, compras: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # dim_tiempo
    anios = sorted(set(rendimiento["anio"]) | set(compras["anio"]))
    dim_tiempo = pd.DataFrame({"anio": anios})
    dim_tiempo["id_tiempo"] = dim_tiempo["anio"]
    dim_tiempo["decada"] = (dim_tiempo["anio"] // 10 * 10).astype(str) + "s"
    dim_tiempo["periodo"] = np.where(dim_tiempo["anio"] < 2000, "1990-1999",
                             np.where(dim_tiempo["anio"] < 2010, "2000-2009",
                             np.where(dim_tiempo["anio"] < 2020, "2010-2019", "2020-2023")))
    dim_tiempo = dim_tiempo[["id_tiempo", "anio", "decada", "periodo"]]

    # dim_geografia
    dim_geografia = (
        rendimiento[["pais"]].drop_duplicates().sort_values("pais").reset_index(drop=True)
    )
    dim_geografia["id_geografia"] = dim_geografia.index + 1
    dim_geografia["region_comercial"] = np.where(
        dim_geografia["pais"] == "Ecuador",
        "Ecuador (mercado propio)",
        np.where(dim_geografia["pais"].isin(PAISES_ANDINOS), "Latinoamérica (referencia)", "Resto del mundo"),
    )
    dim_geografia = dim_geografia[["id_geografia", "pais", "region_comercial"]]

    # dim_cultivo
    dim_cultivo = (
        rendimiento[["cultivo"]].drop_duplicates().sort_values("cultivo").reset_index(drop=True)
    )
    dim_cultivo["id_cultivo"] = dim_cultivo.index + 1
    dim_cultivo["cultivo_es"] = dim_cultivo["cultivo"].map(lambda c: TRADUCCION_CULTIVOS[c][0])
    dim_cultivo["categoria"] = dim_cultivo["cultivo"].map(lambda c: TRADUCCION_CULTIVOS[c][1])
    dim_cultivo = dim_cultivo[["id_cultivo", "cultivo", "cultivo_es", "categoria"]]

    # dim_proveedor (ya llega anonimizada desde la fuente)
    dim_proveedor = (
        compras[["codigo_proveedor", "region"]]
        .drop_duplicates(subset=["codigo_proveedor"])
        .sort_values("codigo_proveedor")
        .reset_index(drop=True)
        .rename(columns={"region": "region_origen"})
    )
    dim_proveedor["id_proveedor"] = dim_proveedor.index + 1
    dim_proveedor = dim_proveedor[["id_proveedor", "codigo_proveedor", "region_origen"]]

    return {
        "dim_tiempo": dim_tiempo,
        "dim_geografia": dim_geografia,
        "dim_cultivo": dim_cultivo,
        "dim_proveedor": dim_proveedor,
    }


def construir_hechos(
    rendimiento: pd.DataFrame, compras: pd.DataFrame, dims: dict[str, pd.DataFrame]
) -> dict[str, pd.DataFrame]:
    fact_rendimiento = (
        rendimiento.merge(dims["dim_geografia"][["id_geografia", "pais"]], on="pais")
        .merge(dims["dim_cultivo"][["id_cultivo", "cultivo"]], on="cultivo")
        .assign(id_tiempo=lambda d: d["anio"])
    )[
        [
            "id_geografia",
            "id_cultivo",
            "id_tiempo",
            "rendimiento_ton_ha",
            "precipitacion_mm",
            "pesticidas_ton",
            "temperatura_media_c",
        ]
    ]

    fact_compras = (
        compras.merge(dims["dim_cultivo"][["id_cultivo", "cultivo"]], left_on="cultivo", right_on="cultivo")
        .merge(dims["dim_proveedor"][["id_proveedor", "codigo_proveedor"]], on="codigo_proveedor")
        .assign(id_tiempo=lambda d: d["anio"])
    )[
        [
            "orden_compra",
            "id_tiempo",
            "mes",
            "id_cultivo",
            "id_proveedor",
            "canal_reventa",
            "hectareas_contratadas",
            "volumen_comprado_ton",
            "precio_compra_usd_ton",
            "precio_reventa_usd_ton",
            "costo_total_usd",
            "ingreso_reventa_usd",
            "margen_bruto_usd",
            "merma_pct",
        ]
    ]

    # Consistencia referencial
    assert fact_rendimiento["id_geografia"].isin(dims["dim_geografia"]["id_geografia"]).all()
    assert fact_rendimiento["id_cultivo"].isin(dims["dim_cultivo"]["id_cultivo"]).all()
    assert fact_compras["id_proveedor"].isin(dims["dim_proveedor"]["id_proveedor"]).all()
    registrar_paso(
        "consistencia_referencial",
        {"resultado": "todas las claves foráneas de los hechos existen en las dimensiones"},
    )

    return {"fact_rendimiento": fact_rendimiento, "fact_compras": fact_compras}


def main() -> None:
    print("ETL — Transformación y carga del esquema estrella")
    RUTA_PROCESSED.mkdir(parents=True, exist_ok=True)

    rendimiento = limpiar_rendimiento()
    compras = pd.read_excel(RUTA_RAW / "compras_internas.xlsx")

    # Verificación de anonimización (Fase 2.3): ninguna columna con PII
    columnas_pii_prohibidas = {"nombre", "cedula", "ruc", "telefono", "direccion", "email"}
    assert not columnas_pii_prohibidas & set(compras.columns), "Fuente interna contiene PII"
    registrar_paso(
        "cumplimiento_normativo",
        {"verificacion": "fuente interna sin columnas PII; proveedores solo con código anónimo"},
    )

    dims = construir_dimensiones(rendimiento, compras)
    hechos = construir_hechos(rendimiento, compras, dims)

    for nombre, tabla in {**dims, **hechos}.items():
        destino = RUTA_PROCESSED / f"{nombre}.csv"
        tabla.to_csv(destino, index=False)
        print(f"  Guardado {nombre}: {len(tabla)} filas -> {destino.name}")

    # Copia de indicadores de la API para el dashboard (si ya se extrajo)
    api_csv = RUTA_EXTERNAL / "worldbank_indicadores.csv"
    if api_csv.exists():
        pd.read_csv(api_csv).to_csv(RUTA_PROCESSED / "api_worldbank.csv", index=False)
        print("  Copiados indicadores de la API del Banco Mundial")

    with open(RUTA_PROCESSED / "reporte_calidad.json", "w", encoding="utf-8") as f:
        json.dump(reporte_calidad, f, ensure_ascii=False, indent=2)
    print("OK — esquema estrella y reporte de calidad generados")


if __name__ == "__main__":
    main()
