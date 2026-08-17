# Reference — instrumentation

## Minimal agent eval record

```jsonc
{
  "input": { "task": "...", "repo_state": "...", "user_context": "..." },
  "expected": { /* reference answer, constraints, or rubric */ },
  "output": {
    "final_answer": "...",
    "steps": [
      { "type": "tool_call", "name": "edit_file", "args": {}, "result": "..." },
      { "type": "llm_call", "model": "...", "prompt_version": "...", "tokens": 812 }
    ]
  },
  "metadata": {
    // every slicing variable you will ever group by:
    "category": "refactor", "difficulty": "complex", "language": "python",
    "source": "production-2026-06", "adversarial": false, "split": "test"
  }
}
```

The `steps` list mirrors the span tree — design them together, not sequentially.
`[guide §3.2]`

## The three fields discovered too late

1. **The raw input artifact, not just the derived text.** For audio, images, PDFs, or
   screenshots, attach the original alongside whatever the pipeline extracted. Without it,
   "the system got this wrong" and "this input was unintelligible" are indistinguishable —
   and that distinction decides whether you fix the model or fix the dataset.
2. **A per-item status field, separate from the score.** `ok`, `provider_error`, `timeout`,
   `parse_failure`, `quota_exhausted`. A score of 0 and a failure to produce a score are
   different facts; an aggregate computed without the distinction silently answers "how did
   the system do *on the items that survived*."
3. **The fully resolved configuration, per item.** Not what you intended to send — what was
   actually sent: exact model string, decoding parameters, every provider-specific option,
   including SDK-filled defaults and parameters the API accepted and ignored. Renamed and
   deprecated options are typically dropped without error.

`[guide §3.2]`

## Serving-path fields

A model string is not a configuration.

```yaml
provider:
endpoint:
tier:
region:
cache_state:        # cold / warm / mixed
batching:
```

Batch size, GPU count, and GPU version all shift generated responses, amplified by BF16
precision. `[guide §8.2 → Yuan et al. 2025]`

## Tool manifest fields

```yaml
tools:
  - name:
    schema_version:
    permissions:
```

Under role-based access, different users see different tool surfaces, so "the agent's tools"
is not fixed even within one deployment. An arm that silently lacks a tool reads as a
capability gap. `[guide §8.2 → Mohammadi et al. 2025]`

## Span discipline

- One span per **LLM call, tool call, and scorer call**, full payloads, **correct nesting**.
- Flat spans cannot localize a cascading failure. Failure attribution depends on this: early
  mistakes cascade, so the module that first erred matters more than the visible symptom.
  `[guide §4.8.3 → Zhu et al. 2025]`
- Scorer name and version in span metadata.

## Provenance

- Everything downstream — scoring, slicing, debugging, release gates — can only see what you
  log. If the trace contains only the final answer, evaluation can only judge the final
  answer. Agents can "show their work," but only if you expose it. `[guide §3.2]`
- Instrument first: traces are the behavioral record, and everything else consumes them. A
  thin trace caps every downstream measurement. `[guide §1]`
- You can only discover what you logged — undertraced systems hide their failure modes.
  `[guide §4.8.3]`
- Dataset-level metadata rubrics are treated in the AIMS resources.
  `[guide §3.2 → Truong & Koyejo 2026]`

## Field dictionary template

```yaml
field: <path>
required: yes | no
purpose: <the decision or slice it serves>
sensitivity: none | pii | secret
retention: <window>
populated_by: <component>
```

## Completeness test

Pick a real past failure. Walk the schema and ask whether you could, from these fields alone:
reconstruct what happened, score it, slice it against its peers, and identify the module that
first erred. Any "no" is a missing field — fix it before building the dataset on top.
