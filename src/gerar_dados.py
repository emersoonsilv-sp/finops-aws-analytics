"""
Gerador de dados mockados de fatura AWS.

Cria um CSV simulando 3 meses de gastos de uma empresa fictícia,
com padrões realistas: serviços com custos diferentes, sazonalidade
semanal (mais uso em dia útil), e variação aleatória.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

# ---------- Configurações ----------

# Quantos dias de histórico gerar (3 meses ≈ 90 dias)
DIAS_DE_HISTORICO = 90

# Data final da fatura (hoje)
DATA_FINAL = date.today()

# Onde salvar o arquivo gerado
ARQUIVO_SAIDA = Path("data") / "faturas_aws.csv"

# Serviços AWS e faixas de custo diário típico (em USD)
# Valores baseados em padrões realistas, mas ficcionais
SERVICOS = {
    "EC2":          {"custo_min": 5.00,  "custo_max": 80.00, "qtd_recursos": 15},
    "S3":           {"custo_min": 0.50,  "custo_max": 12.00, "qtd_recursos": 8},
    "RDS":          {"custo_min": 10.00, "custo_max": 120.00,"qtd_recursos": 4},
    "Lambda":       {"custo_min": 0.10,  "custo_max": 5.00,  "qtd_recursos": 20},
    "CloudWatch":   {"custo_min": 0.20,  "custo_max": 8.00,  "qtd_recursos": 6},
    "DataTransfer":{"custo_min": 1.00,  "custo_max": 25.00, "qtd_recursos": 3},
}

# Regiões AWS comuns
REGIOES = ["us-east-1", "us-west-2", "sa-east-1", "eu-west-1"]


# ---------- Funções ----------

def gerar_id_recurso(servico: str, faker: Faker) -> str:
    """Gera um ID de recurso AWS com formato plausível por serviço."""
    if servico == "EC2":
        return f"i-{faker.hexify(text='^^^^^^^^^^^^')}"
    if servico == "S3":
        return f"bucket-{faker.word()}-{faker.random_int(min=100, max=999)}"
    if servico == "RDS":
        return f"db-{faker.word()}"
    if servico == "Lambda":
        return f"fn-{faker.word()}-{faker.word()}"
    if servico == "CloudWatch":
        return f"log-group-{faker.word()}"
    return f"transfer-{faker.word()}"


def gerar_recursos_fixos(faker: Faker) -> list[dict]:
    """
    Gera a lista de recursos da empresa fictícia.
    Cada recurso tem serviço, região e ID fixos — eles aparecem em
    vários dias da fatura, como na vida real.
    """
    recursos = []
    for servico, config in SERVICOS.items():
        for _ in range(config["qtd_recursos"]):
            recursos.append({
                "servico": servico,
                "regiao": random.choice(REGIOES),
                "recurso_id": gerar_id_recurso(servico, faker),
                "custo_min": config["custo_min"],
                "custo_max": config["custo_max"],
            })
    return recursos


def calcular_custo_diario(recurso: dict, dia: date) -> float:
    """
    Calcula o custo de um recurso num dia específico.
    Aplica sazonalidade: fim de semana custa ~30% menos (menos uso).
    """
    custo_base = random.uniform(recurso["custo_min"], recurso["custo_max"])

    # Fim de semana (5=sábado, 6=domingo) → desconto de uso
    if dia.weekday() >= 5:
        custo_base *= 0.7

    # Adiciona um ruído aleatório de ±15% pra não ficar artificial
    ruido = random.uniform(0.85, 1.15)
    return round(custo_base * ruido, 2)


def gerar_fatura():
    """Função principal: orquestra a geração e salva o CSV."""
    faker = Faker()
    Faker.seed(42)         # reprodutibilidade: sempre gera os mesmos dados
    random.seed(42)

    print("Gerando recursos da empresa fictícia...")
    recursos = gerar_recursos_fixos(faker)
    print(f"  → {len(recursos)} recursos criados")

    print(f"Gerando {DIAS_DE_HISTORICO} dias de fatura...")
    linhas = []
    for offset in range(DIAS_DE_HISTORICO):
        dia = DATA_FINAL - timedelta(days=offset)
        for recurso in recursos:
            linhas.append({
                "data": dia.isoformat(),
                "servico": recurso["servico"],
                "regiao": recurso["regiao"],
                "recurso_id": recurso["recurso_id"],
                "custo_usd": calcular_custo_diario(recurso, dia),
            })

    # Garante que a pasta data/ existe
    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)

    print(f"Salvando em {ARQUIVO_SAIDA}...")
    with open(ARQUIVO_SAIDA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=linhas[0].keys())
        writer.writeheader()
        writer.writerows(linhas)

    print(f"✅ Pronto! {len(linhas)} linhas geradas.")


if __name__ == "__main__":
    gerar_fatura()