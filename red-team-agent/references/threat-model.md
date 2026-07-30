# Reference — red teaming

## Authorization gate

Nothing in this skill proceeds without this recorded:

```yaml
authorized_by: <name/role>
date:
in_scope: [<systems, endpoints, environments>]
out_of_scope: [<explicitly excluded>]
environment: isolated | staging | production   # production requires explicit sign-off
prohibited_outcomes_may_be_triggered: yes | no  # if yes, isolation is mandatory
evidence_handling: <where payloads are stored, who can read them>
```

## Threat model template

```yaml
assets:
  - <what is worth protecting, and to whom>
adversaries:
  - profile: <external user | authenticated user | insider | compromised tool>
    capabilities: <what they can send, see, and repeat>
    budget: <queries, compute, time>
prohibited_outcomes:
  - <stated as an observable event, not a quality>
```

"Observable event" matters: "the agent behaves unsafely" is not testable; "the agent issues
a delete call without an explicit confirmation in the turn" is.

## Four nuances that matter more than any technique

1. **Attack success rate is meaningless without the attacker's budget and adaptivity.** A
   static attack suite goes stale the moment a defense trains on it, so any defense claim
   must be tested against **adaptive** attacks that know the defense — the oldest lesson in
   adversarial ML. Report queries and compute spent alongside ASR.
   `[guide §4.8.4 → Tramèr et al. 2020]`
2. **For evaluation, coverage beats raw success rate.** A reward-maximizing attacker
   collapses onto a few high-reward modes and reports impressive ASR with almost no
   diversity; the objective should be diversity-seeking. **Ten variations of one jailbreak
   teach you less than one instance each of ten families.**
   `[guide §4.8.4 → Samvelyan et al. 2024]`
3. **Human and automated red teaming are complementary, not substitutes** — automation for
   volume, humans for the realistic, creative attacks automation misses.
   `[guide §4.8.4 → Ganguli et al. 2022]`
4. **Red-team results license existence claims only** ("there is an input that…"), and must
   never be averaged into a product-quality metric. Red teaming is also **not safety-only**:
   no unsupported claims and no unjustified destructive tool calls are exactly the kind of
   product behaviors worth attacking. `[guide §4.8.4]`

## Methods

- Human red teams at scale bring creativity and realism about what users actually try.
  `[→ Ganguli et al. 2022]`
- Automated: one model generating attacks against another `[→ Perez et al. 2022a]`;
  gradient-optimized universal and transferable suffixes `[→ Zou et al. 2023]`;
  failure-mode-guided attacks built around competing objectives and mismatched
  generalization `[→ Wei et al. 2023]`.
- HarmBench standardized comparison across attacks and defenses.
  `[→ Mazeika et al. 2024]`

`[all guide §4.8.4]`

## Why completeness is unreachable

A peer-reviewed proof extending the logic of Gödel's incompleteness theorems: **no finite
set of guardrails is universally robust against adversarial prompts.** A guardrail or
rule-based check is a finite formal system, and there will always exist inputs that evade
it. Natural language is unboundedly ambiguous and guardrail sets are necessarily finite, so
no rule-based safety framework achieves complete, contradiction-free coverage.

The recommended posture is continuous monitor-and-update — constant red-teaming, continuous
hardening, operational resilience — rather than one-and-done certification.

`[guide §1.1, §4.8.4 → Vassilev 2026; NIST 2026]`

## Finding template

```yaml
finding_id:
title:
family: <attack family — for the coverage count>
threat_model_ref: <which prohibited outcome>
preconditions: <what the adversary must already have>
realism: <would a real adversary have these?>
reproducible: deterministic | probabilistic
attempts_to_reproduce: <n successes / n tries>
adaptivity: static | adaptive_to_defense
budget: {queries: , compute: }
affected_versions: []
severity: <impact if exploited, not likelihood>
mitigation_owner: <role>
retest_criteria: <what a fix must demonstrate>
regression_case: <dataset item id>
evidence_location: <controlled store — not inline>
disclosure_sequence: <fix before publication>
```

## Coverage report

```yaml
families_attempted: []
families_successful: []
coverage: <successful families / known families>
asr_per_family: [{family: , asr: , budget: }]
completeness_claim: none        # always
```

Report coverage by family first. A single ASR number across a campaign hides whether you
found ten things or one thing ten times.
