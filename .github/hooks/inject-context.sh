#!/bin/bash
# Inject context at session start
# Provides project info, branch, and recent changes

INPUT=$(cat)

# Get project info
PROJECT_NAME=$(node -p "require('./package.json').name" 2>/dev/null || echo "unknown")
PROJECT_VERSION=$(node -p "require('./package.json').version" 2>/dev/null || echo "unknown")
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
NODE_VERSION=$(node -v 2>/dev/null || echo "not installed")

# Get recent changes
RECENT_CHANGES=$(git log --oneline -5 2>/dev/null | head -5 || echo "No git history")

# Format as JSON context
cat <<EOF
{
  "continue": true,
  "systemMessage": "Project: $PROJECT_NAME v$PROJECT_VERSION | Branch: $BRANCH | Node: $NODE_VERSION"
}
EOF
