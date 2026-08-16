# RAG-only enforcement eval

Does behavior-based scoring catch what output-based scoring misses for a coding agent?

This is the eval behind the Braintrust blog post *"Can behavior scoring catch what output scores miss?"*. It gives a Claude Code coding agent one rule — locate the buggy code only through vector (RAG) search, never through agentic `grep`/`glob`/`find` — and measures both whether the agent *obeyed* the rule and whether its fix *passed the tests*, across four enforcement conditions.

The point: `test_passed` is blind to the rule. An agent can pass the test while ignoring the behavior entirely, and only a behavior scorer sees it.

## What it measures

Each task is a real SWE-bench Django bug. The harness resets the repo to the buggy commit, hands the agent only the issue text, lets it work, then applies the held-out test to check the fix.

Four variants:

| Variant | Enforcement |
| --- | --- |
| `agentic` | No rule. Baseline. |
| `vector-vanilla` | The rule is stated in the system prompt. Nothing stops the agent. |
| `vector` | Rule + `--disallowed-tools Grep,Glob,Read`. |
| `vector-lockdown` | Rule + a `PreToolUse` hook that blocks bash-based exploration. |

Scorers:

- `test_passed` / `fail_to_pass_rate` — output. Did the fix work?
- `located_via_rag_only` — deterministic behavior. Did the agent locate the code through vector search only, checked against its trajectory?
- `behavior_compliance` — an LLM-as-a-judge grading the trajectory against `BEHAVIOR.md`.

The behavior spec (`.agents/behaviors/rag-only/BEHAVIOR.md`) is the grading standard, not the agent's prompt. The agent never sees it. It only informs the judge.

## Setup

You need Python 3.12+, [`uv`](https://docs.astral.sh/uv/), and the [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) installed and signed in (the agent runs headless via `claude -p`).

```bash
uv sync                # or: pip install -e .
cp .env.example .env   # then fill in the keys
```

`.env`:

```
BRAINTRUST_API_KEY=...   # from braintrust.dev — results log here
ANTHROPIC_API_KEY=...    # only if you are not signed in to the Claude Code CLI
OPENAI_API_KEY=...       # optional — vector-search embeddings; falls back to the Braintrust proxy
```

## Run

```bash
# smoke-test one variant on a single task
python run_eval.py --variant vector-vanilla -n 1 --dataset dataset_30.json

# full variants (n=30 each)
python run_eval.py --variant agentic         --dataset dataset_30.json
python run_eval.py --variant vector-vanilla  --dataset dataset_30.json
python run_eval.py --variant vector          --dataset dataset_30.json   # tool flag
python run_eval.py --variant vector-lockdown --dataset dataset_30.json   # hook
```

Results log to a Braintrust project (`Behavior vs Output-Only Judge` by default — change `PROJECT_NAME` in `run_eval.py`). Open the experiment to compare the output scorer against the two behavior scorers side by side.

## Files

- `run_eval.py` — the harness: variants, scorers, and the LLM judge
- `.agents/behaviors/rag-only/BEHAVIOR.md` — the behavior spec the judge grades against (never shown to the agent)
- `claude-plugin/hooks/` — the `PreToolUse`/session hooks; `pre_lockdown_block.sh` is what makes the lockdown variant airtight
- `claude-plugin/managed-settings.json` — Claude Code settings applied during a run
- `run_vector_search.sh` / `vector_search.py` — the vector-search tool the agent is given (ChromaDB + embeddings)
- `generate_swebench_dataset.py` — builds the SWE-bench Django task set
- `dataset_30.json` — 30 Django tasks, ready to run

## Notes

The eval must run under Python 3.12 (via `uv`), not a newer system Python. Old Django imports `distutils`, which was removed in Python 3.12+ standard installs but is present in the pinned environment; running the tests under the wrong interpreter silently misreports results.

Dataset derived from [SWE-bench](https://www.swebench.com/) (Jimenez, Yang, et al., ICLR 2024).
