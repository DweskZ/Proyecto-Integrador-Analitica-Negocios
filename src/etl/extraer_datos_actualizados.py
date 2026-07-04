"""
Fase 2.2 — Extracción ACTUALIZADA (1990-2023): reemplaza al dataset de Kaggle.

El dataset de Kaggle llegaba solo hasta 2013. Este módulo reconstruye el mismo
dataset consolidado pero con datos vigentes, usando exclusivamente fuentes
públicas oficiales:

  1. FAOSTAT bulk download (bulks-faostat.fao.org, dominio QCL):
     rendimiento (kg/ha) por país-cultivo-año, hasta 2024.
  2. FAOSTAT bulk download (dominio RP): pesticidas totales (t) por país-año,
     hasta 2023.
  3. API pública del Climate Change Knowledge Portal del Banco Mundial (CCKP):
     temperatura media anual (tas, °C) y precipitación anual (pr, mm) por
     país-año, serie CRU TS 4.08 hasta 2023.

Salida: data/raw/rendimiento_actualizado.csv con el MISMO formato de columnas
que yield_df.csv, de modo que el resto del pipeline funciona sin cambios:
  Area, Item, Year, hg/ha_yield, average_rain_fall_mm_per_year,
  pesticides_tonnes, avg_temp

El clima descargado se cachea en data/external/cckp_clima.csv para no golpear
la API en cada reejecución.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import pycountry
import requests

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_RAW = RUTA_PROYECTO / "data" / "raw"
RUTA_EXTERNAL = RUTA_PROYECTO / "data" / "external"
RUTA_QCL = RUTA_RAW / "Production_Crops_Livestock_E_All_Data_(Normalized).csv"
RUTA_RP = RUTA_RAW / "Inputs_Pesticides_Use_E_All_Data_(Normalized).csv"
RUTA_CACHE_CLIMA = RUTA_EXTERNAL / "cckp_clima.csv"
RUTA_SALIDA = RUTA_RAW / "rendimiento_actualizado.csv"

ANIO_INICIO, ANIO_FIN = 1990, 2023

URL_CCKP = (
    "https://cckpapi.worldbank.org/cckp/v1/"
    "cru-x0.5_timeseries_tas,pr_timeseries_annual_1901-2023_mean_historical_"
    "cru_ts4.08_mean/{iso3}?_format=json"
)

# Código de ítem FAOSTAT -> nombre de cultivo usado en el resto del proyecto
# (mismos nombres del dataset original de Kaggle para no romper dimensiones)
CULTIVOS = {
    27: "Rice, paddy",
    56: "Maize",
    15: "Wheat",
    116: "Potatoes",
    125: "Cassava",
    236: "Soybeans",
    83: "Sorghum",
    122: "Sweet potatoes",
    137: "Yams",
    489: "Plantains and others",
}

# Nombres FAO que pycountry no resuelve solo
ISO3_MANUAL = {
    "Bolivia (Plurinational State of)": "BOL",
    "Venezuela (Bolivarian Republic of)": "VEN",
    "Iran (Islamic Republic of)": "IRN",
    "Republic of Korea": "KOR",
    "Democratic People's Republic of Korea": "PRK",
    "United Republic of Tanzania": "TZA",
    "Democratic Republic of the Congo": "COD",
    "Lao People's Democratic Republic": "LAO",
    "Republic of Moldova": "MDA",
    "Syrian Arab Republic": "SYR",
    "Viet Nam": "VNM",
    "Türkiye": "TUR",
    "Netherlands (Kingdom of the)": "NLD",
    "United Kingdom of Great Britain and Northern Ireland": "GBR",
    "United States of America": "USA",
    "Russian Federation": "RUS",
    "Czechia": "CZE",
    "China, mainland": "CHN",
    "Côte d'Ivoire": "CIV",
    "Cabo Verde": "CPV",
    "North Macedonia": "MKD",
    "Micronesia (Federated States of)": "FSM",
    "China, Taiwan Province of": "TWN",
}

# Agregados regionales de FAOSTAT que no son países (se excluyen)
EXCLUIR = {
    "World", "Africa", "Americas", "Asia", "Europe", "Oceania",
    "China", "European Union (27)", "Net Food Importing Developing Countries",
}


def resolver_iso3(nombre_fao: str) -> str | None:
    if nombre_fao in ISO3_MANUAL:
        return ISO3_MANUAL[nombre_fao]
    try:
        return pycountry.countries.lookup(nombre_fao).alpha_3
    except LookupError:
        return None


def cargar_rendimiento() -> pd.DataFrame:
    print("  Leyendo FAOSTAT QCL (rendimiento)...")
    qcl = pd.read_csv(
        RUTA_QCL,
        usecols=["Area", "Item Code", "Element", "Year", "Value"],
        dtype={"Value": "float64"},
        low_memory=False,
    )
    rend = qcl[
        qcl["Item Code"].isin(CULTIVOS)
        & (qcl["Element"] == "Yield")
        & qcl["Year"].between(ANIO_INICIO, ANIO_FIN)
        & qcl["Value"].notna()
        & (qcl["Value"] > 0)
    ].copy()
    rend["Item"] = rend["Item Code"].map(CULTIVOS)
    # kg/ha -> hg/ha (formato del dataset original)
    rend["hg/ha_yield"] = rend["Value"] * 10
    return rend[["Area", "Item", "Year", "hg/ha_yield"]]


def cargar_pesticidas() -> pd.DataFrame:
    print("  Leyendo FAOSTAT RP (pesticidas)...")
    rp = pd.read_csv(RUTA_RP, low_memory=False)
    pest = rp[
        (rp["Element"] == "Agricultural Use")
        & (rp["Item"] == "Pesticides (total)")
        & rp["Year"].between(ANIO_INICIO, ANIO_FIN)
        & rp["Value"].notna()
    ]
    return pest.rename(columns={"Value": "pesticides_tonnes"})[
        ["Area", "Year", "pesticides_tonnes"]
    ]


def descargar_clima(paises: pd.DataFrame) -> pd.DataFrame:
    """Descarga tas (°C) y pr (mm) anuales por país desde la API CCKP.

    paises: DataFrame con columnas Area, iso3. Usa caché local si existe.
    """
    if RUTA_CACHE_CLIMA.exists():
        cache = pd.read_csv(RUTA_CACHE_CLIMA)
        faltantes = set(paises["iso3"]) - set(cache["iso3"])
        if not faltantes:
            print(f"  Clima: usando caché ({cache['iso3'].nunique()} países)")
            return cache
    else:
        cache = pd.DataFrame(columns=["iso3", "Year", "avg_temp", "average_rain_fall_mm_per_year"])
        faltantes = set(paises["iso3"])

    print(f"  Clima: descargando {len(faltantes)} países desde la API CCKP...")
    filas: list[dict] = []
    for n, iso3 in enumerate(sorted(faltantes), 1):
        for intento in range(3):
            try:
                r = requests.get(URL_CCKP.format(iso3=iso3), timeout=60)
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                datos = r.json()["data"]
                tas = datos.get("tas", {}).get(iso3, {})
                pr = datos.get("pr", {}).get(iso3, {})
                for clave, temp in tas.items():
                    anio = int(clave.split("-")[0])
                    if ANIO_INICIO <= anio <= ANIO_FIN and temp is not None:
                        lluvia = pr.get(clave)
                        if lluvia is None:
                            continue
                        filas.append(
                            {
                                "iso3": iso3,
                                "Year": anio,
                                "avg_temp": round(float(temp), 2),
                                "average_rain_fall_mm_per_year": round(float(lluvia), 1),
                            }
                        )
                break
            except Exception as error:  # noqa: BLE001 — API pública inestable
                if intento == 2:
                    print(f"    AVISO: sin clima para {iso3} ({error}); se omite")
                else:
                    time.sleep(1.5 * (intento + 1))
        if n % 25 == 0:
            print(f"    ... {n}/{len(faltantes)} países")
        time.sleep(0.15)

    clima = pd.concat([cache, pd.DataFrame(filas)], ignore_index=True)
    RUTA_CACHE_CLIMA.parent.mkdir(parents=True, exist_ok=True)
    clima.to_csv(RUTA_CACHE_CLIMA, index=False)
    return clima


def main() -> None:
    print("Extracción actualizada 1990-2023 (FAOSTAT bulk + API CCKP Banco Mundial)")

    rendimiento = cargar_rendimiento()
    pesticidas = cargar_pesticidas()

    paises = (
        rendimiento[["Area"]].drop_duplicates()
        .loc[lambda d: ~d["Area"].isin(EXCLUIR)]
        .assign(iso3=lambda d: d["Area"].map(resolver_iso3))
        .dropna(subset=["iso3"])
    )
    sin_iso = set(rendimiento["Area"].unique()) - set(paises["Area"]) - EXCLUIR
    if sin_iso:
        print(f"  Sin código ISO3 (se excluyen): {sorted(sin_iso)[:8]}{'...' if len(sin_iso) > 8 else ''}")

    clima = descargar_clima(paises)

    consolidado = (
        rendimiento.merge(paises, on="Area")
        .merge(clima, on=["iso3", "Year"])
        .merge(pesticidas, on=["Area", "Year"])
    )[
        ["Area", "Item", "Year", "hg/ha_yield",
         "average_rain_fall_mm_per_year", "pesticides_tonnes", "avg_temp"]
    ].sort_values(["Area", "Item", "Year"])

    consolidado.to_csv(RUTA_SALIDA, index=False)
    ecuador = consolidado[consolidado["Area"] == "Ecuador"]
    print(
        f"OK — {len(consolidado):,} filas | {consolidado['Area'].nunique()} países | "
        f"{consolidado['Year'].min()}-{consolidado['Year'].max()} | "
        f"Ecuador: {len(ecuador)} filas hasta {ecuador['Year'].max()}"
    )
    print(f"Guardado en {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
