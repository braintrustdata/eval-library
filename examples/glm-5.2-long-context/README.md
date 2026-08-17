# GLM-5.2 long-context retrieval eval

Can GLM-5.2 retrieve exact facts from a large code context, and what happens to latency when the same prefix is sent repeatedly?

This is the runnable core of the Braintrust × Baseten benchmark behind [*Benchmarking GLM-5.2 vs Opus 4.8 for real-world long-context retrieval*](https://www.braintrust.dev/blog/glm-52-vs-opus-48-long-context-retrieval). It builds deterministic questions from the CPython AST, gives the model a 25K- or 50K-token source bundle, and scores the answer against mechanically derived ground truth.

It is intentionally a focused retrieval eval, not a general coding benchmark.

## What it measures

The dataset includes six question families:

| Code | Question | Ground truth |
| --- | --- | --- |
| `RT` | Declared return type | `FunctionDef.returns` |
| `CL` | File defining a class | `ClassDef` location |
| `BC` | Class bases | `ClassDef.bases` |
| `FC` | Module-level function count | Top-level AST nodes |
| `DC` | Function decorators | `decorator_list` |
| `DS` | First docstring line | `ast.get_docstring` |

Some rows rename a function only inside the supplied context. These perturbations check retrieval from the prompt instead of memorized source associations.

Each task makes three sequential calls with the same prompt: one cold call and two warm calls. Only the cold answer is scored. Braintrust child spans record time to first token and total latency for each call.

Scorers:

- `ASTSemanticMatch` is the primary deterministic score and applies question-type-specific rules.
- `SubstringMatch` is a lenient retrieval diagnostic.
- `FactualityJudge` is an optional audit judge, not the headline metric.

## Pinned reproduction inputs

- Model: `zai-org/GLM-5.2`, served through Baseten's OpenAI-compatible API.
- Corpus: CPython tag `v3.13.5`, `Lib/` only.
- Dataset version: `cpython-v3.13.5-seed-42`.
- Tokenizer: `cl100k_base`.
- Context tiers: 25,000 and 50,000 tokens.

The generated JSONL repeats the context on every row and is intentionally not checked in. Its manifest records the corpus SHA-256, seed, tier, and question counts.

## Setup

You need Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
git clone --depth 1 --branch v3.13.5 https://github.com/python/cpython.git .cache/cpython-3.13.5
```

Fill in `.env`:

```dotenv
BRAINTRUST_API_KEY=...  # experiment logging
BASETEN_API_KEY=...     # GLM-5.2 and the optional judge
```

## Build the dataset

```bash
# Fast local smoke dataset
uv run python build_dataset.py \
  --lib-path .cache/cpython-3.13.5/Lib \
  --tier T25 --rows 10 --perturbations 2

# Published shape: 100 rows per tier, 60/40 easy/hard, 20 perturbations
uv run python build_dataset.py \
  --lib-path .cache/cpython-3.13.5/Lib \
  --tier T25 --rows 100 --perturbations 20
uv run python build_dataset.py \
  --lib-path .cache/cpython-3.13.5/Lib \
  --tier T50 --rows 100 --perturbations 20
```

## Run

These commands call paid APIs. The first command validates wiring without making any API calls.

```bash
uv run python run_eval.py --dry-run --limit 1

# Cheapest live smoke test: one row, one model call, deterministic scorers only
uv run python run_eval.py --limit 1 --repetitions 1

# Full T25 latency run: 100 rows × 3 calls
uv run python run_eval.py --dataset datasets/cpython-stdlib-T25.jsonl

# Add the Nemotron audit judge used in the benchmark
uv run python run_eval.py --dataset datasets/cpython-stdlib-T25.jsonl --judge
```

Results log to the Braintrust project `GLM-5.2 Long-Context Retrieval`. Use `--update` to update an experiment with the same name. Use `--trial-count` for repeated independent trials; `--repetitions` controls the sequential cold/warm calls within each row.

## Published results

The compact aggregate data from the June 2026 benchmark is checked in at [`results/glm-5.2-results.json`](results/glm-5.2-results.json). It contains scores, sample counts, cold/warm latency means, run-specific costs, and the source artifact IDs for both context tiers.

| Tier | AST semantic match | Substring match | Factuality judge | Mean cost/trace |
| --- | ---: | ---: | ---: | ---: |
| T25 | 83.3% | 76.7% | 80.7% | $0.0208 |
| T50 | 84.5% | 76.5% | 81.7% | $0.0415 |

The full instance-level exports are not duplicated here because every row embeds the 25K- or 50K-token context, inflating the two GLM JSONL files to roughly 72 MB. The aggregate file preserves the resulting metrics and provenance without committing repeated source text.

## Files

- `build_dataset.py` — deterministic corpus packing, AST question generation, sampling, and perturbations.
- `run_eval.py` — GLM-5.2 task, streaming latency instrumentation, and Braintrust harness.
- `scorers.py` — AST-aware primary scorer, substring diagnostic, and optional LLM judge.
- `test_scorers.py` — unit checks for the scorer's important semantic cases.
- `results/glm-5.2-results.json` — published aggregate results and provenance.
