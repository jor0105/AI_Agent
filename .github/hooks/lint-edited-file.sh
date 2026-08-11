#!/usr/bin/env bash

set -euo pipefail

INPUT="$(cat || true)"
declare -a candidates=()

add_candidate() {
  local value="$1"

  if [[ -n "$value" ]]; then
    candidates+=("$value")
  fi
}

if [[ -n "${TOOL_INPUT_FILE_PATH:-}" ]]; then
  add_candidate "$TOOL_INPUT_FILE_PATH"
fi

if [[ -n "${TOOL_INPUT_FILES:-}" ]]; then
  while IFS= read -r file; do
    add_candidate "$file"
  done < <(printf '%s\n' "$TOOL_INPUT_FILES" | tr ' ,' '\n')
fi

if command -v jq >/dev/null 2>&1 && jq -e . >/dev/null 2>&1 <<<"$INPUT"; then
  while IFS= read -r file; do
    add_candidate "$file"
  done < <(
    jq -r '
      [
        .tool_input.file_path?,
        .tool_input.filePath?,
        .tool_input.path?,
        .tool_input.files[]?,
        .tool_input.filePaths[]?,
        .tool_input.edits[]?.filePath?,
        .tool_input.edits[]?.path?
      ] | .[] | select(type == "string" and length > 0)
    ' <<<"$INPUT"
  )
elif command -v node >/dev/null 2>&1 && [[ -n "$INPUT" ]]; then
  while IFS= read -r file; do
    add_candidate "$file"
  done < <(
    HOOK_INPUT="$INPUT" node - <<'NODE'
const input = process.env.HOOK_INPUT;

try {
  const parsed = JSON.parse(input);
  const toolInput = parsed.tool_input ?? {};
  const values = [
    toolInput.file_path,
    toolInput.filePath,
    toolInput.path,
    ...(Array.isArray(toolInput.files) ? toolInput.files : []),
    ...(Array.isArray(toolInput.filePaths) ? toolInput.filePaths : []),
    ...(Array.isArray(toolInput.edits)
      ? toolInput.edits.flatMap((edit) => [edit?.filePath, edit?.path])
      : []),
  ];

  for (const value of values) {
    if (typeof value === "string" && value.length > 0) {
      console.log(value);
    }
  }
} catch {
  process.exit(0);
}
NODE
  )
fi

declare -a files=()
for file in "${candidates[@]}"; do
  case "$file" in
    *.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs)
      ;;
    *)
      continue
      ;;
  esac

  case "$file" in
    node_modules/*|dist/*|.venv/*|.agents/*|.github/*|.opencode/*|.kilo/*)
      continue
      ;;
  esac

  if [[ -f "$file" ]]; then
    files+=("$file")
  fi
done

if (( ${#files[@]} == 0 )); then
  echo "[hook] eslint skipped: no edited JS/TS source file detected"
  exit 0
fi

printf "[hook] eslint focused check:"
printf ' %q' "${files[@]}"
printf '\n'

npx --no-install eslint "${files[@]}"
