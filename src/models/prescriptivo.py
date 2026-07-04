"""
Fase 4 (pilar prescriptivo) — Regla de decisión de compra basada en la predicción.

Según lo definido en la Fase 1.3, el pilar prescriptivo se implementa como una
regla de decisión sobre la predicción del modelo (no como un optimizador
matemático complejo):

  Para cada cultivo del portafolio de AgroComercial del Litoral en Ecuador:
    1. Se predice el rendimiento esperado (ton/ha) para el siguiente ciclo con
       el modelo entrenado, usando las condiciones climáticas y de manejo
       esperadas (promedio de los últimos 3 años como escenario base).
    2. Se compara el rendimiento predicho contra el promedio histórico:
         índice de oferta = rendimiento predicho / promedio histórico
    3. Regla de decisión:
         índice >= 1.05 -> AUMENTAR compra (+15 %): habrá oferta abundante,
                           precios de compra a la baja, oportunidad de margen.
         0.95 - 1.05    -> MANTENER volumen histórico (escenario neutro).
         índice < 0.95  -> REDUCIR compra (-15 %) y asegurar contratos
                           anticipados: riesgo de escasez y quiebre de stock.

Salida: reports/recomendaciones_compra.csv (consumido por el dashboard).
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_PROCESSED = RUTA_PROYECTO / "data" / "processed"
RUTA_MODELO = RUTA_PROYECTO / "models" / "modelo_rendimiento.joblib"
RUTA_SALIDA = RUTA_PROYECTO / "reports" / "recomendaciones_compra.csv"

UMBRAL_AUMENTAR = 1.05
UMBRAL_REDUCIR = 0.95
AJUSTE_VOLUMEN = 0.15


def cargar_historico_ecuador() -> pd.DataFrame:
    fact = pd.read_csv(RUTA_PROCESSED / "fact_rendimiento.csv")
    geo = pd.read_csv(RUTA_PROCESSED / "dim_geografia.csv")
    cultivo = pd.read_csv(RUTA_PROCESSED / "dim_cultivo.csv")
    datos = (
        fact.merge(geo[["id_geografia", "pais"]], on="id_geografia")
        .merge(cultivo[["id_cultivo", "cultivo", "cultivo_es"]], on="id_cultivo")
        .rename(columns={"id_tiempo": "anio"})
    )
    return datos[datos["pais"] == "Ecuador"]


def cargar_volumen_historico() -> pd.DataFrame:
    compras = pd.read_csv(RUTA_PROCESSED / "fact_compras.csv")
    cultivo = pd.read_csv(RUTA_PROCESSED / "dim_cultivo.csv")
    compras = compras.merge(cultivo[["id_cultivo", "cultivo_es"]], on="id_cultivo")
    ultimo_anio = compras["id_tiempo"].max()
    recientes = compras[compras["id_tiempo"] >= ultimo_anio - 2]
    return (
        recientes.groupby("cultivo_es", as_index=False)
        .agg(volumen_anual_promedio_ton=("volumen_comprado_ton", lambda s: s.sum() / 3))
    )


def main() -> None:
    print("Fase 4 — Recomendaciones prescriptivas de compra")
    modelo = joblib.load(RUTA_MODELO)
    historico = cargar_historico_ecuador()
    volumenes = cargar_volumen_historico()

    ultimo_anio = int(historico["anio"].max())
    anio_objetivo = ultimo_anio + 1

    recomendaciones = []
    for (cultivo, cultivo_es), grupo in historico.groupby(["cultivo", "cultivo_es"]):
        recientes = grupo[grupo["anio"] >= ultimo_anio - 2]

        escenario = pd.DataFrame(
            [
                {
                    "anio": anio_objetivo,
                    "precipitacion_mm": recientes["precipitacion_mm"].mean(),
                    "pesticidas_ton": recientes["pesticidas_ton"].mean(),
                    "temperatura_media_c": recientes["temperatura_media_c"].mean(),
                    "pais": "Ecuador",
                    "cultivo": cultivo,
                }
            ]
        )
        rendimiento_predicho = float(modelo.predict(escenario)[0])
        promedio_historico = float(grupo["rendimiento_ton_ha"].mean())
        indice_oferta = rendimiento_predicho / promedio_historico

        if indice_oferta >= UMBRAL_AUMENTAR:
            decision, ajuste = "AUMENTAR compra", AJUSTE_VOLUMEN
            justificacion = "Oferta esperada abundante: comprar más a mejor precio"
        elif indice_oferta < UMBRAL_REDUCIR:
            decision, ajuste = "REDUCIR compra", -AJUSTE_VOLUMEN
            justificacion = "Riesgo de escasez: asegurar contratos y no sobrepagar"
        else:
            decision, ajuste = "MANTENER volumen", 0.0
            justificacion = "Escenario neutro: mantener plan histórico"

        volumen_base = volumenes.loc[
            volumenes["cultivo_es"] == cultivo_es, "volumen_anual_promedio_ton"
        ]
        volumen_base = float(volumen_base.iloc[0]) if len(volumen_base) else None

        recomendaciones.append(
            {
                "cultivo": cultivo_es,
                "anio_objetivo": anio_objetivo,
                "rendimiento_predicho_ton_ha": round(rendimiento_predicho, 2),
                "rendimiento_promedio_historico_ton_ha": round(promedio_historico, 2),
                "indice_oferta": round(indice_oferta, 3),
                "decision": decision,
                "volumen_historico_ton": round(volumen_base, 1) if volumen_base else None,
                "volumen_recomendado_ton": round(volumen_base * (1 + ajuste), 1) if volumen_base else None,
                "justificacion": justificacion,
            }
        )

    tabla = pd.DataFrame(recomendaciones).sort_values("indice_oferta", ascending=False)
    tabla.to_csv(RUTA_SALIDA, index=False)
    print(tabla[["cultivo", "rendimiento_predicho_ton_ha", "indice_oferta", "decision"]].to_string(index=False))
    print(f"OK — recomendaciones guardadas en {RUTA_SALIDA.name}")


if __name__ == "__main__":
    main()
