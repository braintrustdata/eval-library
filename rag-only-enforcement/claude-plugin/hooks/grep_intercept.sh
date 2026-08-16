#!/bin/bash
###
# Grep Intercept Hook - Redirects grep commands to vector search
###

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

debug "Grep intercept hook triggered"

# Check if tool gating is enabled
if [ "${ENABLE_TOOL_GATING:-}" != "true" ]; then
    debug "Grep intercept: Tool gating not enabled, allowing grep"
    exit 0
fi

# Read input from stdin
INPUT=$(cat)
debug "Grep intercept input: $(echo "$INPUT" | jq -c '.' 2>/dev/null | head -c 500)"

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}' 2>/dev/null)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)

# Skip if not a Bash/Terminal tool
if [[ "$TOOL_NAME" != "Bash" ]] && [[ "$TOOL_NAME" != "Terminal" ]]; then
    debug "Grep intercept: Not a terminal tool, skipping"
    exit 0
fi

# Get the command
CMD=$(echo "$TOOL_INPUT" | jq -r '.command // empty' 2>/dev/null)

# Check if this is a grep command
if [[ "$CMD" == *"grep"* ]]; then
    log "WARN" "Grep Intercept: Blocking grep command - must use vector search instead"
    log "WARN" "Original command: $CMD"
    
    # Extract the pattern being searched for
    PATTERN=$(echo "$CMD" | sed -E 's/.*grep[^ ]* "?([^"]*)"?.*/\1/' | head -c 100)
    
    # Return helpful error message
    cat << 'EOF'
ERROR: grep command blocked by policy

You attempted to use grep, but this evaluation requires you to use vector search instead.

INSTEAD OF: grep -r "pattern" .
USE: cd /path/to/eval && uv run python vector_search.py search --repo "{repo_path}" --commit {commit_sha} "your search query"

Vector search is more effective because it understands the MEANING of code, not just text patterns.
It will find related implementations and concepts, not just exact text matches.

Please use vector search to find what you need.
EOF
    exit 1
fi

# Check for other search commands
for cmd in "find" "locate" "ack" "ag" "rg"; do
    if [[ "$CMD" == *"$cmd"* ]]; then
        log "WARN" "Search Intercept: Blocking $cmd command - must use vector search instead"
        log "WARN" "Original command: $CMD"
        
        echo "ERROR: $cmd command blocked by policy - use vector search instead"
        echo ""
        echo "Vector search command:"
        echo 'cd /path/to/eval && uv run python vector_search.py search --repo "{repo_path}" --commit {commit_sha} "your search query"'
        exit 1
    fi
done

debug "Grep intercept: Command allowed"
exit 0
