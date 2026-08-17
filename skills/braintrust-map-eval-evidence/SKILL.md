---
name: braintrust-map-eval-evidence
description: >-
  Create or audit an evidence map that connects eval constructs or behavior specifications to
  observable success signals, failure signals, proxy limitations, and possible gaming paths.
  Use when a quality such as helpfulness, safety, trust, correctness, or task success is not
  directly measurable, when asking "how would we observe this," "what evidence would show this
  behavior happened," or when a BEHAVIOR.md must be translated into trace-review signals. Do
  not use to define storage or schema fields, choose product metrics, or write scorers.
---

# Map constructs to observable evidence

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/evidence-map.md`.

## Trigger

- A construct appearing in no trace field: helpfulness, trustworthiness, safety.
- A behavior spec's review questions needing observable signals.
- Scorers that exist but nobody can say what they are evidence *of*.

## Do

1. For each construct, fill four columns before asking anything: **success evidence**,
   **failure evidence**, **limitation** (what this signal misses), **gaming path** (how to
   raise it without improving the outcome).
2. Require more than one proxy for any consequential outcome — several independent proxies make
   it harder to win the eval without improving the product.
3. Apply the usefulness test: closely connected to the outcome, covers its most important
   dimensions, hard to improve **without** improving real behavior.
4. Surface the most consequential blind spot explicitly and label it `Not yet measurable`
   rather than substituting a convenient proxy.
5. Mark evidence the system cannot currently produce. That list is what the trace schema has to
   be extended to cover.

## Avoid

- Do not invent field names or schemas; that is the next skill.
- Do not write scoring logic or thresholds.
- Do not treat chain-of-thought or a self-reported rationale as behavioral evidence — it is a
  claim about behavior, not a record of it.
- Do not stop at success evidence. Failure evidence is what makes a scorer discriminate.

## Check

- Every construct has success evidence, failure evidence, ≥1 limitation, ≥1 gaming path.
- Consequential constructs carry multiple independent signals.
- Blind spots stated rather than papered over; uncapturable evidence flagged.

## Risk

- Weak proxies look precise. Latency, token count, and polish are easy to measure and routinely
  stand in for outcomes they do not track.
- Process-compliance evidence ("called the right tool") can diverge entirely from outcome
  evidence ("solved the user's problem"); mapping only one produces a confident, wrong
  conclusion.
- Proxies chosen from what is already logged encode last year's instrumentation as this year's
  construct.

## Braintrust

Each signal must be locatable in a span. Signals about **what the agent did** come from
tool-call spans, so they exist only if the agent is instrumented at that granularity. Signals
about the output come from the top-level span. Signals you want to **slice by** are `metadata`,
not evidence — do not conflate them: evidence is what you score, metadata is how you group
scores. **One signal, one scorer** (`references/platform-mechanics.md` §5), so the multi-proxy
requirement shows up as multiple columns; two signals in one scorer breaks the gaming-path
analysis because you can no longer see which proxy moved. A `Not yet measurable` blind spot vanishes once numbers start
appearing — record it in the dataset or experiment description, and where it matters to a gate,
prefer a documented unimplemented placeholder over omitting the dimension and letting its
absence read as a pass.
