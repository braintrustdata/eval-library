#!/bin/bash

# Block exploration commands and direct agent to use vector search instead
# This hook intercepts Terminal/Bash tool usage to block cd, read, ls, etc.

set -euo pipefail

# Get hook context
COMMAND="${1:-}"
EXIT_CODE="${2:-}"

# Check if tool gating is enabled
SESSION_STATE_FILE="${CLAUDE_SESSION_DIR:-.claude}/session_state"

should_gate_tools() {
    # Check environment variable first
    if [[ "${ENABLE_TOOL_GATING:-false}" == "true" ]]; then
        return 0
    fi
    
    # Check session state file
    if [[ -f "$SESSION_STATE_FILE" ]] && grep -q "vector_search_used=true" "$SESSION_STATE_FILE" 2>/dev/null; then
        return 1
    fi
    return 0
}

# Only block if tool gating is enabled and vector search hasn't been used yet
if ! should_gate_tools; then
    exit 0
fi

# List of blocked commands - exploration tools instead of vector search
BLOCKED_PATTERNS=(
    "^cd "
    "^\s*cd "
    "^ls "
    "^ls -"
    "^find "
    "^grep "
    "^read "
    "^cat "
)

# Check if command matches any blocked patterns
for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if [[ "$COMMAND" =~ $pattern ]]; then
        echo "❌ BLOCKED: Tool gating enforced" >&2
        echo "ERROR: This command is blocked during vector search enforcement phase" >&2
        echo "" >&2
        echo "You must use vector search to discover code. Instead of '$COMMAND'," >&2
        echo "use vector_search.py to find what you need semantically." >&2
        echo "" >&2
        echo "Example:" >&2
        echo "  uv run python vector_search.py search --repo \"<repo>\" --commit <commit> \"<your query>\"" >&2
        exit 1
    fi
done

exit 0
