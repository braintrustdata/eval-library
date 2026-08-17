---
name: braintrust-define-eval-objective
description: >-
  Create, edit, or audit an eval objective by working backward from a product decision to the
  target outcome, construct, population, intended claim, and verification-versus-validation
  questions. Use when a team is unsure what an eval should establish, asks "what are we
  actually trying to measure," "is this eval measuring the right thing," "does this benchmark
  support our claim," or needs to turn a product goal into an eval objective and state which
  claims are out of scope. Do not use to select detailed metrics, design datasets, or implement
  scorers.
---

# Define the eval objective

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/objective-card.md`.

## Trigger

- Nobody can name the decision the eval supports.
- A benchmark score being used to argue a claim it may not license.
- A product goal ("make the agent more helpful") that needs to become measurable.

## Do

1. State the decision in one sentence. If several are plausible, ask which one the eval must
   support — the highest-information question available here.
2. Write one sentence each: **construct**, **population** (and its weighting), **intended use
   and non-use**.
3. Answer both questions, not just the first. **Verification:** do the scorers hold the spec?
   **Validation:** do these scorers reflect outcomes users actually need? Validation is the
   half teams skip.
4. Where validation has no evidence behind it, say so and elicit criteria from experts and
   real user signals rather than asserting what users want. Label unevidenced desires `Assumed`.
5. Write **supported** and **unsupported** claims as separate lists, then name the evidence
   that would change the decision. An objective no result could overturn is not an objective.

## Avoid

- Do not pick metrics, thresholds, or scoring methods.
- Do not let the population drift toward whatever data is easy to collect; most bad datasets
  fail here, before a single item exists.
- Do not accept a benchmark name in place of a product property.
- Do not imply model-level claims when the object under test is a system — harness, tools, and
  context are part of what you measure.

## Check

- Decision, construct, population, use, and non-use each in a sentence.
- Supported and unsupported claims listed separately.
- Both V&V questions answered, with validation's evidence source named.

## Risk

- An ambiguous decision produces an eval that is locally measurable and strategically
  irrelevant.
- A construct defined by convenience gets optimized: the score improves, the product does not.
- Loose population statements ("our users") license claims far broader than the sample
  supports, and nobody notices until the number goes external.

## Braintrust

**Write the decision and intended claim into the experiment description** so the
pre-registered claim travels with its results — a claim in a doc gets reinterpreted after the
fact. Record the population and its weighting in **dataset metadata**. Make non-use
enforceable: name datasets for their population (`prod-weighted-py-backend`, not `eval-set-2`)
so quoting a number out of scope is visibly wrong, and keep benchmark scaffolding in
**separate, clearly named datasets** — once mixed with production-derived items, "measures our
construct" vs. "measures the benchmark's" is unrecoverable. Validation cannot be answered
offline: it needs production scoring sliced by escalation, reopen, and abandonment. If nothing
scores production yet, validation is `Not yet measurable`, and standing up online scoring is the
blocker.
