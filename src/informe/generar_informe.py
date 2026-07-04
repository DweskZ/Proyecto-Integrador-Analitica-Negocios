"""
Entregable 1 — Informe Técnico (PDF), estructurado bajo las 4 fases.

Genera informe/Informe_Tecnico.docx con python-docx (figuras incluidas) y lo
convierte a PDF con LibreOffice. Los números del informe se leen de los JSON
producidos por el pipeline, de modo que si se reejecuta el ETL/modelo, el
informe se regenera consistente.
"""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_REPORTES = RUTA_PROYECTO / "reports"
RUTA_FIGURAS = RUTA_REPORTES / "figures"
RUTA_PROCESSED = RUTA_PROYECTO / "data" / "processed"
RUTA_SALIDA = RUTA_PROYECTO / "informe" / "Informe_Tecnico.docx"

VERDE = RGBColor(0x2E, 0x7D, 0x32)
GRIS = RGBColor(0x42, 0x42, 0x42)

with open(RUTA_REPORTES / "eda_resultados.json", encoding="utf-8") as f:
    EDA = json.load(f)
with open(RUTA_REPORTES / "modelo_resultados.json", encoding="utf-8") as f:
    MODELO = json.load(f)
with open(RUTA_PROCESSED / "reporte_calidad.json", encoding="utf-8") as f:
    CALIDAD = json.load(f)

import pandas as pd

RECOMENDACIONES = pd.read_csv(RUTA_REPORTES / "recomendaciones_compra.csv")

FACT_REND = pd.read_csv(RUTA_PROCESSED / "fact_rendimiento.csv")
DIM_GEO = pd.read_csv(RUTA_PROCESSED / "dim_geografia.csv")
FACT_COMPRAS = pd.read_csv(RUTA_PROCESSED / "fact_compras.csv")

N_FILAS = len(FACT_REND)
N_PAISES = len(DIM_GEO)
N_COMPRAS = len(FACT_COMPRAS)
ANIO_MIN = int(FACT_REND["id_tiempo"].min())
ANIO_MAX = int(FACT_REND["id_tiempo"].max())

CONTEO_DECISIONES = RECOMENDACIONES["decision"].value_counts()
CULTIVOS_AUMENTAR = ", ".join(
    RECOMENDACIONES.loc[RECOMENDACIONES["decision"] == "AUMENTAR compra", "cultivo"].str.lower()
)

doc = Document()

estilo_normal = doc.styles["Normal"]
estilo_normal.font.name = "Calibri"
estilo_normal.font.size = Pt(11)


def titulo(texto: str, nivel: int = 1) -> None:
    h = doc.add_heading(texto, level=nivel)
    for run in h.runs:
        run.font.color.rgb = VERDE if nivel <= 2 else GRIS


def parrafo(texto: str, negrita: bool = False) -> None:
    p = doc.add_paragraph()
    run = p.add_run(texto)
    run.bold = negrita
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def vinetas(items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def figura(nombre_archivo: str, leyenda: str, ancho: float = 6.3) -> None:
    ruta = RUTA_FIGURAS / nombre_archivo
    doc.add_picture(str(ruta), width=Inches(ancho))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    run = p.add_run(leyenda)
    run.italic = True
    run.font.size = Pt(9)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def tabla(encabezados: list[str], filas: list[list[str]]) -> None:
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Light Grid Accent 6"
    for i, enc in enumerate(encabezados):
        celda = t.rows[0].cells[i]
        celda.text = enc
        for p in celda.paragraphs:
            for r in p.runs:
                r.bold = True
    for fila in filas:
        celdas = t.add_row().cells
        for i, valor in enumerate(fila):
            celdas[i].text = str(valor)
    doc.add_paragraph()


# ============================ PORTADA =======================================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("\n\nUNIVERSIDAD LAICA ELOY ALFARO DE MANABÍ\n")
r.bold = True
r.font.size = Pt(16)
r = p.add_run("\nPROYECTO INTEGRADOR — ANALÍTICA DE NEGOCIOS\nNivel 7A\n\n")
r.font.size = Pt(13)
r = p.add_run(
    "\nSistema de predicción del rendimiento económico\nde reventa de cosechas\n"
)
r.bold = True
r.font.size = Pt(18)
r.font.color.rgb = VERDE
r = p.add_run("\n\nAgroComercial del Litoral S.A. (empresa simulada)\n")
r.italic = True
r.font.size = Pt(12)
r = p.add_run("\n\nDocente: Ing. Carlos Manosalvas G.\n\nIntegrantes del grupo:\n_________________________\n_________________________\n_________________________\n")
r.font.size = Pt(12)
doc.add_page_break()

# ======================= RESUMEN EJECUTIVO ==================================
titulo("Resumen Ejecutivo", 1)
kpis = EDA["kpis"]
rf = MODELO["metricas_por_modelo"]["Random Forest"]
parrafo(
    "AgroComercial del Litoral S.A. compra cosechas a productores ecuatorianos y las revende a "
    "industrias, supermercados y mercados de exportación. Hoy sus decisiones de compra son reactivas "
    "e intuitivas, lo que la expone a sobrestock (pérdidas por deterioro) y quiebres de stock (ventas "
    "perdidas). Este proyecto construye una solución analítica completa —desde la ingeniería de datos "
    "hasta un modelo predictivo funcional y un dashboard estratégico— que anticipa el rendimiento de los "
    "cultivos (ton/ha) bajo condiciones climáticas y de manejo esperadas, y lo traduce en recomendaciones "
    "concretas de volumen de compra por cultivo."
)
parrafo(
    f"Resultados principales: se integraron tres fuentes (FAOSTAT de la FAO, la API pública de clima del "
    f"Banco Mundial y el Excel interno de compras anonimizado) en un modelo dimensional en estrella con "
    f"{N_FILAS:,} observaciones limpias de {N_PAISES} países entre {ANIO_MIN} y {ANIO_MAX}. El modelo "
    f"predictivo ganador (Random Forest) alcanza un R² de {rf['r2']:.3f} y un error RMSE de "
    f"{rf['rmse_ton_ha']} ton/ha en datos nunca vistos. Con base en la predicción, la regla prescriptiva "
    f"recomienda aumentar la compra en {CONTEO_DECISIONES.get('AUMENTAR compra', 0)} cultivos "
    f"({CULTIVOS_AUMENTAR}), mantener {CONTEO_DECISIONES.get('MANTENER volumen', 0)} y reducir "
    f"{CONTEO_DECISIONES.get('REDUCIR compra', 0)} para el ciclo {int(RECOMENDACIONES['anio_objetivo'].iloc[0])}, "
    f"reduciendo simultáneamente el riesgo de sobrestock y de quiebre."
)
doc.add_page_break()

# ============================== FASE 1 ======================================
titulo("Fase 1 — Definición del Negocio y Entendimiento del Problema", 1)

titulo("1.1 Contexto del Negocio", 2)
parrafo(
    "AgroComercial del Litoral S.A. (empresa simulada) es una comercializadora agrícola que opera como "
    "intermediaria entre productores y compradores mayoristas en Ecuador. Su actividad central consiste en "
    "adquirir cosechas a productores, almacenarlas y revenderlas a industrias procesadoras, supermercados y "
    "mercados de exportación. Su margen depende de comprar el volumen correcto, al precio correcto y en el "
    "momento correcto. Como toda comercializadora agrícola, está expuesta a un factor que no controla: el "
    "rendimiento de los cultivos depende del clima y de las prácticas de manejo (pesticidas, riego), lo que "
    "genera incertidumbre en la oferta disponible cada temporada."
)

titulo("1.2 Planteamiento del Problema (Cultura Data-Driven)", 2)
parrafo(
    "Actualmente las decisiones de compra se toman de forma reactiva e intuitiva: se basan en la experiencia "
    "del jefe de compras y en lo ocurrido la temporada anterior, sin un modelo que anticipe cuánto rendirán "
    "los cultivos bajo las condiciones climáticas esperadas. El dolor del negocio es la incapacidad de "
    "anticipar el rendimiento por país/región y temporada, lo que provoca dos problemas costosos:"
)
vinetas(
    [
        "Sobrestock: comprar más volumen del que el mercado absorbe, generando pérdidas por almacenamiento y "
        "producto deteriorado. En el histórico interno la merma promedio por orden es de "
        f"{kpis['KPI_4_merma_promedio_pct']['valor']} % (supuesto del escenario simulado).",
        "Quiebres de stock: quedarse corto cuando hay demanda, perdiendo ventas y clientes.",
    ]
)
parrafo(
    "La transición hacia una cultura data-driven implica reemplazar la intuición por evidencia: usar datos "
    "históricos de rendimiento, clima y uso de pesticidas para predecir el rendimiento esperado y planificar "
    "las compras con base en esa predicción. La magnitud del riesgo es medible: la variabilidad interanual del "
    f"rendimiento en Ecuador promedia un coeficiente de variación de {kpis['KPI_2_variabilidad_rendimiento_pct']['valor']} %, "
    "derivada de los datos reales (no es un supuesto)."
)

titulo("1.3 Objetivos de Analítica (los 4 pilares)", 2)
tabla(
    ["Pilar", "Pregunta", "En este proyecto"],
    [
        [
            "Descriptiva",
            "¿Qué ha pasado?",
            "Caracterizar el rendimiento histórico por cultivo, país y año; identificar qué cultivos y zonas "
            "rinden más y cómo han variado el clima y los pesticidas.",
        ],
        [
            "Diagnóstica",
            "¿Por qué pasó?",
            "Analizar la relación entre rendimiento y sus factores (lluvia, temperatura, pesticidas), "
            "distinguiendo correlación de causalidad.",
        ],
        [
            "Predictiva",
            "¿Qué pasará?",
            "Estimar el rendimiento (ton/ha) esperado para un cultivo dadas las condiciones de clima y manejo, "
            "mediante modelos de regresión.",
        ],
        [
            "Prescriptiva",
            "¿Qué debo hacer?",
            "Recomendar volúmenes de compra y priorización de cultivos según el rendimiento predicho, mediante "
            "una regla de decisión, para minimizar sobrestock y quiebres.",
        ],
    ],
)

titulo("1.4 Fuentes de Datos y Ética Inicial", 2)
tabla(
    ["Tipo", "Fuente", "Contenido"],
    [
        [
            "Dataset (CSV)",
            "FAOSTAT — bulk download oficial (bulks-faostat.fao.org, dominios QCL y RP)",
            f"Rendimiento (kg/ha) y pesticidas (t) por país-cultivo-año: {N_FILAS:,} filas, {N_PAISES} "
            f"países, 10 cultivos, {ANIO_MIN}-{ANIO_MAX}. Actualiza y reemplaza al dataset de Kaggle "
            "propuesto en la Fase 1, que llegaba solo hasta 2013.",
        ],
        [
            "API pública",
            "Banco Mundial: Climate Change Knowledge Portal (cckpapi.worldbank.org) y World Bank Open Data "
            "(api.worldbank.org/v2)",
            "Clima oficial por país-año extraído en vivo: temperatura media (°C) y precipitación anual (mm), "
            "serie CRU TS 4.08 hasta 2023; más indicadores agrícolas de referencia para Ecuador y 4 países.",
        ],
        [
            "Excel interno (simulado)",
            "Registros de compras de la empresa",
            f"{N_COMPRAS:,} órdenes de compra históricas: volúmenes, precios de compra/reventa, canal, "
            "región y merma.",
        ],
    ],
)
parrafo("Estrategia de gobernanza y ética (privacidad desde el diseño):", negrita=True)
vinetas(
    [
        "Privacidad desde el diseño: los datos de rendimiento/clima son agregados por país y no contienen "
        "datos personales (PII). En el Excel de compras los proveedores figuran únicamente con códigos "
        "anónimos (PROV-001, PROV-002, …), sin nombres, RUC, teléfonos ni ubicaciones exactas.",
        "Calidad y trazabilidad: el origen de cada fuente y cada transformación aplicada quedan documentados "
        "en el pipeline ETL y en el reporte de calidad automatizado (Fase 2).",
        "Uso responsable: el modelo apoya las decisiones de compra, no reemplaza el juicio humano; las "
        "predicciones se comunican siempre con su margen de error.",
        "Sesgo de datos: los datos históricos sobrerrepresentan ciertos países y cultivos; este sesgo se "
        "evalúa cuantitativamente en la Fase 4.2.",
    ]
)
doc.add_page_break()

# ============================== FASE 2 ======================================
titulo("Fase 2 — Ingeniería de Datos y Modelado Multidimensional", 1)

titulo("2.1 Modelado Multidimensional (Esquema Estrella)", 2)
parrafo(
    "Se diseñó un esquema en estrella con dos tablas de hechos y cuatro dimensiones compartidas "
    "(dimensiones conformadas). Se eligió estrella y no copo de nieve porque prioriza la simplicidad de "
    "consulta en Power BI y evita joins innecesarios, con dimensiones pequeñas donde la normalización "
    "adicional no aporta ahorro relevante."
)
parrafo("Tablas de hechos:", negrita=True)
vinetas(
    [
        f"fact_rendimiento ({N_FILAS:,} filas): grano = país × cultivo × año. Métricas: rendimiento_ton_ha, "
        "precipitacion_mm, pesticidas_ton, temperatura_media_c.",
        f"fact_compras ({N_COMPRAS:,} filas): grano = orden de compra. Métricas: volumen_comprado_ton, "
        "precio_compra_usd_ton, precio_reventa_usd_ton, costo_total_usd, ingreso_reventa_usd, "
        "margen_bruto_usd, merma_pct.",
    ]
)
parrafo("Tablas de dimensiones:", negrita=True)
vinetas(
    [
        f"dim_tiempo ({ANIO_MAX - ANIO_MIN + 1} filas): id_tiempo, anio, decada, periodo.",
        f"dim_geografia ({N_PAISES} filas): id_geografia, pais, region_comercial (Ecuador / Latinoamérica de "
        "referencia / resto del mundo).",
        "dim_cultivo (10 filas): id_cultivo, cultivo (inglés FAO), cultivo_es, categoria (cereal, tubérculo, "
        "oleaginosa, musácea).",
        "dim_proveedor (40 filas): id_proveedor, codigo_proveedor (anónimo), region_origen (Costa, Sierra, "
        "Amazonía).",
    ]
)

titulo("2.2 Pipeline de Integración (ETL)", 2)
duplicados = CALIDAD["pasos"][0].get("duplicados_eliminados", 0)
parrafo(
    "El pipeline se implementó en Python (pandas + requests) en cuatro módulos ejecutables y reproducibles: "
    "extraer_datos_actualizados.py (integra el bulk oficial de FAOSTAT con el clima de la API pública CCKP "
    "del Banco Mundial, con caché local y reintentos ante errores transitorios), extract_api.py (indicadores "
    "de referencia del Banco Mundial), generar_compras_internas.py (fuente interna simulada, generada sin "
    "PII desde el origen) y transform_load.py (limpieza, tipado, validación y carga del esquema estrella). "
    "Cada ejecución produce un reporte de calidad en JSON con los pasos aplicados y su efecto."
)
parrafo("Calidad de datos aplicada (valores de la ejecución final):", negrita=True)
vinetas(
    [
        "Integración multi-fuente con claves país-año: los países se homologan a códigos ISO3 (los "
        "agregados regionales de FAOSTAT, como 'Americas' o 'World', se excluyen explícitamente) y solo se "
        "conservan combinaciones país-cultivo-año con las cuatro métricas completas.",
        f"Eliminación de duplicados exactos: {duplicados:,} filas duplicadas en la ejecución final.",
        "Tipado explícito: métricas convertidas a numérico con manejo de errores; el año se tipa como entero.",
        "Manejo de nulos: política de descarte en métricas críticas de negocio (sin imputación, para no "
        "inventar rendimientos).",
        "Validación de rangos físicos: rendimiento > 0, temperatura entre -10 y 45 °C, lluvia entre 0 y "
        "12,000 mm, pesticidas ≥ 0.",
        "Consistencia referencial: verificación automática (assert) de que toda clave foránea de los hechos "
        "existe en su dimensión.",
        "Conversión de unidades a la métrica de negocio: kg/ha → ton/ha.",
    ]
)

titulo("2.3 Cumplimiento Normativo", 2)
parrafo(
    "Alineado con la LOPDP ecuatoriana (Ley Orgánica de Protección de Datos Personales) y el principio de "
    "privacidad desde el diseño: (1) las fuentes públicas (FAO, Banco Mundial) contienen exclusivamente "
    "agregados por país, sin datos personales; (2) la fuente interna se genera anonimizada desde el origen "
    "—los proveedores solo existen como códigos— de modo que ninguna etapa del pipeline procesa PII; (3) el "
    "pipeline incluye una verificación automática que aborta la carga si detecta columnas de PII (nombre, "
    "cédula, RUC, teléfono, dirección, email) en la fuente interna; y (4) la trazabilidad de transformaciones "
    "queda registrada en reporte_calidad.json en cada ejecución."
)
doc.add_page_break()

# ============================== FASE 3 ======================================
titulo("Fase 3 — Analítica Descriptiva, Diagnóstica y Visualización", 1)

titulo("3.1 Análisis Exploratorio de Datos (EDA)", 2)
est = EDA["estadisticas_descriptivas"]
parrafo(
    "Se aplicaron medidas de tendencia central (media, mediana) y de dispersión (desviación estándar, rango "
    "intercuartílico y coeficiente de variación) a las cuatro variables clave, junto con asimetría y curtosis "
    "para identificar la forma de las distribuciones:"
)
tabla(
    ["Variable", "Media", "Mediana", "Desv. est.", "RIQ", "CV %", "Asimetría"],
    [
        [
            v["etiqueta"],
            v["media"],
            v["mediana"],
            v["desv_estandar"],
            v["rango_intercuartilico"],
            v["coef_variacion_pct"],
            v["asimetria"],
        ]
        for v in est.values()
    ],
)
rend_global = est["rendimiento_ton_ha"]
parrafo(
    "Lectura: en todas las variables la media supera con claridad a la mediana y la asimetría es positiva, es "
    f"decir, las distribuciones tienen cola derecha (pocos casos con valores muy altos). El rendimiento global "
    f"promedia {rend_global['media']:.2f} ton/ha pero la mitad de las observaciones está por debajo de "
    f"{rend_global['mediana']:.2f} ton/ha; los pesticidas son la variable más sesgada (unos pocos países "
    "concentran el consumo). Esta forma no normal justifica usar también la correlación de Spearman y modelos "
    "basados en árboles, robustos ante colas largas."
)
figura("01_distribuciones.png", "Figura 1. Distribuciones de las variables clave, con media (roja) y mediana (café).")
figura("02_rendimiento_ecuador.png", f"Figura 2. Rendimiento por cultivo en Ecuador ({ANIO_MIN}-{ANIO_MAX}) y evolución de los 4 cultivos líderes.")
corr_rend = EDA["correlaciones"]["pearson"]["rendimiento_ton_ha"]
parrafo(
    "Correlación vs. causalidad: la matriz de correlaciones muestra relaciones globales débiles entre el "
    f"rendimiento y los factores individuales (lluvia r = {corr_rend['precipitacion_mm']}; temperatura "
    f"r = {corr_rend['temperatura_media_c']}; pesticidas r = {corr_rend['pesticidas_ton']}). "
    "¿Significa que el clima no importa? No: significa que el efecto está condicionado por el tipo de cultivo y "
    "el país. Un ejemplo claro de por qué correlación no implica causalidad: los países con mayor uso de "
    "pesticidas muestran mayores rendimientos, pero el pesticida es en gran parte un indicador (proxy) de "
    "agricultura tecnificada —riego, semillas mejoradas, fertilización— y es esa tecnificación, no el pesticida "
    "por sí solo, la que explica el rendimiento. Por eso el pilar diagnóstico se complementa con el análisis "
    "condicionado por cultivo y con la importancia de variables del modelo (Fase 4)."
)
figura("03_correlaciones.png", "Figura 3. Correlación de Pearson y Spearman entre rendimiento y factores.")
figura("04_dispersion_factores.png", "Figura 4. Dispersión del rendimiento frente a lluvia, temperatura y pesticidas.")

titulo("3.2 Diseño de Indicadores (KPIs)", 2)
tabla(
    ["KPI", "Valor actual", "Pilar al que responde"],
    [
        [k["nombre"], k["valor"], k["objetivo_analitico"]] for k in kpis.values()
    ],
)
parrafo(
    "Los cinco KPIs cubren los cuatro pilares definidos en la Fase 1.3: nivel de oferta esperada (KPI 1), "
    "riesgo de oferta (KPI 2), salud económica (KPI 3), pérdidas operativas (KPI 4) y riesgo de portafolio "
    "(KPI 5). Todos se calculan directamente sobre el esquema estrella y están implementados como medidas DAX "
    "en Power BI."
)
figura("05_negocio_compras.png", "Figura 5. Margen bruto anual de reventa y volumen histórico comprado por cultivo (fuente interna).")

titulo("3.3 Dashboard Estratégico y Storytelling", 2)
parrafo(
    "El dashboard se construyó en Power BI sobre el esquema estrella (guía completa de construcción, medidas "
    "DAX y tema de color en la carpeta powerbi/ del proyecto), acompañado de una versión interactiva "
    "desplegable en Streamlit para la defensa. La narrativa sigue el orden de decisión del comité: "
    "(1) Resumen ejecutivo con los 5 KPIs, (2) Diagnóstico de factores, (3) Predicción y plan de compras."
)
parrafo("Justificación del diseño visual:", negrita=True)
vinetas(
    [
        "Percepción visual (Gestalt): patrón de lectura en Z —los KPIs se ubican en la franja superior, que es "
        "donde entra el ojo—; proximidad para agrupar indicadores relacionados; similitud de color para "
        "vincular el mismo cultivo entre gráficos.",
        "Canales visuales precisos: todas las comparaciones usan posición y longitud (líneas y barras); se "
        "evitaron gráficos de pastel y áreas, cuyos ángulos se perciben con menor precisión.",
        "Psicología del color: verde #2E7D32 como color corporativo (agro, crecimiento, decisión positiva); "
        "el rojo #C62828 se reserva exclusivamente para alertas (reducir compra), de modo que su sola "
        "aparición comunica riesgo; ámbar para neutralidad; neutros tierra para contexto. Máximo 4 colores "
        "semánticos por página.",
        "Tipografía: una sola familia sans-serif (Segoe UI) con jerarquía por tamaño y peso; cifras grandes "
        "en las tarjetas KPI para lectura a distancia durante la defensa.",
    ]
)
doc.add_page_break()

# ============================== FASE 4 ======================================
titulo("Fase 4 — Analítica Predictiva y Gobernanza de IA", 1)

titulo("4.1 Modelado Predictivo (Machine Learning)", 2)
parrafo(
    "Problema de regresión: estimar el rendimiento (ton/ha) a partir de seis variables predictoras: año, "
    "lluvia anual, pesticidas, temperatura media, país y tipo de cultivo. Preprocesamiento con escalado "
    "estándar para variables numéricas y one-hot encoding para categóricas, encapsulado en un Pipeline de "
    "scikit-learn (el mismo objeto sirve para entrenar y para predecir en producción). Partición 80/20 "
    f"({MODELO['particion']['entrenamiento']:,} filas de entrenamiento, {MODELO['particion']['prueba']:,} "
    "de prueba) y validación cruzada de 5 particiones sobre el conjunto de entrenamiento."
)
met = MODELO["metricas_por_modelo"]
tabla(
    ["Modelo", "RMSE (ton/ha)", "MAE (ton/ha)", "R² (prueba)", "R² validación cruzada (5)"],
    [
        [
            nombre,
            m["rmse_ton_ha"],
            m["mae_ton_ha"],
            m["r2"],
            f"{m['r2_validacion_cruzada_media']} ± {m['r2_validacion_cruzada_desv']}",
        ]
        for nombre, m in met.items()
    ],
)
lineal = met["Regresión Lineal"]
parrafo(
    "Se usaron métricas pertinentes para regresión: RMSE (error en las mismas unidades del negocio, ton/ha, "
    "penalizando errores grandes), MAE (error típico) y R² (proporción de la variabilidad explicada). El "
    f"modelo ganador es Random Forest: explica el {rf['r2'] * 100:.1f} % de la variabilidad del rendimiento "
    f"con un error RMSE de {rf['rmse_ton_ha']} ton/ha y un error típico (MAE) de {rf['mae_ton_ha']} ton/ha. "
    f"La regresión lineal, aunque interpretable, se queda en R² = {lineal['r2']:.2f} porque la relación "
    "clima-rendimiento no es lineal y depende de interacciones (cultivo × país × clima) que los árboles "
    f"capturan de forma natural. La cercanía entre el R² de prueba y el de validación cruzada ({rf['r2']:.3f} "
    f"vs {rf['r2_validacion_cruzada_media']:.3f}) descarta sobreajuste relevante."
)
figura("06_comparacion_modelos.png", "Figura 6. Comparación de modelos: R² y RMSE en el conjunto de prueba.")
figura("07_predicho_vs_real.png", "Figura 7. Rendimiento predicho vs real del modelo ganador (línea = predicción perfecta).", 4.6)

parrafo("Pilar prescriptivo — regla de decisión sobre la predicción:", negrita=True)
parrafo(
    "Para cada cultivo del portafolio en Ecuador se predice el rendimiento del siguiente ciclo bajo el "
    "escenario climático base (promedio de los últimos 3 años) y se calcula el índice de oferta = rendimiento "
    "predicho ÷ promedio histórico. La regla: índice ≥ 1.05 → aumentar compra +15 % (oferta abundante, precios "
    "a la baja); 0.95-1.05 → mantener; < 0.95 → reducir −15 % y asegurar contratos anticipados (riesgo de "
    "escasez y sobreprecio)."
)
tabla(
    ["Cultivo", "Predicho (ton/ha)", "Histórico (ton/ha)", "Índice", "Decisión"],
    [
        [
            f["cultivo"],
            f["rendimiento_predicho_ton_ha"],
            f["rendimiento_promedio_historico_ton_ha"],
            f["indice_oferta"],
            f["decision"],
        ]
        for _, f in RECOMENDACIONES.iterrows()
    ],
)

titulo("4.2 Ética de la IA y Gobernanza de Datos", 2)
parrafo("Sesgos algorítmicos — análisis crítico:", negrita=True)
sesgo = MODELO["sesgo_representacion"]
pais_top, filas_top = next(iter(sesgo["paises_mas_representados"].items()))
pais_min, filas_min = list(sesgo["paises_menos_representados"].items())[-1]
errores = MODELO["error_por_grupo"]["rmse_por_cultivo"]
cultivo_peor = max(errores, key=errores.get)
cultivo_mejor = min(errores, key=errores.get)
filas_cultivo = sesgo["cultivos"]
cultivo_menos_repr = min(filas_cultivo, key=filas_cultivo.get)
cultivo_mas_repr = max(filas_cultivo, key=filas_cultivo.get)
vinetas(
    [
        "Sesgo de representación: el dataset sobrerrepresenta países con series estadísticas completas "
        f"({pais_top}: {filas_top:,} filas) frente a otros con muy pocas ({pais_min}: {filas_min}); y "
        f"cultivos globales ({cultivo_mas_repr}: {filas_cultivo[cultivo_mas_repr]:,} filas) frente a "
        f"cultivos regionales ({cultivo_menos_repr}: {filas_cultivo[cultivo_menos_repr]:,}). Ecuador "
        f"cuenta con {sesgo['filas_ecuador']} filas, una representación intermedia razonable.",
        "Consecuencia potencial: el modelo aprende mejor los patrones de los grupos dominantes y podría "
        "predecir peor —'discriminar' estadísticamente— a países o cultivos minoritarios.",
        f"Verificación cuantitativa: se midió el error por grupo. El RMSE para Ecuador es de "
        f"{MODELO['error_por_grupo']['rmse_ecuador']} ton/ha (mejor que el promedio global de "
        f"{rf['rmse_ton_ha']}), por lo que el sesgo no perjudica al mercado objetivo. El error por cultivo "
        f"varía de {errores[cultivo_mejor]} ({cultivo_mejor}) a {errores[cultivo_peor]} ({cultivo_peor}); "
        "el análisis muestra que ese error se explica sobre todo por la magnitud y varianza del rendimiento "
        "de cada cultivo (la papa rinde 5-50 ton/ha según el país; la soya se mueve en un rango estrecho), "
        "además de la representación. Las recomendaciones de los cultivos con mayor error se comunican al "
        "negocio con una advertencia explícita de mayor incertidumbre.",
        f"Sesgo temporal: el histórico llega hasta {ANIO_MAX} (FAOSTAT publica con ~1-2 años de rezago); el "
        "pipeline automatizado permite reentrenar con cada actualización oficial antes de cada campaña.",
    ]
)
parrafo("IA Explicable (XAI):", negrita=True)
xai = MODELO["xai_importancia_permutacion"]
parrafo(
    "Para que el comité confíe en el algoritmo se calculó la importancia de variables por permutación "
    "(cuánto cae el R² al aleatorizar cada variable). El resultado es intuitivo para el negocio: el tipo de "
    "cultivo es por lejos el factor dominante (una papa rinde en toneladas mucho más que un trigo), seguido "
    "del país (proxy de suelo, tecnología y variedades). Entre los factores accionables/monitoreables, "
    f"pesticidas ({xai['Pesticidas (ton)']:.2f}), temperatura ({xai['Temperatura media (°C)']:.2f}) y "
    f"lluvia ({xai['Lluvia anual (mm)']:.2f}) tienen pesos comparables. La explicación al negocio: 'el "
    "modelo primero ubica el cultivo y el país, y luego ajusta la estimación según el clima y el manejo "
    f"del año; funciona como lo haría un agrónomo experimentado, pero con la memoria de {N_FILAS:,} "
    "cosechas'."
)
figura("08_importancia_variables.png", "Figura 8. Importancia de variables por permutación (XAI) del modelo ganador.")
parrafo(
    "Gobernanza del modelo: el pipeline completo (preprocesamiento + modelo) se versiona como un único "
    "artefacto (modelo_rendimiento.joblib); las predicciones se comunican siempre con su margen de error "
    f"(±{rf['rmse_ton_ha']} ton/ha); y la decisión final de compra permanece en el comité humano, con el "
    "modelo como apoyo —principio de supervisión humana definido desde la Fase 1."
)
doc.add_page_break()

# ========================== CONCLUSIONES ====================================
titulo("Conclusiones", 1)
vinetas(
    [
        "Se completó el ciclo analítico de extremo a extremo: tres fuentes integradas (incluida una API "
        "pública), un esquema estrella documentado, EDA con fundamento estadístico, 5 KPIs, un modelo "
        f"predictivo con R² = {rf['r2']:.3f} y una regla prescriptiva que convierte la predicción en "
        "decisiones de compra concretas.",
        "El valor de negocio es directo: anticipar la oferta permite comprar más cuando habrá abundancia "
        "(mejores precios) y asegurar contratos cuando habrá escasez, atacando a la vez el sobrestock y el "
        "quiebre de stock.",
        "La solución es honesta sobre sus límites: errores mayores en cultivos poco representados, rezago "
        f"de publicación de FAOSTAT (histórico hasta {ANIO_MAX}) y compras internas simuladas; cada "
        "limitación tiene su mitigación documentada.",
        "Trabajo futuro: reentrenamiento periódico con cada actualización de FAOSTAT, incorporación de "
        "precios de mercado reales para pasar de regla de decisión a optimización de margen, y "
        "desagregación por provincia cuando existan datos subnacionales.",
    ]
)

RUTA_SALIDA.parent.mkdir(exist_ok=True)
doc.save(RUTA_SALIDA)
print(f"OK — informe generado en {RUTA_SALIDA}")
