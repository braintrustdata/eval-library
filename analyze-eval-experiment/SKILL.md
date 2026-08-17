---
name: analyze-eval-experiment
description: >-
  Analyze completed LLM or agent eval experiments using uncertainty-aware and decision-relevant
  methods. Use to audit run completeness and pairing, calculate confidence intervals, run paired
  comparisons, report wins, losses, and ties, incorporate run-to-run variance, handle multiple
  comparisons, inspect subgroup performance, and test fragility to favorable slices. Use when
  results already exist and someone asks what they mean, whether a difference is real, or which
  model won. Do not use to design an experiment that has not yet collected results.
---

# Analyze completed eval results

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/estimators.md`.

## Trigger

- Completed results needing interpretation: "analyze these," "is this difference real?"
- Requests for intervals, subgroups, multiplicity handling, fragility checks.
- A headline number about to be quoted with no interval.

## Do

1. **Audit before computing anything.** Reconcile effective N per arm — attempted, completed,
   errored — against the design, and confirm pairing keys, run counts, and config versions. An arm
   whose effective N is materially below its peers is not comparable: re-run it rather than
   caveating it, because the survivors are not a random sample.
2. Report every headline number as **point estimate + 95% CI + n + K**, using Wilson near 0 or 1.
3. Apply the two corrections practitioners miss: **cluster standard errors** when items are
   related, and **fold in run-to-run variance** as a second component.
4. Compare **paired** on the same items, reporting the paired difference with its CI **plus
   wins/losses/ties** — never two independent averages.
5. Handle multiplicity: record every arm run including failures, then either correct or treat the
   sweep as exploratory and re-run the winner on a held-out confirmatory set.
6. Look past the average: run distribution and **worst run**; slices by metadata strata; the
   breakdown check — does the conclusion survive dropping the most favorable category?

## Avoid

- Do not read any average before the effective-N reconciliation.
- Do not compare independent averages when item-level pairing is available.
- Do not promote a sweep winner without confirmation — that is an anecdote with a p-value.
- Do not fold errored items into the numerator silently, or adopt a scorer fix because it improves
  one arm.
- Do not write the external report or make the ship call here. If arms differ in more than one
  respect, isolate the factors before attributing the effect to any of them.

## Check

- Effective N per arm and how errors were treated; every estimate carries interval, n, K.
- Clustering and run variance accounted for; paired differences with wins/losses/ties.
- Search denominator disclosed; exploratory vs. confirmatory labeled.
- Subgroup slices and at least one fragility check reported.

## Risk

- Clustering, silent exclusions, repeated benchmark touches, and favorable slices each make
  uncertainty look far smaller than it is.
- Two systems can share an average while differing in reliability; the mean hides what users
  experience.
- Subgroups can rank oppositely to the aggregate, making the aggregate the least informative
  number available.
- Fragility is highest among top-ranked systems, exactly where "best" claims concentrate.

## Braintrust

Two platform facts cause most phantom findings, and both look like data problems: **check
completed-row count against error count** rather than trusting the summary line, and follow the
**1,000-row pagination cursor**, caching locally before analyzing — a truncated pull is
indistinguishable from a missing stratum. Re-fetching makes each analysis pass a fresh
reliability risk, so pull once and work off the cache. Bulk reads get throttled too.

Use **cross-experiment diffs on the same dataset version** for item-paired comparisons; if arms
were not pinned to one version you cannot pair retroactively — fall back to unpaired and note the
limitation. **Group by `metadata`** for subgroups; a stratum never written to metadata cannot be
sliced now, and that is an instrumentation finding worth reporting rather than silently omitting.

Sweep arms kept as **separate experiments** are what make the search denominator recoverable. If
nothing is marked confirmatory, everything is exploratory. Compute κ, clustered SEs, and heatmaps
in **custom columns or an exported notebook** — none are native.
