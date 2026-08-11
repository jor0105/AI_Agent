#!/bin/bash
# Require approval for sensitive operations
# Checks file patterns and requests approval

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILES=$(echo "$INPUT" | jq -r '.tool_input.files[]? // empty')

# Files requiring approval
APPROVAL_PATTERNS=(
  "*.config.ts"
  "*.config.js"
  "package.json"
  "tsconfig*.json"
  "vite.config.*"
  "src/app/store/*"
  "src/app/providers/*"
  ".env*"
  "**/schema*.ts"
  "**/migration*.ts"
)

for file in $FILES; do
  for pattern in "${APPROVAL_PATTERNS[@]}"; do
    if [[ "$file" == $pattern ]]; then
      echo "{\"continue\": false, \"stopReason\": \"Approval required for: $file\", \"askUser\": true}"
      exit 2
    fi
  done
done

echo '{"continue": true}'
exit 0
