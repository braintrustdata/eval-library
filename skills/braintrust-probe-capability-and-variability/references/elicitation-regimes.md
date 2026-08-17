# Reference — capability and variability probing

## The regimes

Two of the four elicitation regimes. Both run the same dataset under variants; they differ
only in which statistic answers the question — and **the single most common eval-reporting
error is mislabeling which one you are in**.

| Regime | Surfacing | Statistic | Claim licensed |
| --- | --- | --- | --- |
| Capability elicitation | the **best** the system can do | max over attempts (`pass@k`) | "can (at least) do X" |
| Variability probing | the **spread** under equivalent conditions | distribution, worst case (`pass^k`) | "*reliably* does X" |

The other two regimes are out of scope here: open-ended failure discovery, and adversarial red
teaming against a threat model. Both have different stopping conditions. `[guide §4.8]`

## Capability: a score is a floor, not a ceiling

An eval score is a **lower bound**. It says "the system did at least this well under this
setup," never "this is the most it can do." A low score is ambiguous between *cannot* and
*did not*. `[guide §4.8.1]`

### The elicitation ladder

| Rung | Change | Records |
| --- | --- | --- |
| 0 | base prompt, as deployed | the floor |
| 1 | improved prompt and formatting | prompt sensitivity |
| 2 | few-shot demonstrations | whether examples unlock it |
| 3 | scaffolding, retries, self-check | harness contribution |
| 4 | tool access | capability vs. access |
| 5 | search / best-of-N | compute-for-capability trade |
| 6 | adaptation or fine-tuning | strongest available elicitation |

- **Password-locked models:** a few high-quality demonstrations often fully elicit a hidden
  capability; fine-tuning generalizes across locks; and "when only evaluations, and not
  demonstrations, are available, approaches like reinforcement learning are still often able
  to elicit capabilities." `[guide §4.8.1 → Greenblatt et al. 2024]`
- **Sandbagging:** models can be prompted or password-locked to selectively underperform,
  even to a target score. `[guide §4.8.1 → van der Weij et al. 2024]`
- **Method matters by task:** prompting recovers capability on multiple-choice QA (steering
  does not), while **only fine-tuning** does for code generation — so one failed attempt
  establishes nothing about absence. `[guide §4.8.1 → Hofstätter et al. 2025]`
- Decoupling LLM capability from harness design is an independent recommendation of the
  agent-eval surveys. `[guide §1, §2.2 → Yehudai et al. 2025]`

### Construct-drift check

The most common false ladder: rung N quietly solves an easier problem than rung 0. Before
accepting a gain, confirm the scorer is unchanged and same-version, items are the same
dataset version, the scaffold does not supply part of the answer, and **no retry loop reads
the score** — a scaffold that can see the score has turned the eval into training.

### Containment

If a rung surfaces capability dangerous to publish or leave accessible, stop climbing and
escalate. The finding is the deliverable. `[guide §4.8.1]`

## Variability: make the spread the measurement

Elsewhere run-to-run variance is noise to average over. Here **the variance is the result** —
vary the eval surface deliberately and report the distribution as a first-class number.
`[guide §4.8.2]`

- **Prompt formatting alone can swing accuracy by double digits**, so a single-prompt ranking
  is a prompt lottery rather than a finding. `[guide §4.8.2 → Sclar et al. 2024]`
- Multi-prompt evaluation is the corrective — 6.5M-instance analysis across 20 LLMs, 39
  tasks. `[guide §4.8.2 → Mizrahi et al. 2024]`
- Design variants as **equivalence classes** (one scenario, several surface forms), which is
  exactly the scenario-by-variant clustering requiring clustered standard errors.
  `[guide §4.8.2, §9.1]`
- Hosted "deterministic" settings are not: up to **15%** accuracy variation across runs of the
  same configuration, best-to-worst gap up to **70%**. `[guide §9.0 → Atıl et al. 2025]`
- Root causes: competing logits flipped by numerical noise, amplified by BF16 precision, batch
  size, GPU count, hardware. `[guide §9.0 → Yuan et al. 2025]`
- Two systems can share an average while differing in reliability; leaderboard gains often
  fail reliability criteria across runs and datasets. `[guide §9.4 → Oh 2026]`

### `pass^k`

Probability that **all** k i.i.d. trials succeed, averaged over tasks — the reliability
counterpart to `pass@k`'s "any of k." Under independence `pass^k` = p^k, so 90% per attempt →
**57% at k = 8**. τ-bench, which introduced it: even state-of-the-art function-calling agents
"succeed on <50% of the tasks, and are quite inconsistent (pass^8 <25% in retail)."
`[guide §9.0, §4.8.2 → Yao et al. 2024]`

### Agreement over repeats

- **TARr@N** — on the raw output.
- **TARa@N** — on the parsed-out answer. **Usually the one you want for scored evals.**

`[guide §9.0 → Atıl et al. 2025]`

## Variant matrix template

```yaml
regime: capability | variability
statistic_reported: max | worst_case | distribution    # must match the regime

# variability: equivalence classes
scenario_id: <the invariant meaning>
factors:
  paraphrase:     [v1, v2, v3]
  formatting:     [plain, markdown, json]
  option_order:   [original, reversed, shuffled]
  seed:           [a, b, c]
  context_length: [25k, 50k]
equivalence_check: <how you verified the correct answer is identical across variants>

# capability: ladder rungs
ladder:
  - rung: 0
    setup: {prompt: , scaffold: none, tools: [], compute: 1x}
    result: {value: , pass_at_k: , k: }
    reproduce: <exact config>
    attributable_to: system | harness | both

held_constant:
  construct: <and how verified>
  serving_path: {provider: , tier: , cache_state: }
  scorer: <name>@<version>
  dataset: <name>@<version>
runs_per_condition_K: <≥3>
design: one_factor_at_a_time | full_factorial
clustering: scenario_level
```

## Reporting

```yaml
per_condition: [{condition: , mean: , sd: , worst: , n: , K: }]
spread: {range: , worst_case: , agreement: {TARa@N: }, pass_k: {k: , value: }}
peak: {rung: , value: , setup_required: , deployment_realistic: yes|no}
claim: <"can at least X under setup S" | "reliably does X, worst case Y">
claim_is_a_floor: <true for capability>
not_a_deployment_estimate: <true for peak elicitation>
conclusion_stability: {survives: [], breaks: []}
```
