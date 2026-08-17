---
name: braintrust-design-eval-metric-bundle
description: >-
  Create, edit, audit, or compare a multi-objective eval metric bundle covering product
  quality, safety, reliability, latency, and cost. Use to choose metrics for an eval, define a
  goodness bundle, distinguish optimization metrics from non-regression guardrails, expose
  tradeoffs, audit a KPI or single composite score for Goodhart and metric-gaming risk, or
  answer "what should improve and what must not regress." Do not use to design trace schemas,
  build datasets, or implement scoring methods.
---

# Design the metric bundle

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/metric-bundle.md`.

## Trigger

- Requests to choose metrics, define "good," or set targets.
- A single headline KPI or composite score driving a ship decision.
- A targeted change being judged by a whole-response average.

## Do

1. Draft the bundle from the objective before asking anything. Cover quality, safety,
   reliability, latency, and cost as **separate** measures — never averaged.
2. Assign each metric a **decision role**: *improve* (the target) or *guardrail* (must not
   regress). Guardrails are constraints, never terms in a weighted sum.
3. Give each metric a direction, threshold type (point estimate vs. upper confidence bound —
   safety rates need the bound), proxy limitation, and named gaming path.
4. Derive each metric from the **causal path** of the change. If the intervention can only
   alter part of the output, the primary metric is restricted to the items and fields it can
   touch, with the aggregate beside it as blast radius.
5. Make cost the production-honest number: cost per **resolved** request, not token price.
   Retries, fallbacks, and human cleanup mean the cheapest model is rarely the cheapest system.

## Avoid

- Do not collapse distinct constructs into one score.
- Do not treat a proxy as the outcome; keep the limitation attached.
- Do not adopt a metric whose scope cannot show the effect under test — a diluted metric
  manufactures confident null results.
- Do not set thresholds from current numbers; derive them from product tolerances and fix them
  before the run.
- Do not make metrics observable or implement them.

## Check

- Every metric has direction, decision role, threshold type, proxy limitation, gaming path.
- All five dimensions represented or explicitly waived with a reason.
- At least two proxies for any outcome consequential enough to gate on.
- Targeted changes carry a narrow primary metric plus the aggregate.

## Risk

- Under optimization pressure the system finds the shortest path to the score, not the outcome:
  unit-test pass rate yields trivially passing suggestions, judge scores yield prompt gaming.
- A single dominant KPI hides regressions by construction.
- Thresholds without uncertainty are decorative — a point estimate crossing a line is not
  evidence the underlying rate did.

## Braintrust

**One scorer per metric** (`references/platform-mechanics.md` §5) — the bundle only works if a
regression in one dimension is visible as its own column. Scores in native `scores` (0–1),
tokens/latency/cost in **native metrics** so cost and quality stay separable. Guardrails become
**experiment-level regression gates**, not charts someone reads; a guardrail in a chart gets
traded away. Upper-bound thresholds (safety) need the bound in a custom column so the gate
reads the right value. Cost per *resolved* request is derived, not native: a resolution scorer
gating the non-negotiables, native cost metrics, then the ratio as a custom column. Run the
same scorers on production traffic via online scoring — a bundle that exists only offline
cannot answer the validation question.
