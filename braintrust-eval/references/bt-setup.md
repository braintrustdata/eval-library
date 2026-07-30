# Braintrust setup

What needs to be installed for this skill to run. Auth (keys) is separate — see
`bt-auth.md`.

Docs: **https://www.braintrust.dev/docs** — the reference for the SDK, CLI, and
MCP server lives here; link the user there rather than guessing at API details.

## SDK

- **Python (preferred):** `pip install braintrust`
- **TypeScript:** `npm install braintrust`

Quick check it imports and sees a key:
```bash
python -c "import braintrust; print('braintrust ok')"
```

## CLI

The `bt` CLI ships with the `braintrust` package. It's used for things the SDK
doesn't cover from code — notably pushing prebuilt logs:

```bash
bt sync push project_logs:"My Project" --in ./out/logs --no-input
```

Other useful subcommands (`bt eval`, `bt push`) are documented in the docs above.

## CLI vs MCP — prefer the CLI

Braintrust also publishes an **MCP server** (query projects/experiments/logs, run
BTQL, summarize experiments), which may be connected in this environment. For this
skill's work, **default to the `bt` CLI (plus the SDK / REST) over the MCP server** —
reach for MCP only when the CLI genuinely can't do the task. Setup for both is in
the docs.

> This file is duplicated into each Braintrust skill on purpose (self-containment);
> keep the copies in sync when it changes.
