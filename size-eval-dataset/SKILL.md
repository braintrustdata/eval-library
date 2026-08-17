---
name: size-eval-dataset
description: >-
  Calculate or audit eval sample sizes, minimum detectable effects, confidence interval
  precision, required repeated runs, and clean-trial counts for bounding rare failures. Use when
  a user asks how many eval cases, items, scenarios, runs, or safety trials are needed, whether
  an existing dataset is adequately powered, whether N examples can detect an X-point gain, or
  how many clean trials certify a low violation rate. Account for paired designs, clustering,
  target confidence, and practical effect size. Do not use for general dataset composition.
---

# Size the dataset

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/power-analysis.md`.

## Trigger

- "How many eval cases do we need?" / "Can 200 examples detect a 3-point gain?"
- "How many clean trials certify a low failure rate?"
- A null result that needs distinguishing from an underpowered one.

## Do

1. Classify the goal first — it selects the method: **detect a difference**, **estimate a
   rate**, or **bound a rare failure**.
2. Take the minimum meaningful effect from the release gate's magnitude criterion, not from what
   the data shows. Ask only if genuinely absent.
3. Compute N with the method and anchors in `reference.md`, applying the **design effect** for
   clustered items — related variants are fewer items than they look.
4. Multiply through the whole matrix: items × arms × runs (K ≥ 3 for gating), and check the
   product against every quota and credit balance in the path before anyone starts.
5. Report a **sensitivity range**, not a single number, and close with the plain-language
   decision implication.

## Avoid

- Do not return a sample size without stating the practical effect, baseline rate, risk
  tolerance, clustering, pairing, confidence, and power assumptions.
- Do not use the normal approximation near 0 or 1 — use Wilson, which is exactly the
  safety-rate case.
- Do not design content here.
- Do not let a cheap smoke run over a handful of items be quoted as evidence about which option
  is better. It verifies plumbing, nothing else.

## Check

- Goal type identified; method named; inputs shown; every assumption listed with its source.
- Design effect applied for clustered or repeated-variant items.
- Sensitivity range alongside the point answer.
- A plain sentence stating what the resulting N can and cannot establish.

## Risk

- Treating correlated variants as independent overstates precision more than any other single
  error in eval reporting.
- Normal approximations near zero produce impossible bounds and false safety assurances.
- Powering for the effect you hope for rather than the effect worth acting on guarantees an
  ambiguous result.
- An underpowered eval and a real null produce the identical sentence: "no measurable effect."

## Braintrust

Shared mechanics: `references/platform-mechanics.md`. Pairing is what buys the sample-size
reduction, and **§3** makes it a platform decision rather than a later statistical one — a design
sized for pairing silently reverts to the unpaired requirement if the arms were never pinned. So
the N you compute here is only achievable if the experiment design honors that.

Planned N and achieved N diverge routinely, which makes the §2 read-safety checks a sizing
concern and not just an analysis one: a truncated pull looks exactly like an underpowered run,
and the two call for opposite responses. K runs means K recorded trials (§7); the worst run is
what a latency or reliability gate reads.
