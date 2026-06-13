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

  echo "==> [DAST] Executando OWASP ZAP Baseline Scan via container..."
  container_id=$(docker create --rm \
    --network taskguard_taskguard-net \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py -t "http://taskguard-web:8000" -c rules.tsv -r zap-report.html -J zap-report.json -I)

  if [ -f "pipeline/zap/rules.tsv" ]; then
    docker cp "pipeline/zap/rules.tsv" "$container_id:/zap/wrk/rules.tsv"
  fi

  docker start -a "$container_id" || true
  docker cp "$container_id:/zap/wrk/zap-report.html" "${REPORTS_DIR}/" || true
  docker cp "$container_id:/zap/wrk/zap-report.json" "${REPORTS_DIR}/" || true
else
  echo "==> [DAST] Escaneando alvo externo: ${TARGET}"
  container_id=$(docker create --rm \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py -t "${TARGET}" -r zap-report.html -J zap-report.json -I)
  docker start -a "$container_id" || true
  docker cp "$container_id:/zap/wrk/zap-report.html" "${REPORTS_DIR}/" || true
  docker cp "$container_id:/zap/wrk/zap-report.json" "${REPORTS_DIR}/" || true
fi

echo "==> [DAST] Scan concluído. Relatório em ${REPORTS_DIR}/zap-report.html"
