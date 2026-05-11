# ---------- Imagem base ----------
FROM python:3.12-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto
COPY src/ ./src/
COPY assets/ ./assets/

# Cria pasta de dados (será populada no entrypoint)
RUN mkdir -p /app/data

# Script de inicialização: gera dados → ingere → roda dashboard
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Porta exposta
EXPOSE 8501

# Healthcheck (Docker verifica se a aplicação está respondendo)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando padrão
ENTRYPOINT ["./docker-entrypoint.sh"]