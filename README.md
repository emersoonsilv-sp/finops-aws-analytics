# FinOps AWS Analytics

Pipeline de análise de custos AWS com ingestão, análise, forecast e dashboard.
Projeto didático/de portfólio usando dados sintéticos.

## Stack
- Python 3
- Pandas (manipulação de dados)
- Faker (geração de dados mockados)
- SQLite (em breve)
- Streamlit (em breve)

## Status
🚧 Em desenvolvimento
- ✅ Fase 0 — Setup do projeto
- ✅ Fase 1 — Geração de dados mockados
- ⬜ Fase 2 — Ingestão pro banco SQLite
- ⬜ Fase 3 — Análises de gasto
- ⬜ Fase 4 — Dashboard executivo
- ⬜ Fase 5 — Forecast e alertas
- ⬜ Fase 6 — Empacotamento (Docker)

## Como rodar

### Pré-requisitos
- Python 3.10+
- Git

### Setup
```bash
# Clonar o repositório
git clone https://github.com/SEU-USUARIO/finops-aws-analytics.git
cd finops-aws-analytics

# Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### Gerar dados mockados
```bash
python src/gerar_dados.py
```
Isso cria `data/faturas_aws.csv` com 90 dias de fatura simulada de uma empresa fictícia.