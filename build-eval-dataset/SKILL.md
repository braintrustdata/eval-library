---
name: build-eval-dataset
description: >-
  Create, edit, audit, or compare eval datasets for LLM applications and agents, including
  target-population definition, case sourcing from production traces, stratified sampling,
  label provenance and label audits, expected values as constraints for open-ended tasks,
  dev/test splits, contamination and leakage controls, headroom checks, refresh policy, and
  datasheets. Use when working on the content or lifecycle of an eval dataset. Do not use for
  sample-size or power calculations, scorer implementation, or open-ended adversarial failure
  discovery.
---

# Build or audit an eval dataset

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/dataset-construction.md`.

## Trigger

- Building eval cases, sampling production traces, or auditing an inherited set.
- Questions about representativeness, labels, splits, contamination, or refresh.
- Open-ended tasks where one gold string is being forced onto many valid answers.
- A set that no longer discriminates: everything passes, or everything fails.

## Do

1. Inspect existing cases first and write the population sentence they appear to represent. Ask
   for the target population only if it cannot be inferred.
2. Source in the priority order in `reference.md`: production traces → expert-authored →
   synthetic to fill documented gaps → public benchmarks for cold start, harness calibration,
   anchoring, or gap mapping only.
3. Stratify rather than vibe: list strata from the instrumentation's metadata fields, measure
   production frequency per stratum, sample proportionally or oversample rare-but-critical
   strata and reweight when aggregating, then deduplicate.
4. Audit labels: provenance per item, double-label a calibration sample, report agreement,
   adjudicate. Require claimed effects to exceed the estimated label error rate. Assume error is
   **systematic**, not just random.
5. For open-ended tasks encode `expected` as **constraints or a rubric, not a string**, and ship
   the constraint set with the item.
6. Set the lifecycle: headroom at both ends, dev/test separation with **counted test touches**,
   the leakage controls in `reference.md`, refresh against current production mix, and the
   datasheet.
7. State the **iteration budget before iterating** (`reference.md`) — how many experiments before
   stopping to reflect, one coherent change each, the same dev slice throughout, and the winner
   running once against test. A budget set afterwards is a description of what you did, not a
   control on it.

## Avoid

- Do not present a public-benchmark score as product-validity proof.
- Do not force one gold string onto an open-ended task.
- Do not do the sample-size arithmetic here.
- Do not treat the transform pipeline as neutral plumbing — assert an invariant after every
  transform and version the pipeline like a scorer.
- Do not store text derived by a component you are still changing. Store the reference to the
  source and re-derive, or the dataset freezes a snapshot of the thing under iteration.
- Do not down-weight a corpus whose labels prove unusable; drop it, and report the drop.

## Check

- Construct, population, non-use documented; coverage matrix including negative cases (refuse,
  ask, do nothing).
- Label provenance per item, agreement on the calibration sample, error rate estimated.
- Difficulty spread checked; headroom confirmed at both ends.
- Splits defined, touches counted, leakage controls in place, refresh cadence set.
- Open-ended items carry constraints or rubrics; a production-failure ingestion path is owned.

## Risk

- Convenient or noisy cases support narrow benchmark claims while misrepresenting deployment.
- Label noise floors detectable effects and can reorder rankings; systematic error penalizes
  exactly the systems faithful to the real input.
- Leakage converts a capability measure into a memory measure, and no corpus can be proven clean.
- Structurally scraped items probe retrieval and precision, not judgment.

## Braintrust

Push the dataset and **version it**. This stage produces the artifact that
`references/platform-mechanics.md` §3 depends on — every paired comparison downstream is only
possible because a version exists to pin to, and a dataset change invalidates cross-experiment
comparisons exactly like a scorer change.

Populate `metadata` with every stratification field — `split`, `source`, `category`,
`difficulty`, `adversarial`, `trap`, `ground_truth_by_construction`, `label_provenance` — since
§4 is unforgiving here: a stratum missing at build time cannot be recovered at report time.

Build the production-to-dataset pipeline with **human review queues**: sample live traces,
review, append. Keep benchmark scaffolding in **separate, clearly named datasets** — once mixed,
the distinction between measuring your construct and the benchmark's is unrecoverable. Counting
test touches is a discipline the platform will not enforce; track it in the dataset description.

For items sourced from logs, store the **reference** — `trace_ref`, `group_ref`, or
`_full_row_id_ref` — not materialized text derived from the trace. Deduplicate on the stable
identity of the referenced unit. Row shapes are in
`discover-trace-topics/references/facet-pipeline.md`.
