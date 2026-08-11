#!/bin/bash
# Block destructive commands hook
# Prevents: rm -rf, DROP TABLE, DELETE FROM without WHERE

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // .tool_input // empty')

# Check for dangerous patterns
DANGEROUS_PATTERNS=(
  "rm\s+-rf"
  "DROP\s+TABLE"
  "DELETE\s+FROM\s+\w+\s*;"
  "TRUNCATE\s+TABLE"
  "DROP\s+DATABASE"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -Ei "$pattern" > /dev/null 2>&1; then
    echo "{\"continue\": false, \"stopReason\": \"Destructive command blocked: $pattern\"}"
    exit 2
  fi
done

echo '{"continue": true}'
exit 0
