# Reference — eliciting criteria

## Provenance

- Construct-first rubric design: decompose the construct into facets and score each
  consistently, the way validated scales measure latent properties.
  `[guide §6.3 → Wang et al. 2026; Truong & Koyejo 2026 ch. 5]`
- Push human expertise **upstream** into reusable evaluation intelligence before
  testing begins — domain context, adversarial traps, juror personas, scoring
  guidance, audit rules — so a harness applies human-designed structure across runs
  instead of experts rescoring each interaction.
  `[guide §6.3 → Bousetouane 2026]`
- The transferable claim, independent of any framework: **human insight scales when
  captured in rubrics, exemplars, scenarios, and review rules — not when recreated
  manually per run.** `[guide §6.3]`
- Direct human attention to ambiguous examples, high-risk domains, newly changed
  behavior, and cases where automated scorers disagree — volume is not the aim.
  `[guide §6.3 → Lazaros et al. 2026]`
- Rubrics work as **anchored examples, not descriptions**: a few explicit criteria,
  each scored separately, each anchored with examples of what earns each score.
  Never a single vague quality score. `[guide §5.3 → Zheng et al. 2023]`
- Adjudication discussion is where the rubric gets sharp — the disagreements are the
  product, not the noise. `[guide §4.4]`
- Independent judgment before conferring: a panel that defers to whoever speaks
  first discards the benefit of having a panel. `[pending — guide §5.4 comment,
  Siu et al. 2025]`

## Elicitation interview shape

Per case, in this order. Stop when three consecutive cases produce no new reason.

1. Show the trace. No rubric, no leading question.
2. "Is this acceptable to ship?" — force a binary before nuance.
3. "What made you say that?" — the answer is a candidate criterion.
4. "What would make it clearly unacceptable?" — the failure boundary.
5. "What would a less experienced reviewer miss here?" — the trap.
6. "Would a user care about this, or is it a house preference?" — separates construct
   from style.

## Facet template

```yaml
facet: <short name>
construct: <the property this facet is part of>
why_it_matters: <consequence if violated>
exemplar_pass:
  output: <verbatim or trace ref>
  why: <the distinguishing reason>
exemplar_near_miss:
  output: <verbatim or trace ref>
  why: <what is missing, stated as the same dimension>
traps:
  - <plausible-looking wrong answer an expert would catch>
status: Confirmed | Assumed
source: <expert name/role, or evidence source>
```

## User-desire evidence sources

Ordered by how directly they express desire rather than proxy for it:

1. Escalation and reopen reasons — a user rejecting a resolution states the gap.
2. Abandoned or restarted sessions at a known step.
3. Explicit feedback (thumbs, free text, survey), noting its complaint bias.
4. Support themes and refund reasons.
5. Task-completion telemetry — weakest, because completion is not satisfaction.

Where none is available, criteria are `Assumed`. Say so in the artifact rather than
letting a team belief inherit the authority of evidence.
