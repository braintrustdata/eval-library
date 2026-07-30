# Reference — scorers

## Choosing the method

| Evidence | Method |
| --- | --- |
| Test results, latency, schema validity, final application state, tool arguments | deterministic check |
| Clarity, tone, whether a response fully addresses a request | anchored rubric or human review |
| **Safety-critical, even when checkable** | deterministic check **plus** sampled human review |

The third row is the criterion teams miss. Objectivity says a deterministic scorer is
*possible*; it does not say it is *sufficient*. The survey of metric-computation methods
reserves human-in-the-loop for subjective aspects **and** "safety-critical judgment
calls." `[guide §5.1 → Mohammadi et al. 2025]`

Worked example — *the coding agent makes a correct change*:

- Evidence: tests pass; requested behavior implemented; unrelated files not modified.
- Scorers: a deterministic test scorer; an LLM judge for implementation completeness; a
  deterministic check on the set of files changed. `[guide §5.1]`

## Rubric pattern

A small number of explicit criteria, each scored separately, **each anchored with
examples of what earns each score** — never a single vague quality score.
`[guide §5.3 → Zheng et al. 2023]`

```text
Criterion: <one dimension only>

Score 1 — <label>
  Example: <verbatim output that earns this>
  Why: <the distinguishing feature>

Score 0.5 — <label>
  Example: ...
  Why: ...

Score 0 — <label>
  Example: ...
  Why: ...

Output JSON: {"score": <n>, "evidence": "<the span or quote that decided it>",
              "criterion": "<name>"}
```

Anchored exemplar pairs elicited from domain experts are the correct source for these
examples — do not invent them.

## Bias and silent-error rules

- **Judge ≠ evaluated model family.** LLM judges systematically prefer their own
  family's outputs. `[guide §5.4 → Zheng et al. 2023]`
- **Control position and verbosity bias.** Randomize and counterbalance order in
  pairwise setups; check whether the judge rewards length independent of quality.
  `[guide §5.4]`
- Position bias is only weakly related to prompt length but **strongly driven by the
  quality gap between candidates** — worst when the two answers are close, i.e. exactly
  the hard comparisons. Counterbalancing matters most there.
  `[pending — guide §5.4 comment, Shi et al. 2024]`
- The documented judge-bias taxonomy has **four** entries: position, length,
  self-enhancement, diversity. Do not cite it as six.
  `[pending — guide §5.4 comment, Gu et al. 2024]`
- **Score refusals, timeouts, and parse failures — never drop them.** A run that errored
  is a data point about the system, not a data-quality problem. `[guide §5.4]`
- **But separate harness from system failures.** A connection reset caused by your own
  runner's parallelism, or credits exhausted mid-arm, is missing data — scoring it zero
  penalizes whichever arm ran when your infrastructure buckled. System failures go into
  the score; harness failures go into effective-N accounting. This is what the per-item
  status field is for. `[guide §5.4, §8.4]`
- **Don't tune the scorer until the numbers look better.** Ask whether the strictness is
  correct for the construct. If it is, keep the artifact and document it as a known bias.
  If it is not, fix it, bump the version, and **re-run every arm**. What you must not do
  is ship a scorer whose strictness was chosen by its effect on the result.
  `[guide §5.4]`
- **Version scorers like code.** A scorer change invalidates cross-experiment
  comparisons exactly like a dataset change. `[guide §5.4]`

## Mitigation beyond order-swapping

A panel of several **smaller models from different families** beats a single large judge,
shows less intra-model bias, and runs substantially cheaper. Juror disagreement flags
items for human review — a natural feed into scorer validation.
`[pending — guide §5.4 comment, Verga et al. 2024]`

## Test matrix

Every scorer, before use:

```yaml
clear_success:      # scores at the top
clear_failure:      # scores at the bottom
edge_case:          # near the boundary, both sides
refusal:            # model declined
timeout:            # no output
parse_failure:      # unparseable output
empty_output:
adversarial:        # gaming attempt — length, confidence, polish
```

## Scorer contract template

```yaml
scorer: <name>              # stable across experiments
version: <n>
criterion: <one dimension>
level: trace | group | both
method: deterministic | reference_match | state_check | rubric_judge | pairwise
evidence_required: <fields or spans it reads>
range: 0-1
judge_model: <family, must differ from system under test>
failure_handling:
  system_failure: score_0 | score_partial
  harness_failure: status_field_not_score
known_artifacts: <strictness that may disadvantage an arm>
```
