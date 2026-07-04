"""
Fase 3.1 y 3.2 — Análisis Exploratorio de Datos (EDA) y KPIs.

Produce:
  - reports/figures/*.png : gráficos del EDA (distribuciones, series, correlación)
  - reports/eda_resultados.json : medidas de tendencia central, dispersión,
    matriz de correlación y valores de los 5 KPIs, para citarlos en el informe
    y en el dashboard.

Contenido metodológico:
  - Medidas de tendencia central (media, mediana) y de dispersión (desviación
    estándar, rango intercuartílico, coeficiente de variación) de las variables
    clave: rendimiento (ton/ha), precipitación, temperatura y pesticidas.
  - Identificación de distribuciones (histogramas + asimetría/curtosis).
  - Correlación (Pearson y Spearman) con discusión de correlación vs causalidad.
  - KPIs de negocio calculados sobre el esquema estrella.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_PROCESSED = RUTA_PROYECTO / "data" / "processed"
RUTA_FIGURAS = RUTA_PROYECTO / "reports" / "figures"
RUTA_RESULTADOS = RUTA_PROYECTO / "reports" / "eda_resultados.json"

# Paleta corporativa del proyecto (verde agro + neutros, ver Fase 3.3)
COLOR_PRINCIPAL = "#2E7D32"
COLOR_SECUNDARIO = "#8D6E63"
COLOR_ALERTA = "#C62828"
PALETA = ["#2E7D32", "#558B2F", "#8D6E63", "#F9A825", "#C62828", "#1565C0"]

sns.set_theme(style="whitegrid", palette=PALETA, font="Helvetica")
plt.rcParams["figure.dpi"] = 130


def cargar_datos() -> dict[str, pd.DataFrame]:
    tablas = {}
    for nombre in [
        "fact_rendimiento",
        "fact_compras",
        "dim_geografia",
        "dim_cultivo",
        "dim_tiempo",
    ]:
        tablas[nombre] = pd.read_csv(RUTA_PROCESSED / f"{nombre}.csv")
    return tablas


def vista_analitica(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Desnormaliza el esquema estrella para análisis (equivale a un JOIN estrella)."""
    return (
        tablas["fact_rendimiento"]
        .merge(tablas["dim_geografia"], on="id_geografia")
        .merge(tablas["dim_cultivo"], on="id_cultivo")
        .merge(tablas["dim_tiempo"], on="id_tiempo")
    )


VARIABLES_CLAVE = {
    "rendimiento_ton_ha": "Rendimiento (ton/ha)",
    "precipitacion_mm": "Precipitación anual (mm)",
    "temperatura_media_c": "Temperatura media (°C)",
    "pesticidas_ton": "Pesticidas (ton)",
}


def estadisticas_descriptivas(datos: pd.DataFrame) -> dict:
    resultado = {}
    for columna, etiqueta in VARIABLES_CLAVE.items():
        serie = datos[columna]
        resultado[columna] = {
            "etiqueta": etiqueta,
            "media": round(float(serie.mean()), 3),
            "mediana": round(float(serie.median()), 3),
            "desv_estandar": round(float(serie.std()), 3),
            "rango_intercuartilico": round(float(serie.quantile(0.75) - serie.quantile(0.25)), 3),
            "coef_variacion_pct": round(float(serie.std() / serie.mean() * 100), 1),
            "minimo": round(float(serie.min()), 3),
            "maximo": round(float(serie.max()), 3),
            "asimetria": round(float(stats.skew(serie)), 3),
            "curtosis": round(float(stats.kurtosis(serie)), 3),
        }
    return resultado


def graficar_distribuciones(datos: pd.DataFrame) -> None:
    fig, ejes = plt.subplots(2, 2, figsize=(12, 8))
    for eje, (columna, etiqueta) in zip(ejes.flat, VARIABLES_CLAVE.items()):
        sns.histplot(datos[columna], bins=50, ax=eje, color=COLOR_PRINCIPAL, kde=True)
        eje.axvline(datos[columna].mean(), color=COLOR_ALERTA, linestyle="--", label="Media")
        eje.axvline(datos[columna].median(), color=COLOR_SECUNDARIO, linestyle=":", label="Mediana")
        eje.set_title(f"Distribución: {etiqueta}", fontsize=11, fontweight="bold")
        eje.set_xlabel(etiqueta)
        eje.legend(fontsize=8)
    fig.suptitle("Distribuciones de variables clave (todas las geografías)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(RUTA_FIGURAS / "01_distribuciones.png", bbox_inches="tight")
    plt.close(fig)


def graficar_rendimiento_ecuador(datos: pd.DataFrame) -> None:
    ecuador = datos[datos["pais"] == "Ecuador"]
    fig, ejes = plt.subplots(1, 2, figsize=(14, 5))

    orden = (
        ecuador.groupby("cultivo_es")["rendimiento_ton_ha"].median().sort_values(ascending=False).index
    )
    sns.boxplot(
        data=ecuador, x="cultivo_es", y="rendimiento_ton_ha", order=orden,
        ax=ejes[0], color=COLOR_PRINCIPAL,
    )
    rango = f"{ecuador['anio'].min()}-{ecuador['anio'].max()}"
    ejes[0].set_title(f"Rendimiento por cultivo en Ecuador ({rango})", fontweight="bold")
    ejes[0].set_xlabel("")
    ejes[0].set_ylabel("Rendimiento (ton/ha)")
    ejes[0].tick_params(axis="x", rotation=30)

    top4 = orden[:4]
    serie = (
        ecuador[ecuador["cultivo_es"].isin(top4)]
        .groupby(["anio", "cultivo_es"], as_index=False)["rendimiento_ton_ha"].mean()
    )
    sns.lineplot(data=serie, x="anio", y="rendimiento_ton_ha", hue="cultivo_es", ax=ejes[1], linewidth=2)
    ejes[1].set_title("Evolución del rendimiento — 4 cultivos líderes (Ecuador)", fontweight="bold")
    ejes[1].set_xlabel("Año")
    ejes[1].set_ylabel("Rendimiento (ton/ha)")
    ejes[1].legend(title="")

    fig.tight_layout()
    fig.savefig(RUTA_FIGURAS / "02_rendimiento_ecuador.png", bbox_inches="tight")
    plt.close(fig)


def graficar_correlaciones(datos: pd.DataFrame) -> dict:
    columnas = list(VARIABLES_CLAVE.keys())
    pearson = datos[columnas].corr(method="pearson")
    spearman = datos[columnas].corr(method="spearman")

    fig, ejes = plt.subplots(1, 2, figsize=(13, 5))
    etiquetas_cortas = ["Rendimiento", "Lluvia", "Temperatura", "Pesticidas"]
    for eje, (matriz, titulo) in zip(ejes, [(pearson, "Pearson (lineal)"), (spearman, "Spearman (monótona)")]):
        sns.heatmap(
            matriz, annot=True, fmt=".2f", cmap="RdYlGn", center=0, vmin=-1, vmax=1,
            xticklabels=etiquetas_cortas, yticklabels=etiquetas_cortas, ax=eje,
        )
        eje.set_title(f"Correlación de {titulo}", fontweight="bold")
    fig.suptitle("Correlación entre rendimiento y sus factores", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(RUTA_FIGURAS / "03_correlaciones.png", bbox_inches="tight")
    plt.close(fig)

    # Dispersión rendimiento vs factores para discusión correlación vs causalidad
    fig, ejes = plt.subplots(1, 3, figsize=(15, 4.5))
    muestra = datos.sample(min(4000, len(datos)), random_state=7)
    for eje, (columna, etiqueta) in zip(
        ejes, [("precipitacion_mm", "Lluvia (mm)"), ("temperatura_media_c", "Temperatura (°C)"), ("pesticidas_ton", "Pesticidas (ton)")]
    ):
        eje.scatter(muestra[columna], muestra["rendimiento_ton_ha"], s=6, alpha=0.25, color=COLOR_PRINCIPAL)
        eje.set_xlabel(etiqueta)
        eje.set_ylabel("Rendimiento (ton/ha)")
        r = float(datos[columna].corr(datos["rendimiento_ton_ha"]))
        eje.set_title(f"r de Pearson = {r:.2f}", fontweight="bold")
        if columna == "pesticidas_ton":
            eje.set_xscale("log")
    fig.suptitle("Rendimiento vs factores — correlación no implica causalidad", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(RUTA_FIGURAS / "04_dispersion_factores.png", bbox_inches="tight")
    plt.close(fig)

    return {
        "pearson": pearson.round(3).to_dict(),
        "spearman": spearman.round(3).to_dict(),
    }


def calcular_kpis(datos: pd.DataFrame, tablas: dict[str, pd.DataFrame]) -> dict:
    """Los 5 KPIs críticos del negocio (Fase 3.2)."""
    ecuador = datos[datos["pais"] == "Ecuador"]
    compras = (
        tablas["fact_compras"]
        .merge(tablas["dim_cultivo"], on="id_cultivo")
    )

    # KPI 1: Rendimiento promedio ponderado en Ecuador (últimos 5 años del dataset)
    ultimos = ecuador[ecuador["anio"] >= ecuador["anio"].max() - 4]
    kpi_rendimiento = float(ultimos["rendimiento_ton_ha"].mean())

    # KPI 2: Variabilidad interanual del rendimiento (CV%) — riesgo de oferta
    cv_por_cultivo = (
        ecuador.groupby("cultivo_es")["rendimiento_ton_ha"]
        .agg(lambda s: s.std() / s.mean() * 100)
    )
    kpi_variabilidad = float(cv_por_cultivo.mean())

    # KPI 3: Margen bruto de reventa promedio (%)
    kpi_margen = float(
        compras["margen_bruto_usd"].sum() / compras["costo_total_usd"].sum() * 100
    )

    # KPI 4: Merma promedio de compra (%) — proxy de sobrestock/deterioro
    kpi_merma = float(compras["merma_pct"].mean())

    # KPI 5: Concentración de compras (top 3 cultivos, % del volumen) — riesgo de portafolio
    volumen_por_cultivo = compras.groupby("cultivo_es")["volumen_comprado_ton"].sum()
    kpi_concentracion = float(
        volumen_por_cultivo.nlargest(3).sum() / volumen_por_cultivo.sum() * 100
    )

    kpis = {
        "KPI_1_rendimiento_promedio_ton_ha": {
            "nombre": "Rendimiento promedio Ecuador (ton/ha, últimos 5 años)",
            "valor": round(kpi_rendimiento, 2),
            "objetivo_analitico": "Descriptivo — nivel base de oferta esperada",
        },
        "KPI_2_variabilidad_rendimiento_pct": {
            "nombre": "Coeficiente de variación interanual del rendimiento (%)",
            "valor": round(kpi_variabilidad, 1),
            "objetivo_analitico": "Diagnóstico — cuantifica el riesgo de oferta",
        },
        "KPI_3_margen_bruto_pct": {
            "nombre": "Margen bruto de reventa (%)",
            "valor": round(kpi_margen, 1),
            "objetivo_analitico": "Descriptivo — salud económica del negocio",
        },
        "KPI_4_merma_promedio_pct": {
            "nombre": "Merma promedio por orden de compra (%)",
            "valor": round(kpi_merma, 1),
            "objetivo_analitico": "Diagnóstico — pérdidas por deterioro/sobrestock",
        },
        "KPI_5_concentracion_top3_pct": {
            "nombre": "Concentración del volumen en top 3 cultivos (%)",
            "valor": round(kpi_concentracion, 1),
            "objetivo_analitico": "Prescriptivo — riesgo de portafolio de compras",
        },
    }
    return kpis


def graficar_negocio(tablas: dict[str, pd.DataFrame]) -> None:
    compras = tablas["fact_compras"].merge(tablas["dim_cultivo"], on="id_cultivo")

    fig, ejes = plt.subplots(1, 2, figsize=(14, 5))

    margen_anual = compras.groupby("id_tiempo", as_index=False).agg(
        margen=("margen_bruto_usd", "sum"), costo=("costo_total_usd", "sum")
    )
    margen_anual["margen_pct"] = margen_anual["margen"] / margen_anual["costo"] * 100
    ejes[0].bar(margen_anual["id_tiempo"], margen_anual["margen"] / 1e6, color=COLOR_PRINCIPAL)
    ejes[0].set_title("Margen bruto anual de reventa (millones USD)", fontweight="bold")
    ejes[0].set_xlabel("Año")
    ejes[0].set_ylabel("Margen bruto (MUSD)")

    volumen = (
        compras.groupby("cultivo_es")["volumen_comprado_ton"].sum().sort_values(ascending=True)
    )
    ejes[1].barh(volumen.index, volumen.values / 1e3, color=COLOR_SECUNDARIO)
    ejes[1].set_title("Volumen histórico comprado por cultivo (miles ton)", fontweight="bold")
    ejes[1].set_xlabel("Volumen (miles de toneladas)")

    fig.tight_layout()
    fig.savefig(RUTA_FIGURAS / "05_negocio_compras.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    print("Fase 3 — EDA y KPIs")
    RUTA_FIGURAS.mkdir(parents=True, exist_ok=True)

    tablas = cargar_datos()
    datos = vista_analitica(tablas)

    resultados = {
        "estadisticas_descriptivas": estadisticas_descriptivas(datos),
        "estadisticas_ecuador": estadisticas_descriptivas(datos[datos["pais"] == "Ecuador"]),
    }
    graficar_distribuciones(datos)
    graficar_rendimiento_ecuador(datos)
    resultados["correlaciones"] = graficar_correlaciones(datos)
    resultados["kpis"] = calcular_kpis(datos, tablas)
    graficar_negocio(tablas)

    with open(RUTA_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"OK — figuras en {RUTA_FIGURAS} y resultados en {RUTA_RESULTADOS.name}")
    for clave, kpi in resultados["kpis"].items():
        print(f"  {kpi['nombre']}: {kpi['valor']}")


if __name__ == "__main__":
    main()
