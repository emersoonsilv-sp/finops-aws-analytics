"""
Módulo de previsão de gastos AWS.
Usa regressão linear simples sobre série temporal diária.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega gastos por dia e prepara features pro modelo.

    Features de entrada (X):
        - dias_desde_inicio: número sequencial (0, 1, 2, ...)
    Target (y):
        - gasto_total do dia
    """
    diario = df.groupby("data")["custo_usd"].sum().reset_index()
    diario.columns = ["data", "gasto_total"]
    diario = diario.sort_values("data").reset_index(drop=True)

    # Feature: dias decorridos desde o primeiro registro
    diario["dias_desde_inicio"] = (
        diario["data"] - diario["data"].min()
    ).dt.days

    return diario


def treinar_modelo(diario: pd.DataFrame) -> LinearRegression:
    """Treina regressão linear: gasto = a * dias + b."""
    X = diario[["dias_desde_inicio"]].values
    y = diario["gasto_total"].values

    modelo = LinearRegression()
    modelo.fit(X, y)
    return modelo


def prever_proximos_dias(
    df: pd.DataFrame,
    dias_a_prever: int = 30,
) -> pd.DataFrame:
    """
    Retorna DataFrame com previsão dos próximos N dias.
    Colunas: data, gasto_previsto
    """
    diario = preparar_dados(df)
    modelo = treinar_modelo(diario)

    ultimo_dia = diario["dias_desde_inicio"].max()
    ultima_data = diario["data"].max()

    # Gera os próximos N dias
    futuros_dias = np.arange(
        ultimo_dia + 1,
        ultimo_dia + 1 + dias_a_prever,
    ).reshape(-1, 1)

    previsoes = modelo.predict(futuros_dias)

    # Garante que previsões não sejam negativas (custo não pode ser negativo)
    previsoes = np.clip(previsoes, 0, None)

    df_previsao = pd.DataFrame({
        "data": [ultima_data + timedelta(days=i) for i in range(1, dias_a_prever + 1)],
        "gasto_previsto": previsoes,
    })

    return df_previsao


def projetar_proximo_mes(df: pd.DataFrame) -> dict:
    """
    Projeta o gasto total dos próximos 30 dias.
    Retorna dicionário com total previsto e comparação com último mês.
    """
    previsao = prever_proximos_dias(df, dias_a_prever=30)
    total_previsto = previsao["gasto_previsto"].sum()

    # Compara com últimos 30 dias reais
    diario = preparar_dados(df)
    ultimos_30 = diario.tail(30)["gasto_total"].sum()

    variacao_pct = ((total_previsto - ultimos_30) / ultimos_30) * 100

    return {
        "total_previsto": total_previsto,
        "ultimos_30_dias": ultimos_30,
        "variacao_pct": variacao_pct,
    }