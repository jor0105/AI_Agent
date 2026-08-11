#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../../.." >/dev/null 2>&1 && pwd)"
OUTPUT_ROOT_DIR="${PLAN_GUARD_OUTPUT_ROOT_DIR:-$REPO_ROOT}"
DEFAULT_TEMPLATE="${REPO_ROOT}/.agents/skills/plan-writing/templates/plan.template.md"

log() {
  printf "[plan-guard] %s\n" "$1"
}

fail() {
  printf "[plan-guard] ERROR: %s\n" "$1" >&2
  exit 1
}

usage() {
  cat <<EOF
Usage:
  bash .agents/skills/plan-writing/scripts/plan_guard.sh init-plan --task <snake_case_slug> --title "<titulo humano>" --author <agent> [--plan PATH] [--template PATH] [--force]

Commands:
  init-plan   Create <task>.md from the official plan template.

Defaults:
  output root: ${OUTPUT_ROOT_DIR}
  template:    ${DEFAULT_TEMPLATE}
EOF
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "File not found: $path"
}

escape_sed_replacement() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\//\\/}"
  value="${value//&/\\&}"
  printf "%s" "$value"
}

replace_placeholder() {
  local file="$1"
  local placeholder="$2"
  local value="$3"
  local escaped_value
  escaped_value="$(escape_sed_replacement "$value")"
  sed -i "s/${placeholder}/${escaped_value}/g" "$file"
}

validate_task_slug() {
  local task="$1"
  [[ "$task" =~ ^[a-z0-9]+(_[a-z0-9]+)*$ ]] || fail "Task slug must be snake_case lowercase, for example: refatorar_backend"
}

resolve_plan_path() {
  local task="$1"
  local explicit_path="$2"

  if [[ -n "$explicit_path" ]]; then
    printf "%s" "$explicit_path"
    return 0
  fi

  printf "%s/%s.md" "$OUTPUT_ROOT_DIR" "$task"
}

init_plan() {
  local task=""
  local title=""
  local author=""
  local plan_path=""
  local template_path="$DEFAULT_TEMPLATE"
  local force="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --task)
        task="${2:-}"
        shift 2
        ;;
      --title)
        title="${2:-}"
        shift 2
        ;;
      --author)
        author="${2:-}"
        shift 2
        ;;
      --plan)
        plan_path="${2:-}"
        shift 2
        ;;
      --template)
        template_path="${2:-}"
        shift 2
        ;;
      --force)
        force="true"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        fail "Unknown argument: $1"
        ;;
    esac
  done

  [[ -n "$task" ]] || fail "--task is required"
  [[ -n "$title" ]] || fail "--title is required"
  [[ -n "$author" ]] || fail "--author is required"

  validate_task_slug "$task"
  require_file "$template_path"

  plan_path="$(resolve_plan_path "$task" "$plan_path")"
  mkdir -p "$(dirname "$plan_path")"

  if [[ -e "$plan_path" && "$force" != "true" ]]; then
    fail "Plan already exists: $plan_path (use --force to overwrite)"
  fi

  cp "$template_path" "$plan_path"

  replace_placeholder "$plan_path" "__PLAN_TITLE__" "$title"
  replace_placeholder "$plan_path" "__PLAN_NAME__" "$task"
  replace_placeholder "$plan_path" "__PLAN_DATE__" "$(date -u +%Y-%m-%d)"
  replace_placeholder "$plan_path" "__PLAN_AUTHOR__" "$author"
  replace_placeholder "$plan_path" "__PLAN_FILE__" "$(basename "$plan_path")"

  log "initialized plan at $plan_path"
}

main() {
  local command="${1:-}"

  case "$command" in
    init-plan)
      shift
      init_plan "$@"
      ;;
    -h|--help|"")
      usage
      ;;
    *)
      fail "Unknown command: $command"
      ;;
  esac
}

main "$@"
