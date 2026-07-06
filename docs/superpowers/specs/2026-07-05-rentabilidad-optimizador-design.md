# Design — "Rentabilidad" tab + input-combination optimizer

**Date:** 2026-07-05 · **Status:** approved by Bryan

## Goal

Answer two business questions inside the dashboard:
1. "How profitable is buying crop X this month?" — historical monthly
   profitability comparison across crops.
2. "What input combination should we aim for?" — model-driven sweep of the
   controllable lever (pesticides) under an assumed climate.

## 1. New tab "💰 Rentabilidad" (between Prescriptiva and Datos)

Data source: `fact_compras` (has `mes`), already filtered by the global
crop/year sidebar filters. Purchases are simulated for the academic scenario —
a visible methodological note says so.

- **Month selector** defaulting to the current calendar month.
- **Summary cards** (existing KPI card component): best crop of the month by
  margin %, month margin % vs annual average, average merma of the month.
- **Month ranking**: horizontal bars, gross margin % by crop for that month
  (aggregated over the filtered years); volume (ton) and USD/ton margin in
  hover.
- **Seasonality heatmap**: crop × month, average gross margin % as color —
  shows at a glance which month suits each crop.
- Empty state when the filters leave no purchases for the selected month.

Margin % is computed as `sum(margen_bruto_usd) / sum(costo_total_usd) * 100`
per group (not the mean of ratios).

## 2. Input optimizer inside Predictiva (below the sensitivity curve)

- **2D heatmap** pesticides (0–20 000 ton, step 1 000) × rainfall
  (200–4 000 mm, step 200) of predicted yield for the selected crop, with
  temperature fixed at the slider value. ⭐ marks the global predicted
  maximum; ✕ marks the current slider scenario.
- **Recommendation callout**: with rainfall/temperature fixed at the slider
  values, the pesticide level that maximizes predicted yield, the expected
  yield, and the delta vs the current scenario. Wording says "según el
  modelo" — the Diagnóstica tab already warns correlation ≠ causation, and
  pesticides is the only controllable input (climate is an assumption).
- Grid (~420 predictions) computed in one `predict` call and cached with
  `st.cache_data` keyed by (crop, temperature, year).

## Non-goals

- No monetary translation of predicted yield (prices live in the simulated
  purchases; mixing them with real FAO yields would overstate precision).
- No optimization of rainfall/temperature — not controllable.

## Verification

Drive with Streamlit AppTest (per `.claude/skills/verify/SKILL.md`): new tab
renders without exceptions, month selector works, optimizer callout present;
probe a month with no purchases under narrow filters.
