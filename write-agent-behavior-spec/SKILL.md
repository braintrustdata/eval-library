---
name: write-agent-behavior-spec
description: >-
  Create, edit, audit, or compare versioned Agent Behavior specifications in
  .agents/behaviors/<name>/BEHAVIOR.md. Use when a user wants to define recurring agent
  conduct, write a behavioral contract, make implicit trace-review expectations explicit,
  specify how an agent should handle uncertainty, destructive actions, or recovery, or
  describe intent, applicability, evidence, decision, execution, recovery, and failure modes.
  Also use to review or diff an existing BEHAVIOR.md. Do not use to implement system prompts,
  tool definitions, or scorer code.
---

# Write an agent behavior spec

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/behavior-spec-template.md`.

## Trigger

- Requests naming `BEHAVIOR.md`, a behavioral contract, or recurring agent conduct.
- Review expectations that live only in reviewers' heads.
- A failure class recurring across prompts and models — the standard is missing, not the prompt.

## Do

1. Name the recurring behavior and why mistakes matter. If traces exist, infer the spec from
   them before asking anything.
2. Write the seven sections in `reference.md`: intent, applicability, evidence, decision,
   execution, recovery, failure modes.
3. Write every clause so a reviewer could mark it satisfied or violated **from a trace alone**.
   Replace "handles uncertainty well" with "states the ambiguity and asks before writing files."
4. Keep clauses durable across a prompt rewrite or model swap. Anything that would not survive
   one belongs in the prompt, not the spec.
5. Version and date it, then emit the observable review questions the spec implies — the contract
   that evidence mapping and scorer work consume.

## Avoid

- Do not turn the spec into a system prompt, tool manual, or task instruction; it outlives all
  three.
- Do not encode tool names, model strings, or prompt wording into durable clauses.
- Do not enumerate every situation; specify the decision rule and its boundaries.
- Do not let the agent's author write the failure-modes section.

## Check

- All seven sections present; every clause observable in a trace and capable of being violated.
- Failure modes named and distinct, not a generic "does the wrong thing."
- Versioned, dated, paired with review questions for the next skill.

## Risk

- Vague conduct produces subjective review, and subjective review produces disagreement that
  gets misread as model variance.
- Over-specification makes the standard brittle: a spec pinned to today's tool set fails the
  day a tool is renamed.
- An orphaned spec is the common failure — written, admired, never scored against. The review
  questions are what prevent it.

## Braintrust

A spec is not a platform object; its clauses become three that are. Each **review question**
becomes a per-criterion score in a **human review queue** with free-text notes — this is how
the spec starts producing labels instead of sitting in a doc. Each **failure mode** becomes its
own scorer (`references/platform-mechanics.md` §5), so a regression in one mode is its own
column rather than averaged away. Applied to live traffic, violations become **trace classifications** you can
alert and slice on. Tag the spec version in scorer span metadata, and treat a spec-version
boundary like a scorer-version boundary: do not compare across it. When a review queue surfaces
a violation the spec does not cover, that is a spec gap — route it back here rather than
widening a scorer.
