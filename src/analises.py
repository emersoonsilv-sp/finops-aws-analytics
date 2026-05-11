"""
Análises de gasto AWS sobre os dados ingeridos.

Responde 5 perguntas de negócio usando SQL + Pandas:
1. Evolução de gasto mês a mês
2. Ranking de gasto por região
3. Top 10 recursos mais caros
4. Gasto médio por dia da semana (validar sazonalidade)
5. Variação percentual mês a mês
"""

import sqlite3
from pathlib import Path

import pandas as pd

ARQUIVO_BANCO = Path("data") / "finops.db"

def conectar() -> sqlite3.Connection:
    if not ARQUIVO_BANCO.exists():
        raise FileNotFoundError(
            f"Banco não encontrado em {ARQUIVO_BANCO}. "
            "Rode antes: python src/ingestao.py"
        )
    return sqlite3.connect(ARQUIVO_BANCO)

def analise_1_evolucao_mensal(conexao: sqlite3.Connection) -> pd.DataFrame:
    """
    Quanto foi gasto em cada mês?
    Nota: o primeiro mês pode estar incompleto (dados começam no meio do mês).
    Filtramos meses com menos de 20 dias de dados pra evitar distorção.
    """
    query = """
        SELECT
            strftime('%Y-%m', data) AS mes,
            ROUND(SUM(custo_usd), 2) AS gasto_total,
            COUNT(DISTINCT data) AS dias_com_dados
        FROM faturas
        GROUP BY mes
        ORDER BY mes
    """
    df = pd.read_sql_query(query, conexao)

    # Meses com menos de 20 dias de dados são considerados incompletos
    df_completo = df[df["dias_com_dados"] >= 20].copy()
    meses_removidos = df[df["dias_com_dados"] < 20]

    if not meses_removidos.empty:
        print(f"\n⚠️  Meses removidos por dados insuficientes:")
        print(meses_removidos.to_string(index=False))

    print("\n=== 1. Evolução de gasto mês a mês (meses completos) ===")
    print(df_completo[["mes", "gasto_total", "dias_com_dados"]].to_string(index=False))
    return df_completo

def analise_2_ranking_regiao(conexao: sqlite3.Connection) -> pd.DataFrame:
    """Qual região concentra mais gasto?"""
    query = """
        SELECT
            regiao,
            ROUND(SUM(custo_usd), 2) AS gasto_total,
            COUNT(*) AS qtd_lancamentos
        FROM faturas
        GROUP BY regiao
        ORDER BY gasto_total DESC
    """
    df = pd.read_sql_query(query, conexao)

    # Adiciona coluna com percentual do total (calculado em Pandas)
    total = df["gasto_total"].sum()
    df["pct_do_total"] = (df["gasto_total"] / total * 100).round(1)

    print("\n=== 2. Ranking de gasto por região ===")
    print(df.to_string(index=False))
    return df

def analise_3_top_recursos(conexao: sqlite3.Connection) -> pd.DataFrame:
    """Quais são os 10 recursos individuais com maior gasto acumulado?"""
    query = """
        SELECT
            recurso_id,
            servico,
            regiao,
            ROUND(SUM(custo_usd), 2) AS gasto_total
        FROM faturas
        GROUP BY recurso_id, servico, regiao
        ORDER BY gasto_total DESC
        LIMIT 10
    """
    df = pd.read_sql_query(query, conexao)

    print("\n=== 3. Top 10 recursos mais caros ===")
    print(df.to_string(index=False))
    return df

def analise_4_dia_da_semana(conexao: sqlite3.Connection) -> pd.DataFrame:
    """Confirma a hipótese: fim de semana tem gasto menor?"""
    query = """
        SELECT
            CASE strftime('%w', data)
                WHEN '0' THEN '0-Domingo'
                WHEN '1' THEN '1-Segunda'
                WHEN '2' THEN '2-Terça'
                WHEN '3' THEN '3-Quarta'
                WHEN '4' THEN '4-Quinta'
                WHEN '5' THEN '5-Sexta'
                WHEN '6' THEN '6-Sábado'
            END AS dia_semana,
            ROUND(AVG(custo_usd), 2) AS gasto_medio,
            COUNT(*) AS qtd_lancamentos
        FROM faturas
        GROUP BY dia_semana
        ORDER BY dia_semana
    """
    df = pd.read_sql_query(query, conexao)

    print("\n=== 4. Gasto médio por dia da semana ===")
    print(df.to_string(index=False))
    return df

def analise_5_variacao_mensal(conexao: sqlite3.Connection) -> pd.DataFrame:
    """
    Variação percentual mês a mês — apenas meses completos.
    """
    query = """
        SELECT
            strftime('%Y-%m', data) AS mes,
            ROUND(SUM(custo_usd), 2) AS gasto_total,
            COUNT(DISTINCT data) AS dias_com_dados
        FROM faturas
        GROUP BY mes
        ORDER BY mes
    """
    df = pd.read_sql_query(query, conexao)
    df = df[df["dias_com_dados"] >= 20].copy()

    df["variacao_pct"] = df["gasto_total"].pct_change() * 100
    df["variacao_pct"] = df["variacao_pct"].round(2)

    print("\n=== 5. Variação percentual mês a mês (meses completos) ===")
    print(df[["mes", "gasto_total", "variacao_pct"]].to_string(index=False))
    return df

def main():
    """Executa todas as análises em sequência."""
    conexao = conectar()
    try:
        analise_1_evolucao_mensal(conexao)
        analise_2_ranking_regiao(conexao)
        analise_3_top_recursos(conexao)
        analise_4_dia_da_semana(conexao)
        analise_5_variacao_mensal(conexao)
    finally:
        conexao.close()


if __name__ == "__main__":
    main()