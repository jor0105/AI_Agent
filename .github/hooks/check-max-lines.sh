#!/usr/bin/env bash

set -euo pipefail

MAX_LINES="${MAX_LINES:-400}"
violations=()

if (( $# > 0 )); then
  candidates=("$@")
else
  # mapfile -t candidates < <(git ls-files src backend .agents/scripts .agents/skills)
  mapfile -t candidates < <(git ls-files src backend)
fi

for file in "${candidates[@]}"; do
  if [[ ! -f "$file" ]]; then
    continue
  fi

  case "$file" in
    backend/.venv/*|src/shared/generated/*|backend/tests/*|backend/testing/*)
      continue
      ;;
    # src/*|backend/*|.agents/scripts/*|.agents/skills/*/scripts/*)
    src/*|backend/*)
      ;;
    *)
      continue
      ;;
  esac

  case "$file" in
    *.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs|*.py)
      ;;
    *)
      continue
      ;;
  esac

  line_count=$(wc -l < "$file")
  if (( line_count > MAX_LINES )); then
    violations+=("$file:$line_count")
  fi
done

if (( ${#violations[@]} == 0 )); then
  exit 0
fi

echo "Erro: arquivos com mais de ${MAX_LINES} linhas detectados:"
for item in "${violations[@]}"; do
  echo "  - $item"
done
echo
echo "Refatore os arquivos acima para manter no maximo ${MAX_LINES} linhas por arquivo."
exit 1
