---
name: design-eval-instrumentation
description: >-
  Design the trace and eval-dataset schema for an LLM app or agent, and wire the system to emit
  it. Use when deciding what to log, designing a trace schema, setting up tracing or
  observability before evals, or when failures cannot be debugged or sliced from existing
  traces — covering inputs, outputs, spans for tool and LLM calls, state changes, metadata,
  resolved configuration, serving path, tool manifest, per-item status, attachments, and
  subgroup variables. Do not use to decide what the evidence should mean, or to write scorers.
---

# Design and wire eval instrumentation

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/trace-schema.md`.

## Trigger

- "What should we log?" / "Design a trace schema." / "Set up tracing before evals."
- Failures that cannot be reconstructed, scored, or sliced after the fact.
- An evidence map with signals nothing currently records.

## Do

1. Work backward from each required decision to the fields needed to reconstruct it. Rule: **if
   a variable matters to interpretation or a release decision, it needs a field.**
2. Design the record shape and the span tree **together** (`reference.md`) — one span per LLM
   call, tool call, and scorer call, nested to mirror actual control flow.
3. Add the four fields always discovered too late: the **raw input artifact**, a **per-item
   status** kept separate from the score, the **fully resolved config** including serving path and
   tool manifest, and a **stable grouping key** on every trace that belongs to a larger unit of
   work — a conversation, session, or thread.
4. Mark each field required or optional with its retention and privacy handling, and scrub
   sensitive values at emission rather than in post-processing.
5. Verify by round trip: run one item, open the trace, confirm you could diagnose a seeded
   failure from it alone. Fix the instrumentation, not the eval, if you cannot.

## Avoid

- Do not log sensitive data because it might be useful someday — every field is a retention
  commitment.
- Do not confuse chain-of-thought collection with behavioral evidence.
- Do not let the score double as the status field.
- Do not decide what the evidence *means* here.

## Check

- A past real failure is reconstructable, scoreable, sliceable, and attributable to the module
  that first erred, from these fields alone.
- Every stratification variable in the dataset plan exists as a field.
- Status separate from score; resolved config present; raw artifact attached for non-text.
- Privacy, PII handling, and retention stated per sensitive field.

## Risk

- Missing fields make later questions permanently unanswerable — you cannot retroactively log a
  subgroup variable, offline or in production.
- Mis-nested spans look complete while making root-cause attribution impossible.
- Renamed provider options are dropped silently; without the resolved config, "the feature
  didn't help" and "it never applied" are indistinguishable.

## Braintrust

Four objects: **traces** (behavioral record), **datasets** (sampled population), **scorers**
(instruments), **experiments** (repeated observations). Traces first — everything consumes them.

Field placement decides what the platform can ever do: scores in native `scores` (0–1);
tokens/latency/cost in **native metrics**, or they cannot be charted or gated on; slicing
variables in record `metadata`, or subgroup analysis needs re-labeling; scorer name/version in
span metadata; raw non-text input as a span **Attachment** (`input.audio = Attachment(...)`),
which renders inline so "listen to the actual clip" is one click. Note experiments surface
attachments more prominently than datasets — if human review of raw artifacts is part of the
loop, make an experiment the review surface.

**A stratum not in metadata is a stratum you cannot report**, with no retroactive fix. Include
`scenario_id` wherever items are variants of one scenario, so clustered standard errors stay
computable.

Instrumentation also fixes the **evaluation scopes available later**. Evaluators run against a
span, a trace, or a **group** of traces joined by a metadata key — so multi-turn behavior is only
measurable if something like `conversation_id`, `session_id`, or `thread_id` was emitted at the
time. Same no-retroactive-fix rule as any other stratum, with a sharper edge: a grouping key that
is present but **inconsistently populated** is worse than one that is absent, because group-scoped
evaluation will silently drop the traffic where it is null and report a confident number over the
remainder. Assert its coverage the way you assert any other transform invariant.
