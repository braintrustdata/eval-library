# Reference — failure discovery

## The loop

This is the one regime where you **cannot write the scorer in advance**, because the point
is to surface behavior you did not anticipate. Discovery evals produce **datasets, not
headline scores**.

```
open-ended search → cluster and triage → name a failure taxonomy
                  → freeze each mode into deterministic regression items
```

## Provenance

- Use a model to generate candidate test cases at scale, surfacing behaviors nobody thought
  to enumerate. `[Perez et al. 2022b]`
- **Constrain the search to realistic intents.** Purely adversarial generation finds
  failures no real user will trigger; adding a realism constraint to a QA-agent failure
  search uncovered **23–78% more** unhelpful responses than adversarial-only baselines.
  `[Lu et al. 2026]` — note the paper's own wording is "23% - 78% more
  unhelpful responses" vs. prior approaches; do not restate this as "genuine failures"
  generally.
- **Freeze flaky failures into stable items:** rather than enumerating the full action
  space, "isolate decision points in deterministic and reproducible manners," snapshotting
  the decision point into a deterministic test case.
  `[Zhang et al. 2025]`
- **Attribute to root cause, not symptom.** In agent trajectories early mistakes cascade, so
  a taxonomy organized by the module that first erred (memory, reflection, planning, action)
  is far more actionable than one organized by the visible end state.
  `[Zhu et al. 2025]`
- **Most agent failures are silent.** One multi-agent study: **75.17%** silent semantic
  failures vs. 24.84% explicit. The silent share breaks down as missing/underspecified
  output 47.61%, wrong fact/entity 27.66%, empty prediction 15.96%; explicit failures are
  exceptions 6.38% and timeouts 1.86%. Silent failures "do not trigger explicit system
  failures and are therefore not immediately visible to users."
  `[Ma et al. 2026]`
- You can only discover what you logged — undertraced systems hide their failure modes.
- The regime licenses **an enumeration** ("here is what goes wrong"), never a rate.

## Silent-failure checklist

Error-rate dashboards look healthy while these accumulate. Search for each by name:

| Mode | What it looks like |
| --- | --- |
| Missing / underspecified output | plausible answer that omits the requested substance |
| Wrong fact or entity | confident, specific, incorrect |
| Empty prediction | structurally valid, semantically vacant |
| Right answer, unacceptable path | correct output via a prohibited action |
| Premature success claim | reports completion of work not done |

## Triage decision

Each candidate is exactly one of:

```yaml
verdict: genuine_system_failure | bad_item | harness_error | label_problem
```

- **genuine_system_failure** → enters the taxonomy, gets a frozen item.
- **bad_item** → dataset fix.
- **harness_error** → effective-N accounting, not a failure mode.
- **label_problem** → label audit.

Only the first counts. Reporting the other three as failure modes is the most common way a
discovery report inflates.

## Taxonomy entry template

```yaml
mode: <short-kebab-name>
root_module: memory | reflection | planning | action | retrieval | tool_interface
symptom: <what a user sees>
root_cause: <what first went wrong — not the same as the symptom>
silent: yes | no
severity: <impact if it reaches a user>
reproducibility: deterministic | flaky | once
evidence: [<trace ids>]
distinct_from: [<other modes it could be confused with, and why it isn't>]
frozen_item: <dataset item id — the decision-point snapshot>
```

## Search disclosure

Every discovery report states:

```yaml
search_method: <generated | production sample | targeted probe>
realism_constraint: <how intents were kept realistic>
candidates_examined: <n>
genuine_failures: <n>
yield: <n/n>          # NOT a population failure rate — label it explicitly
stopping_rule: <coverage or budget rule stated in advance>
```

The yield is a property of the search, not of the system. A discovery report that quotes it
as a rate has made a category error.
