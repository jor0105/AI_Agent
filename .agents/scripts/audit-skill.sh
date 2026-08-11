#!/usr/bin/env bash
# audit-skill.sh — valida uma skill individual contra skill-governance/SKILL.md
# Uso: bash .agents/scripts/audit-skill.sh <skill-name> [base-dir]
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <skill-name> [base-dir]" >&2
  echo "  skill-name  nome da pasta da skill (ex: python-patterns)" >&2
  exit 1
fi

SKILL_NAME="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${2:-$SCRIPT_DIR/../..}"

if [[ ! -d "$BASE_DIR" ]]; then
  echo "Erro: base-dir nao encontrado: $BASE_DIR" >&2
  exit 1
fi

BASE_DIR="$(cd "$BASE_DIR" && pwd)"
VALIDATOR="$BASE_DIR/.agents/scripts/validate-skills.py"

if [[ ! -f "$VALIDATOR" ]]; then
  echo "Erro: validate-skills.py nao encontrado em $VALIDATOR" >&2
  exit 1
fi

uv run python "$VALIDATOR" --skill "$SKILL_NAME"
