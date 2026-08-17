---
name: discover-trace-topics
description: >-
  Design, evaluate, and deploy a Topics pipeline that discovers clusters in trace traffic —
  preprocessor, facet prompt, no-match policy, clustering, and the automation that runs it. Use
  when the label set is unknown and has to come out of the data: finding what a product is
  actually used for, surfacing recurring issues, or building the categorical vocabulary a
  classifier will later enforce. Also use to evaluate or repair an existing facet or
  preprocessor. Do not use when the label set is already known and stable — that is a classifier
  — or to run a hypothesis-driven or adversarial failure hunt.
---

# Discover topics in trace traffic

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/facet-pipeline.md`.

## Trigger

- "What are people actually using this for?" / "What kinds of issues are in our traffic?"
- No label set exists yet and one has to come out of the data.
- An existing facet producing vague, duplicated, or mostly-skipped output.
- A classifier proposal where nobody can enumerate the classes.

## Do

1. Pick the instrument before building one. Known, stable label set → **classifier**. Label set
   unknown and to be discovered → **facet + clustering**. A facet returns 1–2 sentences of
   unstructured, high-signal text; that looseness is exactly what makes clusters findable, and
   exactly what makes it the wrong tool for enforcement.
2. Fix **scope** first — span, trace, or group — and name the grouping key for group scope.
   Default to trace.
3. Get the **preprocessor** right before touching the facet prompt. It must carry user input,
   model output, tool calls, and errors, and drop system and debug noise. **Run it on real
   traces**; do not reason about what it would return.
4. Write the **output policy** before the prompt: what a good facet output looks like, and what
   counts as no-match. Outputs like "no issues" or "neutral" cluster into nothing — they are
   excluded, not scored.
5. Build ground truth with the **strong model**, then evaluate the **cheap facet model** against
   it. Deterministic scorers for output validity and no-match correctness; a semantic-agreement
   scorer for the rest.
6. Iterate under a budget stated in advance (`reference.md`): one hypothesis, one coherent change
   to preprocessor *or* prompt, rerun the same validation slice. Run the winner **once** on the
   untouched split.
7. Estimate the backfill cost and get explicit approval before rewinding.

## Avoid

- Do not enable an automation before validating the facet on the user's own data.
- Do not use a facet where the classes are already known — you are paying discovery cost for
  enforcement work, and getting an unvalidated instrument.
- Do not return one joined transcript string per span from a preprocessor; deduplication operates
  on atomic array items and a joined string defeats it.
- Do not store preprocessed text in the eval dataset. Store the reference and let the pipeline
  re-derive the text, or you are evaluating a frozen snapshot of a preprocessor you are still
  changing.
- Do not keep tuning against the same slice once the budget is spent.

## Check

- Scope named, grouping key named for group scope.
- Preprocessor **executed** on real traces, not assumed; output carries input, output, tool calls,
  and errors, with no system or debug noise.
- No-match policy defined and its pattern tested against real skip cases.
- Facet validated against reviewed examples before any automation is enabled.
- Iteration budget stated up front; test split touched once.
- Backfill cost estimated, presented with its uncertainty, and approved.

## Risk

- Good clusters follow from good facets. A bad preprocessor is invisible until the topic map is
  useless, and by then the cost is already spent.
- Mostly-skipped or duplicated facet output reads as "no signal in this traffic" when it is almost
  always an instrumentation or preprocessing failure.
- A facet promoted into an enforcement role is an unvalidated classifier with no fitness verdict
  attached.
- Clustering finds structure in anything. A clean-looking topic map is not evidence that the facet
  measures what you think it measures.

## Braintrust

**Preprocessor.** `get_project_settings` for the configured and effective defaults; the built-in
`thread` returns the LLM messages per span and the machinery dedups across them. Run
`project_default` on current traces and confirm non-null output before assuming it works — custom
tracing formats are where it silently returns `[]`. A custom preprocessor is TypeScript in QuickJS,
runs independently per source span with no cross-span state, and must return atomic top-level array
items; the system merges them in trace order and exact-dedups. `test_preprocessor_on_trace` before
attaching. If you write one and the project default is still `thread`, set it as the project default
so existing and new facets inherit it.

**Evaluating the facet.** Dataset rows carry **references, never materialized text** (`trace_ref`,
`group_ref`, `_full_row_id_ref` — shapes in `reference.md`). Ground-truth run: `run_eval` with the
facet as task, `expected` unset, **no scorers**; spot-check the outputs. Subsequent runs pass
`{"experiment_name": "<reference-experiment>"}` as the dataset so those outputs become `expected`.
Inline facet tasks wrap the definition in `inline_function` — not `inline_prompt`, not fields
directly under `task`. Facet execution normalizes any `no_match_pattern` hit to `no_match`, so score
the **normalized value**, never source strings like `NONE` or `Neutral`.

**Saving and deploying.** `create_preprocessor`, then `create_facet` with the evaluated prompt and
no-match behavior, then re-run a few reviewed examples through the saved facet to confirm
persistence did not change its behavior. Reuse an existing automation only when data source, scope
and grouping, filter, preprocessor, sampling, topic window, **and** generation cadence are all
compatible — matching scope and filter alone is not sufficient. Sharing an automation batches facet
calls, which is the reason to bother. Pass `automation_id` explicitly whenever more than one exists.

Rewind sizing and the cost formula are in `reference.md`. Present eligible count, window, token
assumptions, base estimate, and uncertainty buffer, and get approval on the window *and* the
estimate — permissions checks on the mutating tool are not a substitute for approving a spend.
