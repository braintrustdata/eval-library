---
name: braintrust-discover-agent-failures
description: >-
  Search open-endedly for unanticipated agent failure modes and convert them into a named taxonomy
  and durable regression items. Use for requests to find out what goes wrong, surface unknown or
  silent failures, do error analysis over traces, cluster and triage production failures, or build a
  failure taxonomy — where the goal is discovering modes nobody thought to test rather than
  measuring a predefined criterion. Produces datasets and taxonomies, not headline scores. Do not
  use for adversarial attacks against a threat model, or to measure a known criterion.
---

# Discover unknown failure modes

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/failure-taxonomy.md`.

## Trigger

- "What goes wrong with this agent?" / "Find failures we haven't thought of."
- Error analysis over a body of traces or production incidents.
- A suite that passes while the product visibly disappoints.

## Do

1. Accept that you cannot write the scorer in advance — that is the point. Run the loop:
   **open-ended search → cluster and triage → name a taxonomy → freeze each confirmed mode into a
   deterministic regression item.**
2. Generate or search at scale, then constrain the search to **realistic intents**, not only
   adversarial ones. Purely adversarial generation finds failures no real user will trigger.
3. Triage each candidate against the trace — genuine system failure, bad item, harness error, or
   label problem? Only genuine failures enter the taxonomy.
4. Attribute each mode to its **root cause, not its visible symptom.** Early mistakes cascade, so
   organize by the module that first erred — memory, reflection, planning, action.
5. Hunt **silent** failures specifically (`reference.md`). Most agent failures raise no error at
   all: plausible-looking but unusable output, missing answers, wrong entities.
6. Freeze each confirmed mode by isolating the decision point where it occurs and snapshotting it,
   so a flaky trajectory failure becomes a stable regression test.

## Avoid

- Do not force an unknown failure into an existing rubric; the rubric is what missed it.
- Do not report the search yield as a population failure rate — a discovery sample is not a
  representative sample.
- Do not stop at anecdotes; without a taxonomy and frozen items the work does not compound.
- Do not run adversarial campaigns against a threat model here.

## Check

- Each mode verified against trace evidence, with severity and reproducibility noted.
- Modes distinct, not restatements of one another at different depths.
- Taxonomy organized by root cause, with the responsible module named.
- At least one durable regression item per confirmed mode.
- Search method and yield disclosed, with the explicit note that yield is not a rate.

## Risk

- Synthetic oddities and unrealistic prompts consume attention without improving reliability.
- Duplicate modes inflate the apparent problem count and split ownership.
- You can only discover what was logged — a thin result may be an instrumentation finding rather
  than a good sign.
- Discovery never terminates. Stop on a coverage or budget rule stated in advance.

## Braintrust

The pipeline, each step load-bearing: **capture full traces** (discovery is bounded by
instrumentation — if tool calls are not spanned, a planning failure and an action failure are
indistinguishable and the root-cause taxonomy collapses into a symptom list) → **trace
classifications** on live traffic to cluster, classified by suspected mode rather than pass/fail so
the classes *are* the emerging taxonomy → **review queues** for triage, since the
genuine-vs-bad-item call needs a human on the trace → **versioned dataset** for confirmed modes as
frozen items.

Freeze by snapshotting the **decision point** — the state where the agent first erred becomes the
item's input — rather than replaying the whole trajectory. Tag frozen items in `metadata`:
`source: discovery-<YYYY-MM>`, `mode`, `root_module`, `frozen_from_trace`, `silent`.

Keep discovery items in a **separate dataset or behind a metadata flag** excluded from population
estimates, or the next aggregate silently becomes "performance on the hardest cases we could find."
Silent modes need real quality scorers; an exception-rate check will never see them.
