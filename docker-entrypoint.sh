#!/bin/sh
set -e

echo "================================"
echo "  FinOps AWS Analytics - Setup"
echo "================================"

# Se o banco não existe, gera dados e ingere
if [ ! -f /app/data/finops.db ]; then
    echo "[1/2] Gerando dados sintéticos..."
    python src/gerar_dados.py

    echo "[2/2] Ingerindo dados no banco..."
    python src/ingestao.py
else
    echo "Banco já existe, pulando geração de dados."
fi

echo ""
echo "Iniciando dashboard em http://localhost:8501"
echo ""

exec streamlit run src/dashboard.py