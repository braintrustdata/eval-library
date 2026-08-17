# eval-library

A library of Claude Code skills for running and analyzing evals in Braintrust.

Every skill lives under [skills/](skills/), named `braintrust-*` so the set namespaces cleanly alongside skills from elsewhere. Each is a directory containing a `SKILL.md` plus any supporting `references/`. Drop one into `~/.claude/skills/`, or symlink it, to use it.

## Workflow skills

Interactive, end-to-end. These orchestrate a whole job and may hand off to the artifact skills below.

- **[braintrust-eval](skills/braintrust-eval/)** — Run an independent, end-to-end eval in Braintrust: from a plain-English idea to a scored, compared experiment (dataset sourcing, scorer design, hygienic experiment runs). Hands off to `braintrust-analyze-eval-experiment` for the analysis pass.

## Eval lifecycle skills

Narrow, composable artifact skills — one per stage of the eval lifecycle. Each owns a single artifact, is invocable on its own, and names the skill that consumes its output next.

Two files are shared by every card and mirrored into each skill's `references/` so a skill directory works standalone: the interaction contract in [INTERACTION.md](INTERACTION.md), and the platform mechanics in [PLATFORM.md](PLATFORM.md). Edit the root copy and re-mirror; never edit a mirror directly.

**Foundation**

- **[braintrust-plan-agent-eval](skills/braintrust-plan-agent-eval/)** — Turn an ambiguous eval request into a staged plan: identify the product decision, inventory what exists, and name the earliest missing artifact.
- **[braintrust-design-eval-instrumentation](skills/braintrust-design-eval-instrumentation/)** — Design the trace and dataset schema and wire the system to emit it: spans, native scores and metrics, metadata, attachments, resolved config, per-item status.
- **[braintrust-write-agent-behavior-spec](skills/braintrust-write-agent-behavior-spec/)** — Define recurring agent conduct as a versioned `BEHAVIOR.md`: intent, applicability, evidence, decision, execution, recovery, failure modes.

**What to measure**

- **[braintrust-define-eval-objective](skills/braintrust-define-eval-objective/)** — Work backward from a product decision to the construct, population, intended claim, and the verification-vs-validation questions.
- **[braintrust-design-eval-metric-bundle](skills/braintrust-design-eval-metric-bundle/)** — Separate quality, safety, reliability, latency, and cost measures; distinguish improvement targets from guardrails; expose Goodhart risk.
- **[braintrust-map-eval-evidence](skills/braintrust-map-eval-evidence/)** — Connect constructs to observable success and failure signals, with each proxy's limitation and gaming path named.

**Human knowledge**

- **[braintrust-elicit-eval-criteria](skills/braintrust-elicit-eval-criteria/)** — Extract criteria from domain experts and real user desires before labeling begins: construct facets, anchored exemplars, adversarial traps.
- **[braintrust-design-human-eval-review](skills/braintrust-design-human-eval-review/)** — Design the review workflow and golden dataset: case selection, rater assignment, rationales, inter-rater agreement, adjudication.

**Datasets**

- **[braintrust-build-eval-dataset](skills/braintrust-build-eval-dataset/)** — Population definition, case sourcing, stratified sampling, label audits, open-ended constraints, splits, contamination controls, refresh policy.
- **[braintrust-size-eval-dataset](skills/braintrust-size-eval-dataset/)** — Sample sizes, minimum detectable effects, clustering design effects, and clean-trial counts for bounding rare failures.

**Scorers**

- **[braintrust-write-eval-scorer](skills/braintrust-write-eval-scorer/)** — Implement one narrow scorer: match method to evidence and stakes, anchor rubrics with examples, handle refusals, timeouts, and parse failures.
- **[braintrust-validate-eval-scorer](skills/braintrust-validate-eval-scorer/)** — Validate a scorer against expert labels: agreement with uncertainty, severity-weighted confusion, shortcut probes, and a fitness verdict for gating.
- **[braintrust-deploy-evaluator](skills/braintrust-deploy-evaluator/)** — Put a validated scorer or classifier on real traffic: input scope, inline testing before saving, online-scoring rules, activation, and backfill with a cost estimate.

**Experiments**

- **[braintrust-design-eval-experiment](skills/braintrust-design-eval-experiment/)** — Pre-specify a comparison: hypothesis with a minimum effect, named variables including serving path and tool surface, pairing, and a pre-analysis plan.
- **[braintrust-analyze-eval-experiment](skills/braintrust-analyze-eval-experiment/)** — Analyze completed results: run-integrity audit, intervals, clustering, paired differences, multiplicity, subgroups, fragility.
- **[braintrust-attribute-multi-variable-change](skills/braintrust-attribute-multi-variable-change/)** — Attribute a change when several things moved at once: difference inventory, isolation designs, and honest bundle-vs-component claims.
- **[braintrust-define-eval-release-gate](skills/braintrust-define-eval-release-gate/)** — Combine magnitude, significance, consistency, stability, reliability, safety bounds, latency, and cost into an explicit ship-or-hold policy.

**Diagnostics and discovery**

- **[braintrust-probe-capability-and-variability](skills/braintrust-probe-capability-and-variability/)** — Run the same dataset under variants to measure either the ceiling of what a system can do (`pass@k`) or the spread of how reliably it does it (`pass^k`).
- **[braintrust-discover-agent-failures](skills/braintrust-discover-agent-failures/)** — Open-ended search for unanticipated failure modes, clustered and triaged into a root-cause taxonomy and frozen regression items.
- **[braintrust-discover-trace-topics](skills/braintrust-discover-trace-topics/)** — Build the clustering instrument itself: preprocessor, facet prompt, no-match policy, and the automation that discovers a label set from traffic when none exists yet.
- **[braintrust-red-team-agent](skills/braintrust-red-team-agent/)** — Adversarial testing against an explicit threat model, prioritizing attack-family coverage over raw success rate, producing existence claims and mitigations.

**Reporting and production**

- **[braintrust-report-eval-results](skills/braintrust-report-eval-results/)** — Turn analysis into a report with claims calibrated to the evidence: intervals, effective n, search disclosure, pinned configuration.
- **[braintrust-monitor-production-evals](skills/braintrust-monitor-production-evals/)** — Online scoring coverage, alert ownership, drift on both input and scorer, and the pipeline from production failure back into the dataset.

## Routing

The artifact named in a request is the strongest routing signal. When a request names a dataset, scorer, experiment, gate, or report, use that artifact's skill rather than `braintrust-plan-agent-eval`.

The four elicitation regimes are easy to confuse, and mislabeling which one you are in is the most common eval-reporting error:

| Regime | Statistic | Skill |
| --- | --- | --- |
| Capability elicitation | max over attempts (`pass@k`) | `braintrust-probe-capability-and-variability` |
| Variability probing | distribution, worst case (`pass^k`) | `braintrust-probe-capability-and-variability` |
| Failure discovery | an enumeration | `braintrust-discover-agent-failures` |
| Red teaming | existence of a breaking input | `braintrust-red-team-agent` |

`braintrust-discover-trace-topics` and `braintrust-discover-agent-failures` both say "discover" and are not the same job.
Topics builds the **instrument** that turns unlabeled traffic into clusters; failure discovery is
the **investigation** that turns candidates into a root-cause taxonomy and frozen regression items.
Topics is usually a step inside failure discovery, not a substitute for it.

Instrument choice, when the request is "label our traffic somehow":

| The label set is | Instrument | Skill |
| --- | --- | --- |
| Known and stable | classifier | `braintrust-write-eval-scorer` → `braintrust-deploy-evaluator` |
| A 0–1 criterion | scorer | `braintrust-write-eval-scorer` → `braintrust-validate-eval-scorer` |
| Not known yet | facet + clustering | `braintrust-discover-trace-topics` |

## Conventions

Directory layout, installing, and the re-mirror procedure are in
[skills/README.md](skills/README.md). The conventions that govern what goes *in* a
skill:

- **Card format.** Lifecycle skills use a five-field card — `Trigger` / `Do` / `Avoid` / `Check` / `Risk` — plus a `Braintrust` section. It is compact procedural memory, retrieved on demand.
- **Shared files are mirrored, not restated.** Mechanics common to every stage live in `PLATFORM.md`; each card's `Braintrust` section cites the relevant section and adds only what is specific to its own stage. If a paragraph would be true of three cards, it belongs in `PLATFORM.md`.
- **Numbers live in `references/`.** Cards carry the procedure; thresholds carry their hedge and provenance in the reference file. A number that *is* the method (rule of three, K ≥ 3 runs, ≥ 2 raters) stays in the card; tunable defaults (κ floors, item counts, gate thresholds) do not.
- **Provenance tags.** Empirical claims in `references/` carry `[guide §N]`, `[guide §N → source]` where the guide is paraphrasing, or `[pending]` where a claim is not yet in published prose and should be re-checked before external use. Platform mechanics — tool names, argument shapes, product defaults — carry `[platform]`. They are not empirical claims and have no guide section, but they go stale the same way, so re-check them against the shipped tool surface before relying on one externally.

## Examples

- **[rag-only-enforcement](rag-only-enforcement/)** — A runnable end-to-end eval (not a skill): does behavior-based scoring catch what `test_passed` misses when a coding agent is given a "locate code via vector search only" rule? Four enforcement variants over SWE-bench Django tasks, with output and behavior scorers side by side.
