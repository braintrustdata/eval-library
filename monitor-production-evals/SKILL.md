---
name: monitor-production-evals
description: >-
  Design or audit online evaluation of live LLM and agent traffic: trace sampling, online scoring
  coverage, alert thresholds and ownership, drift and failure-slice monitoring, incident review, and
  the pipeline that routes production failures back into the offline dataset. Use for questions
  about scoring production traces, monitoring quality after launch, catching regressions in the
  wild, alert fatigue, scorer drift, or closing the loop from incident to eval item. Do not use to
  design offline experiments or to interpret a controlled comparison.
---

# Monitor evals in production

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/monitoring-design.md`.

## Trigger

- "How do we know it's still working?" / "Score our production traces."
- Alerts firing that nobody acts on, or incidents that never became eval items.
- A release gate that passed while users report problems.

## Do

1. Frame the loop: offline experiments gate the release, online scoring monitors the shipped system,
   observed failures become new dataset items, and the next offline eval is more representative.
   Online has perfect distributional realism and **no controlled comparison**.
2. Define coverage deliberately — which traffic, at what rate, which scorers. **Stratify** so
   rare-but-severe slices are covered; proportional sampling misses the failures that matter most.
   The sampling rate is simultaneously the coverage decision and the **cost** decision, and the
   two pull opposite ways; decide it as one tradeoff rather than setting coverage and discovering
   the bill.
3. Reuse offline scorers where they were validated for monitoring, and state which use each is
   approved for. A scorer below the gating bar may still serve trend monitoring.
4. Give every alert a threshold with **documented provenance**, an **owner**, and an **action**. An
   alert with no action is a notification.
5. Monitor drift on **both sides**: input distribution shift and scorer drift. Re-validate on a
   schedule, not on suspicion.
6. Watch the **silent** failures — most agent failures raise no error, so error-rate dashboards look
   healthy while quality degrades.
7. Close the loop mechanically: flagged traces through review into the versioned dataset, with
   provenance and incident reference. Apply privacy and retention controls **at collection time**.

## Avoid

- Do not treat online scores as a controlled experiment; a production metric moving is
  observational and licenses no causal claim.
- Do not collect production data without privacy and retention controls in place first.
- Do not alert on every dip — alert fatigue destroys the channel, and the fix is fewer,
  better-owned alerts.
- Do not let the golden set ossify while traffic drifts; a loop that never updates the dataset is
  not closed.
- Do not design offline experiments here.

## Check

- Sampling plan states rate, stratification, coverage of rare severe slices, and cost at that rate.
- Every online scorer's approved use documented, with its validation date.
- Any historical backfill has its window, eligible-unit count, and estimated cost stated before it
  is submitted.
- Every alert has threshold provenance, owner, action, and review latency.
- Drift monitored on both input distribution and scorer behavior.
- Ingestion path from flagged trace to versioned dataset item exists, with an owner.
- Privacy, PII handling, and retention documented per collected field.

## Risk

- Distribution shift silently invalidates thresholds from an older baseline; the alert stays quiet
  while the population underneath changes.
- Scorer drift under a provider model update looks exactly like a product regression.
- Privacy limits may make the most informative traces uncollectable — design around what is
  retainable rather than discovering the constraint later.
- Monitoring sees only what is instrumented, so trace-schema gaps become permanent production blind
  spots.

## Braintrust

Apply **the same scorers** that ran offline — same names, same versions
(`references/platform-mechanics.md` §5) — via **online scoring**. This is the case §5 exists for:
a differently-named production scorer produces a second series that looks comparable and is not.
Use **trace classifications** for the categorical side —
spec violations, suspected failure modes, attack families — since classifications are what you
slice and alert on, and they double as the clustering step for open-ended failure discovery. Record
each scorer's approved use in its description so nobody promotes a trend scorer into a gate.

Close the loop with **human review queues**: sample live traces → review → append to a **versioned**
golden dataset, with provenance in metadata (`trace_id`, incident ref, date, reviewer,
`source: production-<YYYY-MM>`). Route the scorer-disagreement queue in too.

Standing a scorer up on live traffic — rule configuration, sampling, activation, and historical
backfill — is `deploy-braintrust-evaluator`. Two things from it bear directly on monitoring
design. **Activating a rule for new traffic and rewinding it over history are separate actions
requiring separate authorization**, and a paused rule accepts a rewind without processing it, which
is how teams end up believing history is being scored when nothing is running. And a backfill's
cost is eligible units × sampling rate × per-call judge cost, which on a high-volume project is
easy to misjudge by an order of magnitude — estimate before submitting, and submit once.

Record each alert's baseline window in its own description, so a quiet alert is distinguishable
from a moved population. Detect judge drift by re-running the **calibration experiment** on a
schedule — the same calibration run used to validate it. For non-text inputs, the raw artifact must be a
span **Attachment** or incident review cannot separate "the system failed" from "the input was
unintelligible."
