"""Pestaña Rentabilidad: comparación mensual de márgenes de compra por cultivo."""

import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components import tarjeta_kpi
from dashboard.theme import FONDO, VERDE

_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
_MESES_ABREV = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _margen_pct(df: pd.DataFrame) -> float:
    return df["margen_bruto_usd"].sum() / max(df["costo_total_usd"].sum(), 1) * 100


def _resumen_por_cultivo(del_mes: pd.DataFrame) -> pd.DataFrame:
    resumen = del_mes.groupby("cultivo_es", as_index=False).agg(
        margen_usd=("margen_bruto_usd", "sum"),
        costo_usd=("costo_total_usd", "sum"),
        volumen_ton=("volumen_comprado_ton", "sum"),
        merma=("merma_pct", "mean"),
    )
    resumen["margen_pct"] = resumen["margen_usd"] / resumen["costo_usd"].clip(lower=1) * 100
    resumen["margen_usd_ton"] = resumen["margen_usd"] / resumen["volumen_ton"].clip(lower=1)
    return resumen.sort_values("margen_pct")


def _renderizar_ranking_mes(resumen: pd.DataFrame, nombre_mes: str) -> None:
    fig = px.bar(
        resumen, x="margen_pct", y="cultivo_es", orientation="h",
        title=f"Margen bruto de reventa por cultivo · compras de {nombre_mes.lower()}",
        labels={"margen_pct": "Margen bruto (%)", "cultivo_es": ""},
        color_discrete_sequence=[VERDE], text_auto=".1f",
        custom_data=["volumen_ton", "margen_usd_ton"],
    )
    fig.update_traces(
        textposition="outside", textfont_size=11,
        hovertemplate=(
            "<b>%{y}</b><br>Margen: %{x:.1f} %<br>"
            "Volumen histórico: %{customdata[0]:,.0f} ton<br>"
            "Margen: %{customdata[1]:,.1f} USD/ton<extra></extra>"
        ),
    )
    fig.update_layout(height=420, showlegend=False)
    with st.container(border=False):
        st.plotly_chart(fig, width='stretch')


def _renderizar_heatmap_estacional(compras_f: pd.DataFrame) -> None:
    celdas = compras_f.groupby(["cultivo_es", "mes"]).agg(
        margen_usd=("margen_bruto_usd", "sum"),
        costo_usd=("costo_total_usd", "sum"),
    )
    celdas["margen_pct"] = celdas["margen_usd"] / celdas["costo_usd"].clip(lower=1) * 100
    matriz = celdas["margen_pct"].unstack("mes").reindex(columns=range(1, 13))

    fig = go.Figure(
        go.Heatmap(
            z=matriz.values,
            x=_MESES_ABREV,
            y=matriz.index,
            colorscale=[[0, FONDO], [1, VERDE]],
            hovertemplate="<b>%{y}</b> · %{x}<br>Margen: %{z:.1f} %<extra></extra>",
            colorbar=dict(title="Margen %", thickness=12),
        )
    )
    fig.update_layout(
        title="Estacionalidad del margen · cultivo × mes (todo el histórico filtrado)",
        height=420, margin=dict(t=60, b=10),
    )
    with st.container(border=False):
        st.plotly_chart(fig, width='stretch')


def renderizar_rentabilidad(compras_f: pd.DataFrame) -> None:
    """Dibuja la comparación de rentabilidad mensual con las compras filtradas."""
    st.markdown(
        """
<div class="section-note">
<b>¿Qué tan rentable es comprar cada cultivo en un mes dado?</b> — margen bruto
histórico de reventa agregado por mes de compra. Las compras internas son
<b>simuladas</b> para el escenario académico: el patrón estacional es
ilustrativo de cómo se usaría con datos reales de la empresa.
</div>
""",
        unsafe_allow_html=True,
    )

    mes_actual = datetime.date.today().month
    mes = st.selectbox(
        "Mes de compra",
        list(range(1, 13)),
        index=mes_actual - 1,
        format_func=lambda m: _MESES[m - 1],
    )
    nombre_mes = _MESES[mes - 1]

    del_mes = compras_f[compras_f["mes"] == mes]
    if del_mes.empty:
        st.info(
            f"No hay compras registradas en {nombre_mes.lower()} con los filtros "
            "actuales. Amplía el rango de años o los cultivos."
        )
        return

    resumen = _resumen_por_cultivo(del_mes)
    mejor = resumen.iloc[-1]
    margen_mes = _margen_pct(del_mes)
    margen_anual = _margen_pct(compras_f)
    delta_mes = margen_mes - margen_anual

    k1, k2, k3 = st.columns(3)
    tarjeta_kpi(
        k1, f"Mejor cultivo en {nombre_mes.lower()}", str(mejor["cultivo_es"]),
        f"{mejor['margen_pct']:.1f} %", "DESCRIPTIVO",
    )
    tarjeta_kpi(
        k2, f"Margen del mes vs anual ({margen_anual:.1f} %)",
        f"{margen_mes:.1f}", f"% ({delta_mes:+.1f} pts)",
        "DIAGNÓSTICO", "ambar" if delta_mes < 0 else "",
    )
    tarjeta_kpi(
        k3, f"Merma promedio en {nombre_mes.lower()}",
        f"{del_mes['merma_pct'].mean():.1f}", "%", "DIAGNÓSTICO", "tierra",
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    col_izq, col_der = st.columns(2)
    with col_izq:
        _renderizar_ranking_mes(resumen, nombre_mes)
    with col_der:
        _renderizar_heatmap_estacional(compras_f)
