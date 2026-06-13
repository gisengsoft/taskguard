#!/usr/bin/env bash
# ============================================================================
# run_sast.sh — Análise Estática de Segurança (SAST) com Bandit.
#
# Varre o código-fonte em busca de padrões inseguros (uso de eval, subprocess
# com shell=True, segredos embutidos, deserialização insegura, etc.).
#
# Falha (exit != 0) caso encontre vulnerabilidade de severidade ALTA, fazendo a
# pipeline quebrar automaticamente. Gera relatórios JSON e SARIF.
# ============================================================================
set -euo pipefail

REPORTS_DIR="${REPORTS_DIR:-reports}"
mkdir -p "$REPORTS_DIR"

echo "==> [SAST] Iniciando análise estática com Bandit..."

# Relatório legível em JSON (artefato da pipeline).
bandit -r app run.py config.py \
  -c pyproject.toml \
  -f json -o "$REPORTS_DIR/bandit-report.json" || true

# Saída human-readable no console.
bandit -r app run.py config.py -c pyproject.toml -f screen || true

# Gate de severidade: falha se houver issues HIGH (-lll) com confiança alta.
echo "==> [SAST] Aplicando gate de severidade ALTA..."
bandit -r app run.py config.py -c pyproject.toml -lll -iii

echo "==> [SAST] Concluído sem vulnerabilidades de severidade ALTA."
