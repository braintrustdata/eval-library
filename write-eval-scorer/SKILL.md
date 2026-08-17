---
name: write-eval-scorer
description: >-
  Design, implement, edit, or audit narrow eval scorers for LLM applications and agents,
  including deterministic checks, reference or final-state comparisons, trace and tool-call
  checks, and anchored LLM-as-judge rubrics. Use when translating one observable criterion into
  scoring logic, choosing between deterministic and judge-based scoring, repairing a vague
  rubric, or defining handling for refusals, errors, timeouts, and parse failures. Do not use to
  validate scorer agreement against human labels or to design the human review workflow.
---

# Write one eval scorer

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/scorer-patterns.md`.

## Trigger

- "Write a scorer for this criterion." / "Should this be deterministic or a judge?"
- Turning a behavior-spec clause or evidence-map signal into a check.
- A rubric producing inconsistent scores, or a scorer bundling several qualities.

## Do

1. Name **one** criterion, and its output contract: a **score** (0–1, needs a numeric mapping) or
   a **classification** (one label from a fixed set, needs no-match behavior). If the request
   combines several criteria, split them before writing any code or rubric.
2. Match the method to the evidence — and let **stakes override convenience**. Objective →
   deterministic. Subjective → anchored rubric or human. A checkable outcome on a
   safety-critical path still needs sampled human review, because what is most likely wrong is
   the check's *scope*.
3. Set two **independent** axes and keep them apart. **Input scope** — span, trace, or group; how
   much one evaluator call sees, default trace. **Reporting level** — per-item scoring localizes
   failures, aggregate detects regressions. Most criteria need both reporting levels.
4. For rubrics, write criteria as **anchored examples, not descriptions**, each scored
   separately, requiring structured output that carries the evidence used. Have the model emit
   **semantic classes, not numbers**, and map classes to scores outside the model.
5. Define failure handling, keeping the kinds apart: **system** failures (refusal, invalid
   output, wrong state) are scored, never dropped; **harness** failures (your own parallelism,
   exhausted credits) are missing data in the status field.
6. Version the scorer and pin the version in experiment metadata.

## Avoid

- Do not use a judge where objective state can be checked deterministically, or a judge from the
  same model family as the system under test.
- Do not combine unrelated qualities into one score.
- Do not silently drop errors, refusals, or unparseable outputs.
- Do not tune the scorer until the numbers improve — adopting a normalizer *after* seeing which
  arm it helps is scorer-side p-hacking.
- Do not validate the scorer here.

## Check

- Exactly one criterion; method justified by evidence type **and** stakes.
- Tested against clear successes, clear failures, edges, refusals, timeouts, parse failures.
- Returns interpretable evidence, not just a number.
- Order counterbalanced in pairwise setups; length sensitivity checked.
- Versioned; known artifacts documented with the arms they disadvantage.

## Risk

- Judge bias — self-preference, position, verbosity — produces confident, invalid scores.
- A judge reads text the system under test wrote, and that text can address the judge directly.
  The bias controls assume a miscalibrated judge, not one being spoken to — contract §9.
- A scorer without trace access can only judge the final answer, however the criterion was
  written.
- Silent exclusions are the most dangerous failure: the aggregate answers "how did the system do
  on the items that survived" while appearing to answer the question asked.

## Braintrust

Deterministic criteria → **code scorers**; subjective → **rubric scorers**. Shared mechanics:
`references/platform-mechanics.md`. **§5** is the one this stage creates rather than consumes —
one criterion, one scorer, one name, chosen here and depended on by every downstream diff.

Scores in native `scores` (0–1); the judge's **evidence in span output**, which is what makes a
disagreement adjudicable during validation; **scorer name and version in span metadata**, so a
rubric revision traces to the results it changed.

The harness-vs-system split needs two destinations: system failure → a real score in `scores`;
harness failure → the per-item **status** field, excluded from the aggregate. If both land in
`scores`, the aggregate silently becomes "performance on surviving items" with no way to recover
the distinction.

Iterate the definition **inline before saving it**, then save, then re-test the *saved* version on
the same examples — saving is a step that can change behavior, and only the second test catches it.
Default the judge to a small model and escalate on measured failure, not on the suspicion that a
bigger one would do better; judge cost is paid per item on every run, forever. Getting a saved
evaluator onto live traffic — rule, sampling, activation, backfill — is
`deploy-braintrust-evaluator`.
