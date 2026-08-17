# Reference — evidence map

## Starting proxy catalog

Not a menu to pick from — a starting point to specialize. Every one of these needs its
limitation named for your product.

| Construct | Observable proxies |
| --- | --- |
| Correctness | passing tests, matching a reference answer, reaching the correct final state |
| Helpfulness | resolving the user's issue, answering the actual question, taking the appropriate next action |
| Safety | avoiding prohibited actions, policy violations, exposed secrets, insecure code |
| Efficiency | latency, token usage, number of tool calls, cost |

`[guide §3.1]`

## The four questions

For each outcome:

1. What evidence would indicate success?
2. What evidence would reveal failure?
3. Which parts of the outcome does this proxy capture? Which does it miss?
4. Could the system improve this proxy without improving the outcome users care about?

`[guide §3.1]`

## Provenance

- A proxy is **evidence of** a property, not the property itself. Passing tests is
  evidence a change is correct but does not guarantee it addresses the request, avoids
  unnecessary modifications, or remains maintainable. `[guide §3.1]`
- A useful proxy is closely connected to the outcome, covers its most important
  dimensions, and is **difficult to improve without improving real product
  behavior** — the Goodhart test. `[guide §3.1 → Skalse et al. 2022]`
- Most important outcomes require more than one proxy; several make it harder to win
  the eval without improving the product. `[guide §3.1]`
- Separating **outcome** (did the task get done) from **process-level capability**
  (tool use, planning, memory, coordination) is structural: a single task-success
  number tells you *whether* the system worked, never *which* mechanism carried or
  broke it. `[guide §2 preamble → Mohammadi et al. 2025]`
- Capability-by-capability coverage matrices, plus negative and perturbation tests, as
  the model for enumerating what a construct implies.
  `[guide §4.3 → Ribeiro et al. 2020]`
- Expect most agent failures to be **silent** — plausible-looking but unusable output
  that raises no error. You can only observe what was logged.
  `[guide §4.8.3 → Ma et al. 2026]`

## Evidence map template

```yaml
construct: <name>
source: <objective | behavior-spec clause | elicited criterion>

signals:
  - evidence: <observable, in-trace>
    polarity: success | failure
    captures: <which part of the construct>
    misses: <which part it cannot see>
    gaming_path: <how to raise it without improving the outcome>
    capturable_today: yes | no    # "no" → design-eval-trace-schema

blind_spot: <the part no signal covers>
blind_spot_status: Not yet measurable
proxy_count: <n>                  # ≥2 for anything gated on
```

## Failure-evidence prompts

Success evidence is easy and gets written first. These force the other half:

- What would a reviewer point at to reject this trace?
- What does this look like when it fails *silently* — plausible output, wrong result?
- What would a user complain about that no current signal would catch?
- What does the near-miss look like — right answer, unacceptable path?
