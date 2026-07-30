---
name: report-eval-results
description: >-
  Turn completed eval analysis into a technical report, release summary, chart set, or decision
  document with claims calibrated to the evidence. Use when writing up eval or benchmark results,
  preparing charts or tables of model comparisons, drafting a release note or blog post about eval
  numbers, or auditing a draft writeup for overstated claims, missing uncertainty, undisclosed
  search, or unpinned configuration. Do not use to compute the analysis itself or to decide whether
  to ship.
---

# Report eval results

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/presentation-checklist.md`.

## Trigger

- Writing up completed results: technical report, release summary, chart set, external post.
- Auditing a draft for claims the design does not support.
- A "state-of-the-art" or "best model" claim being drafted.

## Do

1. Give every headline metric **point estimate + 95% CI + n + K**. "82.4%" is not a result;
   "82.4% [79.1, 85.7], n=520, K=3" is.
2. Report the **effective** n — attempted, completed, errored per arm, plus how errors were
   treated. "n=520" on a run where 80 items never completed is a misreport.
3. Run the full presentation checklist in `reference.md`. It is the deliverable's definition of
   done.
4. **Disclose the search**: how many arms were tried before the reported winner, and label every
   number exploratory or confirmatory.
5. Pin the configuration — model string, decoding params, prompt/scorer/dataset versions, serving
   path, date. A result without re-run fields is a rumor.
6. Calibrate language to evidence. "Ranks first on this benchmark, +9 pp [3, 15]" is defensible;
   "state-of-the-art" implies consistency and robustness that must be demonstrated separately.

## Avoid

- Do not imply a ranking from overlapping uncertainty.
- Do not hide attempted arms, killed runs, or abandoned configurations.
- Do not use language broader than the population and design support.
- Do not present a discovery or red-team yield as a population rate.
- Do not recompute or revise the analysis here; if the numbers look wrong, fix them in the
  analysis and re-derive, rather than adjusting them in the writeup.

## Check

- Every headline number carries interval, n, K — and every claim maps to a reported number.
- Effective-N accounting present per arm; search denominator disclosed.
- Every figure has uncertainty where applicable; captions state overlap.
- Re-run fields complete enough for someone else to reproduce the table.
- Known limitations — scorer artifacts, label error, uncovered strata — in the body, not a footnote.

## Risk

- Polished presentation makes weak or exploratory evidence look decisive; the cleaner the chart, the
  stronger the implied claim.
- A number quoted out of the report loses its interval and population immediately — write the
  sentence you would accept being quoted alone.
- Selective reporting of the best arm is the most common integrity failure in eval writeups and is
  invisible unless disclosed.
- External readers situate your numbers against benchmarks with different constructs; say what
  yours measures.

## Braintrust

Every number should come from **one cached pull**, not repeated fetches: follow the **1,000-row
pagination cursor** (a truncated pull produces a confidently wrong n), then run every table and
chart off the cache, since re-fetching makes each pass a fresh reliability risk.

Re-run fields should be readable straight out of **experiment metadata**, because the experiment
design put them there. If they are missing, the report cannot honestly claim reproducibility — say
so as a limitation rather than reconstructing from memory.

The search denominator lives in the experiment list: count arms from **separate sweep experiments**,
not from what anyone remembers trying, and clean smoke tests and partial arms first or they inflate
the count. If nothing is marked **confirmatory**, every number is exploratory. Take effective N
from **completed-row vs. error count**, not the summary line.

Link the experiment or comparison view rather than pasting a screenshot — a permalink carries the
versions, metadata, and item-level data a reader needs to check a claim.
