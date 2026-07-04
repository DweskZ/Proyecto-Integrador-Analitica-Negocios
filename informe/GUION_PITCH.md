# Guion del Pitch — Defensa Práctica (10-15 minutos)

**Sistema de predicción del rendimiento económico de reventa de cosechas**
AgroComercial del Litoral S.A. · Analítica de Negocios 7A

> Orientación: el pitch se dirige al "comité ejecutivo", no a un tribunal técnico.
> Cada sección dice QUÉ decir, QUÉ mostrar y cuánto tiempo asignar.
> Reparto sugerido para 3 integrantes indicado en cada bloque.

---

## 0. Apertura — el gancho (1 min) · Integrante 1

**Decir:** "Imaginen que compran 500 toneladas de arroz apostando a que la
cosecha será como la del año pasado… y la cosecha viene 20 % más baja. Pagaron
caro, y aun así no tienen producto para sus clientes. O al revés: la cosecha
viene abundante, los precios se desploman y ustedes ya compraron caro. Ese es
el día a día de AgroComercial del Litoral, y hoy les mostramos cómo dejamos de
apostar y empezamos a predecir."

**Mostrar:** portada del dashboard.

## 1. El problema en números (2 min) · Integrante 1

**Decir:** la empresa compra cosechas a productores y revende a industrias,
supermercados y exportación. Su margen vive de comprar el volumen correcto al
precio correcto. Pero decide con intuición y con "lo que pasó el año pasado".

**Datos clave (fila de KPIs del dashboard):**
- La variabilidad interanual del rendimiento en Ecuador es **31.2 %** — la
  oferta puede cambiar casi un tercio de un año a otro.
- Merma promedio por orden: **5.5 %** (dinero que se pudre en bodega).
- El 63 % del volumen está concentrado en solo 3 cultivos (riesgo de portafolio).

**Mensaje puente:** "El problema no es falta de datos —FAO y Banco Mundial
publican todo—, es que nadie los estaba usando para decidir."

## 2. La solución en 30 segundos (1 min) · Integrante 1

**Decir:** "Construimos un sistema que integra datos oficiales de FAO y del
Banco Mundial con nuestros registros internos de compras, predice cuánto va a
rendir cada cultivo el próximo ciclo, y convierte esa predicción en una
recomendación concreta: aumentar, mantener o reducir la compra de cada cultivo."

**Mostrar:** diagrama de arquitectura (fuentes → ETL → esquema estrella →
modelo → dashboard).

## 3. Los datos y su gobernanza (2 min) · Integrante 2

**Decir:**
- 3 fuentes: FAOSTAT oficial de la FAO (34 mil cosechas, 183 países,
  **1990-2023, datos vigentes**), la **API pública de clima del Banco Mundial
  (CCKP)** consultada en vivo, y el Excel interno de compras.
- Todo pasa por un pipeline ETL automatizado: homologación de países a ISO3,
  validación de rangos físicos, y un modelo en estrella listo para Power BI.
- Ética desde el diseño: **cero datos personales** — los proveedores son
  códigos anónimos; cumplimos LOPDP sin esfuerzo posterior porque la
  anonimización ocurre en el origen.

**Mostrar:** vista de modelo (estrella) en Power BI, 10 segundos.

## 4. Lo que aprendimos de los datos (2 min) · Integrante 2

**Decir:**
- Papa y plátano son nuestros cultivos de mayor rendimiento; trigo y soya los
  más bajos (mostrar ranking).
- Hallazgo diagnóstico clave: la lluvia y la temperatura por sí solas casi no
  correlacionan con el rendimiento a nivel global. **Correlación no es
  causalidad**: los países con más pesticidas rinden más, pero no por el
  pesticida en sí, sino porque el pesticida delata agricultura tecnificada.
  El rendimiento depende primero del cultivo y del país, y luego del clima
  del año.
- Por eso un promedio simple no sirve para decidir compras — se necesita un
  modelo que combine todos los factores a la vez.

**Mostrar:** pestaña Descriptiva y Diagnóstica del dashboard.

## 5. El modelo — demo en vivo (3 min) · Integrante 3

**Decir:**
- Probamos 3 algoritmos (regresión lineal, árbol de decisión, Random Forest).
- El ganador, Random Forest, acierta con un **R² de 0.96**: explica el 96 % de
  la variabilidad del rendimiento, con un error típico de **±0.81 ton/ha**.
- En Ecuador el error es aún menor: 0.73 ton/ha RMSE.

**DEMO (el momento fuerte):** en la pestaña Predictiva, mover el slider de
lluvia y temperatura en vivo: "si el próximo año llueve 30 % menos, el
rendimiento del arroz cae de X a Y — y eso lo sabemos HOY, antes de comprar."

**Confianza (XAI):** "el modelo no es una caja negra: primero pesa el tipo de
cultivo, luego el país, luego clima y manejo. Decide como un agrónomo con la
memoria de 34,000 cosechas."

## 6. La recomendación de compra (2 min) · Integrante 3

**Decir:** "Y aquí está el entregable que le importa al comité: el plan de
compras del próximo ciclo."

**Mostrar:** pestaña Prescriptiva.
- **Aumentar +15 %**: maíz, trigo, yuca, papa, arroz (oferta abundante → comprar
  más y negociar precio a la baja).
- **Mantener**: sorgo, plátano.
- **Reducir −15 % y asegurar contratos anticipados**: camote y soya (riesgo
  de escasez → no sobrepagar y garantizar abastecimiento).

**Honestidad que da credibilidad:** "en papa y plátano el modelo tiene más error
porque su rendimiento es más variable; esas recomendaciones van acompañadas de
una advertencia — el modelo apoya al comité, no lo reemplaza."

## 7. Cierre (1 min) · los 3

**Decir:** "Hoy AgroComercial decide con evidencia: sabe qué comprar, cuánto y
con qué confianza. Menos producto pudriéndose en bodega, menos clientes
perdidos por quiebre de stock, y un margen del 21 % defendido con datos.
La intuición del jefe de compras sigue valiendo — ahora tiene 34,000 cosechas
de respaldo. Gracias."

---

## Preguntas probables del docente (preparar respuestas)

1. **¿Por qué Random Forest y no la regresión lineal si es más simple?**
   Porque la relación clima-rendimiento no es lineal y depende de interacciones
   cultivo×país×clima. La lineal se queda en R² 0.68 vs 0.96. Mantuvimos la
   lineal como baseline interpretable.
2. **¿Cómo saben que no hay sobreajuste?**
   Validación cruzada de 5 particiones: R² 0.938 ± 0.004, cercano al del
   conjunto de prueba (0.96). Si hubiera sobreajuste fuerte, la CV se derrumbaría.
3. **¿Qué tan actuales son los datos?**
   Hasta 2023 (FAOSTAT publica con ~1-2 años de rezago, como todo dato oficial
   internacional). El pipeline descarga directo de la fuente oficial, así que
   reentrenar con cada actualización de la FAO es un solo comando.
4. **¿Qué pasa con El Niño / eventos extremos?**
   El modelo usa condiciones esperadas; ante pronóstico de El Niño se ingresa
   ese escenario en el simulador (demo del slider) y la recomendación se ajusta.
5. **¿Dónde está la ética/gobernanza?**
   Anonimización desde el origen (códigos de proveedor), verificación
   automática anti-PII en el pipeline, análisis cuantitativo de sesgo por grupo
   (error por cultivo/país) y supervisión humana en la decisión final.
6. **¿El margen del 21 % y las compras son reales?**
   Son del escenario simulado (declarado explícitamente); el rendimiento y el
   clima sí son datos reales de FAO/Banco Mundial.

## Checklist previo a la defensa

- [ ] Dashboard corriendo (`streamlit run dashboard/app.py`) o .pbix abierto
- [ ] Probar la demo del slider con un caso ensayado (arroz, lluvia −30 %)
- [ ] Informe PDF impreso o abierto en segunda pantalla
- [ ] Cronometrar: máximo 13 min para dejar margen de preguntas
- [ ] Cada integrante domina TODO el flujo (el docente puede preguntar cruzado)
