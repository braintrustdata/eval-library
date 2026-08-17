# Reference — behavior spec

## BEHAVIOR.md template

Path: `.agents/behaviors/<name>/BEHAVIOR.md`

```markdown
---
behavior: <short-kebab-name>
version: <n>
updated: <YYYY-MM-DD>
owner: <role or team>
---

# <Behavior title>

## Intent
What good conduct achieves, and for whom. One paragraph. State the consequence of
getting it wrong, because that is what calibrates severity later.

## Applicability
When this behavior is in scope. Equally important: when it is **not** — the
situations where a different behavior governs, so clauses do not get applied where
they were never meant to.

## Evidence
What the agent must establish before acting. The preconditions it is responsible for
checking, and how it should behave when it cannot establish them.

## Decision
How it chooses among available options, including the boundary where it must stop and
ask rather than proceed. State the rule, not an enumeration of cases.

## Execution
What it does. What it must never do. Keep these observable: a reviewer reading a
trace should be able to mark each clause satisfied or violated.

## Recovery
What it does after an error, a wrong turn, or a partially completed action. Include
whether it may retry, what it must disclose, and what it must not silently undo.

## Failure modes
Named, distinct, observable ways this behavior goes wrong. One line each. These
become scorer criteria and dataset items.

- `<name>`: <what it looks like in a trace>

## Review questions
The observable questions a trace reviewer answers. This is the handoff contract that evidence
mapping and scorer implementation consume.

1. <question answerable yes/no from a trace>
```

## Observability test

Every clause must pass this. If it fails, rewrite it.

| Rejected | Accepted |
| --- | --- |
| "handles uncertainty gracefully" | "states the ambiguity and asks before writing files" |
| "is appropriately cautious" | "does not call a destructive tool without an explicit confirmation in the turn" |
| "communicates well" | "names every file it modified in its final message" |
| "recovers from errors" | "on a failed edit, reports the failure rather than proceeding to the next step" |

## Durability test

Ask: would this clause still be correct after a prompt rewrite, a model swap, or a
tool rename? If no, it is implementation detail and belongs in the prompt.

`[guide §1 — behavior as a durable property of the system, not the prompt]`

## Versioning

A behavior change invalidates prior trace reviews the same way a scorer change
invalidates cross-experiment comparisons. Bump the version, date it, and record what
changed. `[guide §5.4 — version scorers like code]`
