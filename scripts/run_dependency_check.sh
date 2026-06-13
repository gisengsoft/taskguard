#!/usr/bin/env bash
# ============================================================================
# run_dependency_check.sh — Análise de Composição de Software (SCA).
#
# Usa o OWASP Dependency-Check para cruzar as dependências declaradas em
# requirements*.txt com a base de vulnerabilidades conhecidas (NVD/CVE).
#
# Roda via container Docker oficial (não exige Java instalado no host).
# Falha a pipeline quando encontra CVE com CVSS >= 7 (--failOnCVSS 7).
# ============================================================================
set -euo pipefail

REPORTS_DIR="${REPORTS_DIR:-reports}"
DC_IMAGE="owasp/dependency-check:latest"
PROJECT_NAME="TaskGuard"
WORKDIR="$(pwd)"
FAIL_ON_CVSS="${FAIL_ON_CVSS:-7}"

mkdir -p "$REPORTS_DIR" "$HOME/.dependency-check-data"

echo "==> [SCA] OWASP Dependency-Check em '$PROJECT_NAME' (gate CVSS >= $FAIL_ON_CVSS)..."

# A flag NVD_API_KEY (opcional) acelera muito o download da base de CVEs.
NVD_ARG=""
if [[ -n "${NVD_API_KEY:-}" ]]; then
  NVD_ARG="--nvdApiKey ${NVD_API_KEY}"
fi

docker run --rm \
  -v "${WORKDIR}:/src:ro" \
  -v "${REPORTS_DIR}:/report:rw" \
  -v "${HOME}/.dependency-check-data:/usr/share/dependency-check/data:rw" \
  "${DC_IMAGE}" \
  --scan /src \
  --project "${PROJECT_NAME}" \
  --format "HTML" \
  --format "JSON" \
  --format "SARIF" \
  --out /report \
  --failOnCVSS "${FAIL_ON_CVSS}" \
  --enableExperimental \
  ${NVD_ARG}

echo "==> [SCA] Nenhuma dependência com CVSS >= ${FAIL_ON_CVSS}. Relatórios em ${REPORTS_DIR}/."
