# eval-library

Agent Skills for evaluating LLM applications and agents, built around [Braintrust](https://www.braintrust.dev).

Most eval tooling helps you *run* an eval. The harder problem is knowing whether the
result means anything — whether the dataset represents your users, whether the judge
agrees with a human, whether a 3-point gain survives run-to-run noise, and whether the
claim you are about to publish is one the design supports.

This library encodes that as **24 skills**: one per stage of the eval lifecycle, each
narrow enough to invoke on its own, each naming the skill that consumes its output next.

## Install

Skills are plain directories. Symlink the ones you want:

```bash
git clone https://github.com/braintrustdata/eval-library.git

# Claude Code
mkdir -p ~/.claude/skills
for d in eval-library/skills/braintrust-*/; do
  ln -sfn "$(cd "$d" && pwd)" ~/.claude/skills/"$(basename "$d")"
done

# Codex CLI
mkdir -p ~/.codex/skills
for d in eval-library/skills/braintrust-*/; do
  ln -sfn "$(cd "$d" && pwd)" ~/.codex/skills/"$(basename "$d")"
done
```

Symlinks beat copies — edits land immediately and there is one source of truth. Copying
works too, since each skill directory is self-contained.

## Start here

**Don't know which one you need?** Invoke `braintrust-plan-agent-eval`. It reads your
project, inventories what already exists, and names the *earliest* missing artifact —
which is usually not the one you were about to build.

**Want to just run an eval?** `braintrust-eval` takes you from "I want to eval X" to a
scored, compared experiment, with approval gates before anything costs money.

**Already have results and want to know if they're real?**
`braintrust-analyze-eval-experiment`.

## Compatibility

Skills follow the [Agent Skills open standard](https://agentskills.io) — a `SKILL.md`
with YAML frontmatter plus optional `references/`, `scripts/`, and `assets/`. All 24
conform: names are lowercase-hyphen and match their directories, descriptions are within
the 1,024-character cap.

That means they work in Claude Code, Codex CLI, and the other tools that adopted the
standard. Agent-specific frontmatter fields are ignored rather than erroring, so nothing
needs forking per tool.

The skills assume Braintrust as the platform — datasets, experiments, scorers, online
scoring. The *methodology* in each card is platform-independent; the `Braintrust`
section at the end of each is where the platform-specific mechanics live.

---

## The skills

Every skill lives under [skills/](skills/), prefixed `braintrust-` so the set groups
together alongside skills from other sources. Directory mechanics and the contributor
workflow are in [skills/README.md](skills/README.md).

### Workflow

Interactive and end-to-end. Orchestrates a whole job and hands off to the artifact skills below.

- **[braintrust-eval](skills/braintrust-eval/)** — Execute an eval against a live project: credentials, dataset import, task and scorer code, smoke gates, quota preflight, agentic tracing. The runbook.

### Foundation

- **[braintrust-plan-agent-eval](skills/braintrust-plan-agent-eval/)** — Turn an ambiguous eval request into a staged plan: identify the product decision, inventory what exists, name the earliest missing artifact.
- **[braintrust-design-eval-instrumentation](skills/braintrust-design-eval-instrumentation/)** — Design the trace and dataset schema and wire the system to emit it: spans, native scores and metrics, metadata, attachments, resolved config, per-item status.
- **[braintrust-write-agent-behavior-spec](skills/braintrust-write-agent-behavior-spec/)** — Define recurring agent conduct as a versioned `BEHAVIOR.md`: intent, applicability, evidence, decision, execution, recovery, failure modes.

### What to measure

- **[braintrust-define-eval-objective](skills/braintrust-define-eval-objective/)** — Work backward from a product decision to the construct, population, intended claim, and the verification-vs-validation questions.
- **[braintrust-design-eval-metric-bundle](skills/braintrust-design-eval-metric-bundle/)** — Separate quality, safety, reliability, latency, and cost measures; distinguish improvement targets from guardrails; expose Goodhart risk.
- **[braintrust-map-eval-evidence](skills/braintrust-map-eval-evidence/)** — Connect constructs to observable success and failure signals, with each proxy's limitation and gaming path named.

### Human knowledge

- **[braintrust-elicit-eval-criteria](skills/braintrust-elicit-eval-criteria/)** — Extract criteria from domain experts and real user desires before labeling begins: construct facets, anchored exemplars, adversarial traps.
- **[braintrust-design-human-eval-review](skills/braintrust-design-human-eval-review/)** — Design the review workflow and golden dataset: case selection, rater assignment, rationales, inter-rater agreement, adjudication.

### Datasets

- **[braintrust-build-eval-dataset](skills/braintrust-build-eval-dataset/)** — Population definition, case sourcing, stratified sampling, label audits, open-ended constraints, splits, contamination controls, refresh policy.
- **[braintrust-size-eval-dataset](skills/braintrust-size-eval-dataset/)** — Sample sizes, minimum detectable effects, clustering design effects, and clean-trial counts for bounding rare failures.

### Scorers

- **[braintrust-write-eval-scorer](skills/braintrust-write-eval-scorer/)** — Implement one narrow scorer: match method to evidence and stakes, anchor rubrics with examples, handle refusals, timeouts, and parse failures.
- **[braintrust-validate-eval-scorer](skills/braintrust-validate-eval-scorer/)** — Validate a scorer against expert labels: agreement with uncertainty, severity-weighted confusion, shortcut probes, and a fitness verdict for gating.
- **[braintrust-deploy-evaluator](skills/braintrust-deploy-evaluator/)** — Put a validated scorer or classifier on real traffic: input scope, inline testing before saving, online-scoring rules, activation, backfill with a cost estimate.

### Experiments

- **[braintrust-design-eval-experiment](skills/braintrust-design-eval-experiment/)** — Pre-specify a comparison: hypothesis with a minimum effect, named variables including serving path and tool surface, pairing, and a pre-analysis plan.
- **[braintrust-analyze-eval-experiment](skills/braintrust-analyze-eval-experiment/)** — Analyze completed results: run-integrity audit, intervals, clustering, paired differences, multiplicity, subgroups, fragility.
- **[braintrust-attribute-multi-variable-change](skills/braintrust-attribute-multi-variable-change/)** — Attribute a change when several things moved at once: difference inventory, isolation designs, honest bundle-vs-component claims.
- **[braintrust-define-eval-release-gate](skills/braintrust-define-eval-release-gate/)** — Combine magnitude, significance, consistency, stability, reliability, safety bounds, latency, and cost into an explicit ship-or-hold policy.

### Diagnostics and discovery

- **[braintrust-probe-capability-and-variability](skills/braintrust-probe-capability-and-variability/)** — Run the same dataset under variants to measure either the ceiling of what a system can do (`pass@k`) or the spread of how reliably it does it (`pass^k`).
- **[braintrust-discover-agent-failures](skills/braintrust-discover-agent-failures/)** — Open-ended search for unanticipated failure modes, clustered and triaged into a root-cause taxonomy and frozen regression items.
- **[braintrust-discover-trace-topics](skills/braintrust-discover-trace-topics/)** — Build the clustering instrument: preprocessor, facet prompt, no-match policy, and the automation that discovers a label set from traffic when none exists yet.
- **[braintrust-red-team-agent](skills/braintrust-red-team-agent/)** — Adversarial testing against an explicit threat model, prioritizing attack-family coverage over raw success rate, producing existence claims and mitigations.

### Reporting and production

- **[braintrust-report-eval-results](skills/braintrust-report-eval-results/)** — Turn analysis into a report with claims calibrated to the evidence: intervals, effective n, search disclosure, pinned configuration.
- **[braintrust-monitor-production-evals](skills/braintrust-monitor-production-evals/)** — Online scoring coverage, alert ownership, drift on both input and scorer, and the pipeline from production failure back into the dataset.

---

## Routing

The artifact named in a request is the strongest signal. When a request names a dataset,
scorer, experiment, gate, or report, use that artifact's skill rather than
`braintrust-plan-agent-eval`.

Four regimes are easy to confuse, and mislabeling which one you are in is the most common
eval-reporting error:

| Regime | Statistic | Skill |
| --- | --- | --- |
| Capability elicitation | max over attempts (`pass@k`) | `braintrust-probe-capability-and-variability` |
| Variability probing | distribution, worst case (`pass^k`) | `braintrust-probe-capability-and-variability` |
| Failure discovery | an enumeration | `braintrust-discover-agent-failures` |
| Red teaming | existence of a breaking input | `braintrust-red-team-agent` |

`braintrust-discover-trace-topics` and `braintrust-discover-agent-failures` both say
"discover" and are not the same job. Topics builds the **instrument** that turns
unlabeled traffic into clusters; failure discovery is the **investigation** that turns
candidates into a root-cause taxonomy and frozen regression items. Topics is usually a
step inside failure discovery, not a substitute for it.

Instrument choice, when the request is "label our traffic somehow":

| The label set is | Instrument | Skill |
| --- | --- | --- |
| Known and stable | classifier | `braintrust-write-eval-scorer` → `braintrust-deploy-evaluator` |
| A 0–1 criterion | scorer | `braintrust-write-eval-scorer` → `braintrust-validate-eval-scorer` |
| Not known yet | facet + clustering | `braintrust-discover-trace-topics` |

## Examples

Runnable evals built with these skills, in [examples/](examples/):

- **[rag-only-enforcement](examples/rag-only-enforcement/)** — Does behavior-based scoring catch what `test_passed` misses when a coding agent is told to locate code via vector search only? Four enforcement variants over SWE-bench Django tasks, with output and behavior scorers side by side.

## Conventions

Lifecycle skills use a five-field card — `Trigger` / `Do` / `Avoid` / `Check` / `Risk` —
plus a `Braintrust` section. Compact procedural memory, retrieved on demand.

**Numbers live in `references/`.** Cards carry the procedure; thresholds carry their
hedge and provenance in the reference file. A number that *is* the method (rule of three,
K ≥ 3 runs, ≥ 2 raters) stays in the card. Tunable defaults — κ floors, item counts, gate
thresholds — do not, and none of them are laws.

**Shared text is mirrored, not restated.** [skills/INTERACTION.md](skills/INTERACTION.md)
defines how every skill handles ambiguity, modes, and uncertainty labelling.
[skills/PLATFORM.md](skills/PLATFORM.md) holds the Braintrust mechanics common to every
stage. Both are mirrored into each skill's `references/` so a directory works standalone.

**Provenance tags**, and their honest limits:

| Tag | Means | Checkable by you? |
| --- | --- | --- |
| `[guide §N → source]` | Paraphrase of a named source; the source is the authority | **Yes** — 106 of these, mostly published papers |
| `[guide §N]` | Traceable to an internal Braintrust evals guide | **No** — 61 of these; the guide is not published |
| `[pending]` | Not yet in published prose; re-check before external use | No |
| `[platform]` | Product behavior — tool names, argument shapes, defaults | Against the shipped tool surface |

Bare `[guide §N]` claims are the ones to treat with most caution if you are quoting this
material externally. Where a claim matters to a decision, prefer the ones carrying a
named source.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Apache 2.0](LICENSE).
