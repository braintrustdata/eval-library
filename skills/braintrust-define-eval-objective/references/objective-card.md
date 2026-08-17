# Reference — eval objective

## Verification vs. validation

Both questions are about the **system**, not the model.

| | Question | Coding-agent example | Support-agent example |
| --- | --- | --- | --- |
| **Verification** | Are we building the agent *right*? (Do my scorers hold the spec?) | Requirements hold across a multi-step trace: never commits failing tests, never modifies protected files | Follows policy, verifies identity, maintains tone, avoids prohibited behavior, reaches an acceptable resolution |
| **Validation** | Are we building the *right* agent? (Do I have the right scorers?) | Bugs are fixed, useful features ship, developers adopt it, productivity or security improves | Customers get correct resolutions, feel understood, trust the interaction, do not reopen; satisfaction, resolution time, escalation rate, support burden |

## Provenance

- Safety and quality are properties of the **deployed system in its operating
  context**, so an evaluation must name which stakeholder needs which evidence at
  which stage rather than reporting one model-level number.
  `[Xia et al. 2024]`
- A score supports a claim only to the extent evidence connects the score to the
  construct and the use case. High performance on a narrow eval justifies a narrow
  claim. `[Salaudeen et al. 2025]`
- Against unscoped "general" benchmarks: define the population.
  `[Raji et al. 2021; Bowman & Dahl 2021]`
- The vocabulary is genuinely contested — six AI-evaluation paradigms grew up
  separately with conflicting terms, worth knowing before arguing about what
  "validation" means. `[Burden et al. 2025]`
- The what-vs-how split: evaluation *objectives* (behavior, capabilities,
  reliability, safety) × evaluation *process* (interaction mode, data, metric
  computation, tooling, contexts). `[Mohammadi et al. 2025]`

## Objective card template

```yaml
decision: <ship or hold / A vs. B / v3 vs. v4 — one sentence>
construct: <the property being measured>
population: <the space of situations the claim must cover, and its weighting>
intended_use: <decisions this licenses>
intended_non_use: <decisions this explicitly does not license>

verification:
  question: <do the scorers hold the spec?>
  evidence: <what would answer it>
validation:
  question: <do these scorers reflect what users need?>
  evidence: <source — escalations, interviews, telemetry — or "none; Assumed">

supported_claims:
  - <claim bounded by population>
unsupported_claims:
  - <claim someone will try to make from this number>

decision_changing_evidence:
  - <result that would flip the decision>
status_per_field: Confirmed | Assumed | Needs decision | Not yet measurable
```

## Population sentence test

A population statement must answer: which situations, drawn from where, weighted how.

- Rejected: "our users' tasks."
- Accepted: "bug-fix requests in our customers' Python repos, weighted like
  production traffic for the last 90 days."
