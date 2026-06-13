# ============================================================================
# TaskGuard — Dockerfile multi-stage
# Estágio 1 (builder): instala dependências numa virtualenv isolada.
# Estágio 2 (runtime): imagem final enxuta, sem ferramentas de build,
#                      rodando como usuário NÃO-root sob Gunicorn.
# ============================================================================

# --------------------------------------------------------------------------- #
# Estágio 1 — Builder
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS builder

# Boas práticas: não gerar .pyc, não bufferizar stdout, pip sem cache.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Cria a virtualenv que será copiada para o runtime.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instala apenas as dependências de produção (camada cacheável).
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --------------------------------------------------------------------------- #
# Estágio 2 — Runtime
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="TaskGuard" \
      org.opencontainers.image.description="Gerenciador seguro de tarefas (DevSecOps)" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_CONFIG=production \
    APP_PORT=8000

# curl é usado pelo HEALTHCHECK; instalado e limpo na mesma camada.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Usuário sem privilégios (princípio do menor privilégio).
RUN groupadd --gid 1000 taskguard \
    && useradd --uid 1000 --gid taskguard --shell /bin/bash --create-home taskguard

WORKDIR /app

# Copia a virtualenv pronta do builder.
COPY --from=builder /opt/venv /opt/venv

# Copia o código da aplicação.
COPY --chown=taskguard:taskguard . /app

# Diretório de logs gravável pelo usuário não-root.
RUN mkdir -p /app/logs && chown -R taskguard:taskguard /app/logs

USER taskguard

EXPOSE 8000

# Verificação de saúde: consulta o endpoint /health a cada 30s.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS "http://localhost:${APP_PORT}/health" || exit 1

# Servidor WSGI de produção. 3 workers + 2 threads é um ponto de partida
# razoável; ajuste conforme CPU disponível.
CMD ["gunicorn", "run:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--threads", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
