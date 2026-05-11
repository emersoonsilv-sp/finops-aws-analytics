"""
Sistema de detecção de alertas sobre gastos AWS.
"""

import pandas as pd


def alerta_servico_em_alta(df: pd.DataFrame, threshold_pct: float = 20.0) -> list[dict]:
    """
    Detecta serviços cujo gasto cresceu mais que threshold_pct
    no último mês comparado ao mês anterior.
    """
    df = df.copy()
    df["mes"] = df["data"].dt.to_period("M").astype(str)

    # Soma por mês e serviço
    mensal = (
        df.groupby(["mes", "servico"])["custo_usd"]
        .sum()
        .reset_index()
    )

    # Mantém apenas os 2 últimos meses
    meses_ordenados = sorted(mensal["mes"].unique())
    if len(meses_ordenados) < 2:
        return []

    mes_atual = meses_ordenados[-1]
    mes_anterior = meses_ordenados[-2]

    atual = mensal[mensal["mes"] == mes_atual].set_index("servico")["custo_usd"]
    anterior = mensal[mensal["mes"] == mes_anterior].set_index("servico")["custo_usd"]

    alertas = []
    for servico in atual.index:
        if servico in anterior.index and anterior[servico] > 0:
            variacao = ((atual[servico] - anterior[servico]) / anterior[servico]) * 100
            if variacao >= threshold_pct:
                alertas.append({
                    "tipo": "Serviço em alta",
                    "servico": servico,
                    "variacao_pct": round(variacao, 1),
                    "gasto_anterior": round(anterior[servico], 2),
                    "gasto_atual": round(atual[servico], 2),
                })

    return sorted(alertas, key=lambda x: x["variacao_pct"], reverse=True)


def alerta_recursos_outliers(df: pd.DataFrame, top_n: int = 3) -> list[dict]:
    """
    Identifica os top N recursos com gasto muito acima da média do serviço.
    Critério: gasto > média + 2 * desvio padrão (dentro do mesmo serviço).
    """
    por_recurso = (
        df.groupby(["recurso_id", "servico"])["custo_usd"]
        .sum()
        .reset_index()
    )

    alertas = []
    for servico in por_recurso["servico"].unique():
        subset = por_recurso[por_recurso["servico"] == servico]
        if len(subset) < 3:
            continue

        media = subset["custo_usd"].mean()
        desvio = subset["custo_usd"].std()
        threshold = media + 2 * desvio

        outliers = subset[subset["custo_usd"] > threshold]
        for _, row in outliers.iterrows():
            alertas.append({
                "tipo": "Recurso outlier",
                "recurso_id": row["recurso_id"],
                "servico": row["servico"],
                "gasto": round(row["custo_usd"], 2),
                "media_servico": round(media, 2),
            })

    # Retorna os top N mais críticos
    return sorted(alertas, key=lambda x: x["gasto"], reverse=True)[:top_n]


def gerar_todos_alertas(df: pd.DataFrame) -> list[dict]:
    """Combina todos os tipos de alerta."""
    return alerta_servico_em_alta(df) + alerta_recursos_outliers(df)