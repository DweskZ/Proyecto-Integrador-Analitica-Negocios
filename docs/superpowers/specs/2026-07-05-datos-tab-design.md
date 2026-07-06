# Design — Raw-data explorer tab ("Datos") + dashboard improvements

**Date:** 2026-07-05 · **Status:** approved by Bryan

## Goal

Let dashboard users see the underlying star-schema data (dimensions, facts, external
source) directly in the Streamlit app, and remove hardcoded model metrics.

## Scope

### 1. New 5th tab: "🗄️ Datos"

Three sections, top to bottom:

1. **Star-schema diagram** — Plotly figure (no new deps). Nodes = tables with name,
   row count and kind (hecho/dimensión); edges = foreign keys. Layout:
   `fact_rendimiento` and `fact_compras` in the middle; `dim_geografia`,
   `dim_cultivo`, `dim_tiempo`, `dim_proveedor` around them. Facts share
   `dim_cultivo` and `dim_tiempo`; `dim_geografia` only joins `fact_rendimiento`;
   `dim_proveedor` only joins `fact_compras`.
2. **Table browser** — selectbox over the 7 CSVs in `data/processed/`
   (4 dims, 2 facts, `api_worldbank.csv` as external source). Shows row/column
   counts, per-column dtypes, a free-text search box (substring match across all
   columns), a preview capped at 1 000 rows (full row count stated), and a
   download button with the complete CSV.
3. **Data-quality report** — `data/processed/reporte_calidad.json` rendered as
   readable cards (one per pipeline step: duplicates, nulls, physical ranges,
   PII compliance, referential integrity) instead of raw JSON.

### 2. Improvements

- **Dynamic model metrics** — hero badge ("R² 0.96") and Predictiva tab
  ("RMSE 1.64", "± 0.73") are hardcoded today. Read winner name, R², RMSE and
  `rmse_ecuador` from `reports/modelo_resultados.json`.
- **Modularize `dashboard/app.py`** (709 lines, would exceed 800 with the new
  tab). New package layout, one focused definition per file, `__init__.py`
  re-exports per code-style rules:

```
dashboard/
  app.py                    # thin orchestrator (sys.path bootstrap, filters, KPI row, tabs)
  theme/      colores.py · plotly_template.py · css.py
  data/       rutas.py · cargar_datos.py · cargar_modelo.py ·
              cargar_resultados_modelo.py · cargar_tablas_estrella.py ·
              cargar_reporte_calidad.py
  components/ silenciar_asyncio.py · hero.py · tarjeta_kpi.py · pie_pagina.py
  tabs/       descriptiva.py · diagnostica.py · predictiva.py ·
              prescriptiva.py · datos.py
```

`streamlit run dashboard/app.py` stays the entry point; `app.py` inserts the
project root into `sys.path` so `from dashboard.x import y` works everywhere.

## Non-goals

- No Streamlit multipage (`pages/`) — keeps single-view tab navigation.
- No changes to ETL, model or Power BI assets.
- No pagination widget for big tables — capped preview + full download is enough.

## Error handling

- Missing CSV/JSON files: loaders raise naturally at startup (same behavior as
  today); the app is only meaningful with the processed data present.
- Empty search results: show an informative empty state, not an error.

## Testing / verification

Run the app headless, exercise every tab (including the new one) and confirm no
exceptions in the server log; verify metrics shown match
`modelo_resultados.json`.

## Delivery

Branch `feat/datos-tab` → push to `origin`
(DweskZ/Proyecto-Integrador-Analitica-Negocios, Bryan is collaborator) → PR.
