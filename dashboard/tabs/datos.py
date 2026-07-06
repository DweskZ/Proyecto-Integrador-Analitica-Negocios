"""Pestaña Datos: modelo estrella, explorador de tablas y reporte de calidad."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.theme import TINTA, TINTA_SUAVE, VERDE, VERDE_OSCURO

# Posiciones (x, y) de cada tabla en el diagrama estrella.
_POSICIONES = {
    "fact_rendimiento": (-1.1, 0.0),
    "fact_compras": (1.1, 0.0),
    "dim_geografia": (-2.4, 0.95),
    "dim_cultivo": (0.0, 1.05),
    "dim_tiempo": (0.0, -1.05),
    "dim_proveedor": (2.4, 0.95),
}

# Relaciones hecho → dimensión con su clave foránea.
_RELACIONES = [
    ("fact_rendimiento", "dim_geografia", "id_geografia"),
    ("fact_rendimiento", "dim_cultivo", "id_cultivo"),
    ("fact_rendimiento", "dim_tiempo", "id_tiempo"),
    ("fact_compras", "dim_cultivo", "id_cultivo"),
    ("fact_compras", "dim_tiempo", "id_tiempo"),
    ("fact_compras", "dim_proveedor", "id_proveedor"),
]

_CLASE_TIPO = {"Hecho": "hecho", "Dimensión": "dimension", "Fuente externa": "externa"}

_FILAS_MAX_VISTA = 1_000


def _figura_modelo_estrella(tablas: dict[str, dict]) -> go.Figure:
    fig = go.Figure()

    # Aristas con la clave foránea anotada en el punto medio.
    for hecho, dimension, fk in _RELACIONES:
        x0, y0 = _POSICIONES[hecho]
        x1, y1 = _POSICIONES[dimension]
        fig.add_shape(
            type="line", x0=x0, y0=y0, x1=x1, y1=y1,
            line=dict(color="#B8CBB9", width=1.6),
            layer="below",
        )
        fig.add_annotation(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=fk, showarrow=False,
            font=dict(size=9, color=TINTA_SUAVE), bgcolor="#F6F8F4",
        )

    # Nodos como anotaciones con caja (hechos en verde, dimensiones en blanco).
    for nombre, (x, y) in _POSICIONES.items():
        es_hecho = tablas[nombre]["tipo"] == "Hecho"
        filas = len(tablas[nombre]["df"])
        fig.add_annotation(
            x=x, y=y,
            text=f"<b>{nombre}</b><br><span style='font-size:10px'>{filas:,} filas</span>",
            showarrow=False,
            font=dict(size=12, color="white" if es_hecho else TINTA),
            bgcolor=VERDE if es_hecho else "white",
            bordercolor=VERDE_OSCURO if es_hecho else VERDE,
            borderwidth=1.6, borderpad=8,
        )

    fig.update_layout(
        title="Modelo dimensional (esquema estrella)",
        xaxis=dict(visible=False, range=[-3.5, 3.5], fixedrange=True),
        yaxis=dict(visible=False, range=[-1.6, 1.6], fixedrange=True),
        height=380, margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def _filtrar_por_texto(df: pd.DataFrame, consulta: str) -> pd.DataFrame:
    if not consulta.strip():
        return df
    coincide = (
        df.astype(str)
        .apply(lambda col: col.str.contains(consulta.strip(), case=False, na=False))
        .any(axis=1)
    )
    return df[coincide]


def _renderizar_explorador(tablas: dict[str, dict]) -> None:
    nombre = st.selectbox(
        "Tabla",
        list(tablas),
        format_func=lambda n: f"{n} · {tablas[n]['tipo']}",
    )
    tabla = tablas[nombre]
    df = tabla["df"]

    st.markdown(
        f"""
<div class="tabla-meta">
  <span class="nombre">{nombre}</span>
  <span class="tipo {_CLASE_TIPO[tabla["tipo"]]}">{tabla["tipo"].upper()}</span>
  <div class="descripcion">{tabla["descripcion"]}<br>
  <b>Grano:</b> {tabla["grano"]} · <b>{len(df):,}</b> filas × <b>{df.shape[1]}</b> columnas</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col_busqueda, col_descarga = st.columns((3, 1), vertical_alignment="bottom")
    consulta = col_busqueda.text_input(
        "🔎 Buscar en la tabla", placeholder="p. ej. Maíz, Ecuador, 2020…", key=f"busqueda_{nombre}"
    )
    col_descarga.download_button(
        "⬇️ Descargar CSV completo",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{nombre}.csv",
        mime="text/csv",
        width='stretch',
    )

    filtrado = _filtrar_por_texto(df, consulta)
    if filtrado.empty:
        st.info(f"Ninguna fila coincide con «{consulta}». Prueba otro término.")
        return

    st.dataframe(filtrado.head(_FILAS_MAX_VISTA), width='stretch', height=420)
    if len(filtrado) > _FILAS_MAX_VISTA:
        st.caption(
            f"Mostrando las primeras {_FILAS_MAX_VISTA:,} de {len(filtrado):,} filas "
            "(descarga el CSV para verlas todas)."
        )
    else:
        st.caption(f"{len(filtrado):,} filas mostradas.")

    with st.expander("📋 Columnas y tipos de dato"):
        esquema = pd.DataFrame(
            {
                "columna": df.columns,
                "tipo": df.dtypes.astype(str).values,
                "no nulos": df.notna().sum().values,
                "valores únicos": df.nunique().values,
            }
        )
        st.dataframe(esquema, width='stretch', hide_index=True)


# Presentación amigable de cada paso del reporte de calidad del ETL.
_PASOS_CALIDAD = {
    "eliminacion_duplicados": ("🧹", "Eliminación de duplicados"),
    "manejo_nulos": ("🕳️", "Manejo de valores nulos"),
    "validacion_rangos_fisicos": ("📏", "Validación de rangos físicos"),
    "resumen_rendimiento": ("📊", "Resumen del procesamiento"),
    "cumplimiento_normativo": ("🔒", "Cumplimiento normativo (PII)"),
    "consistencia_referencial": ("🔗", "Consistencia referencial"),
}


def _detalle_paso(paso: dict) -> str:
    detalles = []
    for clave, valor in paso.items():
        if clave == "paso":
            continue
        if isinstance(valor, dict):
            valor = " · ".join(f"{k}: {v}" for k, v in valor.items())
        etiqueta = clave.replace("_", " ").capitalize()
        detalles.append(f"<b>{etiqueta}:</b> {valor}")
    return "<br>".join(detalles)


def _renderizar_reporte_calidad(reporte: dict) -> None:
    pasos = reporte.get("pasos", [])
    columnas = st.columns(3)
    for i, paso in enumerate(pasos):
        icono, titulo = _PASOS_CALIDAD.get(paso["paso"], ("✅", paso["paso"]))
        columnas[i % 3].markdown(
            f"""
<div class="quality-card">
  <div class="titulo">{icono} {titulo}</div>
  <div class="detalle">{_detalle_paso(paso)}</div>
  <span class="ok">VERIFICADO</span>
</div>
""",
            unsafe_allow_html=True,
        )


def renderizar_datos(tablas: dict[str, dict], reporte_calidad: dict) -> None:
    """Dibuja el diagrama estrella, el explorador de tablas y la calidad de datos."""
    st.markdown(
        """
<div class="section-note">
<b>Datos crudos del modelo dimensional</b> — el pipeline ETL produce un
<b>esquema estrella</b>: dos tablas de hechos (rendimiento y compras) rodeadas de
dimensiones compartidas (cultivo, tiempo) y propias (geografía, proveedor).
Aquí puedes inspeccionar cada tabla tal como se carga en Power BI y verificar
la calidad del procesamiento.
</div>
""",
        unsafe_allow_html=True,
    )

    with st.container(border=False):
        st.plotly_chart(
            _figura_modelo_estrella(tablas),
            width='stretch',
            config={"displayModeBar": False},
        )

    st.markdown("#### 🔍 Explorador de tablas")
    _renderizar_explorador(tablas)

    st.markdown("#### ✅ Reporte de calidad del ETL")
    _renderizar_reporte_calidad(reporte_calidad)
