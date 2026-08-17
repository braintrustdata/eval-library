# Reference — human review

Numbers here are **defaults to justify, not laws**.

## The golden-set floor

A workable floor: **~100 traces, each reviewed by at least 2 raters**, with agreement
(Cohen's κ or Krippendorff's α) reported and disagreements adjudicated **before** the
set is used to calibrate anything.

"~100" is a floor for a first reference set, not a target for a mature one, and it
assumes the set spans clear successes, clear failures, and ambiguous edge cases rather
than 100 easy items.

## Provenance

- Humans decide what "good" means; automation applies that decision at scale.
- The practical pattern: domain experts review real traces, score against explicit
  criteria, attach short notes on what succeeded or failed. Those reviewed traces become
  the reusable reference set for prompt comparisons, regression tests, release gates, and
  scorer development.
- Build the set **construct-first** — decide what you are measuring, then choose items
  that discriminate on it. `[Casabianca 2025]`
- Direct human attention to ambiguous examples, high-risk domains, newly changed
  behavior, and cases where automated scorers disagree. The aim is not annotation volume.
  `[Lazaros et al. 2026]`
- Double-label a calibration sample, report κ or α, adjudicate — **the adjudication
  discussions are where your rubric gets sharp**.
- Record provenance per item: who labeled it, from what source, when.
- Majority voting beats individuals substantially on ground-truth categorical validation,
  with accuracy-weighted voting strongest — but this is *human* crowds on categorical
  tasks, gains vanish under ceiling effects, and weighting barely beat unweighted
  majority in simulation. Groupthink caveat: raters must reach independent judgments
  before conferring.
- Psychometrics upgrade: define the construct, decompose into facets, score criteria
  reflecting those facets consistently across cases, as validated scales do for latent
  properties like trust. `[Wang et al. 2026; Ueno et al. 2022]`
- Refresh the golden set as the product changes.

## Case-selection plan

```yaml
strata:
  representative:      # proportional to production
    n:
  ambiguous:           # where systems disagree or confidence is low
    n:
  severe_failures:     # every class, regardless of frequency
    n:
  clear_successes:     # anchors the top of the scale
    n:
  clear_failures:      # anchors the bottom
    n:
total: <≥100 for a first set>
selection_source: <production sample | scorer-disagreement queue | incident log>
```

## Review form template

```yaml
item_id:
reviewer:
reviewer_qualification:
timestamp:               # fatigue drift is invisible without this
per_criterion:
  - criterion:
    score:
    rationale:           # short free text — the reason, not a restatement
    confidence: low | medium | high
overall_shippable: yes | no
flags:
  - construct_ambiguity  # the rubric does not cover this case
  - item_defect          # the item, not the system, is wrong
  - out_of_scope
```

## Agreement and adjudication

1. Raters label **independently**. No shared doc, no discussion first.
2. Compute κ or α on the overlap. Report it; do not assume it.
3. Adjudicate every disagreement on the record: the decision, the reason, and whether the
   **rubric** changed as a result.
4. A disagreement traced to genuine construct ambiguity is a **finding**, recorded as
   such. Do not resolve it by fiat and do not average it away.
5. Rubric changes from adjudication mean a version bump — and the labels collected before
   it are not interchangeable with those after.

## Interpreting agreement

| κ | Reading |
| --- | --- |
| < 0.4 | the rubric is the problem, not the raters — re-elicit the criteria |
| 0.4–0.7 | usable for trend monitoring; adjudicate heavily before calibrating |
| ≥ 0.7 | usable as a calibration anchor for a gating scorer |

Watch for the ceiling trap: very high agreement on an easy set says nothing about the
rubric's ability to discriminate on hard cases.
