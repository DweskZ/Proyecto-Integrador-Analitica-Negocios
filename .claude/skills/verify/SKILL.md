---
name: verify
description: How to verify dashboard changes in this repo by driving the Streamlit app end-to-end.
---

# Verificar cambios del dashboard

Surface: app Streamlit (`dashboard/app.py`). Dos maneras complementarias:

## 1. AppTest (ejecuta el script real con datos reales)

```python
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("dashboard/app.py", default_timeout=180)
at.run()
assert not at.exception
```

- Correr con `uv run python <script>` desde la raíz del repo.
- La primera ejecución tarda ~15 s (carga fact_rendimiento de 34k filas + modelo joblib).
- Widgets: `at.selectbox`, `at.multiselect`, `at.text_input`, `at.dataframe`,
  `at.markdown` (HTML de tarjetas/hero incluido), `at.caption`, `at.info`, `at.warning`.
- Las opciones de selectbox aparecen ya formateadas por `format_func`, pero
  `.select()` recibe el valor crudo (p. ej. `"fact_rendimiento"`).

## 2. Servidor headless (superficie HTTP real)

```bash
uv run streamlit run dashboard/app.py --server.headless true --server.port 8599
curl http://localhost:8599/_stcore/health   # -> ok, HTTP 200
```

Matar al final: `taskkill //IM streamlit.exe //F` (el kill por
`Get-NetTCPConnection` falla por la ExecutionPolicy del perfil de PowerShell).

## Gotchas

- Streamlit ejecuta `app.py` como script: el bootstrap de `sys.path` al inicio
  de `app.py` es lo que permite `from dashboard.x import y`. No quitarlo.
- Flujos que vale la pena manejar: pestaña Datos (selector de 7 tablas, búsqueda
  con/sin resultados, tabla de 34k filas limitada a 1 000), multiselect de
  cultivos vacío (debe mostrar warning y detenerse), métricas del hero y de la
  pestaña Predictiva (deben coincidir con `reports/modelo_resultados.json`).
