---
name: design-human-eval-review
description: >-
  Design or audit human evaluation workflows and golden datasets for LLM applications and agents.
  Use to set up expert review, select review cases, write reviewer instructions, assign raters,
  capture rationales and confidence, measure inter-rater agreement with kappa or alpha,
  adjudicate disagreements, and preserve reviewed examples with provenance as a versioned
  reference set. Do not use to elicit the criteria or rubric in the first place, to validate a
  scorer once reference labels exist, or to implement the scorer.
---

# Design human review and the golden set

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/review-workflow.md`.

## Trigger

- "Set up human review." / "Build a golden dataset." / "How should we adjudicate?"
- A rubric that exists and now needs applying at scale by people.
- A judge that needs an anchor before it can be trusted.

## Do

1. Identify the expertise required and the decision the labels will support. Draft the review
   form **before** asking about reviewer count.
2. If no rubric or criteria exist yet, stop and elicit them from experts first. This skill
   applies criteria; it does not invent them.
3. Select cases deliberately: representative items, plus the ambiguous region where systems
   differ, plus **every severe failure class**.
4. Collect a short **rationale and confidence** with every label — the rationales are where the
   rubric gets sharp.
5. Have raters judge **independently before conferring**, then adjudicate on the record. A panel
   deferring to whoever speaks first discards the benefit of a panel.
6. Report agreement and adjudicate before the set calibrates anything, then preserve it as a
   versioned dataset with per-item provenance and a refresh trigger.

## Avoid

- Do not treat majority opinion as ground truth without the relevant expertise.
- Do not force adjudication over genuine construct ambiguity — record it; it is a finding about
  the rubric.
- Do not review only the easy middle; a golden set with no severe failures cannot validate a
  safety scorer.
- Do not compare a scorer against these labels here.

## Check

- Reviewer qualifications stated and matched to the construct.
- Independent labeling before discussion; agreement computed, not assumed.
- Adjudication decisions recorded with reasons.
- Coverage spans clear successes, clear failures, ambiguous edges, severe failures.
- Provenance per item; set versioned; refresh trigger defined.

## Risk

- Shared misunderstanding among reviewers produces a consistently wrong reference set that every
  downstream number inherits — **high agreement is not validity**.
- An unrepresentative review sample calibrates the scorer to the wrong distribution.
- Ceiling effects erase the benefit of multiple raters: if nearly every item is obvious,
  agreement is high and uninformative.
- Reviewer fatigue degrades labels across a long session, invisibly without timestamps.

## Braintrust

Run review in **human review queues** with **per-criterion scoring and free-text notes**.
Per-criterion is not optional: a single overall score cannot be adjudicated, and the note is the
rationale the reference set depends on. Promote reviewed traces into a **versioned golden
dataset** — the version is what lets validation state which labels a κ was computed against.

Where reviewers need the raw audio, image, or PDF to judge, run review over an **experiment**
rather than a dataset, since experiments surface attachments more prominently; otherwise
reviewers judge the pipeline's extraction instead of the system's behavior.

Wire two feeds: a stratified **production sample**, and the **scorer-disagreement queue** (items
where scorers disagree or sit near a threshold) — the highest-value human attention available,
at no extra collection cost. Reviewer identity, qualification, and timestamp go in item
metadata; fatigue drift and single-rater dominance are undetectable without them.
