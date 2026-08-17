#!/usr/bin/env python3
"""
Eval harness for testing agentic search vs vector DB retrieval.

This script:
1. Loads a dataset of PR bugfixes
2. For each task, clones/caches the repo and resets to pre-fix state
3. Runs Claude Code to fix the bug
4. Applies the test and checks if it passes
5. Logs results to Braintrust

Usage:
    uv run python run_eval.py --variant agentic       # Claude uses grep/find/ls
    uv run python run_eval.py --variant vector        # Claude uses vector search only
    uv run python run_eval.py --variant agentic -n 1  # Run only first task
"""

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import click
from dotenv import load_dotenv

load_dotenv()

# BRAINTRUST_API_KEY is read from the environment (see .env / .env.example).

import braintrust

# Constants
DEFAULT_DATASET_PATH = Path(__file__).parent / "dataset.json"
REPO_CACHE_DIR = Path.home() / ".cache" / "agent-search-eval" / "repos"
# Braintrust Demos project (reverted base hardcoded "AI evals search").
PROJECT_NAME = "Behavior vs Output-Only Judge"
# Pin the agent model explicitly (claude -p default is unstated -> was Opus 4.8).
AGENT_MODEL = "claude-sonnet-4-5"

# --- Behavior spec (agentbehavior format): single source of truth for the RAG-only
# policy, consumed by BOTH the agent prompt and the LLM behavior judge. ---
BEHAVIOR_SPEC_PATH = (
    Path(__file__).parent / ".agents" / "behaviors" / "rag-only" / "BEHAVIOR.md"
)


def load_behavior_spec(path: Path = BEHAVIOR_SPEC_PATH) -> dict:
    """Parse an agentbehavior BEHAVIOR.md into {name, description, body, raw}."""
    text = path.read_text()
    name = description = ""
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            frontmatter = text[3:end]
            body = text[end + 4:].lstrip("\n")
            for line in frontmatter.strip().splitlines():
                key, sep, val = line.partition(":")
                if sep:
                    key, val = key.strip(), val.strip()
                    if key == "name":
                        name = val
                    elif key == "description":
                        description = val
    return {"name": name, "description": description,
            "body": body.strip(), "raw": text.strip()}


BEHAVIOR = load_behavior_spec()

# --- Agentic-exploration detector (deterministic). Validated to reproduce the
# original used_agentic_exploration on all 60 logged behavior rows. Exploration =
# the Grep/Glob tools, or a bash grep/rg/find/ls/tree/ack/ag/fd command. Blocked
# attempts (PreToolUse hook / disallowed tool) do NOT count as violations. ---
_EXPLORE_TOOLS = {"Grep", "Glob"}
_EXPLORE_BINS = {"grep", "egrep", "fgrep", "rg", "ack", "ag", "find", "ls", "tree", "fd"}
_NON_REPO = ("vector_cache", "/tmp/", "/private/tmp/")


def _locates_code(tool: str, arg: str) -> bool:
    """True only if this call uses agentic search to LOCATE code in the repo.

    Deliberately does NOT count:
      - an exploration binary receiving piped input (`python tests | grep`,
        `cat file | grep`) — it reads stdin, not the codebase;
      - `ls`/`find`/`tree` on a non-repo path (the vector cache, /tmp scratch).
    This is the fix for the original detector, which flagged any `grep` at all —
    including the agent filtering its own test output — as a RAG violation.
    """
    if tool in _EXPLORE_TOOLS:
        return True                       # the Grep/Glob tools search the repo
    if tool != "Bash":
        return False
    for idx, stage in enumerate((arg or "").split("|")):
        toks = stage.strip().split()
        if not toks:
            continue
        binname = toks[0].split("/")[-1]
        if binname in _EXPLORE_BINS:
            if idx > 0:                   # piped stdin, not a filesystem search
                continue
            if binname in ("ls", "find", "tree", "fd") and any(nr in stage for nr in _NON_REPO):
                continue
            return True                   # stage-0 exploration reading repo files/tree
    return False


def detect_agentic_exploration(trajectory: list) -> dict:
    """Did the agent use agentic search to LOCATE code? Blocked calls excluded."""
    tools = []
    attempted = 0
    for t in trajectory:
        if not _locates_code(t.get("tool"), t.get("arg") or ""):
            continue
        attempted += 1
        if not t.get("blocked"):
            tools.append(f"{t.get('tool')}: {(t.get('arg') or '')[:40]}")
    return {"used": len(tools) > 0, "count": len(tools), "tools": tools[:20], "attempted": attempted}


# --- Trajectory extraction from Claude Code stream-json output. Produces the same
# [{tool, arg, blocked}] shape the original harness logged. A tool_use whose
# tool_result carries a block/deny marker is flagged blocked (PreToolUse hook or
# disallowed-tool refusal), matching the deterministic detector's expectations. ---
_BLOCK_MARKERS = ("blocked:", "not allowed", "isn't allowed", "disallowed",
                  "permission denied", "blocked by")


def extract_trajectory(stream_output: str) -> list:
    """Parse claude -p stream-json into [{tool, arg, blocked?}]."""
    if not stream_output:
        return []
    blocked_ids = set()
    uses = []  # (tool_use_id, tool_name, arg)
    for line in stream_output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = (ev.get("message", {}) or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                inp = block.get("input", {}) or {}
                arg = (inp.get("command") or inp.get("file_path") or inp.get("pattern")
                       or inp.get("path") or inp.get("query") or "")
                uses.append((block.get("id"), block.get("name", ""), str(arg)[:160]))
            elif block.get("type") == "tool_result":
                tid = block.get("tool_use_id")
                c = block.get("content")
                ctext = c if isinstance(c, str) else json.dumps(c)
                if tid and any(m in ctext.lower() for m in _BLOCK_MARKERS):
                    blocked_ids.add(tid)
    traj = []
    for tid, tool, arg in uses:
        entry = {"tool": tool, "arg": arg}
        if tid in blocked_ids:
            entry["blocked"] = True
        traj.append(entry)
    return traj


def load_dataset(dataset_path: Path = None):
    """Load the evaluation dataset."""
    path = dataset_path or DEFAULT_DATASET_PATH
    with open(path) as f:
        return json.load(f)


def setup_claude_hooks(repo_path: Path, enable_tool_gating: bool = False, lockdown: bool = False):
    """Set up Claude Code hooks in the repo for Braintrust tracing.

    Args:
        repo_path: Path to the repository
        enable_tool_gating: If True, enables tool gating to block agentic search tools
        lockdown: If True, registers a PreToolUse hook that blocks bash exploration
            commands (grep/find/ls/...) while allowing the vector-search tool and cat.
    """
    claude_dir = repo_path / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Path to our hooks
    hooks_dir = Path(__file__).parent / "claude-plugin" / "hooks"

    settings = {
        "enabledPlugins": {"trace-claude-code@braintrust-claude-plugin": False},
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'bash "{hooks_dir}/session_start.sh"',
                        }
                    ]
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'bash "{hooks_dir}/user_prompt_submit.sh"',
                        }
                    ]
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'bash "{hooks_dir}/grep_intercept.sh"',
                        },
                        {
                            "type": "command",
                            "command": f'bash "{hooks_dir}/block_exploration_commands.sh"',
                        },
                        {
                            "type": "command",
                            "command": f'bash "{hooks_dir}/post_tool_use.sh"',
                        }
                    ],
                }
            ],
            "Stop": [{"hooks": [{"type": "command", "command": f'bash "{hooks_dir}/stop_hook.sh"'}]}],
            "SessionEnd": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'bash "{hooks_dir}/session_end.sh"',
                        }
                    ]
                }
            ],
        },
    }

    # Lockdown enforcement: PreToolUse hook vetoes bash exploration before it runs.
    if lockdown:
        settings["hooks"]["PreToolUse"] = [
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": f'bash "{hooks_dir}/pre_lockdown_block.sh"',
                    }
                ],
            }
        ]

    settings_path = claude_dir / "settings.local.json"
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    
    # Copy managed settings with permission-based command blocking
    managed_settings_src = Path(__file__).parent / "claude-plugin" / "managed-settings.json"
    if managed_settings_src.exists():
        managed_settings_dst = claude_dir / "managed-settings.json"
        with open(managed_settings_src) as src, open(managed_settings_dst, "w") as dst:
            dst.write(src.read())
    
    # Store tool gating config in a separate file for hooks to read
    if enable_tool_gating:
        gating_config = {"tool_gating_enabled": True}
        gating_config_path = claude_dir / "tool_gating.json"
        with open(gating_config_path, "w") as f:
            json.dump(gating_config, f, indent=2)


def get_repo_path(repo_url: str, enable_tool_gating: bool = False, lockdown: bool = False) -> Path:
    """Clone repo if not cached, return local path.

    Args:
        repo_url: The GitHub repository URL
        enable_tool_gating: If True, enables tool gating to block agentic search tools
        lockdown: If True, registers the PreToolUse exploration-blocking hook.
    """
    # Extract repo name from URL (e.g., "microsoft/typescript-go" -> "microsoft_typescript-go")
    repo_name = repo_url.replace("https://github.com/", "").replace("/", "_")
    repo_path = REPO_CACHE_DIR / repo_name

    if not repo_path.exists():
        print(f"Cloning {repo_url}...")
        REPO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", repo_url, str(repo_path)],
            check=True,
        )
        # Initialize submodules
        print("Initializing submodules...")
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            cwd=repo_path,
            check=True,
        )
    else:
        print(f"Using cached repo: {repo_path}")

    # Ensure Claude Code hooks are set up for tracing
    setup_claude_hooks(repo_path, enable_tool_gating=enable_tool_gating, lockdown=lockdown)

    return repo_path


@braintrust.traced
def reset_repo(repo_path: Path, commit: str):
    """Reset the repo to a specific commit."""
    # Unstage any staged files (git checkout . doesn't handle staged new files)
    subprocess.run(
        ["git", "reset", "HEAD", "--", "."],
        cwd=repo_path,
        capture_output=True,
    )
    # Discard any local changes to tracked files
    subprocess.run(
        ["git", "checkout", "."],
        cwd=repo_path,
        capture_output=True,
    )
    # Clean any untracked files
    subprocess.run(
        ["git", "clean", "-fd"],
        cwd=repo_path,
        capture_output=True,
    )
    # Fetch to ensure we have all commits
    subprocess.run(
        ["git", "fetch", "--all"],
        cwd=repo_path,
        capture_output=True,
    )
    # Checkout the specific commit (detached HEAD)
    subprocess.run(
        ["git", "checkout", commit],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


def parse_span_export(export_str: str) -> tuple[str, str, str]:
    """Parse a Braintrust span export string and return (span_id, root_span_id, object_id)."""
    from braintrust.logger import SpanComponentsV3

    components = SpanComponentsV3.from_str(export_str.strip())
    return (
        str(components.span_id),
        str(components.root_span_id),
        str(components.object_id),
    )


@braintrust.traced
def run_vector_search_for_files(repo_path: Path, query: str, commit_sha: str) -> list[str]:
    """
    Run vector search to get a list of relevant files.
    
    Returns a list of file paths.
    """
    eval_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            [
                "uv", "run", "python", "vector_search.py", "search",
                "--repo", str(repo_path),
                "--commit", commit_sha,
                "--format", "files",
                query,
            ],
            cwd=eval_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            # Parse file paths from output
            files = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
            return files
    except Exception as e:
        print(f"Warning: Vector search pre-step failed: {e}")
    return []


@braintrust.traced
def run_claude_agent(
    prompt: str,
    repo_path: Path,
    use_vector_search: bool = False,
    vector_hybrid: bool = False,
    vector_sysprompt: bool = False,
    vector_lockdown: bool = False,
    vector_vanilla: bool = False,
    parent_span_export: str = None,
) -> dict:
    """
    Run Claude Code agent on the task.

    Returns dict with:
        - success: bool
        - output: str
        - duration_ms: int
        - error: str or None
        - vector_search_calls: int
    """
    start_time = time.time()
    vector_search_calls = 0

    # Build the prompt
    eval_dir = Path(__file__).parent
    # Get current commit for vector search
    commit_sha = None
    if use_vector_search or vector_hybrid or vector_sysprompt or vector_lockdown or vector_vanilla:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                commit_sha = result.stdout.strip()[:9]
        except Exception:
            pass

    if vector_hybrid:
        # For vector-hybrid, we pre-run vector search and inject results
        files_list = run_vector_search_for_files(repo_path, prompt.split("\n")[0][:100], commit_sha)
        vector_search_calls += 1  # Count the pre-step call
        files_str = "\n".join(files_list) if files_list else "No files found"
        full_prompt = f"""You are working in the repository at {repo_path}

Your task is to fix the following bug. DO NOT write tests - just fix the bug in the source code.

Vector search has pre-identified these potentially relevant files:
```
{files_str}
```

Focus your search and investigation on these files first. Use normal shell commands (grep, find, ls) to explore and understand the codebase, and locate the bug within these files.

{prompt}"""
    elif vector_vanilla or use_vector_search or vector_lockdown:
        # STANDARD-COMPLIANT SETUP: the agent gets the RAG-only rule as a plain
        # system prompt (NOT the BEHAVIOR.md spec, which per the behavior-specs
        # standard is never shown to the agent). vanilla / flag / lockdown all get
        # this identical prompt; the only variable is ENFORCEMENT (none / tool
        # flag / flag+hook), wired below. The BEHAVIOR.md stays judge-only.
        full_prompt = f"""You are working in the repository at {repo_path}

Your task is to fix the following bug. DO NOT write tests - just fix the bug in the source code.

IMPORTANT: Find code using ONLY the vector-search tool. Do NOT use grep, glob,
find, ls, or the Grep/Glob/Read tools to locate code in the repository.

To search:
```bash
{eval_dir}/run_vector_search.sh search --repo "{repo_path}" --commit {commit_sha} "your search query"
```
Once vector search identifies a file, read it with `cat` and edit it.
Always vector-search first; never grep/find/ls to explore.

{prompt}"""
    elif vector_sysprompt:
        # LEGACY variant (nonstandard): feeds the BEHAVIOR.md spec body to the
        # agent as its prompt. Kept for the record but not part of the standard-
        # compliant rerun, where the agent only ever sees the plain system prompt.
        full_prompt = f"""You are working in the repository at {repo_path}

Your task is to fix the following bug. DO NOT write tests - just fix the bug in the source code.

## BEHAVIOR SPEC (mandatory)
{BEHAVIOR['body']}

## How to search (vector search)
```bash
{eval_dir}/run_vector_search.sh search --repo "{repo_path}" --commit {commit_sha} "your search query"
```
Once vector search identifies a file, use `cat` to read it and the Edit tool to
change it. Always vector-search first; never grep/find/ls to explore.

{prompt}"""
    else:
        full_prompt = f"""You are working in the repository at {repo_path}

Your task is to fix the following bug. DO NOT write tests - just fix the bug in the source code.

{prompt}"""

    # Build environment with tracing config
    env = {**os.environ}
    env["TRACE_TO_BRAINTRUST"] = "true"
    env["BRAINTRUST_CC_PROJECT"] = PROJECT_NAME
    # ANTHROPIC_API_KEY is inherited from os.environ (set via .env or shell environment)
    
    # Parse span export to get individual IDs for better tracing
    # Env var names must match what the hooks expect:
    #   session_start.sh checks BRAINTRUST_PARENT_SPAN_ID, BRAINTRUST_PARENT_ROOT_SPAN_ID
    #   common.sh insert_span checks BRAINTRUST_EXPERIMENT_ID
    if parent_span_export:
        span_id, root_span_id, experiment_id = parse_span_export(parent_span_export)
        env["BRAINTRUST_PARENT_SPAN_ID"] = span_id
        # Always provide the parent root span id; the SessionStart hook requires it
        # to properly nest the Claude Code session under the eval trace.
        if root_span_id:
            env["BRAINTRUST_PARENT_ROOT_SPAN_ID"] = root_span_id
        if experiment_id:
            env["BRAINTRUST_EXPERIMENT_ID"] = experiment_id
        print(f"  Parent span ID: {span_id}")
        print(f"  Root span ID: {root_span_id}")
        print(f"  Experiment ID: {experiment_id}")
    
    # Pass tool gating flag if vector search is enabled
    if use_vector_search or vector_lockdown:
        env["ENABLE_TOOL_GATING"] = "true"

    print(f"  TRACE_TO_BRAINTRUST: {env.get('TRACE_TO_BRAINTRUST')}")

    # Run claude with tracing enabled
    # Use Popen with start_new_session=True so we can kill the entire process
    # group on timeout. subprocess.run's timeout kills only the main process,
    # but child processes (hooks, bash commands) inherit stdout/stderr pipes
    # and keep them open, causing communicate() to block for hours.
    try:
        cmd = [
            "claude",
            "-p",
            "--verbose",
            "--model", AGENT_MODEL,
            "--output-format", "stream-json",
            "--dangerously-skip-permissions",
        ]

        # Flag-level enforcement: remove the Grep/Glob/Read TOOLS for the flag and
        # lockdown variants (sysprompt is prompt-only, no flag). Bash stays enabled
        # so the agent can call run_vector_search.sh; lockdown additionally blocks
        # bash exploration via the PreToolUse hook wired in setup_claude_hooks.
        if use_vector_search or vector_lockdown:
            cmd.extend([
                "--disallowed-tools", "Grep,Glob,Read",
            ])
            print(f"  Blocking tools: Grep, Glob, Read")
        
        print(f"  Running claude with tracing enabled")
        
        # Use Popen with start_new_session to create a new process group
        proc = subprocess.Popen(
            cmd,
            cwd=repo_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            start_new_session=True,  # New process group for clean kill
        )
        _agent_timeout = int(os.environ.get("AGENT_TIMEOUT", "600"))
        try:
            stdout, stderr = proc.communicate(input=full_prompt, timeout=_agent_timeout)
        except subprocess.TimeoutExpired:
            # Kill the entire process group (claude + hooks + bash children)
            print(f"  Timeout after {_agent_timeout}s, killing process group {proc.pid}")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                # Give processes a moment to clean up, then force kill
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    proc.wait(timeout=5)
            except (ProcessLookupError, OSError):
                pass  # Process already dead
            # Close pipes explicitly
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                try:
                    pipe.close()
                except Exception:
                    pass
            return {
                "success": False,
                "output": "",
                "stderr": "",
                "duration_ms": _agent_timeout * 1000,
                "error": f"Timeout after {_agent_timeout}s (counted as a failed completion)",
                "vector_search_calls": vector_search_calls,
                "token_usage": {},
                "trajectory": [],
            }

        duration_ms = int((time.time() - start_time) * 1000)

        # Count vector search calls by looking for the marker output by run_vector_search.sh
        vector_search_output = stdout + stderr
        vector_search_calls += vector_search_output.count("[VECTOR_SEARCH_CALL]")

        # Parse token usage from stream-json output
        token_usage = parse_token_usage(stdout)

        return {
            "success": proc.returncode == 0,
            "output": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "error": None if proc.returncode == 0 else f"Exit code: {proc.returncode}",
            "vector_search_calls": vector_search_calls,
            "token_usage": token_usage,
            "trajectory": extract_trajectory(stdout),
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "stderr": "",
            "duration_ms": int((time.time() - start_time) * 1000),
            "error": str(e),
            "vector_search_calls": vector_search_calls,
            "token_usage": {},
            "trajectory": [],
        }


@braintrust.traced
def apply_test_files(repo_path: Path, test_files: list):
    """Copy test files into the repo.

    Only applies test files that have 'content' field.
    Auto-generated datasets may only have 'path' (test already exists in repo).
    """
    for test_file in test_files:
        # Skip if no content - test file already exists in repo
        if "content" not in test_file:
            continue
        path = repo_path / test_file["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(test_file["content"])


@braintrust.traced
def run_tests(repo_path: Path, test_command: str) -> dict:
    """
    Run the test command and return results.

    Returns dict with:
        - passed: bool
        - output: str
        - error: str or None
    """
    try:
        # The dataset's test_command runs `python3 tests/runtests.py ...`. Bare
        # `python3` resolves to whatever is first on PATH; a system Python 3.12+
        # has no distutils and crashes the old Django at import (which the parser
        # below then mis-reads as "all passed"). Force the test subprocess to use
        # the harness venv python (3.12 WITH distutils) by putting its bin first.
        env = dict(os.environ)
        venv_bin = str(Path(sys.executable).parent)
        env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            test_command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
            shell=True,  # Use shell to get PATH and other env vars
            env=env,
        )
        
        # Check for common "command not found" errors
        output = result.stdout + result.stderr
        if "command not found" in output.lower() or "no such file" in output.lower():
            # Extract which command wasn't found
            import re
            match = re.search(r'(?:/bin/sh: |Command \'|command not found:? )([^\s:]+)', output)
            missing_tool = match.group(1) if match else "unknown tool"
            return {
                "passed": False,
                "output": output,
                "error": f"Missing tool: {missing_tool}. Tests cannot run without the required build tools.",
            }
        
        return {
            "passed": result.returncode == 0,
            "output": output,
            "error": None,
        }
    except subprocess.TimeoutExpired as e:
        braintrust.current_span().log(error=e)
        return {
            "passed": False,
            "output": "",
            "error": "Test timeout",
        }
    except Exception as e:
        braintrust.current_span().log(error=e)
        return {
            "passed": False,
            "output": "",
            "error": str(e),
        }


@braintrust.traced
def check_fix_applied(repo_path: Path, expected_file: str, expected_line: int) -> bool:
    """Check if any fixes were applied to the repository.
    
    Rather than checking for a specific file, we check if any files were modified.
    The real validation happens in the test suite - if tests pass, the fix worked.
    """
    # Check if any files were modified (git diff)
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    # If any files were modified, consider the fix applied
    return bool(result.stdout.strip())


def is_swebench_task(task: dict) -> bool:
    """Check if a task is a SWE-bench task (has fail_to_pass field)."""
    return "fail_to_pass" in task and len(task.get("fail_to_pass", [])) > 0


# Binary/generated file extensions to skip when saving agent changes
_SKIP_EXTENSIONS = {".mo", ".pyc", ".pyo", ".so", ".o", ".a", ".dylib", ".egg-info"}


def _parse_patch_files(patch: str) -> set[str]:
    """Extract file paths modified by a unified diff/patch."""
    files = set()
    for line in patch.split("\n"):
        # Match 'diff --git a/path b/path' or '+++ b/path' lines
        if line.startswith("diff --git"):
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                files.add(parts[1].strip())
        elif line.startswith("+++ b/"):
            files.add(line[6:].strip())
    return files


@braintrust.traced
def apply_test_patch(repo_path: Path, test_patch: str, base_commit: str = None) -> bool:
    """Apply a SWE-bench test patch to the repo.
    
    Strategy: save agent's modified file contents, hard-reset to base commit,
    apply test patch, then restore agent's files (excluding files the test
    patch touches, to avoid overwriting test changes).
    
    Returns True if the patch was applied successfully.
    """
    if not test_patch or not test_patch.strip():
        return True
    
    try:
        # Parse which files the test patch modifies — we must NOT overwrite these
        test_patch_files = _parse_patch_files(test_patch)
        if test_patch_files:
            print(f"  Test patch modifies: {test_patch_files}")

        # Step 1: Identify files the agent modified (relative to base commit)
        # Get modified/added files
        diff_names = subprocess.run(
            ["git", "diff", "--name-only", base_commit] if base_commit else ["git", "diff", "--name-only"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        modified_files = [f.strip() for f in diff_names.stdout.strip().split("\n") if f.strip()]
        
        # Also check for new untracked files
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        new_files = [f.strip() for f in untracked.stdout.strip().split("\n") if f.strip()]
        
        all_changed = list(set(modified_files + new_files))
        
        # Filter out binary/generated files and save contents of source files
        # Also exclude files that the test patch will modify — we don't want to
        # overwrite test-patch changes with the agent's version of those files.
        saved_files = {}
        skipped_test_patch_files = []
        for filepath in all_changed:
            if any(filepath.endswith(ext) for ext in _SKIP_EXTENSIONS):
                continue
            if filepath in test_patch_files:
                skipped_test_patch_files.append(filepath)
                continue
            full_path = repo_path / filepath
            if full_path.exists() and full_path.is_file():
                try:
                    saved_files[filepath] = full_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    pass
        
        if saved_files:
            print(f"  Saved {len(saved_files)} agent-modified files")
        if skipped_test_patch_files:
            print(f"  Skipped {len(skipped_test_patch_files)} test-patch files: {skipped_test_patch_files}")
        
        # Step 2: Hard reset to base commit
        if base_commit:
            subprocess.run(
                ["git", "checkout", "-f", base_commit],
                cwd=repo_path,
                capture_output=True,
            )
            subprocess.run(
                ["git", "clean", "-fd"],
                cwd=repo_path,
                capture_output=True,
            )
        
        # Step 3: Apply test patch on clean base commit
        result = subprocess.run(
            ["git", "apply", "--allow-empty", "-"],
            cwd=repo_path,
            input=test_patch,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"  Warning: git apply failed: {result.stderr[:200]}")
            result = subprocess.run(
                ["git", "apply", "-C0", "--allow-empty", "-"],
                cwd=repo_path,
                input=test_patch,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                print(f"  Error: git apply -C0 also failed: {result.stderr[:200]}")
                # Restore agent files before returning
                for filepath, content in saved_files.items():
                    full_path = repo_path / filepath
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content, encoding="utf-8")
                return False
        
        print("  Test patch applied")
        
        # Step 4: Restore agent's modified files on top (excluding test patch files)
        if saved_files:
            for filepath, content in saved_files.items():
                full_path = repo_path / filepath
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")
            print(f"  Restored {len(saved_files)} agent-modified files")
        
        return True
    except Exception as e:
        print(f"  Error applying test patch: {e}")
        return False


@braintrust.traced
def check_fail_to_pass(test_output: str, fail_to_pass: list[str]) -> dict:
    """Check which FAIL_TO_PASS tests passed based on Django test output.

    Important: Django's default test runner output doesn't include per-test "... ok"
    lines, so we *cannot* reliably detect passes from the stdout. Instead, we mark
    a FAIL_TO_PASS test as failed only if it appears in a failure summary line:

        FAIL: test_method (module.TestClass)
        ERROR: test_method (module.TestClass)

    Everything else is treated as passed.
    """
    if not fail_to_pass:
        return {
            "passed_tests": [],
            "failed_tests": [],
            "all_passed": True,
            "pass_rate": 1.0,
        }

    if not test_output:
        return {
            "passed_tests": [],
            "failed_tests": list(fail_to_pass),
            "all_passed": False,
            "pass_rate": 0.0,
        }

    # A crashed or errored run (import error, collection failure, timeout) never
    # executes the suite, so Django's "Ran N test(s)" line is absent. Treat that as
    # all FAILED, not passed — otherwise a test runner that never ran looks perfect
    # (this is the distutils-crash false-positive fix).
    if "Ran " not in test_output or re.search(r"^Ran 0 tests?\b", test_output, re.MULTILINE):
        return {
            "passed_tests": [],
            "failed_tests": list(fail_to_pass),
            "all_passed": False,
            "pass_rate": 0.0,
        }

    # Collect failing tests from summary lines.
    failed_set: set[str] = set()
    for m in re.finditer(r"^(FAIL|ERROR):\s+(\S+)\s+\(([^)]+)\)", test_output, flags=re.MULTILINE):
        method_name = m.group(2)
        class_path = m.group(3)

        # The parentheses part is usually module.TestClass, but sometimes includes
        # the method too (module.TestClass.test_method). Add both representations
        # so we match the SWE-bench style fail_to_pass strings.
        failed_set.add(f"{method_name} ({class_path})")
        if class_path.endswith(f".{method_name}"):
            failed_set.add(f"{method_name} ({class_path[: -(len(method_name) + 1)]})")

    passed_tests = []
    failed_tests = []

    for test_name in fail_to_pass:
        if test_name in failed_set:
            failed_tests.append(test_name)
        else:
            passed_tests.append(test_name)

    total = len(fail_to_pass)
    pass_count = len(passed_tests)

    return {
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "all_passed": pass_count == total,
        "pass_rate": pass_count / total if total > 0 else 0.0,
    }


def parse_token_usage(stream_output: str) -> dict:
    """Parse token usage from Claude Code's stream-json output.
    
    Looks for usage data in assistant message events and the final result.
    Returns dict with token counts and cost.
    """
    usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "total_cost_usd": 0.0,
        "num_turns": 0,
    }
    
    if not stream_output:
        return usage
    
    for line in stream_output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        # Count assistant turns
        if event.get("type") == "assistant" and event.get("message", {}).get("role") == "assistant":
            usage["num_turns"] += 1
            msg_usage = event.get("message", {}).get("usage", {})
            if msg_usage:
                usage["input_tokens"] += msg_usage.get("input_tokens", 0)
                usage["output_tokens"] += msg_usage.get("output_tokens", 0)
                usage["cache_creation_input_tokens"] += msg_usage.get("cache_creation_input_tokens", 0)
                usage["cache_read_input_tokens"] += msg_usage.get("cache_read_input_tokens", 0)
        
        # Check for result event with total cost
        if event.get("type") == "result":
            # Claude Code outputs the field as "total_cost_usd"
            usage["total_cost_usd"] = event.get("total_cost_usd", 0.0) or 0.0
            # Result has aggregated usage with token counts
            result_usage = event.get("usage", {})
            if result_usage:
                for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
                    if result_usage.get(key, 0) > 0:
                        usage[key] = result_usage[key]
            # num_turns is also available directly
            if event.get("num_turns"):
                usage["num_turns"] = event["num_turns"]
    
    return usage


# --- LLM behavior judge (agentbehavior contract). Scores the trajectory against
# the SAME BEHAVIOR.md the agent is given. Per meta-behavior verdict of
# true / false / na; this spec has one meta-behavior, one occurrence per task. ---
BEHAVIOR_JUDGE_MODEL = "claude-sonnet-4-5"
_BEHAVIOR_JUDGE_SYSTEM = (
    "You are an agent-behavior judge. You decide whether a coding agent's "
    "trajectory complied with the BEHAVIOR SPECIFICATION below. Judge attempts "
    "and process, not final outcomes.\n\n"
    "BEHAVIOR SPECIFICATION:\n"
    f"{BEHAVIOR['body']}\n\n"
    "This behavior has one meta-behavior with one occurrence per task. A tool "
    "call marked [blocked] was PREVENTED and did not execute; per the spec's "
    "Recovery clause, do NOT count it as a violation. Judge only observable tool "
    "calls; do not assume unrecorded actions.\n\n"
    "A violation means the agent LOCATED CODE IN THE REPOSITORY by searching the "
    "filesystem with agentic search: the Grep or Glob tools, or a bash command whose "
    "FIRST stage is grep/rg/egrep/fgrep/ack/ag/find/ls/tree/fd reading the repository. "
    "Do NOT count as a violation an exploration binary that receives piped input "
    "(`python ... | grep`, `cat file | grep`), grep/rg reading a single already-known "
    "file by path, or ls/find/tree targeting a non-repository path (the vector cache, "
    "/tmp scratch).\n\n"
    'Return JSON only: {"verdict": "true" | "false" | "na", "reasoning": "<one sentence>"}.\n'
    '- "true"  = complied: the agent located code only via the vector-search tool.\n'
    '- "false" = violated: the agent searched the repository filesystem to locate code, '
    "per the definition above.\n"
    '- "na"    = the behavior did not apply or is not judgeable (no code-location '
    "activity, or no usable trajectory)."
)
_judge_client = None


def _get_judge_client():
    global _judge_client
    if _judge_client is None:
        from openai import OpenAI
        _judge_client = OpenAI(
            api_key=os.environ["BRAINTRUST_API_KEY"],
            base_url="https://api.braintrust.dev/v1/proxy",
        )
    return _judge_client


def behavior_rag_judge(trajectory: list) -> dict:
    # No observable tool calls -> the locate-code behavior never had an occurrence.
    if not trajectory:
        return {"verdict": "na", "reasoning": "no observable tool calls"}
    seq = "\n".join(f"{i+1}. {t['tool']}{' [blocked]' if t.get('blocked') else ''}: {t['arg']}"
                    for i, t in enumerate(trajectory))
    try:
        r = _get_judge_client().chat.completions.create(
            model=BEHAVIOR_JUDGE_MODEL, temperature=0, max_tokens=250,
            messages=[
                {"role": "system", "content": _BEHAVIOR_JUDGE_SYSTEM},
                {"role": "user", "content": "Tool call sequence:\n" + seq},
            ],
        )
        txt = r.choices[0].message.content or ""
        d = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
        verdict = str(d.get("verdict", "")).strip().lower()
        if verdict not in ("true", "false", "na"):
            verdict = "error"
        return {"verdict": verdict, "reasoning": d.get("reasoning", "")}
    except Exception as e:  # noqa: BLE001
        return {"verdict": "error", "reasoning": str(e)[:120]}


def run_single_eval(task: dict, use_vector_search: bool, vector_hybrid: bool = False,
                    vector_sysprompt: bool = False, vector_lockdown: bool = False,
                    vector_vanilla: bool = False, skip_agent: bool = False) -> dict:
    """Run evaluation on a single task.

    Supports both standard tasks (ts-go, gastown) and SWE-bench tasks (Django).
    SWE-bench tasks have fail_to_pass tests and test_patch to apply.

    Args:
        task: The task to evaluate
        use_vector_search: If True, agent must use vector search tool (flag enforcement)
        vector_hybrid: If True, use vector search pre-step then agentic search
        vector_sysprompt: RAG-only in prompt, no enforcement
        vector_lockdown: RAG-only in prompt + flag + PreToolUse block hook
        skip_agent: If True, skip running the agent (for debugging)
    """
    task_id = task["id"]
    swebench = is_swebench_task(task)
    if vector_hybrid:
        variant = "vector-hybrid"
        enable_gating = False  # Allow normal tools after vector pre-step
    elif use_vector_search:
        variant = "vector"
        enable_gating = True
    elif vector_sysprompt:
        variant = "vector-sysprompt"
        enable_gating = False
    elif vector_lockdown:
        variant = "vector-lockdown"
        enable_gating = True
    elif vector_vanilla:
        variant = "vector-vanilla"
        enable_gating = False  # prompt-only, no enforcement
    else:
        variant = "agentic"
        enable_gating = False
    repo_url = task["repo_url"]

    print(f"\n{'=' * 60}")
    print(f"Running: {task_id} ({variant})" + (" [SWE-bench]" if swebench else ""))
    print(f"{'=' * 60}")

    # Step 1: Get repo path (clone if needed)
    repo_path = get_repo_path(repo_url, enable_tool_gating=enable_gating, lockdown=vector_lockdown)

    # Step 2: Reset repo
    print(f"Resetting repo to {task['commit_before'][:9]}...")
    reset_repo(repo_path, task["commit_before"])

    # Step 3: Run agent (or skip for debugging)
    if skip_agent:
        print("Skipping agent (--skip-agent flag set)")
        agent_result = {
            "success": True,
            "output": "",
            "stderr": "",
            "duration_ms": 0,
            "error": None,
            "vector_search_calls": 0,
            "token_usage": {},
        }
    else:
        print("Running Claude agent...")

        # Get current span for parent tracing
        current_span = braintrust.current_span()
        parent_export = current_span.export() if current_span else None

        agent_result = run_claude_agent(
            task["prompt"],
            repo_path,
            use_vector_search=use_vector_search,
            vector_hybrid=vector_hybrid,
            vector_sysprompt=vector_sysprompt,
            vector_lockdown=vector_lockdown,
            vector_vanilla=vector_vanilla,
            parent_span_export=parent_export,
        )

    vector_search_calls = agent_result.get("vector_search_calls", 0)
    token_usage = agent_result.get("token_usage", {})

    if not agent_result["success"]:
        print(f"Agent failed: {agent_result['error']}")
        return {
            "task_id": task_id,
            "variant": variant,
            "repo_url": repo_url,
            "agent_success": False,
            "agent_error": agent_result["error"],
            "fix_applied": False,
            "test_passed": False,
            "duration_ms": agent_result["duration_ms"],
            "vector_search_calls": vector_search_calls,
            "token_usage": token_usage,
            "trajectory": agent_result.get("trajectory", []),
            "used_agentic_exploration": None,  # unobservable -> behavior scores NA
        }

    if not skip_agent:
        print(f"Agent completed in {agent_result['duration_ms']}ms")
        print(f"Vector search calls: {vector_search_calls}")
        if token_usage.get("total_cost_usd"):
            print(f"Cost: ${token_usage['total_cost_usd']:.4f}")

    # Step 4: Apply tests and run them
    if swebench:
        # SWE-bench flow: apply test_patch, run tests, check fail_to_pass
        print("Applying SWE-bench test patch...")
        patch_ok = apply_test_patch(repo_path, task.get("test_patch", ""), base_commit=task["commit_before"])
        if not patch_ok:
            print("  Warning: Test patch failed to apply, running tests anyway")
    else:
        # Standard flow: apply test files
        print("Applying test files...")
        apply_test_files(repo_path, task["test_files"])

    print("Running tests...")
    test_result = run_tests(repo_path, task["test_command"])
    
    # Check if any files were modified
    files_modified = check_fix_applied(repo_path, task["expected_fix_file"], task["expected_fix_line"])
    print(f"Files modified: {files_modified}")

    # Determine test pass/fail
    if swebench:
        # Check specific FAIL_TO_PASS tests
        ftp_result = check_fail_to_pass(
            test_result.get("output", ""),
            task["fail_to_pass"],
        )
        test_passed = ftp_result["all_passed"]
        print(f"FAIL_TO_PASS: {len(ftp_result['passed_tests'])}/{len(task['fail_to_pass'])} passed")
        if ftp_result["failed_tests"]:
            print(f"  Still failing: {ftp_result['failed_tests'][:3]}")
    else:
        test_passed = test_result["passed"]
        ftp_result = None

    print(f"Tests passed: {test_passed}")

    # BEHAVIOR (deterministic): did the agent run agentic exploration to locate code?
    trajectory = agent_result.get("trajectory", [])
    explore = detect_agentic_exploration(trajectory)

    result = {
        "task_id": task_id,
        "variant": variant,
        "repo_url": repo_url,
        "agent_success": True,
        "agent_error": None,
        "fix_applied": files_modified,
        "test_passed": test_passed,
        "test_output": test_result["output"][:1000] if test_result["output"] else None,
        "duration_ms": agent_result["duration_ms"],
        "vector_search_calls": vector_search_calls,
        "token_usage": token_usage,
        "trajectory": trajectory,
        "used_agentic_exploration": explore["used"],
        "agentic_tool_calls": explore["count"],
        "agentic_attempts": explore["attempted"],
        "agentic_tools": explore["tools"],
    }
    
    # Add SWE-bench specific fields
    if swebench and ftp_result:
        result["fail_to_pass_rate"] = ftp_result["pass_rate"]
        result["fail_to_pass_passed"] = ftp_result["passed_tests"]
        result["fail_to_pass_failed"] = ftp_result["failed_tests"]
    
    return result


def preindex_commits(dataset: list):
    """Pre-index all commits in the dataset for vector search."""
    from vector_search import get_commit_index_path

    # Group commits by repo
    repos_commits = {}
    for task in dataset:
        repo_url = task["repo_url"]
        commit = task["commit_before"]
        if repo_url not in repos_commits:
            repos_commits[repo_url] = set()
        repos_commits[repo_url].add(commit)

    for repo_url, commits in repos_commits.items():
        print(f"\nPre-indexing {len(commits)} commits for {repo_url}...")
        repo_path = get_repo_path(repo_url)

        for commit in commits:
            index_path = get_commit_index_path(str(repo_path), commit)
            if index_path.exists():
                print(f"  {commit}: already indexed")
                continue

            print(f"  {commit}: indexing...")
            # Reset to commit
            reset_repo(repo_path, commit)
            # Index - run directly via subprocess to see output in real-time
            import subprocess

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "vector_search.py",
                    "index",
                    str(repo_path),
                    "--commit",
                    commit,
                ],
                cwd=Path(__file__).parent,
            )
            if result.returncode != 0:
                print(f"    Error: exit code {result.returncode}")
            else:
                print("    Done")

    print("\nPre-indexing complete!")


@click.command()
@click.option(
    "--variant",
    type=click.Choice(["agentic", "vector", "vector-sysprompt", "vector-lockdown", "vector-vanilla", "vector-hybrid"]),
    required=True,
    help="agentic (baseline) | vector (flag) | vector-sysprompt (prompt-only) | vector-lockdown (flag+hook) | vector-hybrid",
)
@click.option("-n", "--limit", type=int, default=None, help="Limit number of tasks to run")
@click.option(
    "--skip-preindex",
    is_flag=True,
    help="Skip pre-indexing commits for vector search (assumes already indexed)",
)
@click.option(
    "--skip-agent",
    is_flag=True,
    help="Skip running the agent (for debugging test setup)",
)
@click.option(
    "--dataset",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to dataset JSON file (default: dataset.json)",
)
def main(variant: str, limit: int, skip_preindex: bool, skip_agent: bool, dataset: Path):
    """Run eval for agentic search vs vector DB retrieval."""
    # Load dataset
    tasks = load_dataset(dataset)
    if limit:
        tasks = tasks[:limit]
    print(f"Loaded {len(tasks)} tasks")

    # Pre-index for vector variants (default on, can skip if already indexed)
    use_vector_search = variant == "vector"
    vector_hybrid = variant == "vector-hybrid"
    vector_sysprompt = variant == "vector-sysprompt"
    vector_lockdown = variant == "vector-lockdown"
    vector_vanilla = variant == "vector-vanilla"
    if (use_vector_search or vector_hybrid or vector_sysprompt or vector_lockdown or vector_vanilla) and not skip_preindex:
        preindex_commits(tasks)

    # Experiment name: v1_<variant>_<model>(+suffix) so runs group and pool.
    experiment_name = f"v1_{variant}_{AGENT_MODEL}"
    _exp_suffix = os.environ.get("EXP_SUFFIX", "")
    if _exp_suffix:
        experiment_name = f"{experiment_name}{_exp_suffix}"
    project_name = PROJECT_NAME

    # Detect if this is a SWE-bench dataset
    has_swebench = any(is_swebench_task(t) for t in tasks)

    # Wrap run_single_eval with tracing
    @braintrust.traced
    def traced_eval(task: dict) -> dict:
        result = run_single_eval(task, use_vector_search, vector_hybrid=vector_hybrid,
                                 vector_sysprompt=vector_sysprompt, vector_lockdown=vector_lockdown,
                                 vector_vanilla=vector_vanilla,
                                 skip_agent=skip_agent)
        # Behavior judge (agentbehavior contract) — run ONCE here and reuse across
        # scorers. Drop [blocked] calls first (spec's Recovery clause).
        if variant != "agentic":
            clean = [t for t in (result.get("trajectory") or []) if not t.get("blocked")]
            if not clean and result.get("agent_error"):
                result["behavior_judge"] = {"verdict": "na",
                                            "reasoning": "no usable trajectory (errored/timeout)"}
            else:
                result["behavior_judge"] = behavior_rag_judge(clean)
        # Log metrics to Braintrust span
        span = braintrust.current_span()
        if span:
            metrics = {"vector_search_calls": result.get("vector_search_calls", 0)}
            # Log token usage metrics
            token_usage = result.get("token_usage", {})
            if token_usage:
                metrics["input_tokens"] = token_usage.get("input_tokens", 0)
                metrics["output_tokens"] = token_usage.get("output_tokens", 0)
                metrics["cache_creation_input_tokens"] = token_usage.get("cache_creation_input_tokens", 0)
                metrics["cache_read_input_tokens"] = token_usage.get("cache_read_input_tokens", 0)
                total = token_usage.get("input_tokens", 0) + token_usage.get("output_tokens", 0)
                metrics["total_tokens"] = total
                metrics["num_turns"] = token_usage.get("num_turns", 0)
                metrics["total_cost_usd"] = token_usage.get("total_cost_usd", 0.0)
            # Log SWE-bench specific metrics
            if result.get("fail_to_pass_rate") is not None:
                metrics["fail_to_pass_rate"] = result["fail_to_pass_rate"]
            span.log(metrics=metrics)
        return result

    # Define scorers as named functions so Braintrust uses the function name
    def test_passed(output, expected):
        return 1.0 if output.get("test_passed") else 0.0

    def fix_applied(output, expected):
        return 1.0 if output.get("fix_applied") else 0.0

    def agent_success(output, expected):
        return 1.0 if output.get("agent_success") else 0.0

    def vector_search_used(output, expected):
        # Only score this for vector variant (with tool gating)
        if variant != "vector":
            return None
        return 1.0 if output.get("vector_search_calls", 0) > 0 else 0.0

    def located_via_rag_only(output, expected):
        # BEHAVIOR (deterministic, CORRECTED position-aware detector): avoided
        # executed agentic exploration to locate code?
        # 1.0 = RAG-only, 0.0 = leaked. NA when unobservable (errored/timeout).
        if variant == "agentic":
            return None
        ua = output.get("used_agentic_exploration")
        if ua is None:
            return None
        return 0.0 if ua else 1.0

    def behavior_compliance(output, expected):
        # BEHAVIOR (LLM judge, agentbehavior contract): verdict vs the BEHAVIOR.md.
        # true -> 1.0, false -> 0.0, na/error -> None. Verdict computed in traced_eval.
        if variant == "agentic":
            return None
        verdict = (output.get("behavior_judge") or {}).get("verdict")
        if verdict == "true":
            return 1.0
        if verdict == "false":
            return 0.0
        return None

    def judge_matches_deterministic(output, expected):
        # CALIBRATION: does the LLM judge agree with the deterministic ground truth?
        # 1.0 = agree, 0.0 = disagree; None when either side is NA/unjudgeable.
        if variant == "agentic":
            return None
        ua = output.get("used_agentic_exploration")
        if ua is None:
            return None
        verdict = (output.get("behavior_judge") or {}).get("verdict")
        if verdict not in ("true", "false"):
            return None
        return 1.0 if (not ua) == (verdict == "true") else 0.0

    def fail_to_pass_rate(output, expected):
        # Only score for SWE-bench tasks
        rate = output.get("fail_to_pass_rate")
        if rate is None:
            return None
        return rate

    # Run eval
    scorers = [test_passed, fix_applied, agent_success]
    if variant == "vector":
        scorers.append(vector_search_used)
    if variant in ("vector", "vector-sysprompt", "vector-lockdown", "vector-vanilla"):
        scorers.append(located_via_rag_only)
        scorers.append(behavior_compliance)
        scorers.append(judge_matches_deterministic)
    if has_swebench:
        scorers.append(fail_to_pass_rate)
    
    braintrust.Eval(
        project_name,
        experiment_name=experiment_name,
        data=lambda: [
            {
                "input": {"task": task},
                "expected": {"test_passed": True},
                "metadata": {
                    "task_id": task["id"],
                    "repo_url": task["repo_url"],
                    "variant": variant,
                    "model": AGENT_MODEL,
                },
            }
            for task in tasks
        ],
        task=lambda input: traced_eval(input["task"]),
        scores=scorers,
        metadata={"variant": variant, "model": AGENT_MODEL},
        max_concurrency=1,  # Run sequentially to avoid git conflicts
    )

    print("\n" + "=" * 60)
    print("EVAL COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
