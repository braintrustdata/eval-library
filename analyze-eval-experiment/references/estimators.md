# Reference — analysis

## Step 0: run integrity, before any average

Compute effective N per arm — **attempted, completed, errored** — and compare against the
design *before* looking at a single average.

A run can report completion and still be mostly wreckage: in one six-model comparison an
arm logged **240 rows of which 197 had errored**, so every average it reported was
computed over the 43 survivors, and nothing in the summary said so.

Two corollaries:

- "Finished with N errors" is not a diagnosis — get the completed-row count before
  believing anything.
- An arm whose effective N is materially below its peers is **not comparable**. Re-run it
  rather than caveating it; the survivors are not a random sample, since whatever killed
  the others correlates with load, input size, or item difficulty.

`[guide §8.4]`

## Non-determinism baseline

- A single run is one draw from a distribution, not a measurement of a constant.
- Even temperature 0 with a fixed seed is not deterministic in hosted environments:
  accuracy variation **up to 15%** across runs of the same configuration, and a
  best-to-worst gap up to **70%**. The unit is percent, not percentage points.
  `[guide §9.0 → Atıl et al. 2025]`
- Root causes are mundane: small gaps between competing logits flipped by numerical noise,
  amplified by BF16 precision, batch size, GPU count, hardware.
  `[guide §9.0 → Yuan et al. 2025]`
- Agentic systems amplify: one different early token means a different tool call,
  different environment state, different outcome.
- K = **3–5** floor for gating; K = 1 only for exploratory work, labeled as such.
- Report mean, SD across runs, and the **worst run** — never only best or average.

## Estimators

**CI on a pass rate.** 150/200 → p = 0.75, SE = √(0.75 × 0.25 / 200) ≈ 3.1 pp, 95% CI ≈
[69%, 81%]. Any score inside that range is not distinguishable from yours on this eval; a
competitor's 78% on the same 200 tasks is consistent with no difference. Use **Wilson**
near 0 or 1 or when n is small. `[guide §9.1]`

**Rates near zero.** 0 violations in 200 trials does **not** mean 0%. Rule of three: 95%
upper bound ≈ 3/n = 1.5%. A 0.1% tolerance needs ~3,000 clean trials. `[guide §9.1]`

**Two corrections practitioners routinely miss:**

- **Cluster standard errors when items are related.** 200 tasks that are really 40
  scenarios × 5 variants have an effective n closer to 40. Unclustered SEs on clustered
  data is **the most common way eval reports overstate precision**. `[→ Miller 2024]`
- **Fold in run-to-run variance.** Two components: item sampling and generation noise.
  Report both or model them jointly. GLMMs estimate generalized accuracy while decomposing
  variance into item and model components, more efficiently than mean-of-scores.
  Generalizability Theory is the general framework — it decomposes error into sources
  (items, runs, judges, prompts) and tells you which the protocol must average over.
  `[guide §9.1 → NIST AI 800-3 2026; Truong & Koyejo 2026 ch. 5]`

**Bootstrap, for anything that is not a proportion** — mean judge score, latency, cost:

```python
import numpy as np

def bootstrap_ci(x, n=2000):
    x = np.asarray(x)
    means = [np.mean(np.random.choice(x, len(x), replace=True)) for _ in range(n)]
    return np.percentile(means, 2.5), np.percentile(means, 97.5)
```

**Paired comparison.** Compare M1 vs. M0 on the same tasks and analyze per-task
differences; item difficulty cancels and sensitivity improves. Report the paired
difference with its CI plus wins/losses/ties — never two independent scores side by side.
`[guide §9.2]`

```python
diff = np.array(score_B) - np.array(score_A)   # per-item, same order
lo, hi = bootstrap_ci(diff)
print(f"mean Δ = {diff.mean():.3f}, 95% CI [{lo:.3f}, {hi:.3f}], "
      f"B wins {np.mean(diff > 0):.0%} of items")
```

A CI on the difference excluding 0 means the improvement is real at that confidence; the
win fraction is what tells you whether it is *consistent* or carried by a few items. Both
snippets assume the clustering correction above has been applied where items are related —
bootstrapping rows that are really scenario variants reproduces the unclustered error.

An alternative framing worth knowing: report **P(A > B)** rather than an average
difference, testing against H₀: P(A>B) = 0.5 with a meaningfulness threshold. The source
recommends **γ = 0.75** for strong claims. `[guide §9.1, §10 → Bouthillier et al. 2021]`

## Multiplicity

Every additional arm is another lottery ticket. **10 prompt variants at α = 0.05 with none
actually helping: P(at least one clears the bar) = 1 − 0.95¹⁰ ≈ 40%.** If you try 20
variants and show only the best, you are almost guaranteed to be fooling yourself.

Practices:

- Record every arm run, including failures — **the denominator of the search is part of
  the evidence**.
- Correct (Bonferroni α/k, or Holm / Benjamini–Hochberg for less conservatism) **or**,
  usually better for eval workflows: treat the sweep as **exploratory**, then re-run only
  the chosen candidate on a held-out **confirmatory** eval it has never touched. One
  pre-registered comparison needs no correction.
- Interpretation rule: sweep winner + confirmatory replication = trustworthy; sweep winner
  shipped without confirmation = **an anecdote with a p-value**.

`[guide §9.3]`

## Beyond averages

- **Variance.** M0 and M1 can both average 85% while one clusters tightly and the other
  spreads wide — the average hides the reliability difference users experience.
- **Subgroups.** Slice every headline metric by metadata strata. Real precedent: the same
  base models aligned toward fast-heuristic vs. deliberate reasoning ranked **oppositely**
  depending on benchmark category — System 2-aligned excelled at arithmetic and symbolic,
  System 1-aligned did better on commonsense. An aggregate would have flattened it.
  `[guide §9.4 → Ziabari et al. 2025]`
- **Fragility.** Does the conclusion survive dropping the single most favorable task
  category? A cross-domain analysis of ten leaderboards found that in **over half** of
  top-model comparisons at least one implied property of superiority fails. Fragility is
  highest among top-ranked models, and adding more correlated tasks does not fix it.
  `[guide §9.3, §9.4 → Oh 2026]`
- Synthetic suites and in-the-wild production tasks will often rank systems differently —
  that disagreement is signal, not noise.

## Output template

```yaml
integrity:
  per_arm: [{arm: , attempted: , completed: , errored: , error_treatment: }]
  comparable: yes | no    # "no" → re-run, do not caveat
  pairing_verified:
  runs_K:
  versions: {dataset: , scorers: [], prompts: []}

headline:
  - {metric: , estimate: , ci_95: , n: , K: , interval_method: wilson|normal,
     clustered: yes|no, run_variance_folded: yes|no}

paired:
  - {arms: [A, B], diff: , ci_95: , wins: , losses: , ties: , p_a_gt_b: }

multiplicity:
  arms_tried: <the search denominator>
  handling: correction | exploratory_then_confirmatory
  confirmatory_run: <name, or "none — exploratory only">

subgroups:
  - {stratum: , estimate: , ci_95: , n: }

fragility:
  drop_most_favorable_category: {conclusion_survives: yes|no, delta: }

claims_supported: []
claims_not_supported: []
```
