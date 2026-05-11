"""
Dashboard executivo de FinOps AWS.
Rode com: streamlit run src/dashboard.py
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from forecast import prever_proximos_dias, projetar_proximo_mes
from alertas import gerar_todos_alertas

# ---------- Configuração da página ----------

st.set_page_config(
    page_title="FinOps AWS Analytics",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Paleta ----------

AWS_ORANGE = "#FF9900"
BLUE_PRIMARY = "#4A90E2"
BLUE_SCALE = ["#1F3A5F", "#2E5C8A", "#3D7EB5", "#4A90E2", "#7BB0E8", "#A8CCF0"]
BG_CARD = "#1A1F2E"
BG_PAGE = "#0E1117"
BG_TOPBAR = "#151A26"
TEXT_MUTED = "#8B92A8"
BORDER = "#2A3142"

# ---------- CSS global ----------

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Esconde a sidebar completamente */
    [data-testid="stSidebar"] {{display: none;}}
    [data-testid="collapsedControl"] {{display: none;}}

    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }}

    /* Cards de métricas */
    [data-testid="stMetric"] {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 18px 20px;
    }}

    [data-testid="stMetricLabel"] {{
        color: {TEXT_MUTED};
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 28px;
        font-weight: 700;
        color: #FFFFFF;
    }}

    /* Subheaders dos gráficos */
    h3 {{
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0 !important;
        margin-bottom: 12px !important;
    }}

    /* Estilo dos inputs na topbar */
    .stSelectbox > div > div,
    .stDateInput > div > div {{
        background-color: {BG_CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 6px !important;
    }}

    .stSelectbox label,
    .stDateInput label {{
        color: {TEXT_MUTED} !important;
        font-size: 10px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }}
    </style>
""", unsafe_allow_html=True)

ARQUIVO_BANCO = Path("data") / "finops.db"

# ---------- Dados ----------

@st.cache_data
def carregar_dados() -> pd.DataFrame:
    conexao = sqlite3.connect(ARQUIVO_BANCO)
    df = pd.read_sql_query("""
        SELECT data, servico, regiao, recurso_id, custo_usd
        FROM faturas
        ORDER BY data
    """, conexao)
    conexao.close()
    df["data"] = pd.to_datetime(df["data"])
    return df


@st.cache_data
def carregar_mensal() -> pd.DataFrame:
    conexao = sqlite3.connect(ARQUIVO_BANCO)
    df = pd.read_sql_query("""
        SELECT
            strftime('%Y-%m', data) AS mes,
            ROUND(SUM(custo_usd), 2) AS gasto_total,
            COUNT(DISTINCT data) AS dias_com_dados
        FROM faturas
        GROUP BY mes
        ORDER BY mes
    """, conexao)
    conexao.close()
    return df[df["dias_com_dados"] >= 20].copy()


# ---------- Topbar (logo + título + filtros) ----------

def renderizar_topbar(df: pd.DataFrame) -> tuple:
    # Carrega SVG
    svg_html = ""
    svg_path = Path("assets") / "aws-color.svg"
    if svg_path.exists():
        svg_content = svg_path.read_text(encoding="utf-8")
        svg_content = re.sub(r'\swidth="[^"]*"', '', svg_content, count=1)
        svg_content = re.sub(r'\sheight="[^"]*"', '', svg_content, count=1)
        svg_content = svg_content.replace(
            '<svg',
            '<svg style="width:100%; height:auto; display:block;"',
            1,
        )
        svg_html = svg_content

    # Header HTML (logo + título)
    col_logo, col_filtros = st.columns([2, 3], gap="large")

    with col_logo:
        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                gap: 16px;
                padding: 12px 0 16px 0;
            ">
                <div style="width: 56px; flex-shrink: 0;">
                    {svg_html}
                </div>
                <div>
                    <div style="
                        font-size: 10px;
                        color: {AWS_ORANGE};
                        font-weight: 600;
                        letter-spacing: 1.5px;
                        text-transform: uppercase;
                    ">
                        Cloud Financial Operations
                    </div>
                    <div style="
                        font-size: 22px;
                        font-weight: 700;
                        color: #FFFFFF;
                        line-height: 1.2;
                        margin-top: 2px;
                    ">
                        AWS Cost Analytics
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_filtros:
        f1, f2, f3 = st.columns(3, gap="small")

        with f1:
            servicos = ["Todos"] + sorted(df["servico"].unique().tolist())
            servico_selecionado = st.selectbox("Serviço", servicos)

        with f2:
            regioes = ["Todas"] + sorted(df["regiao"].unique().tolist())
            regiao_selecionada = st.selectbox("Região", regioes)

        with f3:
            data_min = df["data"].min().date()
            data_max = df["data"].max().date()
            intervalo = st.date_input(
                "Período",
                value=(data_min, data_max),
                min_value=data_min,
                max_value=data_max,
            )

    # Linha divisória
    st.markdown(
        f"<div style='height:1px; background:{BORDER}; margin: 4px 0 24px 0;'></div>",
        unsafe_allow_html=True,
    )

    return servico_selecionado, regiao_selecionada, intervalo


# ---------- Filtros ----------

def aplicar_filtros(df: pd.DataFrame, servico, regiao, intervalo) -> pd.DataFrame:
    if servico != "Todos":
        df = df[df["servico"] == servico]
    if regiao != "Todas":
        df = df[df["regiao"] == regiao]
    if len(intervalo) == 2:
        df = df[
            (df["data"].dt.date >= intervalo[0]) &
            (df["data"].dt.date <= intervalo[1])
        ]
    return df


# ---------- KPIs ----------

def renderizar_kpis(df: pd.DataFrame, df_mensal: pd.DataFrame) -> None:
    total_gasto = df["custo_usd"].sum()
    media_diaria = df.groupby("data")["custo_usd"].sum().mean()
    servico_top = df.groupby("servico")["custo_usd"].sum().idxmax()

    if len(df_mensal) >= 2:
        ultimo = df_mensal.iloc[-1]["gasto_total"]
        penultimo = df_mensal.iloc[-2]["gasto_total"]
        variacao = ((ultimo - penultimo) / penultimo) * 100
        variacao_str = f"{variacao:+.1f}%"
        delta_color = "inverse" if variacao > 0 else "normal"
    else:
        variacao_str = "N/A"
        delta_color = "off"

    col1, col2, col3, col4 = st.columns(4, gap="small")
    with col1:
        st.metric("Total no Período", f"${total_gasto:,.0f}")
    with col2:
        st.metric("Média Diária", f"${media_diaria:,.0f}")
    with col3:
        st.metric("Maior Serviço", servico_top)
    with col4:
        st.metric(
            "Variação Mensal",
            variacao_str,
            delta=variacao_str,
            delta_color=delta_color,
        )


# ---------- Tema gráficos ----------

def aplicar_tema_plotly(fig) -> None:
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#FFFFFF",
        font_family="-apple-system, BlinkMacSystemFont, sans-serif",
        font_size=12,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        coloraxis_showscale=False,
    )


# ---------- Gráficos ----------

def grafico_evolucao_mensal(df_mensal: pd.DataFrame) -> None:
    st.markdown("### Evolução Mensal")
    fig = px.bar(
        df_mensal,
        x="mes",
        y="gasto_total",
        text_auto=".2s",
        color_discrete_sequence=[BLUE_PRIMARY],
    )
    fig.update_traces(
        marker_line_width=0,
        textfont_size=11,
        textfont_color="#FFFFFF",
        textposition="outside",
    )
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, tickformat="$,.0f")
    aplicar_tema_plotly(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def grafico_distribuicao_servico(df: pd.DataFrame) -> None:
    st.markdown("### Por Serviço")
    por_servico = df.groupby("servico")["custo_usd"].sum().reset_index()
    por_servico = por_servico.sort_values("custo_usd", ascending=False)

    fig = px.pie(
        por_servico,
        values="custo_usd",
        names="servico",
        hole=0.6,
        color_discrete_sequence=BLUE_SCALE,
    )
    fig.update_traces(
        textposition="outside",
        textinfo="label+percent",
        textfont_size=11,
        marker=dict(line=dict(color=BG_PAGE, width=2)),
    )
    fig.update_layout(showlegend=False)
    aplicar_tema_plotly(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def grafico_tendencia_diaria(df: pd.DataFrame) -> None:
    st.markdown("### Tendência Diária & Previsão")

    diario = df.groupby("data")["custo_usd"].sum().reset_index()
    diario.columns = ["data", "gasto_total"]

    # Calcula previsão dos próximos 30 dias
    previsao = prever_proximos_dias(df, dias_a_prever=30)

    fig = go.Figure()

    # Histórico (linha sólida)
    fig.add_trace(go.Scatter(
        x=diario["data"],
        y=diario["gasto_total"],
        mode="lines",
        name="Histórico",
        line=dict(color=BLUE_PRIMARY, width=2),
        fill="tozeroy",
        fillcolor="rgba(74, 144, 226, 0.15)",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>$%{y:,.2f}<extra></extra>",
    ))

    # Previsão (linha pontilhada laranja)
    fig.add_trace(go.Scatter(
        x=previsao["data"],
        y=previsao["gasto_previsto"],
        mode="lines",
        name="Previsão (30d)",
        line=dict(color=AWS_ORANGE, width=2, dash="dash"),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>$%{y:,.2f} (previsto)<extra></extra>",
    ))

    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, tickformat="$,.0f")
    aplicar_tema_plotly(fig)
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def grafico_regiao(df: pd.DataFrame) -> None:
    st.markdown("### Por Região")
    por_regiao = (
        df.groupby("regiao")["custo_usd"]
        .sum()
        .reset_index()
        .sort_values("custo_usd", ascending=True)
    )
    fig = px.bar(
        por_regiao,
        x="custo_usd",
        y="regiao",
        orientation="h",
        text_auto=".2s",
        color_discrete_sequence=[BLUE_PRIMARY],
    )
    fig.update_traces(
        marker_line_width=0,
        textfont_size=11,
        textfont_color="#FFFFFF",
        textposition="outside",
    )
    fig.update_xaxes(title=None, tickformat="$,.0f")
    fig.update_yaxes(title=None)
    aplicar_tema_plotly(fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def tabela_top_recursos(df: pd.DataFrame) -> None:
    st.markdown("### Top Recursos por Custo")
    top = (
        df.groupby(["recurso_id", "servico", "regiao"])["custo_usd"]
        .sum()
        .reset_index()
        .sort_values("custo_usd", ascending=False)
        .head(10)
        .rename(columns={
            "recurso_id": "Recurso",
            "servico": "Serviço",
            "regiao": "Região",
            "custo_usd": "Custo Total",
        })
    )
    top["Custo Total"] = top["Custo Total"].round(2)

    st.dataframe(
        top,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Custo Total": st.column_config.NumberColumn(format="$ %.2f"),
        },
    )
    
def renderizar_alertas(df: pd.DataFrame) -> None:
    """Renderiza cards de alertas em destaque."""
    alertas = gerar_todos_alertas(df)
    projecao = projetar_proximo_mes(df)

    st.markdown("### Alertas & Projeções")

    # Card de projeção do próximo mês
    cor_projecao = "#E74C3C" if projecao["variacao_pct"] > 10 else AWS_ORANGE
    sinal = "+" if projecao["variacao_pct"] >= 0 else ""

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {BG_CARD} 0%, #1F2937 100%);
            border-left: 3px solid {cor_projecao};
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 16px;
        ">
            <div style="
                font-size: 11px;
                color: {TEXT_MUTED};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 600;
                margin-bottom: 6px;
            ">
                Projeção · Próximos 30 dias
            </div>
            <div style="display: flex; align-items: baseline; gap: 16px;">
                <div style="font-size: 26px; font-weight: 700; color: #FFFFFF;">
                    ${projecao['total_previsto']:,.0f}
                </div>
                <div style="font-size: 14px; color: {cor_projecao}; font-weight: 600;">
                    {sinal}{projecao['variacao_pct']:.1f}% vs últimos 30 dias
                </div>
            </div>
            <div style="font-size: 12px; color: {TEXT_MUTED}; margin-top: 4px;">
                Baseado em regressão linear sobre a tendência atual
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Alertas detectados
    if not alertas:
        st.markdown(
            f"""
            <div style="
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 16px 20px;
                color: {TEXT_MUTED};
                font-size: 13px;
            ">
                Nenhum alerta crítico detectado no período.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for alerta in alertas[:5]:  # Top 5 alertas
        if alerta["tipo"] == "Serviço em alta":
            titulo = f"{alerta['servico']} cresceu {alerta['variacao_pct']}%"
            descricao = f"De ${alerta['gasto_anterior']:,.2f} para ${alerta['gasto_atual']:,.2f} no último mês"
            cor = "#E74C3C"
        else:  # Recurso outlier
            titulo = f"{alerta['recurso_id']} ({alerta['servico']})"
            descricao = f"Gasto de ${alerta['gasto']:,.2f} — média do serviço: ${alerta['media_servico']:,.2f}"
            cor = AWS_ORANGE

        st.markdown(
            f"""
            <div style="
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-left: 3px solid {cor};
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 8px;
            ">
                <div style="
                    font-size: 10px;
                    color: {cor};
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    font-weight: 600;
                    margin-bottom: 4px;
                ">
                    {alerta['tipo']}
                </div>
                <div style="font-size: 14px; font-weight: 600; color: #FFFFFF; margin-bottom: 2px;">
                    {titulo}
                </div>
                <div style="font-size: 12px; color: {TEXT_MUTED};">
                    {descricao}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------- Main ----------

def main():
    df = carregar_dados()
    df_mensal = carregar_mensal()

    servico, regiao, intervalo = renderizar_topbar(df)
    df_filtrado = aplicar_filtros(df.copy(), servico, regiao, intervalo)

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    renderizar_kpis(df_filtrado, df_mensal)

    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1], gap="medium")
    with col1:
        grafico_evolucao_mensal(df_mensal)
    with col2:
        grafico_distribuicao_servico(df_filtrado)

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    # Nova linha: tendência+forecast (esquerda) + alertas (direita)
    col3, col4 = st.columns([2, 1], gap="medium")
    with col3:
        grafico_tendencia_diaria(df_filtrado)
    with col4:
        renderizar_alertas(df_filtrado)

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    col5, col6 = st.columns([1, 2], gap="medium")
    with col5:
        grafico_regiao(df_filtrado)
    with col6:
        tabela_top_recursos(df_filtrado)


if __name__ == "__main__":
    main()