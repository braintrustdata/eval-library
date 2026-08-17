---
name: braintrust-deploy-evaluator
description: >-
  Take a validated scorer or classifier from definition to running instrument in Braintrust —
  scope selection, inline testing before saving, saving as an evaluator, attaching an
  online-scoring rule, activating it for new traffic, and backfilling history with a rewind. Use
  when a scorer needs to actually run against production logs, when an online-scoring rule needs
  to be created or changed, or when historical traces need scoring. Do not use to decide what the
  scorer should measure, to write its rubric, or to establish that it agrees with human judgment.
---

# Deploy an evaluator to production traffic

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/evaluator-deployment.md`.

## Trigger

- "Run this scorer against our logs." / "Score the last two weeks."
- A validated scorer that still only exists inside an offline experiment.
- An online-scoring rule to create, retarget, resample, or pause.
- Backfilling a newly deployed evaluator over history.

## Do

1. Confirm the evaluator has a **fitness verdict** before deploying it. Trend monitoring and
   release gating are different approvals; a scorer cleared for one is not cleared for the other.
   No verdict yet → `braintrust-validate-eval-scorer` first.
2. Fix **scope** — span for a single LLM call or tool call, trace for behavior spanning a request,
   group for behavior spanning several traces joined by a key. Default to trace. Confirm the
   grouping key exists in real metadata rather than assuming it.
3. Fix the **output contract**: a scorer returns 0–1 and needs its numeric mapping; a classifier
   returns one of a fixed label set and needs its no-match behavior. Declare skip behavior for
   both.
4. **Test inline before saving.** Iterate on the definition against representative examples with
   no saved artifact, then save, then re-test the *saved* version on the same examples — saving is
   a step that can change behavior, and the second test is what catches it.
5. Treat **activation** and **rewind** as two separate authorizations. Neither implies the other.
   A paused rule will not process a rewound range until it is activated; say so rather than
   letting the user believe the backfill is running.
6. Before rewinding, **estimate the eligible target count** over the exact rule configuration and
   window, and account for the sampling rate in the number you report.
7. After results land, read the distribution and inspect representative passes, failures, and
   borderline cases before drawing any conclusion from the aggregate.

## Avoid

- Do not deploy an evaluator whose approved uses are undocumented — absence of a verdict is not
  approval for trend monitoring.
- Do not set 100% sampling without explicit approval; sampling rate is the primary cost control.
- Do not resubmit a rewind to check on it. Resubmission is not a progress query.
- Do not rename an evaluator across deployments (`references/platform-mechanics.md` §5) — the
  name is the join key for every cross-experiment and offline-to-online comparison.
- Do not report a preliminary backfill aggregate without saying it is preliminary.

## Check

- Fitness verdict exists and names this deployment's use as allowed.
- Scope justified; grouping key verified present in real data.
- Output contract declared, including skip and no-match behavior.
- Inline test passed, then the saved version re-tested on the same examples.
- Sampling rate and filters approved; rule status intentional, not defaulted into.
- Rewind window and estimated target count stated before the rewind, not after.

## Risk

- An evaluator deployed without a verdict produces an authoritative-looking series that no one can
  say is valid, and it accumulates history that later looks like a baseline.
- Activation and rewind get conflated constantly. The usual outcome is a user who believes history
  is being scored while a paused rule does nothing.
- Backfill cost scales with eligible units × sampling and is easy to underestimate by an order of
  magnitude on a high-volume project.
- Judge drift under a provider model update is indistinguishable from a product regression in the
  resulting series unless the evaluator version is recorded alongside it.

## Braintrust

**Build and test.** `sql_query` first to find representative data and locate where the behavior
actually appears — `input`, `output`, `metadata`, or elsewhere. Code evaluators (Python or
TypeScript) for anything checkable without a model; LLM evaluators where judgment is required.
Follow the project's existing language. Test with `test_evaluator` and
`function: {inline_evaluator: <definition>}` — the same definition `create_evaluator` accepts, no
save required. Inline code must define a top-level function named `handler`.

**Save.** `create_evaluator` with `output_type: "score"` and `choice_scores` for numeric output, or
`output_type: "classification"` and `choices` for labels. Code evaluators declare `output_type` but
use neither. Then re-run `test_evaluator` with `function: {function_id: "<saved id>"}` on the same
examples to confirm the save round-tripped.

**Rule.** `update_online_scoring_rule` with `operation: "save"`, the evaluator `function_ids`,
scope, filters, sampling rate, and logging behavior. New rules default to `status: "paused"`; pass
`status: "active"` only on explicit authorization. When updating an existing rule, **omit `status`**
to preserve its lifecycle state unless a change was requested. Activate separately via
`set_automation_status`.

**Rewind.** Estimate first with `sql_query` — count spans for span scope, distinct traces for trace
scope, distinct grouping values for group scope — then apply the sampling rate. Call
`update_online_scoring_rule` with `operation: "rewind"`, the `automation_id`, and an inclusive
`start_time`, **once**. For a natural-language window, resolve the timestamp yourself and state the
plan ("the last three full days, roughly 1,400 spans") rather than making the user confirm arithmetic.

**Read the results.** Distribution first, then representative cases at both ends and the boundary.
`generate_monitor_chart` for a histogram of score distribution or a time series of trend; group by a
category only where it improves interpretation. Keep previews unsaved unless asked to persist.
Preprocessors and the `{{preprocessed}}` variable for trace- and group-scoped LLM evaluators are
covered in `braintrust-discover-trace-topics`.
