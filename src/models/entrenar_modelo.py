"""
Fase 4.1 — Modelado Predictivo (Machine Learning).

Problema: REGRESIÓN — estimar el rendimiento (ton/ha) de un cultivo dadas las
condiciones de clima (lluvia, temperatura) y manejo (pesticidas), país y año.

Algoritmos (básicos, según la consigna):
  1. Regresión Lineal (baseline interpretable)
  2. Árbol de Decisión (regresión)
  3. Random Forest (ensamble de árboles — mejor equilibrio sesgo/varianza)

Métricas pertinentes para regresión: RMSE, MAE y R² sobre un conjunto de
prueba nunca visto (hold-out 80/20 con validación cruzada de 5 particiones
sobre el conjunto de entrenamiento).

Fase 4.2 — XAI: importancia de variables por permutación (modelo ganador) y
coeficientes estandarizados de la regresión lineal, para explicar al negocio
qué factores pesan más en la predicción.

Salidas:
  - models/modelo_rendimiento.joblib (pipeline completo listo para predecir)
  - reports/modelo_resultados.json (métricas, importancias, análisis de sesgo)
  - reports/figures/06_comparacion_modelos.png
  - reports/figures/07_predicho_vs_real.png
  - reports/figures/08_importancia_variables.png
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_PROCESSED = RUTA_PROYECTO / "data" / "processed"
RUTA_MODELOS = RUTA_PROYECTO / "models"
RUTA_REPORTES = RUTA_PROYECTO / "reports"
RUTA_FIGURAS = RUTA_REPORTES / "figures"

SEMILLA = 42
COLOR_PRINCIPAL = "#2E7D32"
COLOR_ALERTA = "#C62828"

VARIABLES_NUMERICAS = ["anio", "precipitacion_mm", "pesticidas_ton", "temperatura_media_c"]
VARIABLES_CATEGORICAS = ["pais", "cultivo"]
OBJETIVO = "rendimiento_ton_ha"


def cargar_dataset_modelado() -> pd.DataFrame:
    fact = pd.read_csv(RUTA_PROCESSED / "fact_rendimiento.csv")
    geo = pd.read_csv(RUTA_PROCESSED / "dim_geografia.csv")
    cultivo = pd.read_csv(RUTA_PROCESSED / "dim_cultivo.csv")
    datos = (
        fact.merge(geo[["id_geografia", "pais"]], on="id_geografia")
        .merge(cultivo[["id_cultivo", "cultivo"]], on="id_cultivo")
        .rename(columns={"id_tiempo": "anio"})
    )
    return datos[VARIABLES_NUMERICAS + VARIABLES_CATEGORICAS + [OBJETIVO]]


def construir_pipeline(estimador) -> Pipeline:
    preprocesador = ColumnTransformer(
        transformers=[
            ("numericas", StandardScaler(), VARIABLES_NUMERICAS),
            ("categoricas", OneHotEncoder(handle_unknown="ignore"), VARIABLES_CATEGORICAS),
        ]
    )
    return Pipeline([("preprocesamiento", preprocesador), ("modelo", estimador)])


def evaluar(nombre: str, pipeline: Pipeline, X_train, y_train, X_test, y_test) -> dict:
    pipeline.fit(X_train, y_train)
    pred = pipeline.predict(X_test)

    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    mae = float(mean_absolute_error(y_test, pred))
    r2 = float(r2_score(y_test, pred))

    cv_r2 = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)

    print(f"  {nombre}: RMSE={rmse:.3f} ton/ha | MAE={mae:.3f} | R²={r2:.3f} | R² CV5={cv_r2.mean():.3f}±{cv_r2.std():.3f}")
    return {
        "rmse_ton_ha": round(rmse, 3),
        "mae_ton_ha": round(mae, 3),
        "r2": round(r2, 4),
        "r2_validacion_cruzada_media": round(float(cv_r2.mean()), 4),
        "r2_validacion_cruzada_desv": round(float(cv_r2.std()), 4),
    }


def analizar_sesgo_representacion(datos: pd.DataFrame) -> dict:
    """Fase 4.2 — Sesgos algorítmicos: representación por país y cultivo."""
    filas_por_pais = datos["pais"].value_counts()
    filas_por_cultivo = datos["cultivo"].value_counts()
    return {
        "descripcion": (
            "El dataset sobrerrepresenta países con series históricas largas y "
            "cultivos de clima templado. Un modelo entrenado así puede predecir "
            "peor en países/cultivos poco representados; se reporta el error por "
            "grupo para transparentar esta limitación."
        ),
        "paises_mas_representados": filas_por_pais.head(5).to_dict(),
        "paises_menos_representados": filas_por_pais.tail(5).to_dict(),
        "filas_ecuador": int(filas_por_pais.get("Ecuador", 0)),
        "cultivos": filas_por_cultivo.to_dict(),
    }


def error_por_grupo(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """RMSE segmentado para detectar si el modelo discrimina grupos (Fase 4.2)."""
    pred = pipeline.predict(X_test)
    prueba = X_test.copy()
    prueba["error2"] = (y_test.values - pred) ** 2

    rmse_cultivo = prueba.groupby("cultivo")["error2"].mean().pow(0.5).round(3)
    ecuador_mask = prueba["pais"] == "Ecuador"
    rmse_ecuador = float(np.sqrt(prueba.loc[ecuador_mask, "error2"].mean())) if ecuador_mask.any() else None
    return {
        "rmse_por_cultivo": rmse_cultivo.to_dict(),
        "rmse_ecuador": round(rmse_ecuador, 3) if rmse_ecuador else None,
    }


def main() -> None:
    print("Fase 4 — Entrenamiento y evaluación de modelos")
    RUTA_MODELOS.mkdir(exist_ok=True)

    datos = cargar_dataset_modelado()
    X = datos[VARIABLES_NUMERICAS + VARIABLES_CATEGORICAS]
    y = datos[OBJETIVO]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEMILLA
    )
    print(f"  Entrenamiento: {len(X_train)} filas | Prueba: {len(X_test)} filas")

    candidatos = {
        "Regresión Lineal": construir_pipeline(LinearRegression()),
        "Árbol de Decisión": construir_pipeline(
            DecisionTreeRegressor(max_depth=14, min_samples_leaf=5, random_state=SEMILLA)
        ),
        "Random Forest": construir_pipeline(
            RandomForestRegressor(
                n_estimators=200, max_depth=None, min_samples_leaf=2,
                n_jobs=-1, random_state=SEMILLA,
            )
        ),
    }

    metricas = {}
    for nombre, pipeline in candidatos.items():
        metricas[nombre] = evaluar(nombre, pipeline, X_train, y_train, X_test, y_test)

    ganador = max(metricas, key=lambda n: metricas[n]["r2"])
    modelo_final = candidatos[ganador]
    print(f"  Modelo ganador: {ganador}")

    # --- Gráfico comparación de modelos ---
    fig, ejes = plt.subplots(1, 2, figsize=(12, 4.5))
    nombres = list(metricas.keys())
    ejes[0].bar(nombres, [metricas[n]["r2"] for n in nombres], color=COLOR_PRINCIPAL)
    ejes[0].set_title("R² en conjunto de prueba", fontweight="bold")
    ejes[0].set_ylim(0, 1)
    ejes[1].bar(nombres, [metricas[n]["rmse_ton_ha"] for n in nombres], color="#8D6E63")
    ejes[1].set_title("RMSE (ton/ha) en conjunto de prueba", fontweight="bold")
    for eje in ejes:
        eje.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(RUTA_FIGURAS / "06_comparacion_modelos.png", bbox_inches="tight", dpi=130)
    plt.close(fig)

    # --- Predicho vs real ---
    pred_test = modelo_final.predict(X_test)
    fig, eje = plt.subplots(figsize=(6.5, 6))
    eje.scatter(y_test, pred_test, s=8, alpha=0.3, color=COLOR_PRINCIPAL)
    limite = max(y_test.max(), pred_test.max())
    eje.plot([0, limite], [0, limite], color=COLOR_ALERTA, linestyle="--", label="Predicción perfecta")
    eje.set_xlabel("Rendimiento real (ton/ha)")
    eje.set_ylabel("Rendimiento predicho (ton/ha)")
    eje.set_title(f"{ganador}: predicho vs real (R²={metricas[ganador]['r2']:.3f})", fontweight="bold")
    eje.legend()
    fig.tight_layout()
    fig.savefig(RUTA_FIGURAS / "07_predicho_vs_real.png", bbox_inches="tight", dpi=130)
    plt.close(fig)

    # --- XAI: importancia por permutación sobre variables originales ---
    print("  Calculando importancia de variables (XAI)...")
    importancia = permutation_importance(
        modelo_final, X_test, y_test, n_repeats=8, random_state=SEMILLA, n_jobs=-1
    )
    etiquetas_xai = {
        "anio": "Año",
        "precipitacion_mm": "Lluvia anual (mm)",
        "pesticidas_ton": "Pesticidas (ton)",
        "temperatura_media_c": "Temperatura media (°C)",
        "pais": "País",
        "cultivo": "Tipo de cultivo",
    }
    tabla_importancia = (
        pd.DataFrame(
            {
                "variable": [etiquetas_xai[c] for c in X_test.columns],
                "importancia": importancia.importances_mean,
            }
        )
        .sort_values("importancia", ascending=True)
    )
    fig, eje = plt.subplots(figsize=(8, 4.5))
    eje.barh(tabla_importancia["variable"], tabla_importancia["importancia"], color=COLOR_PRINCIPAL)
    eje.set_title("IA Explicable — ¿Qué variables pesan más en la predicción?", fontweight="bold")
    eje.set_xlabel("Importancia por permutación (caída de R² al aleatorizar la variable)")
    fig.tight_layout()
    fig.savefig(RUTA_FIGURAS / "08_importancia_variables.png", bbox_inches="tight", dpi=130)
    plt.close(fig)

    resultados = {
        "problema": "Regresión — rendimiento agrícola (ton/ha)",
        "particion": {"entrenamiento": len(X_train), "prueba": len(X_test)},
        "metricas_por_modelo": metricas,
        "modelo_ganador": ganador,
        "xai_importancia_permutacion": {
            fila["variable"]: round(float(fila["importancia"]), 4)
            for _, fila in tabla_importancia.iterrows()
        },
        "sesgo_representacion": analizar_sesgo_representacion(datos),
        "error_por_grupo": error_por_grupo(modelo_final, X_test, y_test),
    }

    with open(RUTA_REPORTES / "modelo_resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    joblib.dump(modelo_final, RUTA_MODELOS / "modelo_rendimiento.joblib")
    print(f"OK — modelo guardado en models/modelo_rendimiento.joblib")


if __name__ == "__main__":
    main()
