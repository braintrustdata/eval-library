# Reference — reporting

## Presentation checklist

This is the definition of done. `[guide — Presentation checklist]`

- **Every headline metric:** point estimate + 95% CI + n (items) + K (runs). "82.4%" is not
  a result; "82.4% [79.1, 85.7], n=520, K=3 runs" is.
- **Report the effective n, not the intended one:** attempted, completed, and errored per
  arm, plus how errors were treated. "n=520" on a run where 80 items never completed is a
  misreport, not a rounding choice.
- **For a targeted change, report the targeted metric and the aggregate together** — the
  subset effect with its subset n, and the whole-population effect beside it. One without
  the other either oversells or hides the finding.
- **In multi-system comparisons, table the per-arm implementation of the intervention.** An
  arm that could not receive the treatment is not evidence that the treatment fails.
- **State known scorer artifacts and label-quality limits explicitly**, including which arms
  they plausibly disadvantage.
- **Error bars on every figure;** if intervals overlap heavily, say so in the caption instead
  of letting bar heights imply a ranking.
- **Comparisons:** report the paired difference with its CI, plus wins/losses/ties — never
  just two independent scores side by side.
- **Multi-run results:** show the distribution (dots or box per run) and the worst run.
  `[style precedent: Abdin et al. 2025]`
- **Near-zero rates (safety):** report the upper confidence bound, never "0%".
- **Disclose the search:** how many arms were tried before the reported winner; label numbers
  as exploratory or confirmatory.
- **Pin the configuration:** model string, decoding params, prompt/scorer/dataset versions,
  date. A result without re-run fields is a rumor. `[→ NIST AI 800-2 draft]`
- **Calibrate language to evidence:** "ranks first on this benchmark, +9 pp [3, 15]" is
  defensible; "state-of-the-art" implies consistency and robustness that must be separately
  demonstrated. `[→ Oh 2026]`

## Claim language

| Evidence | Defensible phrasing |
| --- | --- |
| Paired win, CI excludes zero, confirmatory | "improves task success by 4.2 pp [1.8, 6.6] on <population>, n=, K=" |
| Paired win, exploratory sweep only | "in an exploratory sweep of 12 variants, the best candidate showed +5 pp; unconfirmed" |
| Overlapping intervals | "we cannot distinguish these two on this eval" — not "A slightly outperforms B" |
| Zero observed violations | "violation rate below 1.5% (95% upper bound, 0/200)" — never "0%" |
| Discovery search | "we found 14 distinct failure modes"; never "14% of traffic fails" |
| Red team | "there exists an input that produces X" — never an averaged rate |
| Bundle change | "the migration improved X; it changed model, serving path, and tools together and does not attribute the gain to any one" |

## Report skeleton

```yaml
claim: <one sentence you would accept being quoted alone>
population: <construct + weighting>
decision_supported: <ship/hold, A vs B>

headline:
  - {metric: , estimate: , ci_95: , n_effective: , K: , method: }

integrity:
  per_arm: [{arm: , attempted: , completed: , errored: , treatment: }]

paired: [{arms: , diff: , ci_95: , wins: , losses: , ties: }]

targeted_change:              # if applicable
  subset: {metric: , effect: , n: }
  aggregate: {metric: , effect: , n: }

per_arm_treatment_table:      # multi-system comparisons
  - {arm: , implementation: , could_receive: yes|no}

search_disclosure:
  arms_tried:
  reported_winner:
  status: exploratory | confirmatory
  confirmatory_set: <name>@<version>

subgroups: [{stratum: , estimate: , ci_95: , n: }]
fragility: {drop_top_category: , survives: }

limitations:
  scorer_artifacts: [<and which arms they disadvantage>]
  label_quality: <estimated error rate; effects must exceed it>
  uncovered_strata: []
  blind_spots: [<from the evidence map>]

rerun_fields:
  model_string: ; decoding_params: ; serving_path: ; prompt_version: ;
  scorer_versions: [] ; dataset_version: ; date:
```

## Chart rules

- Error bars on everything, or a stated reason there are none.
- Multi-run: dots or box per run, worst run visible. Never a bar of the mean alone.
- Overlapping intervals: say it in the caption. Bar height reads as ranking whether or not
  you intend it.
- Near-zero rates: plot the upper bound, not the point.
- Do not truncate a y-axis to make a small difference look large.
- Label every axis with its unit, and say whether points are items or runs.

## Audit questions for a draft

1. Does every number have an interval, n, and K?
2. Is the effective n reported, or the intended n?
3. Is the search denominator stated anywhere?
4. Is any number exploratory but written as if confirmatory?
5. Could a reader reproduce the table from the re-run fields given?
6. Does any sentence claim more than the population supports?
7. Are the known scorer artifacts and label limits in the body?
8. Would each headline sentence survive being quoted with no surrounding context?
