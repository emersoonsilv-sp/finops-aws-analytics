"""
Ingestão dos dados de fatura do CSV para o banco SQLite.

Lê data/faturas_aws.csv, cria o banco data/finops.db (se não existir),
cria a tabela 'faturas' (sempre do zero) e insere todos os registros.
"""

import csv
import sqlite3
from pathlib import Path

# ---------- Configurações ----------

ARQUIVO_CSV = Path("data") / "faturas_aws.csv"
ARQUIVO_BANCO = Path("data") / "finops.db"


# ---------- Funções ----------

def criar_tabela(conexao: sqlite3.Connection) -> None:
    """
    Cria a tabela 'faturas' do zero.
    Se já existir, apaga e recria — ingestão idempotente.
    """
    cursor = conexao.cursor()

    # Apaga a tabela se já existir (pra rodar o script múltiplas vezes sem duplicar)
    cursor.execute("DROP TABLE IF EXISTS faturas")

    # Cria a tabela com schema definido
    cursor.execute("""
        CREATE TABLE faturas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            data        DATE    NOT NULL,
            servico     TEXT    NOT NULL,
            regiao      TEXT    NOT NULL,
            recurso_id  TEXT    NOT NULL,
            custo_usd   REAL    NOT NULL
        )
    """)

    conexao.commit()
    print("Tabela 'faturas' criada.")


def inserir_dados(conexao: sqlite3.Connection, caminho_csv: Path) -> int:
    """
    Lê o CSV linha a linha e insere no banco.
    Retorna a quantidade de linhas inseridas.
    """
    cursor = conexao.cursor()

    with open(caminho_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        linhas = list(reader)

    # Insere em lote (mais rápido que linha a linha)
    cursor.executemany("""
        INSERT INTO faturas (data, servico, regiao, recurso_id, custo_usd)
        VALUES (:data, :servico, :regiao, :recurso_id, :custo_usd)
    """, linhas)

    conexao.commit()
    return len(linhas)


def verificar_ingestao(conexao: sqlite3.Connection) -> None:
    """Conta as linhas e mostra uma amostra pra confirmar que deu certo."""
    cursor = conexao.cursor()

    cursor.execute("SELECT COUNT(*) FROM faturas")
    total = cursor.fetchone()[0]
    print(f"\nTotal de linhas no banco: {total}")

    cursor.execute("SELECT * FROM faturas LIMIT 3")
    print("\nAmostra das 3 primeiras linhas:")
    for linha in cursor.fetchall():
        print(f"  {linha}")


def main():
    """Orquestra a ingestão completa."""
    if not ARQUIVO_CSV.exists():
        print(f"❌ Arquivo {ARQUIVO_CSV} não existe. Rode primeiro: python src/gerar_dados.py")
        return

    # Garante que a pasta data/ existe
    ARQUIVO_BANCO.parent.mkdir(parents=True, exist_ok=True)

    print(f"Conectando ao banco {ARQUIVO_BANCO}...")
    conexao = sqlite3.connect(ARQUIVO_BANCO)

    try:
        criar_tabela(conexao)
        qtd = inserir_dados(conexao, ARQUIVO_CSV)
        print(f"✅ {qtd} linhas inseridas.")
        verificar_ingestao(conexao)
    finally:
        conexao.close()
        print("\nConexão fechada.")


if __name__ == "__main__":
    main()