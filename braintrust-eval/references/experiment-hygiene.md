# Experiment hygiene

The API calls and row-level definitions behind a hygienic run. Loaded during
Phase 5–6.

General mechanics — naming convention, why names are join keys, deleting smoke and
partial runs, the 1,000-row cursor — are in `references/platform-mechanics.md`
(§5, §7, §2). This file is the executable half: the exact requests, the row
arithmetic, and the policy this skill applies on top.

Base URL is `BRAINTRUST_API_URL` (default `https://api.braintrust.dev`); auth is
`Authorization: Bearer <the org's key>`. The key is chosen in Phase 1 — never
re-prompt for it here.

## Rename after the run

`Eval()` often generates a `<model>_v2`-style suffix, which sorts wrong. Flip it to
the version-first form (`v2_gpt-4o`) once the run exists:

```bash
curl -X PATCH "$BRAINTRUST_API_URL/v1/experiment/$EXPERIMENT_ID" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"name": "v2_gpt-4o"}'
```

## Delete

```bash
curl -X DELETE "$BRAINTRUST_API_URL/v1/experiment/$EXPERIMENT_ID" \
  -H "Authorization: Bearer $KEY"
```

Policy this skill applies, beyond the general rule that smoke and partial runs must
not survive to be read as arms:

- **Smoke runs** — delete as soon as one passes, not later. It is never a result.
- **Partial / errored / killed mid-run** — delete automatically before re-running.
- **Completed runs** — confirm with the user first. Braintrust experiments are
  **unrecoverable** once deleted.

## Survivor arithmetic

The row-level form of the completed-vs-errored check. A run can report "completed"
while most rows threw — rate limits in particular log the rows and then error them.

- **`roots`** — rows that are root spans (`span_id == root_span_id`, or no
  `span_parents`).
- **`errored`** — rows with a non-null `error`.
- **`ok = roots − errored`** — trust the averages only when this matches the dataset
  size you expected.

Fetch rows via BTQL or the experiment fetch endpoint, paginating with the cursor.
Show `ok` next to every score in the batch table, since that is what stops a
half-errored run from reading as a clean one.

## Trace sanity-scan checklist

Open the lowest-scoring rows and every errored one, and look for a broken *run*
rather than a bad model:

- Output **empty, truncated, or garbled**.
- **Tool/function calls erroring**, or never firing when they should.
- A scorer **stuck at 0 or 1 for every row** — a mapping or rubric bug, not a signal.
- **Inputs mangled** — wrong field mapped into `input`, template not filled.
- Latency or timing metrics missing or absurd.
