#!/usr/bin/env bash
# Fail the commit when the generated harness mirrors drift from the .agents
# source of truth. .agents/ is canonical; .claude, .github, .codex and
# opencode.json are generated. Run the printed fix command (without
# --check) and re-stage when this hook fails.
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 1

# .agents/ is gitignored, so a clean clone has no harness to keep in sync.
# Skip rather than block commits for contributors who never installed it.
if [ ! -d .agents ]; then
  exit 0
fi

fail=0

run_check() {
  local label="$1" script="$2"
  if ! python3 "$script" --check >/dev/null 2>&1; then
    echo "  x ${label}  ->  fix: python3 ${script}" >&2
    fail=1
  fi
}

echo "Checking harness mirror sync (.agents = source of truth)..." >&2
run_check "agent mirrors (claude/github/codex/opencode)" \
  ".agents/scripts/sync-config-agents.py"
run_check "workflow mirrors (github/opencode/claude commands)" \
  ".agents/scripts/sync-workflows.py"
run_check "skill index (.agents/skill-index.md)" \
  ".agents/scripts/generate-skill-index.py"

if [ "$fail" -ne 0 ]; then
  echo "" >&2
  echo "Harness mirrors drifted from .agents. Run the fix command(s) above and re-stage." >&2
  exit 1
fi

echo "  ok harness mirrors in sync" >&2
