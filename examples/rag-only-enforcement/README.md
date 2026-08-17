# RAG-only enforcement for coding agents

Can a coding agent pass the tests while breaking the rule you gave it?

This eval gives a Claude Code agent one process constraint: locate the buggy code through vector search, never through agentic `grep`, `glob`, or `find`. It then runs 30 real SWE-bench Django tasks under four enforcement setups and scores two separate outcomes: whether the patch works and whether the agent followed the required behavior.

That distinction is the study. `test_passed` can tell you that the final patch is correct. It cannot tell you whether the agent used an approved data source, respected a safety boundary, followed a tool policy, or took a prohibited shortcut. For those claims, the trajectory is part of the output.

## What this eval shows

Output scoring and behavior scoring answer different questions:

- **Did the fix work?** Apply the held-out test and score the patch.
- **Did the agent follow the rule?** Inspect the tool trajectory for prohibited search behavior.
- **Did stronger enforcement change either outcome?** Compare the same task set across four conditions.

The example puts all three scores beside one another in Braintrust so a passing patch cannot hide a process violation.

## Study design

### Dataset and task

Each row is a real SWE-bench Django issue. The harness checks out the buggy commit, gives the agent only the issue text, lets it edit the repository, then applies the held-out test to the resulting patch.

The checked-in `dataset_30.json` contains 30 tasks. Every enforcement condition runs against the same set.

### Four enforcement conditions

| Variant | What changes |
| --- | --- |
| `agentic` | No RAG-only rule. This is the unconstrained baseline. |
| `vector-vanilla` | The system prompt states the rule, but nothing enforces it. |
| `vector` | The rule is paired with `--disallowed-tools Grep,Glob,Read`. |
| `vector-lockdown` | A `PreToolUse` hook also blocks shell-based exploration before it runs. |

This progression separates a written instruction from tool restrictions and hard runtime enforcement.

### Three views of success

- `test_passed` / `fail_to_pass_rate` — deterministic output score. Did the held-out test pass?
- `located_via_rag_only` — deterministic behavior score. Did the trajectory show only approved code-location behavior?
- `behavior_compliance` — LLM audit of the trajectory against the versioned behavior specification.

The behavior specification lives at `.agents/behaviors/rag-only/BEHAVIOR.md`. It is the grading standard, not part of the agent prompt. The agent never sees it; the deterministic scorer and judge use it to decide what counts as compliant behavior.

## Reproduce it

### Setup

You need Python 3.12, [`uv`](https://docs.astral.sh/uv/), and the [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) installed and signed in. The agent runs headlessly through `claude -p`.

```bash
uv sync
cp .env.example .env
```

Fill in `.env`:

```dotenv
BRAINTRUST_API_KEY=...  # experiment logging
ANTHROPIC_API_KEY=...   # only if Claude Code is not already signed in
OPENAI_API_KEY=...      # optional; vector embeddings otherwise use the Braintrust proxy
```

### Run a smoke test

Start with one task and the prompt-only condition:

```bash
uv run python run_eval.py \
  --variant vector-vanilla \
  -n 1 \
  --dataset dataset_30.json
```

### Run the full comparison

These commands run a coding agent and may cost money.

```bash
uv run python run_eval.py --variant agentic         --dataset dataset_30.json
uv run python run_eval.py --variant vector-vanilla  --dataset dataset_30.json
uv run python run_eval.py --variant vector          --dataset dataset_30.json
uv run python run_eval.py --variant vector-lockdown --dataset dataset_30.json
```

Results log to the Braintrust project `Behavior vs Output-Only Judge`. Open the experiments together to compare functional success with deterministic and judge-based behavior compliance.

## What is in this directory

- `dataset_30.json` — the 30 Django tasks used by every condition.
- `run_eval.py` — experiment variants, repository setup, agent harness, tests, and scorers.
- `.agents/behaviors/rag-only/BEHAVIOR.md` — the versioned grading standard for compliant behavior.
- `claude-plugin/hooks/` — tracing and enforcement hooks; `pre_lockdown_block.sh` implements the strict condition.
- `claude-plugin/managed-settings.json` — Claude Code settings applied during a run.
- `run_vector_search.sh` and `vector_search.py` — the ChromaDB-backed search tool available to the agent.
- `generate_swebench_dataset.py` — the script used to build the checked-in task set.

## Reproduction note

Run the eval through the `uv` environment configured for this example. The pinned environment supplies compatibility needed by the older Django checkouts; using a newer system Python can make dependency failures look like task failures and silently corrupt the result.

The dataset is derived from [SWE-bench](https://www.swebench.com/) (Jimenez, Yang, et al., ICLR 2024).
