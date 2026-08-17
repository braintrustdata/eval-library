#!/bin/bash
# PreToolUse hook (lockdown variant): enforce RAG-only by vetoing bash exploration
# BEFORE it runs. Always allows the sanctioned vector-search tool and cat-ing an
# already-located file. Reads Claude Code's hook payload (JSON) on stdin and
# inspects tool_input.command. exit 2 => block and return the reason to the agent.
input=$(cat)
cmd=$(printf '%s' "$input" | python3 -c "import sys,json;
try:
    d=json.load(sys.stdin); print((d.get('tool_input') or {}).get('command','') or '')
except Exception:
    print('')" 2>/dev/null)

# Not a bash command (empty) -> nothing to inspect; allow.
[ -z "$cmd" ] && exit 0

# Always allow the sanctioned vector-search tool.
printf '%s' "$cmd" | grep -qE 'run_vector_search\.sh|vector_search\.py' && exit 0

# Block agentic exploration anywhere in the command line (handles `cat x | grep y`).
if printf '%s' "$cmd" | grep -qE '(^|[|;&[:space:]])(grep|egrep|fgrep|rg|find|ls|tree|ack|ag|fd)([[:space:]]|$)'; then
    echo "BLOCKED: use the vector-search tool to LOCATE code, not grep/find/ls." >&2
    exit 2
fi

exit 0
