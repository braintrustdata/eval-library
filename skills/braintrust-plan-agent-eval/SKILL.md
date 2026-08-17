---
name: braintrust-plan-agent-eval
description: >-
  Plan an evaluation workflow for an LLM application or agent by identifying the product
  decision, expected behavior, target population, evidence, datasets, scorers, validation,
  analysis, and release criteria. Use for broad or early-stage requests such as "help me
  evaluate this agent," "design an eval strategy," "where do we start with evals," or when a
  user describes an agent, a product goal, or a production failure without naming an eval
  artifact. Do not use when the user already names a behavior spec, dataset, sample size,
  scorer, human review, experiment, analysis, release gate, or report — route to that skill.
---

# Plan an agent eval

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/lifecycle-inventory.md`.

## Trigger

- Broad eval requests naming no artifact and no stage.
- An agent, goal, or incident described with no eval scaffolding.
- A stalled effort: metrics exist, but nobody can say which decision they serve.

## Do

1. Restate the product decision in one sentence. Every downstream choice serves it.
2. Inventory existing artifacts against the staged lifecycle in `references/lifecycle-inventory.md`,
   labeling each stage `Confirmed` / `Assumed` / `Needs decision` / `Not yet measurable`.
3. Name the **earliest** missing artifact, not the most interesting one. A gap upstream makes
   every downstream number uninterpretable.
4. Check the two prerequisites teams skip: is the system instrumented well enough to reconstruct
   a failure, and can anyone state what "good" means?
5. Hand off the one stage to do next, its concrete first action, and the reason it blocks the rest.

## Avoid

- Do not walk the whole lifecycle in one pass or produce every artifact at once.
- Do not intercept a request that already names an artifact.
- Do not propose a public benchmark as the starting point; it measures its own construct.
- Do not manufacture process for a low-stakes, reversible decision — say so instead.

## Check

- Decision stated; construct and population named or flagged unknown.
- Every lifecycle stage carries a status label.
- Exactly one recommended next stage, with its blocking reason.
- Assumptions listed separately from confirmed facts.

## Risk

- A broad router over-triggers: it will invent process for someone who asked a narrow question.
  Whenever the request already names an artifact, that artifact's own stage owns the work.
- The earliest gap is usually unglamorous — instrumentation, population definition — and gets
  skipped for scorer work.
- Plans go stale as soon as the product changes. Date it; it is a map, not a contract.

## Braintrust

Read the project before asking — most planning questions answer themselves. Which of the four
objects (`references/platform-mechanics.md` §1) already exist, and in what state? Are datasets
**versioned** (§3)? Are scorers named consistently across experiments, or renamed per run (§5)?
Do experiments record independent variables in metadata, or only scores (§4)? Is anything
scoring production traffic?

Each "no" is a lifecycle gap. Record it in the inventory rather than acting on it here — and
note that the §3 and §4 gaps are the ones with no retroactive fix, which usually makes them the
earliest missing artifact even when they are not the most interesting one.
