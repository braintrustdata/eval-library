# Reference — scorers

Platform mechanics carry `[platform]` rather than a guide section. They are product behavior, not
empirical claims — but they go stale the same way, so re-check them against the shipped tool
surface before relying on one externally.

## Choosing the method

| Evidence | Method |
| --- | --- |
| Test results, latency, schema validity, final application state, tool arguments | deterministic check |
| Clarity, tone, whether a response fully addresses a request | anchored rubric or human review |
| **Safety-critical, even when checkable** | deterministic check **plus** sampled human review |

The third row is the criterion teams miss. Objectivity says a deterministic scorer is
*possible*; it does not say it is *sufficient*. The survey of metric-computation methods
reserves human-in-the-loop for subjective aspects **and** "safety-critical judgment
calls." `[Mohammadi et al. 2025]`

Worked example — *the coding agent makes a correct change*:

- Evidence: tests pass; requested behavior implemented; unrelated files not modified.
- Scorers: a deterministic test scorer; an LLM judge for implementation completeness; a
  deterministic check on the set of files changed.

## Rubric pattern

A small number of explicit criteria, each scored separately, **each anchored with
examples of what earns each score** — never a single vague quality score.
`[Zheng et al. 2023]`

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

## Emit classes, map to numbers

Do not ask a model for a number. Asked for a score in 0–1 it clusters on round values, and the
distance between 0.6 and 0.8 carries no stable meaning across items or across runs. Asked for a
**label from described categories** it is doing the thing it is actually good at. Have the model
return the class; configure the class→score mapping outside it.

```text
Classes, and the score each maps to:
  consistent          1.0
  minor_omission      0.7
  lacking_citation    0.4
  contradicted        0.0
```

This is the same move the rubric pattern already makes — the class *is* the anchor — carried
through to the output rather than dropped at the last step. Three things follow from it:

- The mapping becomes a reviewable, versionable artifact, separate from the prompt.
- Re-weighting severity no longer requires re-running the judge.
- Disagreements become adjudicable. "The judge called this `lacking_citation`" is a claim a human
  can argue with; "the judge said 0.4" is not.

`[platform]` mapping mechanics: LLM score evaluators configure this as `choice_scores`.

## Scorer or classifier

| | Scorer | Classifier |
| --- | --- | --- |
| Returns | number in 0–1 | one label from a fixed set |
| Needs | numeric mapping, skip behavior | allowed labels, no-match behavior |

Pick classifier when the answer is genuinely categorical and the categories are known and stable.
Flattening categories onto a 0–1 scale so the instrument "matches the other scorers" discards the
distinction the instrument was built to capture — and an ordering imposed on unordered categories
is an assertion about severity that nobody reviewed.

If the categories are not known yet, this is discovery, not scoring: see `braintrust-discover-trace-topics`.

## Bias and silent-error rules

- **Judge ≠ evaluated model family.** LLM judges systematically prefer their own
  family's outputs. `[Zheng et al. 2023]`
- **Control position and verbosity bias.** Randomize and counterbalance order in
  pairwise setups; check whether the judge rewards length independent of quality.
- Position bias is only weakly related to prompt length but **strongly driven by the
  quality gap between candidates** — worst when the two answers are close, i.e. exactly
  the hard comparisons. Counterbalancing matters most there.
- The documented judge-bias taxonomy has **four** entries: position, length,
  self-enhancement, diversity. Do not cite it as six.
- **Score refusals, timeouts, and parse failures — never drop them.** A run that errored
  is a data point about the system, not a data-quality problem.
- **But separate harness from system failures.** A connection reset caused by your own
  runner's parallelism, or credits exhausted mid-arm, is missing data — scoring it zero
  penalizes whichever arm ran when your infrastructure buckled. System failures go into
  the score; harness failures go into effective-N accounting. This is what the per-item
  status field is for.
- **Don't tune the scorer until the numbers look better.** Ask whether the strictness is
  correct for the construct. If it is, keep the artifact and document it as a known bias.
  If it is not, fix it, bump the version, and **re-run every arm**. What you must not do
  is ship a scorer whose strictness was chosen by its effect on the result.
- **Version scorers like code.** A scorer change invalidates cross-experiment
  comparisons exactly like a dataset change.
- **The judged text can address the judge.** Output produced by the system under test may contain
  content directed at the evaluator — a claim that the answer is complete, an instruction about how
  to score it. The four documented biases all describe a *miscalibrated* judge; none of them
  describes one that is being spoken to, and counterbalancing does nothing about it. Include a
  probe for it in the test matrix, and read the judge's evidence field rather than only its score.
  Contract §9.

## Mitigation beyond order-swapping

A panel of several **smaller models from different families** beats a single large judge,
shows less intra-model bias, and runs substantially cheaper. Juror disagreement flags
items for human review — a natural feed into scorer validation.

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
addressed_judge:    # output containing text aimed at the evaluator
```

## Scorer contract template

```yaml
scorer: <name>              # stable across experiments
version: <n>
criterion: <one dimension>
output_type: score | classification
input_scope: span | trace | group          # how much one call sees; default trace
reporting_level: per_item | aggregate | both
method: deterministic | reference_match | state_check | rubric_judge | pairwise
evidence_required: <fields or spans it reads>
range: 0-1                  # score only
classes: <label: score, ...>               # rubric judges: emit the label, map here
judge_model: <family, must differ from system under test>
failure_handling:
  system_failure: score_0 | score_partial
  harness_failure: status_field_not_score
known_artifacts: <strictness that may disadvantage an arm>
```
