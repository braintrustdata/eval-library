---
name: bt-analyze-eval-results
description: >
  Take eval results straight to a defensible ship / no-ship decision in one pass —
  confidence intervals, run-to-run variance and reliability, subgroup breakdowns,
  paired comparisons, multiple-comparison discipline, benchmark fragility, and a
  stats-grounded release gate. Use for a fast, self-contained decision on a single
  completed experiment where the arms differ in one respect. Not for a
  stage-by-stage treatment with run-integrity auditing, clustered standard errors,
  or a gate policy as its own reviewed artifact.
---

# Analyze Eval Results

An eval score is an **estimate of a random variable**, not a fixed truth. The same agent behaves differently across runs, inputs, and conditions, so a bare "85%" is meaningless without its spread and the conditions behind it. This skill takes raw experiment output and produces a decision that accounts for uncertainty.

## When to use / when this is the wrong altitude

- **Use this** for the fast path: one completed experiment, one decision, six steps, done.
- **Not this** when the numbers must survive outside scrutiny. A rigorous pass adds a run-integrity audit — effective n as attempted / completed / errored, reconciled *before* any average is read — plus clustered standard errors on related items and explicit exploratory-vs-confirmatory labelling. None of that is below.
- **Not this** when the gate itself is the deliverable: a per-row policy with named owners, thresholds sourced to product tolerances rather than to current numbers, and a distinct reading for each kind of failure. Step 6 gives you a checklist, not a policy.
- **Not this** when several things changed at once. Step 4 assumes arms differ in one respect; if a migration bundled model, serving path, and tools, isolate the factors first or the attribution is invented.

## Step 1: Confidence intervals on every headline metric

Never report a point estimate alone. Report the range.

**Proportion (pass rate, violation rate)** — Wald interval:

```
p̂ ± 1.96 · sqrt( p̂(1 − p̂) / n )
```

> 85% over n = 100 → ±7 points → **[0.78, 0.92]**. "85%" that could be 78% or 92% is a very different claim from "85% ± 2." Use the **Wilson** interval instead when n is small or p̂ is near 0/1 (Wald misbehaves there).

**Anything else (mean judge score, latency, cost)** — bootstrap:

```python
import numpy as np
def bootstrap_ci(x, n=2000):
    x = np.asarray(x)
    means = [np.mean(np.random.choice(x, len(x), replace=True)) for _ in range(n)]
    return np.percentile(means, 2.5), np.percentile(means, 97.5)
```

Report a CI for correctness, every guardrail, and latency.

## Step 2: Variance and reliability

A single run hides instability. The same agent varies run-to-run from sampling and nondeterminism, so **run each item multiple times** and report the spread, not just the mean.

Two systems can share an average and differ completely in reliability: M0 and M1 both average 85% correctness, but M0 clusters tightly (82–88%) while M1 swings wildly (70–99%). They are not equivalent — the wide one is a worse bet. Report variance / standard deviation, and for pass/fail tasks consider consistency across repeats (e.g. pass@k or fraction of items that pass on every run).

## Step 3: Subgroup breakdown

Averages hide reversals. Break every headline metric down by the **control/subgroup dimensions you logged** (task complexity, language, segment, repo area).

> M0 and M1 both average 85%. Split by difficulty: M0 wins on simple refactors, M1 wins on complex ones. Identical average, opposite recommendation depending on your traffic mix.

If a subgroup regresses severely, that can block the ship even when the average improves.

## Step 4: Paired comparison

If both arms ran on the **same items** (a paired design, fixed before the run), don't just compare the two averages. Analyze **task-by-task differences**, which removes between-item variance and reveals whether B is *consistently* better or just better on average because of a few items.

```python
import numpy as np
diff = np.array(score_B) - np.array(score_A)        # per-item, same order
lo, hi = bootstrap_ci(diff)                          # CI on the mean difference
print(f"mean Δ = {diff.mean():.3f}, 95% CI [{lo:.3f}, {hi:.3f}], "
      f"B wins {np.mean(diff > 0):.0%} of items")
```

If the CI on the difference excludes 0, the improvement is real at that confidence. The fraction of items where B wins tells you consistency.

## Step 5: Multiple comparisons and fragility

If you compared many arms, the winner may be lucky (with 20 arms, ~64% chance of a spurious winner). Before trusting it:
- **Adjust** for multiplicity (Bonferroni for a few arms, Benjamini–Hochberg for many), **or**
- Run a **confirmatory eval on fresh data** for the apparent winner — the cleaner fix.

**Fragility:** a gain that doesn't hold across datasets, item samples, or repeated runs isn't a real gain. Be especially wary when a synthetic benchmark improves but in-the-wild traces don't. A leaderboard delta is a hypothesis, not a result.

## Step 6: Release gate

Combine everything into an explicit ship / no-ship decision. Ship only if **all** hold:

- [ ] Primary metric improves by at least the **MDE** (fixed in the experiment design, before the run).
- [ ] The **CI on the improvement excludes 0** (ideally excludes the MDE) — the gain isn't noise.
- [ ] Every **guardrail within bounds**, with its own CI on the right side of the threshold.
- [ ] **No severe subgroup regression.**
- [ ] If selected from many arms, the result **survived multiplicity correction or a confirmatory run.**

Any box unchecked → don't ship, or gather more data. The gate was defined before running; don't renegotiate it now.

## Anti-Patterns

- **Point estimates with no CI.** "85%" with no range is not a result.
- **Single run.** One run can't reveal variance; a lucky run looks like a win.
- **Average-only.** No subgroup breakdown hides reversals that flip the decision.
- **Unpaired analysis of paired data.** Comparing two averages throws away the power pairing gave you.
- **Cherry-picking the best of many arms** without correction or confirmation.
- **Trusting a fragile benchmark.** Gains that don't replicate across datasets/runs aren't real.
- **Moving the gate after seeing results.** The thresholds were set up front — honor them.
