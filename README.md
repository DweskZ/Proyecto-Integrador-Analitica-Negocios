# Sistema de predicción del rendimiento económico de reventa de cosechas

**Proyecto Integrador — Analítica de Negocios 7A · AgroComercial del Litoral S.A. (empresa simulada)**

Solución analítica completa: ingeniería de datos (ETL + esquema estrella),
analítica descriptiva/diagnóstica, modelo predictivo de rendimiento agrícola
(ton/ha) y regla prescriptiva de compras, con dashboard estratégico.

## Arquitectura

```
FUENTES                     ETL (Python)              MODELO DIMENSIONAL         CONSUMO
─────────                   ────────────              ──────────────────         ───────
FAOSTAT bulk (hasta 2023/24)─┐                        Esquema estrella:          Power BI (guía en powerbi/)
API CCKP Banco Mundial      ─┼→ limpieza, tipado,  →  fact_rendimiento           Dashboard Streamlit
(clima en vivo, hasta 2023)  │  validación, calidad   fact_compras               Modelo ML (joblib)
Excel compras (sin PII)     ─┘                        dim_cultivo/geo/tiempo/    Informe técnico (PDF)
                                                      proveedor
```

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `src/etl/` | Pipeline ETL: extracción de la API, fuente interna, esquema estrella |
| `src/analytics/eda.py` | EDA: estadísticas, distribuciones, correlaciones, KPIs |
| `src/models/` | Entrenamiento (3 algoritmos), XAI, sesgos y regla prescriptiva |
| `src/informe/` | Generador del informe técnico (DOCX → PDF) |
| `dashboard/` | Dashboard interactivo (Streamlit + Plotly): `app.py` + paquetes `theme/`, `data/`, `components/`, `tabs/` |
| `powerbi/` | Guía paso a paso de Power BI, medidas DAX y tema de color |
| `data/processed/` | Esquema estrella en CSV (listo para importar a Power BI) |
| `reports/` | Figuras, resultados del EDA/modelo y recomendaciones de compra |
| `informe/` | Informe técnico (PDF/DOCX) y guion del pitch |
| `models/` | Modelo entrenado (`modelo_rendimiento.joblib`) |

## Reproducir todo el pipeline

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Requiere los bulks de FAOSTAT en data/raw/ (se descargan una sola vez):
#   curl -L "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip" -o qcl.zip && unzip qcl.zip -d data/raw/
#   curl -L "https://bulks-faostat.fao.org/production/Inputs_Pesticides_Use_E_All_Data_(Normalized).zip" -o rp.zip && unzip rp.zip -d data/raw/

python src/etl/extraer_datos_actualizados.py # 1. FAOSTAT + clima CCKP (1990-2023)
python src/etl/extract_api.py                # 2. Indicadores Banco Mundial
python src/etl/generar_compras_internas.py   # 3. Fuente interna (sin PII)
python src/etl/transform_load.py             # 4. Esquema estrella + calidad
python src/analytics/eda.py                  # 5. EDA + KPIs + figuras
python src/models/entrenar_modelo.py         # 6. Modelos + métricas + XAI
python src/models/prescriptivo.py            # 7. Recomendaciones de compra
python src/informe/generar_informe.py        # 8. Informe técnico
```

## Dashboard

```bash
streamlit run dashboard/app.py
```

Seis pestañas: los 4 pilares analíticos —Descriptiva, Diagnóstica, Predictiva
(simulador en vivo con el modelo + optimizador de insumos pesticidas × lluvia)
y Prescriptiva (plan de compras)— más **Rentabilidad** (comparación mensual
del margen de compra por cultivo con heatmap de estacionalidad) y **Datos**
(diagrama del esquema estrella, explorador de las tablas crudas con búsqueda
y descarga CSV, y reporte de calidad del ETL).
Para el archivo Power BI, seguir `powerbi/GUIA_POWER_BI.md`.

## Resultados clave

- **Modelo ganador:** Random Forest — R² = 0.96, RMSE = 1.64 ton/ha (prueba),
  validación cruzada 5-fold R² = 0.938 ± 0.004. En Ecuador: RMSE 0.73 ton/ha.
- **KPIs:** rendimiento Ecuador 4.61 ton/ha (últ. 5 años), variabilidad
  interanual 31.2 %, margen bruto 21.4 %, merma 5.5 %, concentración top 3 62.9 %.
- **Prescriptivo (ciclo 2024):** aumentar compra en maíz, trigo, yuca, papa y
  arroz; mantener sorgo y plátano; reducir camote y soya.

## Nota sobre los datos

Rendimiento, clima y pesticidas son **datos reales y actualizados**
(FAOSTAT bulk oficial + API pública CCKP del Banco Mundial, 1990-2023,
183 países). Los registros internos de compras son **simulados** para el
escenario académico y se declaran como tales; se generan sin ningún dato
personal (proveedores anonimizados por código desde el origen).
