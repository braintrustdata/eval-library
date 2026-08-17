# Reference — facet pipelines and topics

Thresholds here are **defaults to justify, not laws**. Quote the hedge with the number.

Platform mechanics carry `[platform]` rather than a guide section. They are product behavior, not
empirical claims — but they go stale the same way, so re-check them against the shipped tool
surface before relying on one externally.

## Choosing the instrument

| You have | You want | Instrument |
| --- | --- | --- |
| A known, stable set of labels | Every item assigned to one | **classifier** |
| A criterion with a defensible 0–1 mapping | A number to track or gate on | **scorer** |
| No label set yet | To find out what the classes even are | **facet** + clustering |

The distinguishing property is that a facet returns **unstructured** high-signal text. That is what
makes clusters discoverable, and it is why a facet is the wrong instrument for enforcement: nothing
constrains its output to a vocabulary, so nothing can be gated on it. `[platform]`

Discovery output is a *hypothesis-generating* artifact. Once a cluster is real and worth tracking,
it graduates into a classifier or a scorer with its own validation — see `validate-eval-scorer`.

## Why the pipeline has a preprocessing stage

Embedding raw traces directly does not work: traces run to millions of tokens against embedding
context windows on the order of 8k, and truncation yields noisy clusters. The Clio approach
summarizes each conversation into **facets** — targeted short summaries (use case, sentiment,
issues) — and clusters those instead. Traces are more complex than conversations, so extracting
something an LLM can read requires a preprocessing step first.
`[platform — after Anthropic's Clio]`

Pipeline: **scope → preprocess spans into text → apply facets → cluster facet outputs → topic map**.
The topic map then classifies new spans, traces, or groups cheaply.

## Preprocessor requirements

A good preprocessor:

- Contains user-provided input, model output, tool calls, and errors.
- Omits superfluous system and debugging information. The minimal useful representation is an array
  of `{"role": "...", "content": "..."}`.
- Returns **atomic top-level array items**, so cross-span deduplication can work.

Anti-patterns, both of which look fine until the topic map is useless:

- One joined transcript string per span — dedup operates on array items and a single string is one
  item, so redundant content survives into every facet call.
- Cross-span state. A custom preprocessor runs independently per source span; there is nowhere to
  keep it. `[platform]`

Test: run the `Task` facet over the candidate preprocessor. Sensible `Task` output is a good proxy
for a sound preprocessor, because `Task` is the facet most dependent on the trace being legible.

## No-match policy

Decide before writing the prompt which outputs are effectively null. The default is to instruct the
model to return `NONE` and set `^NONE$` as the no-match pattern, but the real question is which
values would be useless to cluster — "no issues," "neutral" sentiment, and similar filler produce
large, meaningless clusters that crowd out signal.

Facet execution applies the candidate's `no_match_pattern` and **normalizes every matching output to
`no_match`**. Score that normalized value. Hardcoding source strings into a scorer means the scorer
silently stops working the moment the pattern changes. `[platform]`

## Dataset row shapes

Store the reference, never the preprocessed text — the preprocessor is still under change, and a
materialized snapshot freezes the thing you are iterating on. Deduplicate by the stable identity of
the selected unit. `[platform]`

Span:

```json
{
  "_full_row_id_ref": {
    "object_type": "project_logs",
    "object_id": "<project-id>",
    "row_id": "<span-row-id>",
    "root_span_id": "<root-span-id>"
  }
}
```

Trace:

```json
{
  "trace_ref": {
    "object_type": "project_logs",
    "object_id": "<project-id>",
    "root_span_id": "<root-span-id>"
  }
}
```

Group:

```json
{
  "group_ref": {
    "object_type": "project_logs",
    "object_id": "<project-id>",
    "root_span_ids": ["<root-span-id-1>", "<root-span-id-2>"]
  }
}
```

Sample across time, common traffic, structural variation, edge cases, and likely no-match cases.
Up to ~100 examples is a reasonable validation set where the project has them. `[platform]`

## Inline facet task shape

The eval task must be a facet. Built-in:

```json
{ "global_function": "Task", "function_type": "facet" }
```

Inline — the definition wraps in `inline_function`, not `inline_prompt`, and `model` stays inside it:

```json
{
  "task": {
    "inline_function": {
      "type": "facet",
      "preprocessor": { "type": "inline", "code": "<complete JavaScript preprocessor>" },
      "prompt": "<facet-prompt>",
      "model": "<model>",
      "no_match_pattern": "^NONE$"
    },
    "function_type": "facet",
    "name": "<facet-name>"
  }
}
```

Omit `preprocessor` for the project default, or reference a saved one with
`{"type":"function","id":"<preprocessor-function-id>"}`. `[platform]`

## Default deterministic scorers

Validity and no-match correctness are always deterministic. `Factuality` validates neither, so it
cannot stand in for them; use it only for the semantic-agreement dimension.

```json
[
  {
    "inline_context": { "runtime": "node", "version": "22" },
    "code": "function handler({ output }) { return typeof output === \"string\" && output.trim().length > 0 && output !== \"skipped\" ? 1 : 0; }",
    "function_type": "scorer",
    "name": "Valid facet output"
  },
  {
    "inline_context": { "runtime": "node", "version": "22" },
    "code": "function handler({ output, expected }) { if (typeof output !== \"string\" || typeof expected !== \"string\") return 0; const actualNoMatch = output.trim() === \"no_match\"; const expectedNoMatch = expected.trim() === \"no_match\"; return actualNoMatch === expectedNoMatch ? 1 : 0; }",
    "function_type": "scorer",
    "name": "No-match correctness"
  }
]
```

## Strong-model-as-reference

The ground-truth run uses a strong model where `validate-eval-scorer` would use adjudicated human
labels. This is a **cheaper, weaker tier** and inherits the reference model's blind spots wholesale —
agreement with it is agreement with one model's judgment, not with the construct.

It is adequate for iterating a facet toward a discovery-grade instrument. It does not license
gating, trend reporting, or any external claim. Anchor the reference run itself on a handful of
human-reviewed examples first, so at least the reference is known to be sane.

## Iteration budget

Defaults, to state in advance and justify if changed:

- **≤ 5 experiments** before stopping to reflect and report progress.
- **One hypothesis and one coherent change** per experiment — preprocessor or prompt, not both.
- The same validation slice across iterations; the **test split is touched once**, by the winner.

The discipline exists because facet iteration is unusually easy to overfit: the validation set is
small, the model is cheap enough to rerun freely, and "the output looks better" is available as a
stopping rule at every step.

## Rewind sizing and cost

Clusters need roughly **1,000 labeled units** to come out well. Low-volume projects need a longer
window to reach that; high-volume projects a shorter one. `[platform]`

Count eligible span, trace, or group units over the exact scope, filter, and proposed window. Use
pilot-eval token usage from the frozen pipeline for each facet the rewind will invoke:

```text
cost_per_call_for_facet_i =
  mean_input_tokens_i  / 1,000,000 * $0.05
  + mean_output_tokens_i / 1,000,000 * $0.40

estimated_rewind_cost =
  eligible_units * sampling_rate * sum(cost_per_call_for_facet_i)
```

Per-token rates are the current facet-model rates and date fast — re-derive them rather than
quoting these. Present the eligible count, window, token assumptions, base estimate, and a **20%
uncertainty buffer**, then get approval on the window and the estimate together. `[platform]`

## Facet pipeline contract template

```yaml
facet: <name>
scope: span | trace | group
grouping_key: <metadata field, group scope only>
filter: <e.g. metadata.application = 'foo'>

preprocessor:
  source: project_default | saved:<id> | custom
  validated_on: <n traces, date>
  carries: [user_input, model_output, tool_calls, errors]

output_policy: <what a good 1-2 sentence output looks like>
no_match:
  pattern: <regex>
  excluded_values: <the filler this is meant to catch>

validation:
  reference: strong_model | human_adjudicated
  reference_model: <model, if applicable>
  n_items:
  scorers: [valid_output, no_match_correctness, semantic_agreement]
  experiments_run: <n of budget>
  test_split_touched: <count, should be 1>

deployment:
  automation_id:
  sampling_rate:
  eligible_units:
  estimated_cost: <base + 20% buffer>
  approved_by:
```
