#!/usr/bin/env bash
# ============================================================================
# run_dast.sh — Teste Dinâmico de Segurança (DAST) com OWASP ZAP.
#
# Sobe a aplicação via docker compose, aguarda o health check e executa o
# ZAP Baseline Scan (varredura passiva) contra a instância em execução.
# Gera relatório HTML/JSON. Pensado tanto para uso local quanto na pipeline.
#
# Uso:
#   ./scripts/run_dast.sh                 # sobe tudo, escaneia e derruba
#   TARGET=http://localhost:8000 ./scripts/run_dast.sh --no-compose
# ============================================================================
set -euo pipefail

REPORTS_DIR="${REPORTS_DIR:-reports}"
ZAP_WORK="pipeline/zap"
TARGET="${TARGET:-http://web:8000}"
USE_COMPOSE=true

[[ "${1:-}" == "--no-compose" ]] && USE_COMPOSE=false

mkdir -p "$REPORTS_DIR" "$ZAP_WORK"

cleanup() {
  if [[ "$USE_COMPOSE" == true ]]; then
    echo "==> [DAST] Derrubando containers..."
    docker compose down -v || true
  fi
}
trap cleanup EXIT

if [[ "$USE_COMPOSE" == true ]]; then
  echo "==> [DAST] Subindo a aplicação..."
  docker compose up -d --build web

  echo "==> [DAST] Aguardando health check ficar saudável..."
  for i in $(seq 1 30); do
    status=$(docker inspect --format '{{.State.Health.Status}}' taskguard-web 2>/dev/null || echo "starting")
    if [[ "$status" == "healthy" ]]; then
      echo "    aplicação saudável."
      break
    fi
    sleep 3
  done

  echo "==> [DAST] Executando OWASP ZAP Baseline Scan via compose..."
  docker compose --profile security run --rm zap || true
  # Move os relatórios gerados em pipeline/zap para reports/.
  cp -f "${ZAP_WORK}/zap-report.html" "${REPORTS_DIR}/" 2>/dev/null || true
  cp -f "${ZAP_WORK}/zap-report.json" "${REPORTS_DIR}/" 2>/dev/null || true
else
  echo "==> [DAST] Escaneando alvo externo: ${TARGET}"
  docker run --rm -v "$(pwd)/${REPORTS_DIR}:/zap/wrk:rw" \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py -t "${TARGET}" -r zap-report.html -J zap-report.json -I || true
fi

echo "==> [DAST] Scan concluído. Relatório em ${REPORTS_DIR}/zap-report.html"
