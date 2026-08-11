#!/usr/bin/env bash
# Validates commit messages against Conventional Commits, using the type list
# documented in docs/dev-guide/contribute.md.

MSG_FILE="${1:-.git/COMMIT_EDITMSG}"
MSG=$(head -1 "$MSG_FILE")

# Git creates this message while MERGE_HEAD exists; do not trust the prefix
# alone because a normal commit could use it to bypass validation.
if [[ "$MSG" =~ ^Merge\  ]] && \
  git rev-parse --verify MERGE_HEAD >/dev/null 2>&1
then
  exit 0
fi

# Regex: type(scope)!: description
# Types: the six documented in contribute.md, plus the remaining standard ones
# Scope: optional, lowercase, allows &, /, _, -
# Breaking change: optional '!' before the colon
# Description: required, starts lowercase, no trailing period
TYPES="feat|fix|docs|test|refactor|chore|style|perf|build|ci|revert"
PATTERN="^(${TYPES})(\([a-z0-9/&_-]+\))?!?:\ [a-z].{0,499}[^.]$"

if ! echo "$MSG" | grep -Eq "$PATTERN"; then
  echo ""
  echo "Commit message rejected. Use: type(scope): description"
  echo ""
  echo "  feat      - New feature"
  echo "  fix       - Bug fix"
  echo "  docs      - Documentation only"
  echo "  test      - Adding or improving tests"
  echo "  refactor  - Code change, no behavior change"
  echo "  chore     - Tooling, config, deps"
  echo "  also allowed: style, perf, build, ci, revert"
  echo ""
  echo "Rules:"
  echo "  - Scope is optional (lowercase, hyphens, and '&' allowed)"
  echo "  - Append '!' before ':' for a breaking change"
  echo "  - Description starts lowercase"
  echo "  - Max 500 chars, no trailing period"
  echo ""
  echo "Examples:"
  echo "  feat(chat): add thinking mode toggle"
  echo "  fix(openai): resolve 401 on streaming retry"
  echo "  refactor(tools): extract file reader modules"
  echo "  chore: update pre-commit hooks"
  echo ""
  echo "Your message: \"$MSG\""
  echo ""
  exit 1
fi
