# Reference — experiment design

## Variables

- **Independent:** model choice, prompts, retrieval on/off, caching, guardrail
  strictness.
- **Dependent:** correctness vs. tests, judge scores, latency (p50, p95), cost
  (tokens/dollars).
- **Control:** language, domain, repo segment, user segment, time window, **tool
  surface**, **serving environment**.

If a control variable matters, it must be a schema field — otherwise you cannot hold it
constant or slice by it, and confounds enumerated on a whiteboard stay on the whiteboard.
`[guide §8.2]`

## Hypothesis shape

> **H1:** On the confirmatory task set (population: backend Python repos,
> production-weighted), M1 improves paired task-success rate over M0 by ≥3 pp, with the
> safety-violation upper bound below 0.5% and p95 latency below 2 s in every run.

Thresholds are illustrative — substitute your own from product tolerances. Note that H1
**is** the release gate stated in advance; that is the point. `[guide §8.1]`

Good hypotheses are directional, specific, tradeoff-aware, and name their constructs,
proxies, scorers, and population.

The elicitation regime dictates the hypothesis form and the estimator:

| Regime | Statistic | Claim |
| --- | --- | --- |
| Capability | max over attempts (`pass@k`) | "can at least do X" |
| Variability | distribution, worst case (`pass^k`) | "reliably does X" |
| Failure discovery | an enumeration | "here is what goes wrong" |
| Red teaming | existence of a breaking input | "there exists an input that breaks X" |

`[guide §4.8, §8.1]`

## Confound mitigation, done well

Ziabari et al. noticed System 2 responses in their training data were systematically
longer than System 1 responses, and knew preference-alignment methods reward length
itself. They rewrote responses to equalize lengths, then **verified the fix with
statistical equivalence tests before training**, so downstream differences could be
attributed to reasoning style rather than verbosity.

The full pattern in three steps: **name the confound, intervene, verify the intervention
actually worked.** `[guide §8.2 → Ziabari et al. 2025]`

## What hides inside a model string

```yaml
provider:            # same weights, different provider ≠ same system
endpoint_tier:
region:
decoding_params:
cache_state:         # cold vs. warm moves latency and cost more than most prompt edits
batching:
```

Batch size, GPU count, and GPU version all shift generated responses, amplified by BF16
precision. `[guide §8.2 → Yuan et al. 2025]`

Under role-based access the tool surface is not fixed even within one deployment; pin the
manifest (names, schemas, permissions) per arm, because an arm silently lacking a tool
reads as a capability gap. `[guide §8.2 → Mohammadi et al. 2025]`

## Two disciplines once runs start

**Fix nothing mid-comparison.** Noticing a defect in arm 3 of 6 creates an almost
irresistible urge to correct and carry on. Don't: the arms stop being comparable, and
unlike a dataset or scorer version, the discrepancy **leaves no trace in the results
table**. The choice is binary — restart the whole matrix under the corrected
configuration, or finish as designed and record the defect as a stated limitation. A
better configuration discovered mid-run is an input to the next round, not a patch for
this one. `[guide §8.2]`

**Verify the treatment is implementable in every arm.** Suppose the hypothesis is
"supplying a domain glossary improves extraction accuracy": one vendor takes free-form
prose, a second takes only a flat list of literal terms, a third offers no such input.
"Glossary on/off" is now a different treatment per arm, and one arm cannot receive it.
Enumerate the per-arm implementation before running, publish it as a table beside the
results, and exclude arms that cannot receive the treatment from the treatment-effect
claim rather than recording them as "no benefit." Confirm too that the option you set is
one the API still reads — renamed and deprecated parameters are usually accepted in
silence and ignored. `[guide §8.2]`

## Run integrity, pre-planned

- **Throttle your own concurrency — mandatory at scale, not tuning.** Unbounded
  parallelism yields resets, socket exhaustion, and provider throttling, all of which
  arrive as low scores or missing rows rather than a stack trace pointing at your runner.
  Make the cap a configurable parameter, treat rate limits as retry-with-backoff honoring
  `Retry-After`, and run free/trial-tier arms slower on purpose.
- **Budget quota against the whole matrix in advance:** items × arms × runs against every
  metered limit and credit balance in the path.
- **Keep the comparison surface clean:** name every run for the variables it varies,
  most-significant first (`v2_model-a` groups; `model-a_v2` scatters); delete superseded
  runs as you go; pin each run to dataset, prompt, and scorer versions.

`[guide §8.4]`

## Manifest template

```yaml
hypothesis: <H1, directional, minimum effect, guardrail bounds>
population: <construct + weighting>
regime: capability | variability | failure_discovery | red_team
arms:
  - name: <variable-first prefix>
    independent_vars: {}
    serving_path: {provider: , tier: , cache_state: }
    tool_manifest: []
    treatment_implementation: <or "cannot receive — excluded from claim">
paired: yes | no
pairing_key: <item id>
runs_K: <≥3 for gating>
dataset: <name>@<version>
scorers: [<name>@<version>]
sample_plan: <from the power analysis>
pre_analysis:
  estimators: []
  intervals: <clustered? run variance folded in?>
  stopping_rule:
  exclusion_rules:
  multiplicity: bonferroni | holm | bh | exploratory_then_confirmatory
  confirmatory_set: <held-out, never touched>
run_integrity:
  max_concurrency:
  quota_budget: <items × arms × runs vs. limits>
```
