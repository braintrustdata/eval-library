# eval-library

A library of Claude Code skills for running and analyzing evals in Braintrust.

Each skill is a directory containing a `SKILL.md` (and any supporting `references/` or `scripts/`). Drop a skill directory into `~/.claude/skills/` to use it.

## Workflow skills

Interactive, end-to-end. These orchestrate a whole job and may hand off to the artifact skills below.

- **[braintrust-eval](braintrust-eval/)** — Run an independent, end-to-end eval in Braintrust: from a plain-English idea to a scored, compared experiment (dataset sourcing, scorer design, hygienic experiment runs).
- **[bt-analyze-eval-results](bt-analyze-eval-results/)** — Turn eval results into a defensible ship / no-ship decision: confidence intervals, run-to-run variance, subgroup breakdowns, paired comparisons, and a stats-grounded release gate.

## Eval lifecycle skills

Narrow, composable artifact skills — one per stage of the eval lifecycle. Each owns a single artifact, is invocable on its own, and names the skill that consumes its output next. All share the interaction contract in [INTERACTION.md](INTERACTION.md), mirrored into each skill's `references/` so a skill directory works standalone.

**Foundation**

- **[plan-agent-eval](plan-agent-eval/)** — Turn an ambiguous eval request into a staged plan: identify the product decision, inventory what exists, and name the earliest missing artifact.
- **[design-eval-instrumentation](design-eval-instrumentation/)** — Design the trace and dataset schema and wire the system to emit it: spans, native scores and metrics, metadata, attachments, resolved config, per-item status.
- **[write-agent-behavior-spec](write-agent-behavior-spec/)** — Define recurring agent conduct as a versioned `BEHAVIOR.md`: intent, applicability, evidence, decision, execution, recovery, failure modes.

**What to measure**

- **[define-eval-objective](define-eval-objective/)** — Work backward from a product decision to the construct, population, intended claim, and the verification-vs-validation questions.
- **[design-eval-metric-bundle](design-eval-metric-bundle/)** — Separate quality, safety, reliability, latency, and cost measures; distinguish improvement targets from guardrails; expose Goodhart risk.
- **[map-eval-evidence](map-eval-evidence/)** — Connect constructs to observable success and failure signals, with each proxy's limitation and gaming path named.

**Human knowledge**

- **[elicit-eval-criteria](elicit-eval-criteria/)** — Extract criteria from domain experts and real user desires before labeling begins: construct facets, anchored exemplars, adversarial traps.
- **[design-human-eval-review](design-human-eval-review/)** — Design the review workflow and golden dataset: case selection, rater assignment, rationales, inter-rater agreement, adjudication.

**Datasets**

- **[build-eval-dataset](build-eval-dataset/)** — Population definition, case sourcing, stratified sampling, label audits, open-ended constraints, splits, contamination controls, refresh policy.
- **[size-eval-dataset](size-eval-dataset/)** — Sample sizes, minimum detectable effects, clustering design effects, and clean-trial counts for bounding rare failures.

**Scorers**

- **[write-eval-scorer](write-eval-scorer/)** — Implement one narrow scorer: match method to evidence and stakes, anchor rubrics with examples, handle refusals, timeouts, and parse failures.
- **[validate-eval-scorer](validate-eval-scorer/)** — Validate a scorer against expert labels: agreement with uncertainty, severity-weighted confusion, shortcut probes, and a fitness verdict for gating.
- **[deploy-braintrust-evaluator](deploy-braintrust-evaluator/)** — Put a validated scorer or classifier on real traffic: input scope, inline testing before saving, online-scoring rules, activation, and backfill with a cost estimate.

**Experiments**

- **[design-eval-experiment](design-eval-experiment/)** — Pre-specify a comparison: hypothesis with a minimum effect, named variables including serving path and tool surface, pairing, and a pre-analysis plan.
- **[analyze-eval-experiment](analyze-eval-experiment/)** — Analyze completed results: run-integrity audit, intervals, clustering, paired differences, multiplicity, subgroups, fragility.
- **[attribute-multi-variable-change](attribute-multi-variable-change/)** — Attribute a change when several things moved at once: difference inventory, isolation designs, and honest bundle-vs-component claims.
- **[define-eval-release-gate](define-eval-release-gate/)** — Combine magnitude, significance, consistency, stability, reliability, safety bounds, latency, and cost into an explicit ship-or-hold policy.

**Diagnostics and discovery**

- **[probe-capability-and-variability](probe-capability-and-variability/)** — Run the same dataset under variants to measure either the ceiling of what a system can do (`pass@k`) or the spread of how reliably it does it (`pass^k`).
- **[discover-agent-failures](discover-agent-failures/)** — Open-ended search for unanticipated failure modes, clustered and triaged into a root-cause taxonomy and frozen regression items.
- **[discover-trace-topics](discover-trace-topics/)** — Build the clustering instrument itself: preprocessor, facet prompt, no-match policy, and the automation that discovers a label set from traffic when none exists yet.
- **[red-team-agent](red-team-agent/)** — Adversarial testing against an explicit threat model, prioritizing attack-family coverage over raw success rate, producing existence claims and mitigations.

**Reporting and production**

- **[report-eval-results](report-eval-results/)** — Turn analysis into a report with claims calibrated to the evidence: intervals, effective n, search disclosure, pinned configuration.
- **[monitor-production-evals](monitor-production-evals/)** — Online scoring coverage, alert ownership, drift on both input and scorer, and the pipeline from production failure back into the dataset.

## Routing

The artifact named in a request is the strongest routing signal. When a request names a dataset, scorer, experiment, gate, or report, use that artifact's skill rather than `plan-agent-eval`.

The four elicitation regimes are easy to confuse, and mislabeling which one you are in is the most common eval-reporting error:

| Regime | Statistic | Skill |
| --- | --- | --- |
| Capability elicitation | max over attempts (`pass@k`) | `probe-capability-and-variability` |
| Variability probing | distribution, worst case (`pass^k`) | `probe-capability-and-variability` |
| Failure discovery | an enumeration | `discover-agent-failures` |
| Red teaming | existence of a breaking input | `red-team-agent` |

`discover-trace-topics` and `discover-agent-failures` both say "discover" and are not the same job.
Topics builds the **instrument** that turns unlabeled traffic into clusters; failure discovery is
the **investigation** that turns candidates into a root-cause taxonomy and frozen regression items.
Topics is usually a step inside failure discovery, not a substitute for it.

Instrument choice, when the request is "label our traffic somehow":

| The label set is | Instrument | Skill |
| --- | --- | --- |
| Known and stable | classifier | `write-eval-scorer` → `deploy-braintrust-evaluator` |
| A 0–1 criterion | scorer | `write-eval-scorer` → `validate-eval-scorer` |
| Not known yet | facet + clustering | `discover-trace-topics` |

## Conventions

- **Card format.** Lifecycle skills use a five-field card — `Trigger` / `Do` / `Avoid` / `Check` / `Risk` — plus a `Braintrust` section carrying the platform mechanics for that stage. It is compact procedural memory, retrieved on demand.
- **Numbers live in `references/`.** Cards carry the procedure; thresholds carry their hedge and provenance in the reference file. A number that *is* the method (rule of three, K ≥ 3 runs, ≥ 2 raters) stays in the card; tunable defaults (κ floors, item counts, gate thresholds) do not.
- **Provenance tags.** Empirical claims in `references/` carry `[guide §N]`, `[guide §N → source]` where the guide is paraphrasing, or `[pending]` where a claim is not yet in published prose and should be re-checked before external use. Platform mechanics — tool names, argument shapes, product defaults — carry `[platform]`. They are not empirical claims and have no guide section, but they go stale the same way, so re-check them against the shipped tool surface before relying on one externally.

## Examples

- **[rag-only-enforcement](rag-only-enforcement/)** — A runnable end-to-end eval (not a skill): does behavior-based scoring catch what `test_passed` misses when a coding agent is given a "locate code via vector search only" rule? Four enforcement variants over SWE-bench Django tasks, with output and behavior scorers side by side.
