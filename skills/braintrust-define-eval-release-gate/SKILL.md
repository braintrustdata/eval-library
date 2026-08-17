---
name: braintrust-define-eval-release-gate
description: >-
  Create, edit, audit, or apply release gates for LLM applications and agents. Use to combine
  minimum meaningful improvement, statistical significance, regression rate, subgroup consistency,
  worst-run stability, all-attempts reliability, safety upper bounds, latency, and cost into an
  explicit ship-or-hold policy, to turn metrics into a CI gate, or to explain why a candidate
  failed a gate and what evidence would justify reconsideration. Do not use for general result
  analysis without a deployment decision.
---

# Define or apply a release gate

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/gate-rows.md`.

## Trigger

- "Create release gates." / "Should this ship?" / "Why did this candidate fail?"
- A ship decision being made from a single average.
- A gate that exists but has no owner and blocks nothing.

## Do

1. Identify the shipping claim and the failures that cannot be traded away. Draft the table before
   pinning thresholds needing product-owner input — mark those `Needs decision`.
2. Build a row per property the claim implicitly makes, using the row set in `reference.md`:
   magnitude, significance, consistency, stability, reliability, safety, latency/cost. A gate
   should test **every** property, not just the average.
3. Keep improvement metrics and guardrails structurally separate: guardrails are constraints,
   never terms in a weighted sum.
4. Require the run-integrity precondition — effective N and error accounting per arm. A gate on a
   run with unexplained missing items is a gate-shaped artifact of whichever items survived.
5. Enter red-team findings as **existence constraints**, never averaged scores, re-tested every
   round rather than retired once passed.
6. Emit both forms: machine-readable rules for CI, and a human-readable rationale per row. On
   failure, name the failed rows, what each failure **means**, and the evidence that would justify
   reconsideration.

## Avoid

- Do not let an average improvement buy down a safety or reliability constraint.
- Do not gate on point estimates for near-zero rates; size n to the tolerance.
- Do not gate on a scorer not validated for gating, or on the set the candidate was tuned against.
- Do not write thresholds nobody owns; an unowned gate becomes a dashboard.
- Do not compute the statistics here.

## Check

- Every row has a rule, a statistical basis, and a threshold with a stated source and owner.
- Guardrails expressed as constraints; reliability and safety rows use bounds and worst cases.
- Effective-N precondition explicit.
- Machine-readable rules match the human-readable rationale exactly.
- Failure interpretation written per row — each failure means something different.

## Risk

- Thresholds without uncertainty, or without operational ownership, turn gates into decoration.
- A gate that passes says nothing about inputs the set does not cover; completeness is
  unreachable, so gates pair with monitoring rather than replacing it.
- Gates tuned until the current candidate passes are not gates.

## Braintrust

**Encode each row as a scorer-plus-threshold check on the confirmatory experiment and block
promotion on any failing row.** A gate producing a chart instead of a block is not a gate. Reuse
scorers by name and version (`references/platform-mechanics.md` §5); a gate wired to a
differently-named scorer silently stops testing what it was written for. Check each scorer's
fitness statement first — where a scorer is prohibited from gating, **do not attach it at all**,
since absence beats a warning nobody reads.

Rows needing a derived value rather than a native score: the paired difference with clustered CI;
per-category win rate and regression rate; the leave-one-out recomputation; `pass^k` across the K
runs; the Wilson or rule-of-three **upper bound** for safety; p95 per run then the **worst** run.
§8 lists the wiring failures these invite — the last two attract them most.

Gate against the experiment marked **confirmatory**, pinned to the held-out dataset version, on a
cached pull.
