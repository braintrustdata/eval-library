# Tracing `claude -p` subprocess agents (trace-claude-code plugin)

For agentic evals where the task spawns headless Claude Code (`claude -p`):
Braintrust's `trace-claude-code` plugin (repo:
`braintrustdata/braintrust-claude-plugin`, open source) hooks every session
event and logs the agent's **full internal trace** — session root → turns →
every tool/MCP call with inputs+outputs — to Braintrust. A working in-repo
example of the env setup and parent-span nesting is
`rag-only-enforcement/run_eval.py`.

## The recipe (what actually works)

1. **Config is env-only**: `TRACE_TO_BRAINTRUST=true`,
   `BRAINTRUST_CC_PROJECT=<project NAME — never an id>`,
   `BRAINTRUST_API_KEY=<org key>`.
2. **Deliver it via `--settings <file>`, not the subprocess env.** The user's
   `~/.claude/settings.json` env block **overrides subprocess env vars**, so a
   stale global value silently hijacks tracing. A `--settings` file outranks
   user settings. Generate it at runtime (never commit — it holds the key),
   `chmod 600`, gitignore it — a temp JSON file holding just an `env` block with
   the three variables above, passed to `--settings`.
3. **Traces land in project Logs, never in experiments** (the plugin inserts
   via `/v1/project_logs`). Cross-link instead of nesting: the trace's root
   span id == the run's `session_id` (already in `claude -p --output-format
   json/stream-json` output) → store
   `agent_trace_url = .../p/<project>/logs?r=<session_id>` in the experiment
   span's metadata. One click from experiment row → full agent internals.

## Verify — never assume it's tracing

Hooks swallow every failure by design, so broken tracing looks identical to
working tracing from the outside. After a smoke run, count spans per session:

```
BTQL: select: id from: project_logs('<project_id>')
      filter: root_span_id = '<session_id>'
```

Expect ~15–50 spans for a real agent run. 0 spans → read
`~/.claude/state/braintrust_hook.log` (with `BRAINTRUST_CC_DEBUG=true`), and
check the failure catalog below.

## Failure catalog (all hit in practice, 2026-07)

- **"Failed to get project" + project name is a UUID** → a settings-file env
  block is overriding `BRAINTRUST_CC_PROJECT` (see recipe #2), and/or the
  config passes a project id where the plugin wants a name.
- **State file corrupt (e.g. 1 byte)** → the plugin's shared
  `~/.claude/state/braintrust_state.json` uses unlocked read-modify-write;
  **concurrent sessions corrupt it**, after which ALL tracing dies machine-wide
  until the file is deleted. Immediate fix: delete the file. If you need
  concurrent tracing before the upstream fix lands, the workaround is atomic
  temp+rename writes, self-healing reads, and per-session state sharding in the
  plugin's `hooks/common.sh` — but a plugin update overwrites any local patch, so
  re-check after every update.
- **Latent parse bug** the above masks: `get_project_id` reads `.id` from
  `GET /v1/project?project_name=...`, which returns `{"objects":[...]}` — only
  the POST-create fallback (which returns the existing project) saves it.
- **Env leakage quirk**: a nested claude with `CLAUDECODE=1` still in its env
  skips settings-env application — which can make ad-hoc manual tests behave
  differently from a scrubbed-env harness. Test with the harness's exact env.

## Cost/latency

Each hook is a curl per event (~30–60 per agent run). Negligible next to
agent runtime; keep `BRAINTRUST_CC_DEBUG=true` during setup, drop it for
long runs if the log file's growth bothers you.
