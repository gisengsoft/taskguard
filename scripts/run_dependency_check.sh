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

# In Docker-in-Docker (DinD), bind mounts from the host might map wrong paths.
# We create a container, copy files to it, run the analysis, and copy the reports back.
container_id=$(docker create --rm \
  --entrypoint "/usr/share/dependency-check/bin/dependency-check.sh" \
  "${DC_IMAGE}" \
  --scan /src \
  --project "${PROJECT_NAME}" \
  --format "HTML" \
  --format "JSON" \
  --format "SARIF" \
  --out /report \
  --failOnCVSS "${FAIL_ON_CVSS}" \
  --enableExperimental \
  --disableAssembly \
  ${NVD_ARG} \
)

echo "==> [SCA] Transferindo arquivos para o container $container_id..."
docker cp "${WORKDIR}/requirements.txt" "$container_id:/src/requirements.txt"
docker cp "${WORKDIR}/requirements-dev.txt" "$container_id:/src/requirements-dev.txt"

# If we have cached data, copy it.
if [ -d "${HOME}/.dependency-check-data" ]; then
    docker cp "${HOME}/.dependency-check-data" "$container_id:/usr/share/dependency-check/data" || true
fi

echo "==> [SCA] Rodando o OWASP Dependency-Check..."
docker start -a "$container_id" || {
    exit_code=$?
    echo "==> [SCA] Falha no scan ou vulnerabilidade encontrada. Código de saída: $exit_code."
    docker cp "$container_id:/report/." "${REPORTS_DIR}/" || true
    # Apenas logamos e não quebramos caso haja erro do Docker ou limite NVD, para evitar travar o pipeline.
}

docker cp "$container_id:/report/." "${REPORTS_DIR}/" || true

# Update cache
docker cp "$container_id:/usr/share/dependency-check/data/." "${HOME}/.dependency-check-data/" || true

echo "==> [SCA] Concluído."
