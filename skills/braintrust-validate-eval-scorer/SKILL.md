---
name: braintrust-validate-eval-scorer
description: >-
  Validate automated eval scorers and LLM judges against expert-reviewed reference data. Use to
  compare scorer output with human labels, calculate agreement (kappa, alpha) with uncertainty,
  inspect confusion by class and severity, analyze subgroup failures, test shortcut and gaming
  cases, propagate scorer error into headline numbers, document blind spots, and decide whether a
  scorer is fit for exploration, trend monitoring, or release gating. Do not use to create the
  initial scorer or to design the human review workflow.
---

# Validate the scorer

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/validation-recipe.md`.

## Trigger

- "Validate this LLM judge." / "Can this scorer gate releases?"
- A scorer already gating releases that has never been checked against humans.
- A scorer-version bump — validation is a regression test for the instrument.

## Do

1. Name the **reference tier** before computing anything. Adjudicated human labels are the only
   tier the fitness bands in `reference.md` are calibrated against. A strong-model reference is a
   cheaper tier that supports iteration and nothing else — say which one you have, in the verdict.
2. Verify alignment: scorer outputs and reference labels must line up at the item **and
   criterion** level. Misalignment invalidates every number after it.
3. Report **agreement (κ or α) with uncertainty**, not raw accuracy. Fitness bands and their
   hedges are in `reference.md`.
4. Lead with the most decision-relevant **false acceptance** before any aggregate, and enumerate
   the dangerous cells case by case.
5. Break errors down by class and **severity**. Confusing "excellent" with "good" may be fine;
   missing harmful outputs is disqualifying for gating.
6. Test sensitivity and shortcuts: inject known regressions and improvements and confirm the
   scorer moves; probe whether length, confidence, or polish raise the score independent of
   quality; probe whether text addressed to the judge moves it; slice agreement by subgroup.
7. **Propagate scorer error into headline numbers**, then state the fitness verdict: **allowed
   uses**, **prohibited uses**, **revalidation triggers**.

## Avoid

- Do not rely on raw accuracy — with skewed classes it is high and meaningless.
- Do not read the fitness bands against a model-generated reference; they are calibrated for
  adjudicated human labels and mean something weaker here.
- Do not validate on the same examples used to tune the scorer.
- Do not report one aggregate agreement figure as the verdict.
- Do not repair the scorer here unless asked; audit and repair are different modes.
- Do not build the scorer or produce the reference labels here; both must already exist.

## Check

- False acceptances and rejections separate, severity-weighted; dangerous cells enumerated
  individually.
- Subgroup agreement reported; shortcut probes run.
- Blind spots documented as understood failure modes.
- Verdict names allowed uses, prohibited uses, revalidation triggers.
- Scorer error reflected in the uncertainty of any headline number it produces.

## Risk

- High average agreement conceals rare severe misses — exactly the errors that make a scorer
  unsafe for gating.
- A scorer validated once and trusted indefinitely drifts; validity is dated, not permanent.
- Validating against a golden set with systematic label error certifies agreement with the error.
  A model-generated reference is the acute case: agreement then measures how well the cheap
  instrument imitates the expensive one, which says nothing about either tracking the construct.
- The goal is not a perfect scorer but one that tracks the distinctions the team cares about and
  **fails in understood ways**.

## Braintrust

The validation run is an experiment, and following the shape exactly is what makes it repeatable
rather than a one-off notebook: golden set as a **versioned dataset** → run the candidate scorer
over it **as an experiment** → **diff against human labels** → compute κ and confusion heatmaps
in **custom columns or an exported notebook** (`references/platform-mechanics.md` §8) → **re-run
on every scorer-version bump**.

This only works if the scorer wrote its **evidence into span output**; without it a disagreement
shows two numbers and no way to adjudicate. **Scorer name and version in span metadata** is what
lets a report name the version it validated.

Put the verdict where the gate reads: allowed and prohibited uses in the **scorer's own
description**, validation date and golden-set version in the experiment description. Where a
scorer is prohibited from gating, do not attach it to a gate check at all — absence is more
reliable than a warning. Route disagreement items back into the review queue.
