"""Registro del template global "agro" de Plotly."""

import plotly.graph_objects as go
import plotly.io as pio

from dashboard.theme.colores import SECUENCIA_CULTIVOS, TINTA


def registrar_tema_plotly() -> None:
    """Registra y activa el template corporativo de Plotly."""
    pio.templates["agro"] = go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, 'Segoe UI', sans-serif", size=13, color=TINTA),
            title=dict(font=dict(size=15, color=TINTA), x=0, xanchor="left"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            colorway=SECUENCIA_CULTIVOS,
            xaxis=dict(gridcolor="#E3EAE0", zerolinecolor="#E3EAE0", linecolor="#CBD8C6"),
            yaxis=dict(gridcolor="#E3EAE0", zerolinecolor="#E3EAE0", linecolor="#CBD8C6"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=11)),
            margin=dict(l=10, r=10, t=60, b=10),
            hoverlabel=dict(font_family="Inter, 'Segoe UI', sans-serif"),
        )
    )
    pio.templates.default = "agro"
