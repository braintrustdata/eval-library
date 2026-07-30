# Reference — multi-variable attribution

## Provenance

- **A model string is not a configuration.** Batch size, GPU count, and GPU version
  all shift generated responses, amplified by BF16 precision. Cache state moves
  latency and cost more than most prompt edits.
  `[guide §8.2 → Yuan et al. 2025 (arXiv:2506.09501); Braintrust GLM-Opus 2026]`
- **Hosted "deterministic" settings are not deterministic.** Across five API LLMs
  and eight tasks with 10 runs each: accuracy variation **up to 15%** across runs of
  the same configuration, and a gap up to **70%** between best-possible and
  worst-possible performance. The unit is percent, not percentage points.
  `[guide §9.0 → Atıl et al. 2025]`
- **Verify the treatment is implementable in every arm.** Where vendors differ, one
  independent variable quietly becomes several. Enumerate the per-arm implementation,
  publish it beside the results, and exclude arms that cannot receive the treatment
  from the treatment-effect claim rather than recording them as "no benefit."
  `[guide §8.2]`
- **Fix nothing mid-comparison.** A mid-run correction makes arms incomparable and,
  unlike a dataset or scorer version change, leaves **no trace in the results
  table**. Either restart the matrix under the corrected configuration or finish as
  designed and record the defect as a stated limitation. `[guide §8.2]`
- Renamed and deprecated API parameters are usually accepted in silence and ignored
  — indistinguishable in results from a treatment that does not work. Log the
  **resolved** config per item. `[guide §3.2, §8.2]`
- The agent-eval taxonomies treat serving environment only as a data-collection
  setting ("evaluation contexts": the environment in which an evaluation is
  performed, from controlled simulations to open-world browsers and APIs), not as a
  variable with metrics of its own. Treat it as first-class anyway.
  `[guide §8.2 → Mohammadi et al. 2025]`

## Difference inventory template

Fill one column per arm. Any row that differs is a candidate confound.

```yaml
model_string:
provider:
endpoint_tier:
region:
decoding_params:          # temperature, top_p, max_tokens, seed
cache_state:              # cold / warm / mixed
batching:
prompt_version:
system_prompt_diff:
tool_manifest:            # names, schemas, permissions
retrieval_config:
guardrail_config:
harness_version:
scorer_version:
dataset_version:
```

## Choosing the isolation design

| Situation | Design | Runs needed |
| --- | --- | --- |
| One factor suspected, others must hold | Ablation: baseline + toggle | 2 arms |
| Bundle already won; decide what to keep | One-factor-at-a-time from the new baseline | 1 + k arms |
| Interactions are the question | Factorial | 2^k arms |
| A factor cannot be held constant | Stratify and report per stratum; exclude from the component claim | varies |

Cost check before committing: items × arms × runs against every quota and credit
balance in the path. A metered ceiling reached partway through one arm leaves a
partial result, which is worse than a missing one. `[guide §4.2, §8.4]`

## Claim language

- Bundle only: "migrating from A to B improved task success by X pp [CI]. The
  migration changed model, serving provider, and tool schema together; this result
  does not attribute the gain to any one of them."
- Component, isolated: "holding serving path and tools fixed, the model change alone
  accounts for Y pp [CI] of the X pp bundle effect."
- Non-uniform treatment: "arm C's provider exposes no equivalent parameter; it is
  excluded from the treatment-effect estimate and reported separately."
