# Experiment hygiene

How to name, rename, delete, and *trust* experiments so a batch stays comparable
and a lying aggregate never slips through. Loaded during Phase 5–6 of the run.

Base URL is `BRAINTRUST_API_URL` (default `https://api.braintrust.dev`); auth is
`Authorization: Bearer <the org's key>`. The key is chosen in Phase 1 — never
re-prompt for it here.

## Naming — by example

Name every experiment `v<version>_<model>` and let the examples do the talking:

| Good | Bad | Why |
|---|---|---|
| `v1_gpt-4o`, `v1_claude-opus-4-8` | `gpt-4o_v1`, `claude_run` | version-first groups all v1s together and sorts cleanly in the UI |
| `v2_gpt-4o` (rerun of the same variant) | `gpt-4o_final`, `test2` | reusing the name lets Braintrust auto-diff against the previous same-named run |
| `v3_gpt-4o_biasing` | `experiment_2026_07_08` | the name encodes the variable under test, so the diff is meaningful |

Rule of thumb the examples encode: **version first, then model, then the one
thing that changed.** A reader should know what a run *is* from its name alone.

## Rename after the run

`Eval()` often generates a `<model>_v2`-style suffix. Flip it to the version-first
form once the run exists:

```bash
curl -X PATCH "$BRAINTRUST_API_URL/v1/experiment/$EXPERIMENT_ID" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"name": "v2_gpt-4o"}'
```

## Deleting

```bash
curl -X DELETE "$BRAINTRUST_API_URL/v1/experiment/$EXPERIMENT_ID" \
  -H "Authorization: Bearer $KEY"
```

Policy the skill applies:
- **Smoke runs**: delete the smoke experiment as soon as it passes — it is never a
  result and pollutes comparisons.
- **Partial / errored / killed-mid-run**: delete automatically before re-running.
- **Completed runs**: confirm with the user before deleting.

## Verify completion — don't trust "completed"

A run can report "completed" and still be mostly errored (e.g. rate limits logged
the rows but most of them threw). Before believing *any* aggregate, pull the
experiment's rows and check the survivor count:

- **`roots`** = rows that are root spans (`span_id == root_span_id`, or no
  `span_parents`).
- **`errored`** = rows with a non-null `error`.
- Trust the averages only when **`ok = roots − errored`** matches the dataset size
  you expected.

Fetch the rows via BTQL / the experiment fetch endpoint (`bt_helpers.py` already does
paginated, retrying pulls). Note the fetch
**caps at 1000 rows** — paginate with the cursor, or you'll silently summarize a
partial set.

## Batch results table (Phase 6)

Summarize every experiment in the batch in one table, headline scores side by side
so variants compare at a glance. Always show `n (ok)` next to the scores so a
half-errored run can't masquerade as a clean one:

| Experiment | n (ok) | <score A> | <score B> | avg latency |
|---|---|---|---|---|
| `v1_gpt-4o` | 30 | 0.82 | 0.90 | 1.2s |
| `v1_claude-opus-4-8` | 30 | 0.88 | 0.93 | 1.6s |

## Trace sanity-scan checklist (Phase 6)

A first implementation is usually not fully correct, so open a sample of
traces — the lowest-scoring rows and any errored ones — and look for signs the
*run itself* is broken rather than the model being bad:

- Output is **empty, truncated, or garbled**.
- **Tool/function calls erroring** or never firing when they should.
- A scorer **stuck at 0 or 1 for every row** (mapping/rubric bug, not a real
  signal).
- **Inputs look mangled** — wrong field mapped into `input`, template not filled.
- Latency/timing metrics missing or absurd.

Flag anything suspicious *explicitly* before presenting scores as final — "these
numbers may not be trustworthy because X" beats a confident wrong summary.
