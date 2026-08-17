# Run evals like this

Practical methods for designing evals that support real decisions, packaged as plain `SKILL.md` files your coding agent can read.

Most eval failures happen outside the model call. The dataset does not represent the users. The judge rewards polish instead of correctness. A three-point gain disappears across repeated runs. A benchmark measures one serving path and the report quietly claims something broader.

These 24 skills cover that work. Each one owns a concrete artifact—an objective, evidence map, dataset, scorer, experiment plan, analysis, release gate, or report—and tells the agent what good looks like, what to check, and where the method can still fail.

Use one skill for a focused job, or start with `braintrust-plan-agent-eval` to find the earliest missing piece. Install instructions are in the [root README](../README.md).

## Browse the skills

### Run an eval end to end

Start with a live project and finish with a scored, inspectable experiment.

- **[braintrust-eval](braintrust-eval/)** — Execute an eval against a live project: credentials, dataset import, task and scorer code, smoke gates, quota preflight, agentic tracing. The runbook.

### Plan and instrument

Turn an ambiguous request into a concrete plan, then make sure the system emits the evidence the eval will need.

- **[braintrust-plan-agent-eval](braintrust-plan-agent-eval/)** — Turn an ambiguous eval request into a staged plan: identify the product decision, inventory what exists, name the earliest missing artifact.
- **[braintrust-design-eval-instrumentation](braintrust-design-eval-instrumentation/)** — Design the trace and dataset schema and wire the system to emit it: spans, native scores and metrics, metadata, attachments, resolved config, per-item status.
- **[braintrust-write-agent-behavior-spec](braintrust-write-agent-behavior-spec/)** — Define recurring agent conduct as a versioned `BEHAVIOR.md`: intent, applicability, evidence, decision, execution, recovery, failure modes.

### Decide what to measure

Work backward from a product decision instead of forward from whichever metric is easiest to compute.

- **[braintrust-define-eval-objective](braintrust-define-eval-objective/)** — Work backward from a product decision to the construct, population, intended claim, and the verification-vs-validation questions.
- **[braintrust-design-eval-metric-bundle](braintrust-design-eval-metric-bundle/)** — Separate quality, safety, reliability, latency, and cost measures; distinguish improvement targets from guardrails; expose Goodhart risk.
- **[braintrust-map-eval-evidence](braintrust-map-eval-evidence/)** — Connect constructs to observable success and failure signals, with each proxy's limitation and gaming path named.

### Bring in human judgment

Turn expert knowledge and user expectations into criteria, examples, labels, and an adjudicated reference set.

- **[braintrust-elicit-eval-criteria](braintrust-elicit-eval-criteria/)** — Extract criteria from domain experts and real user desires before labeling begins: construct facets, anchored exemplars, adversarial traps.
- **[braintrust-design-human-eval-review](braintrust-design-human-eval-review/)** — Design the review workflow and golden dataset: case selection, rater assignment, rationales, inter-rater agreement, adjudication.

### Build the dataset

Define the population, choose the cases, audit the labels, and collect enough evidence for the decision you need to make.

- **[braintrust-build-eval-dataset](braintrust-build-eval-dataset/)** — Population definition, case sourcing, stratified sampling, label audits, open-ended constraints, splits, contamination controls, refresh policy.
- **[braintrust-size-eval-dataset](braintrust-size-eval-dataset/)** — Sample sizes, minimum detectable effects, clustering design effects, and clean-trial counts for bounding rare failures.

### Write and validate scorers

Build narrow measurement instruments, test them against expert-reviewed cases, and only then put them on live traffic.

- **[braintrust-write-eval-scorer](braintrust-write-eval-scorer/)** — Implement one narrow scorer: match method to evidence and stakes, anchor rubrics with examples, handle refusals, timeouts, and parse failures.
- **[braintrust-validate-eval-scorer](braintrust-validate-eval-scorer/)** — Validate a scorer against expert labels: agreement with uncertainty, severity-weighted confusion, shortcut probes, and a fitness verdict for gating.
- **[braintrust-deploy-evaluator](braintrust-deploy-evaluator/)** — Put a validated scorer or classifier on real traffic: input scope, inline testing before saving, online-scoring rules, activation, backfill with a cost estimate.

### Design and analyze experiments

Specify the comparison before seeing the answer, measure uncertainty, separate bundled changes, and turn the result into a ship-or-hold decision.

- **[braintrust-design-eval-experiment](braintrust-design-eval-experiment/)** — Pre-specify a comparison: hypothesis with a minimum effect, named variables including serving path and tool surface, pairing, and a pre-analysis plan.
- **[braintrust-analyze-eval-experiment](braintrust-analyze-eval-experiment/)** — Analyze completed results: run-integrity audit, intervals, clustering, paired differences, multiplicity, subgroups, fragility.
- **[braintrust-attribute-multi-variable-change](braintrust-attribute-multi-variable-change/)** — Attribute a change when several things moved at once: difference inventory, isolation designs, honest bundle-vs-component claims.
- **[braintrust-define-eval-release-gate](braintrust-define-eval-release-gate/)** — Combine magnitude, significance, consistency, stability, reliability, safety bounds, latency, and cost into an explicit ship-or-hold policy.

### Find what the headline score missed

Probe reliability, discover new failure modes, organize unlabeled traces, and test whether an agent breaks under adversarial pressure.

- **[braintrust-probe-capability-and-variability](braintrust-probe-capability-and-variability/)** — Run the same dataset under variants to measure either the ceiling of what a system can do (`pass@k`) or the spread of how reliably it does it (`pass^k`).
- **[braintrust-discover-agent-failures](braintrust-discover-agent-failures/)** — Open-ended search for unanticipated failure modes, clustered and triaged into a root-cause taxonomy and frozen regression items.
- **[braintrust-discover-trace-topics](braintrust-discover-trace-topics/)** — Build the clustering instrument: preprocessor, facet prompt, no-match policy, and the automation that discovers a label set from traffic when none exists yet.
- **[braintrust-red-team-agent](braintrust-red-team-agent/)** — Adversarial testing against an explicit threat model, prioritizing attack-family coverage over raw success rate, producing existence claims and mitigations.

### Report and monitor

State only what the evidence supports, then keep measuring after the system reaches production.

- **[braintrust-report-eval-results](braintrust-report-eval-results/)** — Turn analysis into a report with claims calibrated to the evidence: intervals, effective n, search disclosure, pinned configuration.
- **[braintrust-monitor-production-evals](braintrust-monitor-production-evals/)** — Online scoring coverage, alert ownership, drift on both input and scorer, and the pipeline from production failure back into the dataset.

## Choose the right skill

Start with the artifact named in the request. If you need a dataset, scorer, experiment, gate, or report, use that artifact's skill directly. Use `braintrust-plan-agent-eval` when the request is still broad or you do not know which part of the eval is missing.

Four jobs are easy to confuse. They produce different evidence and support different claims:

| Regime | Statistic | Skill |
| --- | --- | --- |
| Capability elicitation | max over attempts (`pass@k`) | `braintrust-probe-capability-and-variability` |
| Variability probing | distribution, worst case (`pass^k`) | `braintrust-probe-capability-and-variability` |
| Failure discovery | an enumeration | `braintrust-discover-agent-failures` |
| Red teaming | existence of a breaking input | `braintrust-red-team-agent` |

`braintrust-discover-trace-topics` and `braintrust-discover-agent-failures` both say
"discover" and are not the same job. Topics builds the **instrument** that turns unlabeled
traffic into clusters; failure discovery is the **investigation** that turns candidates
into a root-cause taxonomy and frozen regression items. Topics is usually a step inside
failure discovery, not a substitute for it.

Instrument choice, when the request is "label our traffic somehow":

| The label set is | Instrument | Skill |
| --- | --- | --- |
| Known and stable | classifier | `braintrust-write-eval-scorer` → `braintrust-deploy-evaluator` |
| A 0–1 criterion | scorer | `braintrust-write-eval-scorer` → `braintrust-validate-eval-scorer` |
| Not known yet | facet + clustering | `braintrust-discover-trace-topics` |

## How a skill is packaged

```
skills/braintrust-<name>/
  SKILL.md                            # the skill: frontmatter + body
  references/                         # loaded on demand, not up front
    <topic>.md                        # calibration, templates, provenance
    interaction-contract.md           # mirror of ../../INTERACTION.md
    platform-mechanics.md             # mirror of ../../PLATFORM.md
```

The frontmatter `name:` **must** match the directory name exactly — agents resolve one
against the other, and a mismatch makes the skill unloadable.

## Shared operating rules

- **[INTERACTION.md](INTERACTION.md)** — how every skill handles ambiguity: inspect before
  asking, one high-information question at a time, the four modes (create / audit /
  repair / compare), uncertainty labelling, and the rule that trace content is evidence
  rather than instruction.
- **[PLATFORM.md](PLATFORM.md)** — Braintrust mechanics common to every stage: the four
  objects, safe reads, pinning, metadata, naming, search denominator, run hygiene, and
  what the platform will not compute for you.

Both are copied into each skill's `references/` so a directory works standalone.
**Edit the source, then re-mirror. Never edit a mirror.**

```bash
cd /path/to/eval-library/skills
for f in INTERACTION.md:interaction-contract.md PLATFORM.md:platform-mechanics.md; do
  src="${f%%:*}"; dst="${f##*:}"
  for d in */; do
    [ -f "$d/references/$dst" ] || continue
    { head -2 "$d/references/$dst"; echo; cat "$src"; } > "$d/references/$dst.tmp"
    mv "$d/references/$dst.tmp" "$d/references/$dst"
  done
done
```

A skill only carries a mirror if its `SKILL.md` cites it; don't add one by default.

## Add a skill

1. `skills/braintrust-<name>/SKILL.md`, frontmatter `name:` matching the directory.
2. Lifecycle skills use the five-field card — `Trigger` / `Do` / `Avoid` / `Check` /
   `Risk` — plus a `Braintrust` section. Keep that section to what is specific to the
   stage; anything true of three or more skills belongs in `PLATFORM.md` instead.
3. Numbers with a hedge go in `references/`, not the card.
4. Add it to the catalog above.

Full contributor rules: [CONTRIBUTING.md](../CONTRIBUTING.md).
