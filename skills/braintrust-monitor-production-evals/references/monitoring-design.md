# Reference — production monitoring

## The loop

**Offline evals** run against a curated dataset before shipping: controlled, repeatable,
cheap to iterate. **Online evals** score live production traffic: perfect distributional
realism, no controlled comparison. **Neither substitutes for the other.**

```
offline experiments gate the release
  → online scoring monitors the shipped system on real traffic
  → observed production failures become new dataset items
  → the next offline eval is more representative than the last
```

Mature engineering fields earned trust exactly this way: pre-deployment gates paired with
post-deployment monitoring. `[Weidinger et al. 2025]`

Because completeness is unreachable — no finite guardrail set is universally robust — the
recommended posture is continuous monitor-and-update rather than one-and-done
certification. `[Vassilev 2026; NIST 2026]`

## Sampling plan

Proportional sampling under-covers exactly the slices that matter. Stratify.

```yaml
overall_rate: <% of traffic>
strata:
  - {slice: , production_share: , sample_rate: , rationale: }
  - {slice: rare_severe, production_share: 0.1%, sample_rate: 100%,
     rationale: "cannot be estimated at proportional rate"}
scorers_online: [{name: , version: , approved_use: trend|gating|exploration}]
oversample_triggers:
  - newly changed behavior
  - high-risk domains
  - items where automated scorers disagree
```

Place human attention on ambiguous examples, high-risk domains, newly changed behavior, and
scorer disagreements — not on volume. `[Lazaros et al. 2026]`

## Alert specification

Every alert, or it does not ship:

```yaml
alert: <name>
metric: <scorer or native metric>
threshold: <value>
threshold_provenance: <which baseline, which window, computed how, by whom, when>
window: <evaluation period>
owner: <role who acts>
action: <the specific thing the owner does>
review_latency: <how fast someone must look>
suppression: <conditions under which it should not fire>
```

An alert with no action is a notification. An alert with no owner is a dashboard.

## Drift, on both sides

| Drift | Symptom | Check |
| --- | --- | --- |
| **Input distribution** | traffic no longer matches the eval population | stratum shares vs. dataset weights, on a schedule |
| **Scorer / judge** | the instrument's behavior moves under a model update | re-run the calibration experiment against the golden set |

Scorer drift under a provider model update is indistinguishable from a product regression
without the calibration re-run. Re-validate on a schedule, not on suspicion.

Also refresh the golden set as the product changes; a judge only works while it stays
anchored.

## Silent failures

Error-rate dashboards look healthy while these accumulate. One multi-agent study found
**75.17%** of failures were silent semantic failures vs. 24.84% explicit — explicit being
exceptions 6.38% and timeouts 1.86%. Silent failures "do not trigger explicit system
failures and are therefore not immediately visible to users."
`[Ma et al. 2026]`

Consequence: monitor **quality scorers**, not just exception rates. A dashboard showing only
errors is monitoring a quarter of the problem.

## Closing the loop

```yaml
ingestion:
  eligibility: <what makes a flagged trace worth keeping>
  reviewer: <role>
  review_latency: <SLA>
  destination: <golden dataset>@<version>
  provenance_attached: [trace_id, incident_ref, date, reviewer]
  pii_scrubbed_before_storage: true
retirement:
  saturated_items: <retired in favor of harder ones from recent failures>
  stratum_reweight_cadence: <against current production mix>
```

Every production incident and user-flagged failure is a free, maximally relevant test item —
route them in as a standing pipeline.

## Privacy and retention

Applied at collection time, per field:

```yaml
field:
sensitivity: none | pii | secret
scrub_at: collection | never_collected
retention_window:
access: <who>
```

The most informative traces may be the ones you are not permitted to keep. Design the
measurement around what is retainable rather than discovering the constraint after building
on it.

## Observational, not causal

A production metric moving does not license a causal claim about a change: an offline A/B on
the same items supports a causal claim, an observational drift in production metrics does
not.
