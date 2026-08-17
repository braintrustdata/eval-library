# Reference — eval dataset

## Sourcing priority

1. **Production traces.** Gold standard for representativeness — real inputs, real
   distribution, real messiness. Sample live traffic, scrub PII, label. Every incident
   and user-flagged failure is a free, maximally relevant item; route them in as a
   standing pipeline.
2. **Expert-authored.** Necessary for situations production has not shown you (new
   features, rare-but-severe risks) and for adversarial cases. Have someone **other
   than the system's author** write the adversarial items — authors probe where they
   already know the system is strong. `[→ Kiela et al. 2021]`
3. **Synthetic (LLM-generated).** Cheap scale, two known hazards: generated items
   cluster in a narrower distribution than real usage, and a generator from the same
   family as the evaluated model imports that family's blind spots. Use to fill
   *documented gaps* in a stratification plan, then human-review a sample.
4. **Public benchmarks.** Four legitimate jobs — cold start (label as scaffolding to be
   displaced), **harness calibration** (reproduce published numbers through your
   pipeline before trusting custom results), external anchoring, and gap mapping. In
   all four: a benchmark measures *its* construct, not yours.

## Label quality

- Record **provenance** per item: who labeled it, from what source, when.
- Double-label at least a calibration sample (≥2 raters), report Cohen's κ or
  Krippendorff's α, adjudicate — the adjudication discussions are where the rubric gets
  sharp.
- Estimate the label error rate and require claimed effects to exceed it. **A 4 pp
  improvement measured against labels with 6% error is not a finding.**

Three systematic patterns to check by name in any inherited corpus:

- Labels transcribed from a **script** record what the subject was supposed to produce,
  so every faithful deviation scores as a system error.
- Machine-generated or auto-extracted references inherit every error of the tool that
  made them.
- Crowd-sourced labels range from usable to unusable — audit a sample up front.

`[Northcutt et al. 2021]`

**Free label audit from a multi-system comparison:** compute how closely each system
agrees with the reference, and how closely systems agree with *each other*. Items where
systems converge tightly among themselves while all diverging from the reference are
where the reference is most likely wrong. Confirm by hand; a failure mode shared by all
arms produces the same signature.

**Engineer one stratum true by construction:** items whose expected output you authored
first and then rendered into the input format, so ground truth is known exactly. That
stratum is the calibration anchor. Keep it small, mark it synthetic, never let its
numbers stand in for the population.

## Open-ended `expected`, in increasing order of openness

| Option | Shape | Note |
| --- | --- | --- |
| Multiple references | max over a set of acceptable answers | cheap; bounded by what you thought of |
| Constraint / property checks | verifiable properties | creativity is free; CheckList at item level |
| Rubric + LLM judge | criteria with anchored examples | standard for helpfulness/clarity |
| Pairwise preference | head-to-head, Bradley–Terry | counterbalance order for position bias |

Reference-overlap metrics correlate poorly with human judgment on open-ended
generation. `[Novikova et al. 2017; Ribeiro et al. 2020; Zheng et al.
2023; Chiang et al. 2024]`

## Leakage controls, not guarantees

*Corpus-side:* n-gram/substring overlap scans, canary strings in private sets,
version-pinning the corpus by commit hash. Recency helps but is a **heuristic, not
proof**.

*Behavioral (stronger — needs no access to training data):*

- Items whose answer exists **exactly once** in the supplied context, so retrieval is
  the only path.
- **Perturbation rows** renaming a real symbol only inside the injected context: a
  model reading the window follows the modified source, a model leaning on memorized
  associations gets it wrong. Collapse on perturbed rows but not ordinary ones is a
  direct measurement of memorization.
- **Context-size tiers** (same questions at 25k vs. 50k tokens) — answering from
  weights is size-insensitive, answering from context is not.

Caveat: a drop on perturbed items only implies memorization if task complexity was held
constant. Side effect: perturbation breaks prompt-cache reuse, so those rows double as
a serving-cost stress test.

`[Sainz et al. 2023; Braintrust GLM-Opus 2026; pending: White et al. 2024,
Chen et al. 2025]`

## Transform-pipeline invariants

Items rarely reach the scorer untouched — chunked, truncated, redacted, reformatted,
resampled. Preprocessing bugs do not raise errors; they produce plausible-looking inputs
that are no longer the task. A threshold-based silence trim once turned a 13-second
utterance into 1.8 seconds while the pipeline reported success.

Defense: after every transform, assert an invariant a corrupted item would violate
(duration, byte size, token count, field count within a bounded ratio of the input) and
**reject** rather than pass through. Order destructive steps last and gentlest,
spot-check distribution extremes by hand, version the pipeline, and normalize to one
canonical format at the end so no arm is disadvantaged by a format its provider handles
badly.

## Lifecycle

- **Headroom:** baselines at 95%+ (ceiling) or near zero (floor) cannot show a
  difference. Check both before investing.
- **Dev/test discipline:** iterate against dev; touch test rarely and **count the
  touches**. Refresh when the count gets embarrassing.
- **Refresh cadence:** review stratum weights against the current production mix; retire
  saturated items for harder ones drawn from recent failures.
- **Datasheet:** motivation, composition stats, collection process, labeling process and
  agreement, recommended and discouraged uses.

`[Gebru et al. 2021; Kiela et al. 2021; Reuel et al. 2024]`

## Iteration budget

"Touch test rarely" is not enforceable as written. The operational form, defaults to justify:

- **≤ 5 experiments** against the dev slice before stopping to reflect and report.
- **One hypothesis and one coherent change** per experiment. Two changes at once means the next
  result attributes to neither.
- **The same dev slice** throughout. Rotating the slice when results disappoint is test-touching
  with extra steps.
- **One test touch**, by the winning candidate, after iteration has stopped.

Set the budget before the first run. Set afterwards, it describes what happened rather than
constraining it — and the number chosen will be however many runs it took.

The regime this protects against is specific and easy to fall into: a small validation set, a
candidate cheap enough to rerun freely, and "the outputs look better now" available as a stopping
rule at every step. Under those three conditions, iteration converges on the slice rather than the
construct, and nothing in the numbers reveals it.

## Diagnostics

- **Difficulty spread:** per-item confidence and variability across runs/models reveals
  whether the set is all easy-and-redundant or contains the ambiguous, hard region where
  systems actually differ. `[→ Swayamdipta et al. 2020]`
- **Coverage:** enumerate capabilities and failure modes the construct implies, verify
  each has items — including negative cases. `[→ Ribeiro et al. 2020]`
