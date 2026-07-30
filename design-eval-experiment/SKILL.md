---
name: design-eval-experiment
description: >-
  Design or audit controlled eval experiments for model, prompt, retrieval, tool, guardrail, or
  agent-architecture changes. Use before data collection to state directional and minimum-effect
  hypotheses, name independent, dependent, and control variables including the serving
  environment and tool surface, choose paired designs, set repetitions and allocation,
  distinguish exploratory from confirmatory comparisons, and pre-specify stopping, exclusion,
  multiplicity, and analysis rules. Do not use primarily to analyze results already collected.
---

# Design the experiment

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/experiment-manifest.md`.

## Trigger

- A planned comparison: prompt A vs. B, M0 → M1, retrieval on/off, a new guardrail.
- "Write a hypothesis." / "Create a pre-analysis plan." / "Name the stopping rule."
- A sweep about to run with no plan for how the winner gets confirmed.

## Do

1. Convert the change into **one tradeoff-aware hypothesis**: directional, minimum effect,
   naming what may not regress, plus population, proxies, and scorers. This **is** the release
   gate stated in advance.
2. Name independent, dependent, and control variables (`reference.md`). Any control that matters
   must be a schema field, or it cannot be held constant or sliced by.
3. Pin what hides inside apparently atomic variables: the **serving path** behind a model
   string, the **tool manifest** behind "the agent." If more than one thing changes per arm, the
   design cannot attribute the effect to any single factor — isolate first.
4. Choose **pairing** (same items across arms — the default, far more sensitive) and K = 3–5 runs
   for anything gating.
5. **Verify the treatment is implementable in every arm.** Publish the per-arm implementation
   table, and exclude arms that cannot receive it from the treatment-effect claim rather than
   recording them as "no benefit."
6. Pre-specify stopping, exclusions, exploratory vs. confirmatory, multiplicity, and estimators —
   the elicitation regime dictates the estimator.

## Avoid

- Do not choose the analysis after seeing outcomes, or relabel a sweep as confirmatory.
- Do not fix a defect mid-comparison. Restart under the corrected config, or finish as designed
  and record the defect — a mid-run correction leaves no trace in the results table.
- Do not run unbounded parallelism; it is the most productive source of fake failures.
- Do not analyze results here.

## Check

- One hypothesis with direction, minimum effect, and guardrail bounds.
- All three variable classes enumerated; every control exists as a field.
- Serving environment and tool manifest pinned per arm.
- Pairing and K stated; stopping rules fixed; exploratory vs. confirmatory labeled in advance.
- Per-arm treatment implementation table drafted; manifest reproducible.

## Risk

- Flexible stopping, undocumented arms, and uncontrolled changes make an apparent improvement
  indistinguishable from selection noise.
- A treatment with no uniform implementation quietly becomes several treatments.
- Metered ceilings fail in the worst available way — partway through one arm, leaving a partial
  result that resembles data.
- Confounds enumerated on a whiteboard stay there unless they become fields.

## Braintrust

**Write H1 into the experiment description** so the pre-registered claim travels with the
results — the cheapest integrity control available. Mark the confirmatory run explicitly in its
**name and description**.

Encode each arm as an experiment **pinned to the same dataset version** (this is what makes
cross-arm diffs item-paired, and why pairing must be decided before running). Record independent
variables in **experiment metadata**: model string, decoding params, prompt/scorer versions,
serving path, tool manifest. Keep sweep arms as **separate experiments**, losers included, so the
search denominator survives.

Name experiments with the variable under test as a **prefix**: `v2_model-a`, `v2_model-b` groups
into readable blocks; `model-a_v2`, `model-b_v2` scatters alphabetically. Braintrust groups and
auto-diffs by name, so **prefix order determines whether arms line up at all**.

Run integrity: `maxConcurrency` from an **environment variable** so one fragile provider can be
throttled alone; **delete** smoke-test and partially-errored experiments
(`DELETE /v1/experiment/{id}`) so they never get read as arms; plan for **1,000-row pagination**
and cache locally before analyzing.
