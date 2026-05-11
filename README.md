# FinOps AWS Analytics

> Pipeline completo de análise de custos AWS com ingestão automatizada, forecast por regressão linear e detecção de outliers.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green.svg)

![Dashboard Preview](assets/screenshot.png)

---

## Visão Geral

**FinOps AWS Analytics** é uma aplicação de análise financeira para custos de nuvem AWS. O projeto simula o pipeline completo que uma empresa real construiria internamente para monitorar gastos com cloud: ingestão de faturas, modelagem em banco relacional, análises descritivas e preditivas, e dashboard executivo interativo.

Os dados são **sintéticos**, gerados com padrões realistas (sazonalidade semanal, distribuição típica de gastos por serviço AWS, recursos persistentes ao longo do tempo).

## Features

**Análise Descritiva**
- KPIs consolidados: total no período, média diária, serviço dominante, variação mensal
- Evolução mensal de gastos com filtro automático de meses parciais
- Distribuição de custos por serviço e região AWS
- Tendência diária com 90 dias de histórico

**Análise Preditiva**
- Forecast de 30 dias via regressão linear sobre série temporal
- Projeção orçamentária com comparação vs último mês real

**Detecção Automática de Anomalias**
- Alertas para serviços com crescimento acima de 20% mês a mês
- Identificação de recursos outliers (gasto acima de média + 2 desvios padrão dentro do serviço)

**Interatividade**
- Filtros dinâmicos por serviço, região e período
- Cache de dados em memória para performance
- Gráficos interativos (hover, zoom, download) via Plotly

## Quick Start

### Opção 1 — Docker (recomendado)

Pré-requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado.

~~~bash
git clone https://github.com/emersoonsilv-sp/finops-aws-analytics.git
cd finops-aws-analytics
docker compose up
~~~

Acesse [http://localhost:8501](http://localhost:8501) no navegador.

Na primeira execução, o container gera dados sintéticos automaticamente. Nas próximas, reutiliza o banco persistido em volume Docker.

### Opção 2 — Execução local

Pré-requisitos: Python 3.10+ e Git.

~~~bash
git clone https://github.com/emersoonsilv-sp/finops-aws-analytics.git
cd finops-aws-analytics

# Ambiente virtual
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # Linux/Mac

# Dependências
pip install -r requirements.txt

# Pipeline: gerar dados, ingerir, abrir dashboard
python src/gerar_dados.py
python src/ingestao.py
streamlit run src/dashboard.py
~~~

## Arquitetura

~~~
gerar_dados.py  ──▶  faturas_aws.csv  ──▶  ingestao.py
                     (90 dias,                  │
                      5040 linhas)              ▼
                                          finops.db
                                          (SQLite)
                                                │
                              ┌─────────────────┴─────────────────┐
                              ▼                                   ▼
                      analises.py                          dashboard.py
                      (CLI reports)                        (Streamlit UI)
                                                                  │
                                                                  ▼
                                                          forecast.py
                                                          alertas.py
~~~

## Stack Técnica

| Camada | Tecnologia | Razão |
|---|---|---|
| Linguagem | Python 3.12 | Padrão da indústria para data engineering |
| Banco de dados | SQLite | Zero-config, embedded, ideal para projeto auto-contido |
| Manipulação de dados | Pandas | Padrão para ETL e análise tabular em Python |
| ML / Forecast | scikit-learn | Regressão linear sobre série temporal |
| Visualização | Streamlit + Plotly | Dashboards interativos em Python puro |
| Geração de dados | Faker | Dados sintéticos realistas |
| Containerização | Docker + Compose | Portabilidade e reprodutibilidade |
| Versionamento | Git + Conventional Commits | Histórico semântico e auditável |

## Estrutura do Projeto

~~~
finops-aws-analytics/
├── src/
│   ├── gerar_dados.py     # Gera CSV sintético com padrões realistas
│   ├── ingestao.py        # Carrega CSV no SQLite
│   ├── analises.py        # 5 análises SQL + Pandas (CLI)
│   ├── forecast.py        # Modelo de regressão linear
│   ├── alertas.py         # Detecção de outliers e crescimento anômalo
│   └── dashboard.py       # Interface Streamlit
├── assets/
│   ├── aws-color.svg      # Logo
│   └── screenshot.png     # Preview do dashboard
├── data/                  # Gerada em runtime (gitignored)
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── requirements.txt
└── README.md
~~~

## Decisões de Design

**Por que dados sintéticos?**
O objetivo é demonstrar o pipeline e a análise, não a coleta real de billing AWS. Dados sintéticos com sazonalidade e padrões realistas permitem foco na engenharia, são reproduzíveis e não dependem de conta AWS ativa.

**Por que SQLite e não PostgreSQL?**
Para um projeto auto-contido, SQLite elimina dependência de banco externo sem perder poder analítico. O SQL escrito é majoritariamente compatível com PostgreSQL — migração é trivial.

**Por que filtrar meses incompletos nas análises temporais?**
Comparar um mês parcial (ex: 4 dias) com meses completos gera variações artificiais que distorcem a interpretação. A análise descarta automaticamente meses com menos de 20 dias de dados.

**Por que regressão linear simples no forecast?**
Para séries de 90 dias com tendência linear, modelos mais complexos (Prophet, ARIMA) não trazem ganho proporcional à complexidade adicionada. Linear é interpretável, rápido e suficiente para o horizonte de 30 dias.

## Próximos Passos

- [ ] Integração real com AWS Cost Explorer API
- [ ] Modelagem dimensional (star schema) para análises OLAP
- [ ] Forecast com Prophet para sazonalidade complexa
- [ ] Autenticação multi-tenant
- [ ] Migração SQLite para PostgreSQL
- [ ] CI/CD com GitHub Actions
- [ ] Deploy em Streamlit Community Cloud ou Render

## Licença

MIT. Sinta-se à vontade para usar como referência ou base para projetos próprios.

---

**Autor:** Emerson Silva
**Repositório:** [github.com/emersoonsilv-sp/finops-aws-analytics](https://github.com/emersoonsilv-sp/finops-aws-analytics)