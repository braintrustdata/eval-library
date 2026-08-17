# Reference — planning

## Lifecycle inventory template

One row per stage, in dependency order. Status uses the four labels from
`interaction-contract.md`. Stages are described by the artifact they produce, so the plan reads
the same whether or not a given stage has tooling behind it.

```yaml
decision: <one sentence — ship/hold, A vs B, v3 vs v4>

stages:
  - stage: instrumentation
    artifact: trace + dataset schema, emitted and verified on one item
    status: Confirmed | Assumed | Needs decision | Not yet measurable
    evidence: <what you read to decide this>
    blocks: <which downstream stages are unusable without it>
  - {stage: behavior spec,     artifact: versioned BEHAVIOR.md + review questions}
  - {stage: objective,         artifact: decision, construct, population, claim, non-use}
  - {stage: metric bundle,     artifact: per-metric direction, role, threshold, gaming path}
  - {stage: evidence map,      artifact: construct → signals, limitations, blind spots}
  - {stage: criteria,          artifact: facets + anchored exemplar pairs + traps}
  - {stage: dataset,           artifact: stratified items, labels with provenance, datasheet}
  - {stage: sizing,            artifact: required n, assumptions, sensitivity range}
  - {stage: scorers,           artifact: one scorer per criterion, versioned, tested}
  - {stage: human reference,   artifact: golden set, agreement reported, adjudicated}
  - {stage: scorer validation, artifact: agreement, severity confusion, fitness verdict}
  - {stage: experiment design, artifact: hypothesis + variables + pre-analysis plan}
  - {stage: analysis,          artifact: effective n, intervals, paired diffs, subgroups}
  - {stage: release gate,      artifact: per-row rules with owners and failure readings}
  - {stage: reporting,         artifact: claims calibrated to evidence, re-run fields}
  - {stage: monitoring,        artifact: sampling, alerts with owners, ingestion loop}

earliest_gap: <stage>
next_action: <one concrete thing>
blocking_reason: <why this stage blocks the others>
assumptions: []
```

Diagnostic work sits outside this order and is pulled in on demand rather than sequenced:
variant probing for stability or hidden capability, multi-variable attribution when several
things changed at once, open-ended failure discovery, and adversarial red teaming.

## Why the earliest gap, not the most interesting one

Each stage consumes the previous one's artifact. A scorer built before the evidence map measures
whatever was convenient to log; a dataset built before the population definition drifts toward
whatever was easy to gather; an experiment run before instrumentation cannot attribute a failure
to a module. Recommending a downstream stage while an upstream one is missing produces work that
has to be redone.

`[guide §2.1, §3.2, §4.1]`

## The two prerequisites teams skip

- **Instrumentation.** Traces are the behavioral record and everything else consumes them; a thin
  trace caps every downstream measurement, and you cannot retroactively log a field.
  `[guide §1, §3.2]`
- **Criteria.** Human judgment defines the target; automation extends it. If nobody can say what
  "good" means, every scorer downstream encodes a guess. `[guide §6]`

## When not to build process

The suite is for decisions worth defending. Say so plainly when the decision is low-stakes and
reversible, and recommend the smallest useful step instead — usually a handful of items reviewed
by a human, with the explicit note that it is not evidence about which option is better.

A cheap smoke run verifies plumbing end to end. It is never evidence about a comparison, and its
numbers should not be quoted. `[guide §2.5]`

## Scope of a public benchmark

Four legitimate jobs — cold start, harness calibration, external anchoring, gap mapping. In all
four, a benchmark measures *its* construct, not yours, so it is never the starting point for a
product-readiness question. `[guide §4.2]`
