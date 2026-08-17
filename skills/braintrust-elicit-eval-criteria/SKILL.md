---
name: braintrust-elicit-eval-criteria
description: >-
  Extract evaluation criteria out of domain experts and real user desires, and capture them as
  reusable evaluation assets before any labeling or scoring begins — construct facets, anchored
  exemplars, adversarial traps, scoring guidance, audit rules, and the signals that reveal what
  users actually want. Use when nobody can say what "good" means, when a rubric does not exist
  yet, when expert knowledge lives only in reviewers' heads, or when validating that an eval
  reflects user desires rather than team assumptions. Do not use to run the labeling workflow or
  to compare a scorer against finished labels.
---

# Elicit criteria from experts and users

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/elicitation-guide.md`.

## Trigger

- No rubric exists, and review is happening on instinct.
- Experts disagree about what "good" means, or agree without being able to say why.
- An eval built entirely from team assumptions about what users want.

## Do

1. Gather both sources. **Expert knowledge**: what a qualified reviewer knows that the rubric
   does not say. **User desire**: what users actually want, evidenced rather than assumed.
2. Elicit from cases, not abstractions. Put a real trace in front of the expert, ask for a
   judgment, then ask *why* — the reason is the criterion. Repeat until reasons stop being new.
3. Capture each facet as an **anchored exemplar pair**: one output earning the top score, one
   that just misses, and the distinguishing reason. A pair beats a paragraph of description.
4. Harvest user desire from evidence that already exists — escalations, reopened tickets,
   abandoned sessions, thumbs-down, support themes. Where none exists, say so and label the
   criteria `Assumed`.
5. Capture what experts know about **failure**: the traps, the plausible-looking wrong answer,
   what juniors get wrong. Highest-value output, and the part rubrics usually omit.

## Avoid

- Do not ask experts to write a rubric from a blank page; elicit from cases.
- Do not substitute team intuition for user desire, or present it as evidence when you do.
- Do not run the labeling workflow or implement scoring here; this stage produces the criteria
  those steps consume.
- Do not resolve genuine expert disagreement by averaging it — a contested criterion is a
  finding about the construct.

## Check

- Every facet has an anchored exemplar pair with the distinguishing reason.
- Failure knowledge captured explicitly, not just success criteria.
- Each criterion labeled `Confirmed` (evidenced) or `Assumed` (team belief).
- User-desire signals named with their source, or their absence stated.

## Risk

- Experts articulate what they can defend, not always what they use; the reason given may not be
  the reason applied, which is why exemplars beat prose.
- A single expert encodes one house style as a universal standard.
- Available evidence of desire is biased toward users who complain; silent dissatisfaction leaves
  no trace.
- Criteria elicited once ossify — they need the dataset's refresh cadence.

## Braintrust

Run the elicitation session itself as **human review** over real traces with **per-criterion
scoring and free-text notes** — the notes are the output, because they carry the *reason*.
Promote reviewed traces into a **versioned golden dataset** so exemplars travel with the
criteria instead of living in a doc. Each facet then becomes its own scorer with a consistent
name; anchored pairs become the few-shot content of a rubric scorer. Flag traps in `metadata`
(`trap: true`) so they can be sliced out of headline numbers and reported separately. Treat a
criteria revision like a scorer change: bump the version, and do not compare results across the
boundary.
