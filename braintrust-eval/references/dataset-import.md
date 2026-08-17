# Importing data into Braintrust

The dataset-landing step: take the source chosen in Phase 3 (a HuggingFace dataset,
CSV/JSON/JSONL, or existing agent traces) and put it into Braintrust in the right
shape. **Write the import script fresh in the eval's project folder** following the
contract below — there is no shared cookbook to import from. For a HuggingFace pull,
`rag-only-enforcement/generate_swebench_dataset.py` is a minimal in-repo example.

**Environment:** create a per-eval venv (`python3 -m venv .venv && .venv/bin/pip
install braintrust`) and run scripts with `.venv/bin/python`. Do NOT trust a bare
`import braintrust` check from a workspace root that also holds a `braintrust/`
repo clone — the clone shadows the SDK as a namespace package and false-positives.

## Which target? run → Dataset, analyze → Logs

| You have… | You want to… | Target | Shape |
|---|---|---|---|
| A benchmark with golden answers | run + score evals | **Braintrust Dataset** | rows of `{input, expected, metadata}` |
| Already-run agent traces | explore / cluster / score them | **Braintrust Logs** | a span tree per row |

Have traces but want a gradable benchmark? Lift each trace's task into `input` and its
recorded answer into `expected` (*traces-as-expected*) — but grade with a judge /
similarity scorer, because a recorded answer is a **reference, not ground truth**.

## Steps

1. **Preflight.** The org key is already selected in Phase 1; confirm the destination
   dataset name (Dataset) or project (Logs).
2. **Map the source** (explicitly):
   - *Dataset path:* write `to_record(row, i) -> {id, input, expected?, metadata}`. That
     function *is* the mapping — recipes + variations in `dataset-mapping.md`.
   - *Logs path:* point at the session-id / trace / metadata / score columns; each row
     becomes a root `task` span + one child `llm` span per call (`trace-structure.md`).
   - Pull HF rows via the dataset **viewer REST API**, not the `datasets` lib.
3. **Preview, THEN push.** Default to no network writes — print the first few mapped
   records so the shape is visible. Only `--push` (or `PUSH = True`) writes: Dataset via
   SDK/REST, Logs via `bt sync push`.
4. **Re-runs are safe.** Deterministic `uuid5` ids → re-importing **upserts**, no
   duplicates. Scores write back by rebuilding the **COMPLETE row + score and re-pushing**
   (same id). **Never** `logger.log(id=..., scores=...)` — it REPLACES the row, wiping
   input/output/metadata.

## Guardrails (in the helpers, applied visibly)
- Credentials env-only + pattern redaction of secret shapes (`sk-…`, `hf_…`, tokens).
- Long strings truncated; metadata byte-capped (largest keys dropped, recorded).
- Malformed message JSON kept as raw text so the row survives.

> Kept as a reference under `braintrust-eval` for now. If "import data into Braintrust"
> becomes a task you do on its own, promote this + `dataset-mapping.md` into a
> standalone skill.
