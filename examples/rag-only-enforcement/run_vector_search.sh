#!/bin/bash
# Wrapper script for vector_search.py that works without needing 'cd'
# This allows Claude Code to call vector search without using 'cd' command

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Track that this script was called
echo "[VECTOR_SEARCH_CALL]"

uv run python vector_search.py "$@"
