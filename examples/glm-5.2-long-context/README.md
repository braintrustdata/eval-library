# GLM-5.2 long-context retrieval

Do open-source models fall apart once the context gets long?

We gave GLM-5.2 exact questions over 25K and 50K tokens of CPython source. The questions and answer keys are generated mechanically from the Python AST, so the primary score is code-graded rather than judged by preference. Every prompt is called three times to measure cold and warm latency, and a perturbation control changes symbols inside the supplied code to check whether the model is reading the context instead of repeating memorized facts.

This is the runnable GLM-5.2 portion of Braintrust's [long-context comparison with Opus 4.8 and Sonnet 5](https://www.braintrust.dev/blog/glm-52-vs-opus-48-long-context-retrieval). It is a focused retrieval study, not a general coding leaderboard.

## Result

GLM-5.2's exact retrieval score stayed effectively flat as the context doubled: 83.3% at 25K tokens and 84.5% at 50K. In this run, mean provider cost per trace rose from $0.0208 to $0.0415.

| Context | AST semantic match | Substring match | Factuality judge | Mean cost/trace |
| --- | ---: | ---: | ---: | ---: |
| 25K tokens | 83.3% | 76.7% | 80.7% | $0.0208 |
| 50K tokens | 84.5% | 76.5% | 81.7% | $0.0415 |

The compact aggregate data is published in [`results/glm-5.2-results.json`](results/glm-5.2-results.json), including sample counts, three-run latency means, costs, and source artifact IDs.

Costs are specific to the June 2026 benchmark run. Provider pricing, routing, caching, retries, and serving configuration can change them.

## Study design

### Dataset

The builder sorts the CPython 3.13.5 `Lib/` tree, packs complete files into a 25K- or 50K-token context, and derives six kinds of questions:

| Code | Question | Ground truth |
| --- | --- | --- |
| `RT` | What return type is declared? | `FunctionDef.returns` |
| `CL` | Which file defines this class? | `ClassDef` location |
| `BC` | Which base classes does it inherit from? | `ClassDef.bases` |
| `FC` | How many module-level functions are defined? | Top-level AST nodes |
| `DC` | Which decorators are applied? | `decorator_list` |
| `DS` | What is the first docstring line? | `ast.get_docstring` |

Twenty of the 100 rows in each published tier are perturbation controls. The builder renames a function inside the supplied context and updates the question while leaving the underlying CPython checkout unchanged. A correct answer must follow the prompt-local source.

### Task and traces

Each row sends the same prompt three times in sequence:

1. Cold call—the returned answer is scored.
2. Warm call 1—retained for latency and cache observation.
3. Warm call 2—retained for latency and cache observation.

Braintrust records each call as a child span with time to first token and total latency. The wrapped OpenAI-compatible client records the provider request and token usage.

### Scoring

- `ASTSemanticMatch` is the primary metric. It uses the semantics of each question family: exact numeric equality for counts, order-independent membership for bases and decorators, normalized paths for class locations, and equivalent syntax for return types.
- `SubstringMatch` is a lenient recall diagnostic.
- `FactualityJudge` is an optional Nemotron-based audit signal. It is not the headline metric.

## Reproduce it

### Pinned inputs

- Model: `zai-org/GLM-5.2`, served through Baseten's OpenAI-compatible API.
- Corpus: CPython tag `v3.13.5`, `Lib/` only.
- Dataset version: `cpython-v3.13.5-seed-42`.
- Tokenizer: `cl100k_base`.
- Context tiers: 25,000 and 50,000 tokens.
- Published shape: 100 rows per tier, 60/40 easy/hard split, 20 perturbations.

The generated JSONL repeats the context on every row and is not checked in. Its manifest records the corpus SHA-256, seed, tier, and question counts. The builder rejects a CPython checkout that does not match the pinned version.

### Setup

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

### Build the dataset

Start with 10 rows so you can inspect the generated records before paying for a full run:

```bash
uv run python build_dataset.py \
  --lib-path .cache/cpython-3.13.5/Lib \
  --tier T25 --rows 10 --perturbations 2
```

Build the published 100-row tiers:

```bash
uv run python build_dataset.py \
  --lib-path .cache/cpython-3.13.5/Lib \
  --tier T25 --rows 100 --perturbations 20

uv run python build_dataset.py \
  --lib-path .cache/cpython-3.13.5/Lib \
  --tier T50 --rows 100 --perturbations 20
```

### Run the eval

These commands call paid APIs except where noted.

```bash
# Validate the dataset and harness without calling a model
uv run python run_eval.py --dry-run --limit 1

# Cheapest live smoke test: one row, one call, deterministic scorers
uv run python run_eval.py --limit 1 --repetitions 1

# Full T25 latency run: 100 rows × 3 sequential calls
uv run python run_eval.py --dataset datasets/cpython-stdlib-T25.jsonl

# Add the audit judge used in the published study
uv run python run_eval.py \
  --dataset datasets/cpython-stdlib-T25.jsonl \
  --judge
```

Results log to the Braintrust project `GLM-5.2 Long-Context Retrieval`. Use `--update` to update an experiment with the same name. `--trial-count` controls repeated independent trials; `--repetitions` controls cold and warm calls inside each row.

## What is in this directory

- `build_dataset.py` — deterministic corpus packing, AST question generation, sampling, and perturbations.
- `run_eval.py` — GLM-5.2 task, streaming latency instrumentation, and Braintrust harness.
- `scorers.py` — AST-aware primary scorer, substring diagnostic, and optional LLM judge.
- `test_scorers.py` — unit checks for the scorer's important semantic cases.
- `results/glm-5.2-results.json` — published aggregate results and provenance.

The full instance-level exports are not duplicated here because every row embeds the 25K- or 50K-token context, making the two GLM JSONL files roughly 72 MB. The aggregate file preserves the result and provenance without committing the same source text hundreds of times.
