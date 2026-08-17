---
name: red-team-agent
description: >-
  Plan and run adversarial worst-case testing of an authorized LLM or agent system against an
  explicit threat model, policy boundary, or high-impact prohibited behavior. Use for requests to
  red team, attack, jailbreak-test, or stress a system's guardrails, to assess prompt-injection or
  unsafe-tool-use exposure, or to turn adversarial findings into severity-ranked reports,
  mitigations, and regression cases. Do not use for open-ended discovery of ordinary failures, for
  measuring average quality, or without authorization over the target system.
---

# Red team an agent

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/threat-model.md`.

## Trigger

- Explicit adversarial testing against a stated threat model or policy boundary.
- Guardrail, prompt-injection, or unsafe-tool-use exposure assessment.
- A defense claim needing a test ("our filter stops this").

## Do

1. **Confirm authorization and scope before generating anything.** Record what is in scope, what is
   out, and who approved it.
2. Define the threat model concretely: **assets**, **adversaries** and their realistic
   capabilities, **prohibited outcomes** stated as observable events.
3. Prioritize **coverage over raw success rate.** Ten variations of one jailbreak teach less than
   one instance each of ten families.
4. Test defenses with **adaptive** attacks that know the defense, and report attacker budget —
   queries and compute — alongside any success rate. ASR without budget and adaptivity is
   meaningless.
5. Combine human and automated effort: automation for volume, humans for the realistic and creative
   attacks automation misses.
6. Verify each finding end to end, rank by severity, name affected versions and the mitigation
   owner, set retest criteria, and freeze a regression case. Report findings as **existence
   claims** entering gates as constraints re-tested every round — never averaged scores.

## Avoid

- Do not broaden the threat model or touch systems beyond the authorized scope.
- Do not include more actionable exploit detail than the mitigation owner needs; handle payloads as
  sensitive artifacts.
- Do not claim completeness — a clean campaign is evidence of effort, not of safety.
- Do not average red-team results into product-quality metrics.
- Do not treat this as safety-only: unjustified destructive tool calls and unsupported claims are
  equally worth attacking.

## Check

- Authorization and scope recorded before testing; threat model states assets, adversaries,
  capabilities, prohibited outcomes.
- Findings reproducible, with affected versions and realistic preconditions.
- Attack diversity reported across families, with budget and adaptivity.
- Severity ranking, mitigation owner, retest criteria, regression case per finding.
- Evidence stored with appropriate handling controls.

## Risk

- Testing can create harmful artifacts or affect real systems and users; run against isolated
  environments wherever the prohibited outcome has external effects.
- A passed campaign gives false assurance against an open-ended space — completeness is formally
  unreachable, so this is a standing process, not a pre-launch gate that retires once green.
- Findings leaking before mitigation shift risk onto users; sequence disclosure with the fix.
- Defenses tuned against the recorded attack set will pass it and fail the next variant.

## Braintrust

Keep the **adaptive attack set as its own versioned dataset, scored by existence-of-violation
rather than an average.** This is the structural difference from every other dataset here, and
getting it wrong is how red-team results become a misleading quality metric. **Never** let attack
items into a dataset used for population estimates — separate dataset, or at minimum a hard
metadata flag excluded from every aggregate. Version the set each round; an attack set is expected
to grow as defenses adapt.

Metadata that makes the coverage report computable: `family`, `threat_model_ref`, `adaptivity`,
`budget_queries`, `affected_versions`, `severity`, `finding_id`. Coverage-by-family is the headline
metric and is only computable if `family` is a field — without it you can report ASR but not
diversity, the number that matters less.

Wire findings as **blocking existence constraints** on the attack dataset, re-tested every round.
Prefer references over inline payloads in spans and restrict access on the project holding them.
Run the same existence scorers as trace classifications on live traffic.
