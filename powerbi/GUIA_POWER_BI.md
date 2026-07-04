# Guía de construcción del Dashboard en Power BI

**AgroComercial del Litoral S.A. — Fase 3.3 del Proyecto Integrador**

Esta guía permite construir el archivo `.pbix` en menos de una hora. Se necesita
Power BI Desktop (Windows) o Power BI Service (app.powerbi.com, navegador).

---

## 1. Importar el modelo de datos (esquema estrella)

`Inicio → Obtener datos → Texto/CSV` e importar, desde `data/processed/`:

| Archivo | Rol en el modelo |
|---|---|
| `fact_rendimiento.csv` | Tabla de hechos — rendimiento agrícola |
| `fact_compras.csv` | Tabla de hechos — compras y reventa |
| `dim_cultivo.csv` | Dimensión cultivo |
| `dim_geografia.csv` | Dimensión geografía |
| `dim_tiempo.csv` | Dimensión tiempo |
| `dim_proveedor.csv` | Dimensión proveedor (anonimizada) |

Adicionales para la página prescriptiva:

| Archivo | Rol |
|---|---|
| `reports/recomendaciones_compra.csv` | Salida del modelo predictivo + regla de decisión |
| `data/processed/api_worldbank.csv` | Indicadores de la API pública del Banco Mundial |

## 2. Relaciones (vista de modelo)

Power BI detecta la mayoría automáticamente; verificar que queden así
(todas **1 → * (uno a varios)**, filtro en una sola dirección):

```
dim_cultivo[id_cultivo]     1 → *  fact_rendimiento[id_cultivo]
dim_geografia[id_geografia] 1 → *  fact_rendimiento[id_geografia]
dim_tiempo[id_tiempo]       1 → *  fact_rendimiento[id_tiempo]
dim_cultivo[id_cultivo]     1 → *  fact_compras[id_cultivo]
dim_tiempo[id_tiempo]       1 → *  fact_compras[id_tiempo]
dim_proveedor[id_proveedor] 1 → *  fact_compras[id_proveedor]
```

El resultado visual es la **estrella** exigida en la Fase 2.1: cada tabla de
hechos al centro, rodeada de sus dimensiones.

## 3. Medidas DAX (copiar y pegar)

Crear en `fact_rendimiento`:

```dax
Rendimiento Promedio (ton/ha) =
AVERAGE ( fact_rendimiento[rendimiento_ton_ha] )
```

```dax
Rendimiento Ecuador Últ. 5 Años =
VAR AnioMax = CALCULATE ( MAX ( dim_tiempo[anio] ), ALL ( dim_tiempo ) )
RETURN
CALCULATE (
    AVERAGE ( fact_rendimiento[rendimiento_ton_ha] ),
    dim_geografia[pais] = "Ecuador",
    dim_tiempo[anio] >= AnioMax - 4
)
```

```dax
Variabilidad Rendimiento (CV %) =
DIVIDE (
    STDEV.P ( fact_rendimiento[rendimiento_ton_ha] ),
    AVERAGE ( fact_rendimiento[rendimiento_ton_ha] )
) * 100
```

Crear en `fact_compras`:

```dax
Margen Bruto (USD) = SUM ( fact_compras[margen_bruto_usd] )
```

```dax
Margen Bruto % =
DIVIDE (
    SUM ( fact_compras[margen_bruto_usd] ),
    SUM ( fact_compras[costo_total_usd] )
) * 100
```

```dax
Merma Promedio % = AVERAGE ( fact_compras[merma_pct] )
```

```dax
Volumen Comprado (ton) = SUM ( fact_compras[volumen_comprado_ton] )
```

```dax
Concentración Top 3 Cultivos % =
VAR VolumenTotal = CALCULATE ( [Volumen Comprado (ton)], ALL ( dim_cultivo ) )
VAR Top3 =
    SUMX (
        TOPN ( 3, ALL ( dim_cultivo[cultivo_es] ), [Volumen Comprado (ton)], DESC ),
        [Volumen Comprado (ton)]
    )
RETURN DIVIDE ( Top3, VolumenTotal ) * 100
```

## 4. Estructura de páginas del dashboard

### Página 1 — "Resumen Ejecutivo" (descriptiva)
- Fila superior: 5 **tarjetas KPI** (las medidas de arriba). Principio Gestalt de
  *proximidad*: los KPIs agrupados arriba se leen como una unidad.
- Centro: **gráfico de líneas** — Rendimiento Promedio por `dim_tiempo[anio]`,
  leyenda `dim_cultivo[cultivo_es]`, filtrado a Ecuador.
- Derecha: **barras horizontales** — Rendimiento promedio por cultivo
  (posición/longitud es el canal visual más preciso; evitar pastel).
- Segmentadores (slicers): cultivo y rango de años.

### Página 2 — "Diagnóstico" (¿por qué?)
- **Dispersión**: eje X = temperatura media, eje Y = rendimiento, leyenda cultivo.
- **Dispersión**: eje X = pesticidas, eje Y = rendimiento (escala log si se desea).
- Cuadro de texto con la conclusión: la correlación clima-rendimiento es débil a
  nivel global; el factor dominante es el tipo de cultivo y el país
  (**correlación ≠ causalidad**).

### Página 3 — "Predicción y Plan de Compras" (predictiva + prescriptiva)
- Tabla desde `recomendaciones_compra.csv` con **formato condicional** en la
  columna `decision`: verde = AUMENTAR, ámbar = MANTENER, rojo = REDUCIR.
- Barras horizontales del `indice_oferta` con línea de referencia constante en 1.0.
- Tarjetas: R² = 0.96 y RMSE = 1.64 ton/ha del modelo (credibilidad del dato).

## 5. Justificación de diseño (para el informe y la defensa)

- **Percepción visual (Gestalt)**: jerarquía Z — el ojo entra arriba-izquierda,
  por eso los KPIs van primero; proximidad para agrupar; similitud de color para
  vincular el mismo cultivo entre gráficos.
- **Canales visuales**: comparaciones con posición y longitud (líneas, barras);
  nunca ángulos ni áreas (se evitó el gráfico de pastel).
- **Psicología del color**: verde `#2E7D32` = agro, crecimiento, decisión
  positiva; rojo `#C62828` **reservado solo para alertas** (reducir compra), de
  modo que cuando aparece, comunica riesgo sin leer texto; ámbar `#F9A825` =
  neutralidad/espera; neutros tierra `#8D6E63` para contexto. Máximo 4 colores
  semánticos por página.
- **Tipografía**: una sola familia sans-serif (Segoe UI, la nativa de Power BI);
  jerarquía por tamaño y peso, no por cambiar de fuente. Números grandes en
  tarjetas KPI para lectura a distancia (defensa en aula).

## 6. Tema de colores (opcional)

`Ver → Temas → Buscar temas → Personalizar`: importar `powerbi/tema_agro.json`
para aplicar la paleta corporativa de una vez.
