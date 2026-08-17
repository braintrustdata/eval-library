# Reference — sizing

All numbers below are **defaults to justify, not laws**. Quote the hedge with the
number.

## Three planning situations

| Goal | Method | Report |
| --- | --- | --- |
| Detect a difference between arms | power analysis on the minimum effect worth acting on | required n per arm, MDE at the n you have |
| Estimate a rate with stated precision | CI width (Wilson near 0/1) | n for target half-width |
| Bound a rare failure | rule of three | clean trials needed for the tolerance |

`[guide §4.6, §9.1 → Card et al. 2020; Miller 2024]`

## Anchors

- Detecting a **5 pp improvement on a 75% baseline** needs on the order of **1,100
  items per arm unpaired**. Pairing on the same items cuts this substantially, which is
  why paired designs are the default for prompt and model comparisons. `[guide §4.6]`
- **Clustered items are fewer items than they look.** 200 tasks that are really 40
  scenarios × 5 variants have an effective N closer to **40**. Plan and analyze with
  cluster-aware standard errors. `[guide §4.6, §9.1 → Miller 2024]`
- **Near-zero rates need large N.** Zero violations in 200 trials only certifies a rate
  below **~1.5%** (rule of three, 3/n). A **0.1% tolerance needs ~3,000 clean trials**.
  Do this arithmetic before promising the gate. `[guide §4.6, §9.1 → Miller 2024]`
- Most NLP evaluations historically have been **underpowered** — typical test sets are
  too small to reliably detect the 1–2 point differences papers claim.
  `[guide §4.6 → Card et al. 2020]`

## Formulas

**CI on a pass rate.** 150/200 passes: p = 0.75.
SE = √(p(1−p)/n) = √(0.75 × 0.25 / 200) ≈ 3.1 pp → 95% CI ≈ 75% ± 6 pp = [69%, 81%].

Interpretation: any score inside [69%, 81%] is not distinguishable from yours on this
eval; a competitor's 78% on the same 200 tasks is consistent with no difference.

Use **Wilson** instead of the normal approximation when p is near 0 or 1, or n is small.

**Rule of three.** 0 events in n trials → 95% upper bound ≈ 3/n.
n = 200 → 1.5%. Tolerance 0.1% → n ≈ 3,000.

**Design effect for clustering.** effective n ≈ n / (1 + (m − 1)ρ), where m is items per
cluster and ρ the intra-cluster correlation. With high ρ and m = 5, effective n
approaches the cluster count.

`[guide §9.1 → Miller 2024]`

## Runs, not just items

Two independent variance components: **item sampling** (which items) and **generation
noise** (which run). Sizing only the first understates uncertainty.

- K = **3–5** runs as the floor for gating decisions; K = 1 only for exploratory work,
  labeled as such. `[guide §9.0]`
- Precedent for treating a metric as a distribution: the Phi-4-reasoning report
  approximates AIME accuracy by kernel density estimation over **50 independent runs**,
  because AIME 2025 has only 30 problems and average-of-5 results from two independent
  runs differed by 5–10 pp. `[guide §9.0 → Abdin et al. 2025]`
- Hosted "deterministic" settings are not deterministic: accuracy variation **up to
  15%** across runs of the same configuration, best-to-worst gap up to **70%**.
  `[guide §9.0 → Atıl et al. 2025]`

## Matrix budget

Before the first run, price **items × arms × runs** against every quota, credit balance,
and metered limit in the path. Metered ceilings fail in the worst available way: partway
through one arm, leaving a partial result that resembles data. `[guide §4.2, §8.4]`

## Output template

```yaml
goal: detect_difference | estimate_rate | bound_rare_failure
assumptions:
  baseline_rate:
  minimum_effect:          # source: release gate magnitude criterion
  confidence:
  power:
  paired: yes | no
  clustering: {items_per_cluster: , assumed_rho: }
method: <formula or calculator>
required_n: <per arm>
runs_K: <≥3 for gating>
matrix_total: <items × arms × runs>
sensitivity:
  - {effect: , n: }
decision_implication: <one plain sentence>
what_this_n_cannot_establish: <the claim it will not support>
```
