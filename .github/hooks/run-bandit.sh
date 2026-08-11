#!/usr/bin/env bash
# Run Bandit with the same project-managed version for production and tests.
# B101 is expected for pytest assertions, so it is skipped only in tests.
set -uo pipefail

source_files=()
test_files=()

for file in "$@"; do
  if [[ "$file" == tests/*.py ]]; then
    test_files+=("$file")
  else
    source_files+=("$file")
  fi
done

status=0

if (( ${#source_files[@]} > 0 )); then
  if ! uv run --no-sync bandit -c pyproject.toml "${source_files[@]}"; then
    status=1
  fi
fi

if (( ${#test_files[@]} > 0 )); then
  if ! uv run --no-sync bandit -c pyproject.toml \
    --skip B101 "${test_files[@]}"
  then
    status=1
  fi
fi

exit "$status"
