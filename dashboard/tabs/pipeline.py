"""Sección Pipeline de la pestaña Datos: linaje del dato y estado de cada etapa."""

import datetime
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from dashboard.data import RUTA_PROYECTO
from dashboard.theme import AMBAR, TIERRA, TINTA, TINTA_SUAVE, VERDE, VERDE_OSCURO

# ------------------------- Diagrama de flujo ---------------------------------
# Nodos: (x, y, tipo) — tipo controla el color: fuente / script / artefacto / entregable
_NODOS = {
    "FAOSTAT bulk": (0, 3.0, "fuente"),
    "Clima CCKP": (0, 2.0, "fuente"),
    "API Banco Mundial": (0, 1.0, "fuente"),
    "Compras internas<br>(simulado)": (0, 0.0, "fuente"),
    "extraer_datos_<br>actualizados.py": (1, 2.5, "script"),
    "extract_api.py": (1, 1.0, "script"),
    "generar_compras_<br>internas.py": (1, 0.0, "script"),
    "transform_load.py<br>esquema estrella + calidad": (2, 1.25, "artefacto"),
    "eda.py": (3, 2.5, "script"),
    "entrenar_modelo.py": (3, 1.25, "script"),
    "prescriptivo.py": (3, 0.0, "script"),
    "Dashboard /<br>Power BI": (4, 1.9, "entregable"),
    "Informe técnico": (4, 0.6, "entregable"),
}

_ARISTAS = [
    ("FAOSTAT bulk", "extraer_datos_<br>actualizados.py"),
    ("Clima CCKP", "extraer_datos_<br>actualizados.py"),
    ("API Banco Mundial", "extract_api.py"),
    ("Compras internas<br>(simulado)", "generar_compras_<br>internas.py"),
    ("extraer_datos_<br>actualizados.py", "transform_load.py<br>esquema estrella + calidad"),
    ("extract_api.py", "transform_load.py<br>esquema estrella + calidad"),
    ("generar_compras_<br>internas.py", "transform_load.py<br>esquema estrella + calidad"),
    ("transform_load.py<br>esquema estrella + calidad", "eda.py"),
    ("transform_load.py<br>esquema estrella + calidad", "entrenar_modelo.py"),
    ("entrenar_modelo.py", "prescriptivo.py"),
    ("eda.py", "Informe técnico"),
    ("entrenar_modelo.py", "Informe técnico"),
    ("transform_load.py<br>esquema estrella + calidad", "Dashboard /<br>Power BI"),
    ("prescriptivo.py", "Dashboard /<br>Power BI"),
]

_COLUMNAS = ["FUENTES", "EXTRACCIÓN", "TRANSFORMACIÓN", "ANALÍTICA", "CONSUMO"]

_ESTILO_NODO = {
    "fuente": dict(bg="white", borde=VERDE, texto=TINTA),
    "script": dict(bg=VERDE, borde=VERDE_OSCURO, texto="white"),
    "artefacto": dict(bg=VERDE_OSCURO, borde=VERDE_OSCURO, texto="white"),
    "entregable": dict(bg="#FDF3D5", borde=AMBAR, texto=TINTA),
}


def _figura_flujo() -> go.Figure:
    fig = go.Figure()

    for origen, destino in _ARISTAS:
        x0, y0, _ = _NODOS[origen]
        x1, y1, _ = _NODOS[destino]
        fig.add_annotation(
            x=x1 - 0.18, y=y1, ax=x0 + 0.18, ay=y0,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1.1, arrowwidth=1.4,
            arrowcolor="#B8CBB9", text="",
        )

    for etiqueta, (x, y, tipo) in _NODOS.items():
        estilo = _ESTILO_NODO[tipo]
        fig.add_annotation(
            x=x, y=y, text=f"<b>{etiqueta}</b>", showarrow=False,
            font=dict(size=10.5, color=estilo["texto"]),
            bgcolor=estilo["bg"], bordercolor=estilo["borde"],
            borderwidth=1.5, borderpad=6,
        )

    for i, titulo in enumerate(_COLUMNAS):
        fig.add_annotation(
            x=i, y=3.8, text=f"<b>{titulo}</b>", showarrow=False,
            font=dict(size=11, color=TINTA_SUAVE, family="Inter, sans-serif"),
        )

    fig.update_layout(
        title="Pipeline de datos: de las fuentes públicas al dashboard",
        xaxis=dict(visible=False, range=[-0.55, 4.55], fixedrange=True),
        yaxis=dict(visible=False, range=[-0.55, 4.2], fixedrange=True),
        height=430, margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# ------------------------- Tarjetas de etapas --------------------------------
_ETAPAS = [
    {
        "icono": "agriculture", "titulo": "Extracción FAOSTAT + clima", "fase": "Fase 2.2",
        "script": "src/etl/extraer_datos_actualizados.py",
        "descripcion": "Reconstruye el dataset consolidado 1990–2023 desde los bulks de FAOSTAT y la API de clima CCKP del Banco Mundial.",
        "salidas": ["data/raw/rendimiento_actualizado.csv"],
    },
    {
        "icono": "public", "titulo": "Extracción API Banco Mundial", "fase": "Fase 2.2",
        "script": "src/etl/extract_api.py",
        "descripcion": "Consume la API pública de World Bank Open Data: fertilizantes, lluvia, cereales y tierra agrícola por país-año.",
        "salidas": ["data/processed/api_worldbank.csv"],
    },
    {
        "icono": "corporate_fare", "titulo": "Fuente interna (compras)", "fase": "Fase 2.2",
        "script": "src/etl/generar_compras_internas.py",
        "descripcion": "Genera el Excel de compras históricas simuladas, coherentes con el rendimiento real de Ecuador y sin PII.",
        "salidas": ["data/raw/compras_internas.xlsx"],
    },
    {
        "icono": "hub", "titulo": "Transformación y carga", "fase": "Fases 2.1–2.2",
        "script": "src/etl/transform_load.py",
        "descripcion": "Integra las tres fuentes en el esquema estrella (2 hechos + 4 dimensiones) y emite el reporte de calidad.",
        "salidas": ["data/processed/fact_rendimiento.csv", "data/processed/fact_compras.csv",
                     "data/processed/reporte_calidad.json"],
    },
    {
        "icono": "monitoring", "titulo": "EDA y KPIs", "fase": "Fases 3.1–3.2",
        "script": "src/analytics/eda.py",
        "descripcion": "Estadísticas descriptivas, distribuciones, correlaciones, KPIs de negocio y figuras del informe.",
        "salidas": ["reports/eda_resultados.json", "reports/figures/01_distribuciones.png"],
    },
    {
        "icono": "smart_toy", "titulo": "Entrenamiento del modelo", "fase": "Fase 4.1",
        "script": "src/models/entrenar_modelo.py",
        "descripcion": "Compara 3 algoritmos de regresión, valida con hold-out + CV 5-fold y reporta XAI y sesgos.",
        "salidas": ["models/modelo_rendimiento.joblib", "reports/modelo_resultados.json"],
    },
    {
        "icono": "track_changes", "titulo": "Regla prescriptiva", "fase": "Fase 4",
        "script": "src/models/prescriptivo.py",
        "descripcion": "Aplica la regla de decisión de compra (índice de oferta) sobre las predicciones del próximo ciclo.",
        "salidas": ["reports/recomendaciones_compra.csv"],
    },
    {
        "icono": "description", "titulo": "Informe técnico", "fase": "Entregable 1",
        "script": "src/informe/generar_informe.py",
        "descripcion": "Compone el informe DOCX/PDF con las cifras leídas de los JSON: reejecutar el pipeline actualiza el informe.",
        "salidas": ["informe/Informe_Tecnico.docx"],
    },
]


def _tamanio_legible(bytes_: int) -> str:
    if bytes_ >= 1_048_576:
        return f"{bytes_ / 1_048_576:.1f} MB"
    return f"{bytes_ / 1024:.0f} KB"


def _estado_artefacto(relativo: str) -> str:
    ruta = RUTA_PROYECTO / Path(relativo)
    nombre = ruta.name
    if not ruta.exists():
        return f"<span class='falta'>✗ {nombre} — pendiente de generar</span>"
    stat = ruta.stat()
    fecha = datetime.date.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y")
    return f"<span class='ok'>✓ {nombre}</span> · {_tamanio_legible(stat.st_size)} · {fecha}"


def renderizar_pipeline() -> None:
    """Dibuja el diagrama de linaje y las tarjetas de etapas con estado en disco."""
    with st.container(border=False):
        st.plotly_chart(_figura_flujo(), width='stretch', config={"displayModeBar": False})

    columnas = st.columns(2)
    for i, etapa in enumerate(_ETAPAS):
        estado = "<br>".join(_estado_artefacto(s) for s in etapa["salidas"])
        columnas[i % 2].markdown(
            f"""
<div class="stage-card">
  <div class="titulo"><span class="icono-material">{etapa["icono"]}</span> {i + 1}. {etapa["titulo"]}
    <span class="fase">{etapa["fase"]}</span></div>
  <div class="detalle">{etapa["descripcion"]}</div>
  <div class="script">{etapa["script"]}</div>
  <div class="artefactos">{estado}</div>
</div>
""",
            unsafe_allow_html=True,
        )
