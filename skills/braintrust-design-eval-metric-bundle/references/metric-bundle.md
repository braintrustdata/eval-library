# Reference — metric bundle

## Illustrative bundle

These four thresholds are **illustrative, not borrowed from a benchmark**. Pick your
own from product tolerances, then hold them fixed across the comparison.

| Metric | Role | Example threshold | Threshold type |
| --- | --- | --- | --- |
| Task success | improve | ≥ 90% solved correctly | point estimate + CI |
| Security-violation rate | guardrail | < 0.5% | 95% **upper** bound |
| p95 latency | guardrail | < 2 s | worst run, not mean |
| Cost per resolved request | guardrail | within budget | point estimate |

`[guide §2.2]`

## Provenance

- Correctness, safety, efficiency, and cost are **different constructs** and should be
  measured and reported separately. `[guide §2.2 → NIST AI 800-3 2026; Truong &
  Koyejo 2026]`
- Distinguish metrics to **improve** from guardrail metrics **not to regress**; the
  two play different roles in a release gate and should never be averaged — a
  composite lets strength in one dimension hide a regression in another.
  `[guide §2.2]`
- Cost as cost per *resolved* request: "total spend by tickets that were actually
  resolved well." Escalation policies held ~93% resolution at roughly 23–34% lower
  cost than always using the frontier model, while an always-cheapest policy resolved
  only ~68–70%. `[guide §2.2, §4.8.5 → Braintrust CostEff 2026]`
- **Goodhart, formally:** a proxy reward is *unhackable* only if increasing the proxy
  can never decrease the true reward — a condition that rarely holds.
  `[guide §2.3 → Skalse et al. 2022]`
- **Goodhart, empirically:** models exploit weaknesses in evaluation setups and use
  rubric-following shortcuts that raise the score without raising task success.
  `[guide §2.3 → Weng 2024; promptfoo]`
- Reliability and safety are peer top-level categories in the agent-eval taxonomy,
  measured at whichever layer is under test rather than folded into quality.
  `[guide §2 preamble → Mohammadi et al. 2025]`
- Cost/efficiency as a first-class metric is an independent recommendation of the
  agent-eval surveys, not just a product concern. `[guide §2.2 → Yehudai et al. 2025]`

## Metric record template

```yaml
metric: <name>
construct: <what it is evidence of>
direction: higher_is_better | lower_is_better
decision_role: improve | guardrail
threshold: <value>
threshold_type: point_estimate | upper_confidence_bound | worst_run
scope: <all items | the subset the change can touch>
proxy_limitation: <what this metric cannot see>
gaming_path: <how to raise it without improving the outcome>
```

## Scope-mismatch test

Before accepting a metric, confirm it **could** show the effect under test.

If a change rewrites a handful of tokens per response, a response-level similarity
average dilutes the effect toward zero — the denominator is dominated by tokens the
change could never alter. The honest pair is both numbers: "+0.11 entity recall on
the 38% of items with structured identifiers, +0.004 overall." Both sentences are
true, and only the pair is informative.

A null result on a diluted metric is not a null result. `[guide §2.5]`

## Defenses against gaming, in rough order of value

1. Several proxies per outcome.
2. A guardrail bundle, so gaming one metric shows up in another.
3. Scorer validation against humans.
4. A confirmatory set the optimization loop never touches.

`[guide §2.3]`
