"""Tarjeta KPI de la fila superior."""


def tarjeta_kpi(columna, etiqueta: str, valor: str, unidad: str, pilar: str, clase: str = "") -> None:
    """Dibuja una tarjeta KPI dentro de la columna de Streamlit dada."""
    columna.markdown(
        f"""
<div class="kpi {clase}">
  <div class="etiqueta">{etiqueta}</div>
  <div class="valor">{valor} <span class="unidad">{unidad}</span></div>
  <span class="pilar">{pilar}</span>
</div>
""",
        unsafe_allow_html=True,
    )
