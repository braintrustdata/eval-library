---
name: braintrust-probe-capability-and-variability
description: >-
  Run the same dataset under controlled variants to measure either the ceiling of what a system can
  do or the spread of how reliably it does it. Use for questions about sensitivity to prompt
  paraphrases, formatting, ordering, seeds, or repeated runs; output consistency and agreement;
  whether a ranking survives a different prompt; flaky results; and equally for hidden, suppressed,
  sandbagged, or under-elicited capability, whether a low score means "cannot" or "did not," or how
  prompting, demonstrations, scaffolding, tools, and fine-tuning compare. Do not use to find unknown
  failure modes or run adversarial attacks.
---

# Probe capability and variability

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/elicitation-regimes.md`.

## Trigger

- "Is this result stable?" / "Does this hold with a different prompt?" / flaky numbers.
- "Is the model bad at this, or is our harness bad?" / a low score read as a ceiling.
- A ranking derived from one prompt, one seed, or one run.

## Do

1. **Name the regime first — it selects the statistic, and mislabeling it is the most common
   reporting error here.** Capability = max over variants (`pass@k`), licensing "can at least do X."
   Variability = spread and worst case (`pass^k`), licensing "reliably does X."
2. Build the variant set for that regime: an **elicitation ladder** for capability (prompt →
   demonstrations → scaffolding → tools → search → fine-tuning), or **equivalence classes** for
   variability (one scenario, several surface forms).
3. Change one thing per variant, hold the construct and serving path constant, and record the exact
   setup that produced each result.
4. Repeat each condition K = 3–5 times; report mean, SD, and the **worst run** — never only best or
   average.
5. Attribute the result: separate what the **system** contributed from what the **harness**
   contributed, and state which conclusions survive which variants.

## Avoid

- Do not average the spread away when the spread **is** the measurement.
- Do not read a peak-elicited score as typical deployment performance, or fold peaks into an average
  with ordinary runs.
- Do not change the construct while improving the harness — a scaffold solving an easier task has
  elicited nothing, and a "paraphrase" that changes the correct answer measures difficulty.
- Do not treat scenario variants as independent items; cluster at the scenario level.
- Do not confuse harness instability (rate limits, cache warming) with behavioral sensitivity.

## Check

- Regime named, and the reported statistic matches it.
- Variant matrix published: factors, levels, how the construct was held constant.
- K stated; run distribution and worst case reported.
- Harness contribution separated from system; each result reproducible from its recorded setup.
- Capability claims stated as a **floor**, never a ceiling.

## Risk

- A narrow variant set falsely suggests robustness; prompt formatting alone can swing accuracy by
  double digits, so single-prompt rankings are a lottery.
- Elicitation proves presence, never absence — "we could not elicit it" is a bounded statement about
  effort spent.
- Stronger elicitation can create a deployment condition no user will be in, making the number true
  and irrelevant; if it surfaces dangerous capability, stop and escalate.

## Braintrust

Both regimes share one shape: **run the same dataset under several variants as separate
experiments**, then compare the max (capability) or the spread (variability). Shared mechanics:
`references/platform-mechanics.md`. Two apply with unusual force here, because a variant matrix
turns any inconsistency into apparent signal: pin every variant to one dataset version (§3) or
you are measuring dataset drift, and keep the **scorer name and version identical** across
variants (§5), since a scorer change between variants is indistinguishable from a real effect.
Keep per-run results (§7) — a stored mean cannot be un-averaged, and the spread is the
measurement.

Put the variant dimension in the **prefix** so the matrix reads: `r0-base`, `r1-prompt`,
`r2-fewshot`, `r3-scaffold`; or `fmt-json_set`, `fmt-md_set`. Prefix elicitation runs distinctly
(`elicit-*`) and say in the description that a peak is a floor, not a deployment estimate —
otherwise the project's highest number gets quoted as the product's performance.

This is where an unpinned serving path actively misleads: provider change, cache warming, or batch
variation all present as behavioral sensitivity. Record provider, tier, and cache state per variant
and run the matrix close together in time. Put `scenario_id` in `metadata` or every interval over
the matrix overstates precision, with no retroactive fix.
