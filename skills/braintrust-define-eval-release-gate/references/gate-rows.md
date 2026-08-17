# Reference — release gate

## The gate table

Thresholds below are **illustrative** — from a worked example for a
coding-assistant model update, K = 3 runs on the confirmatory task set. Substitute your
own from product tolerances and fix them **before** the run.

| Criterion | Rule | Statistical basis |
| --- | --- | --- |
| **Magnitude** | Mean paired improvement ≥ 3 pp on task success | Effect big enough to matter, not merely detectable; report Cohen's d of per-task differences alongside |
| **Significance** | 95% CI on the paired difference excludes zero (clustered SEs, run variance included) | paired analysis |
| **Consistency** | Wins ≥ 60% of differing task categories; regression rate ≤ 2% of previously-passing tasks | a mean-score winner can still lose most categories; P(new > old) ≥ 0.75 suggested for strong claims |
| **Stability** | Conclusion survives dropping the single most favorable task category | leave-one-out / breakdown check |
| **Reliability** *(if the product promises all-attempts, not average-case)* | `pass^k` at the k users actually retry to, above threshold — not `pass@k`, not the mean | audit and compliance guarantees are all-attempts by nature |
| **Safety** | Violation-rate 95% **upper bound** (Wilson or rule of three) below threshold — not the point estimate | with 0 observed violations the bound is ≈ 3/n, so size n to the tolerance |
| **Latency** | p95 below target in **every run**, not on average across runs | users experience runs, not means |

`[Oh 2026; Bouthillier et al. 2021; Yao et al. 2024; Mohammadi et al. 2025]`

## `pass^k` vs `pass@k`

- `pass@k` — **any** of k attempts succeeded. A capability statistic.
- `pass^k` — **all** k attempts succeeded. A reliability statistic.

Under independence `pass^k` = p^k, so a system succeeding 90% per attempt is at **57%** by
k = 8. τ-bench introduced the metric and found even state-of-the-art function-calling
agents "succeed on <50% of the tasks, and are quite inconsistent (pass^8 <25% in retail)."

Quoting the first while promising the second is one of the more common honest-looking
reporting errors. `[Yao et al. 2024]`

## Interpreting gate failures — each row means something different

- **Magnitude fails:** the change is not worth migration cost even if real.
- **Consistency fails while magnitude passes:** the model specialized; investigate which
  categories regressed before deciding.
- **Stability fails:** the improvement is one favorable task slice wearing a trenchcoat.
- **Reliability fails while magnitude passes:** the mean moved and the tail did not. You
  have a better average system and the same unreliable one — a ship decision only if users
  tolerate retries.

## Precondition

Every row presumes the runs behind it are intact. Confirm effective N and error accounting
per arm first: **a gate computed on a run with unexplained missing items is not a gate, it
is a gate-shaped artifact of whichever items happened to survive.**

## Red-team findings enter as existence constraints

Never as an averaged score. Because completeness is unreachable — no finite set of
guardrails is universally robust against adversarial prompts — the constraint is
**re-tested every round** rather than retired once passed.
`[Vassilev 2026; NIST 2026]`

## Gate spec template

```yaml
shipping_claim: <one sentence — what shipping asserts>
non_negotiables:
  - <failure that cannot be traded away>
confirmatory_set: <name>@<version>   # never the tuning set
runs_K:
precondition:
  effective_n_reconciled: required

rows:
  - criterion: magnitude
    rule: <expression>
    threshold: <value>
    threshold_source: <product tolerance | benchmark | Needs decision>
    threshold_type: point_estimate | upper_confidence_bound | worst_run
    role: improve | guardrail
    scorer: <name>@<version>
    scorer_fit_for_gating: yes | no    # per its validation verdict
    owner: <role>
    on_failure: <what it means, and the evidence that would justify reconsideration>

existence_constraints:
  - <red-team finding, re-tested each round>
```

## Ownership

A threshold with no owner is a dashboard. Every row names the role that can waive it, and
a waiver is recorded with its reason — otherwise the gate erodes silently, one exception
at a time.
