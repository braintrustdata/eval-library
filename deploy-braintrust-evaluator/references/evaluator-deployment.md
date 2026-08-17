# Reference — evaluator deployment

Thresholds here are **defaults to justify, not laws**. Quote the hedge with the number.

Platform mechanics carry `[platform]` rather than a guide section. They are product behavior, not
empirical claims — but they go stale the same way, so re-check them against the shipped tool
surface before relying on one externally.

## Two things called "level" — keep them apart

The suite uses one word for two independent axes, and conflating them produces evaluators that
answer a question nobody asked.

| Axis | Values | Question it answers |
| --- | --- | --- |
| **Input scope** | span, trace, group | How much of the data does one evaluator call see? |
| **Reporting level** | per-item, aggregate | Is the number about one case or the population? |

They are orthogonal. A span-scoped evaluator still aggregates across the dataset; a group-scoped one
still produces a per-group score you can localize. When `write-eval-scorer` says per-item scoring
localizes failures and aggregate detects regressions, that is the **reporting** axis — it says
nothing about how much data one evaluator call sees.

Note the collision this replaces: "group" on the input axis means *several traces joined by a
metadata key*, and older phrasing used "group-based" for what is here called aggregate reporting.
If you encounter the latter in an inherited scorer contract, it is the reporting axis.

## Input scope selection

| Scope | Use when | Identity |
| --- | --- | --- |
| **span** | The behavior lives in one LLM call or one tool call | span row id |
| **trace** | The behavior spans a request — planning, retries, tool sequences | root span id |
| **group** | The behavior spans several traces — multi-turn conversations, sessions | a metadata key |

**Default to trace.** It is the scope at which most product-relevant behavior is visible, and the
one that keeps a failure attributable to a request. `[platform]`

Group scope needs a grouping key that actually exists — commonly `metadata.conversation_id`,
`session_id`, or `thread_id`. Download traces and inspect metadata to confirm it is populated and
stable before committing; a grouping key that is null on a third of traffic silently drops that
traffic from the evaluator's view.

## Output contract

| | Scorer | Classifier |
| --- | --- | --- |
| Returns | number in 0–1 | one label from a fixed set |
| Configure | `choice_scores` (LLM) | `choices`, no numeric mapping |
| `output_type` | `"score"` | `"classification"` |
| Needs | numeric mapping, skip behavior | allowed labels, no-match behavior |

Code evaluators declare `output_type` to describe their output but use neither `choice_scores` nor
`choices`. `[platform]`

Pick classifier when the answer is categorical and the categories are known. Forcing categories onto
a 0–1 scale so it "matches the other scorers" discards the distinction you built the instrument to
capture. If the categories are *not* known yet, you are doing discovery — see
`discover-trace-topics`.

## LLM evaluator defaults

- **Emit classes, map to numbers.** Have the model return semantic labels and configure
  `choice_scores` to map them. Full rationale in `write-eval-scorer/references/scorer-patterns.md`.
- **Start cheap.** Default to a small model and escalate only on measured failure against the
  reviewed examples, not on the suspicion that a bigger model would do better. Judge cost is paid
  per trace, forever, on every sampled item. `[platform]`
- The judge model still must not share a family with the system under test — the cost default does
  not override the bias rule.

## Rule configuration

```yaml
evaluator_ids: [<function ids>]
scope: span | trace | group
grouping_key: <metadata field, group scope only>
filters: <which traffic>
sampling_rate: <fraction>       # primary cost control
status: paused | active         # new rules default to paused
log_behavior:
```

Sampling defaults worth stating: begin below full coverage on any project whose volume you have not
measured, and treat 100% as a decision requiring approval rather than a starting point. Stratify
where rare-but-severe slices matter — `monitor-production-evals` owns that argument. `[platform]`

## Activation and rewind are separate

```text
                 set_automation_status(active)
   paused  ──────────────────────────────────────▶  active
     │                                                │
     │ operation:"rewind"                             │ operation:"rewind"
     │ (queued, nothing processes)                    │ (processes)
     ▼                                                ▼
  rewound + paused ── activate ──────────────▶  rewound + processing
```

Authorization for one never implies the other. The failure this prevents: a user authorizes a
backfill, the rule is paused, the rewind is accepted, and nothing runs — while everyone believes
history is being scored. When only a rewind was requested on a paused rule, state the dependency and
ask. `[platform]`

Submit a rewind **once**. Resubmitting is not a progress query and does not return status.

## Rewind estimation

Count eligible units over the *exact* rule configuration and the proposed window:

| Scope | Count |
| --- | --- |
| span | spans |
| trace | distinct traces |
| group | distinct grouping values |

```text
estimated_scored_units = eligible_units * sampling_rate
```

Then multiply by per-call judge cost for LLM evaluators. Report the approximation with the sampling
rate visible in it, so a reader can tell 1,400 scored spans from 14,000 eligible ones.

Resolve natural-language windows yourself. "The past few days" becomes a stated inclusive start
time and a stated estimate; asking the user to confirm a timestamp they described in words is
friction, not diligence. Ask only where the window is ambiguous enough to change the outcome
materially.

## Reading backfill results

A rewind in progress produces a **preliminary** aggregate over whatever has been scored so far, and
the earliest-processed slice is not a random sample of the window. Say preliminary, or the first
number becomes the remembered one.

Then: distribution first, representative cases at both ends and at the boundary, and only then a
conclusion. Charts — histogram for distribution, time series for trend, grouping by a category only
where it improves interpretation. Validate any chart against a bounded query over the same window
before presenting it; an empty or all-null chart is a bug in the chart far more often than an
absence of signal.

## Deployment record template

```yaml
evaluator: <name>@<version>       # name stable across every deployment
output_type: score | classification
fitness_verdict:
  allowed_uses: [exploration, trend_monitoring, release_gating]
  validated_against: <golden set>@<version>
  date:

scope: span | trace | group
grouping_key:
grouping_key_coverage: <fraction of traffic where it is populated>

rule:
  automation_id:
  filters:
  sampling_rate:
  status:
  activated_by:
  activated_date:

rewind:
  window_start:
  eligible_units:
  estimated_scored_units:
  estimated_cost:
  approved_by:
  submitted_date:
```
