# Trace structure

How to shape spans so a trace is readable in the Braintrust UI and clusters well
in Topics/Issues. Apply this convention every time — getting it right up front
avoids re-prompting the run to "log the trace the way I like."

**Language:** use whatever the user picked in Phase 2 intake. The Braintrust SDK
supports the same tracing in every language — snippets below are Python and
TypeScript, but the shape is identical anywhere. **Language and mode are
independent**; neither implies the other.

## The convention (all languages, both modes)

- **One root span, `type: "task"`** — carries the overall `input`/`output` and
  top-level `metadata` for the whole call/example.
- **One named child span per stage** (or per LLM call) — e.g. `retrieve`,
  `generate`, `tool:lookup`. Each logs its *own* `input`/`output` plus `metrics`
  (tokens, latency). Use `type: "llm"` for model calls, `"tool"` for tool/function
  calls, `"task"` otherwise.
- **Surface errors onto the root.** If a child errors or a tool fails, also note it
  on the root's `output`/`error` so Topics/Issues cluster on the failure instead of
  burying it in a leaf.
- **Log inputs/outputs, not just scores** — a span with no `input`/`output` is dead
  weight in the UI.

Do / don't:
- ✅ name spans for *what the stage is* (`retrieve`, `generate`), not `step_1`.
- ✅ put token/latency on the child that produced them, not all on the root.
- ❌ don't flatten everything into one span — you lose the per-stage view.
- ❌ don't log giant blobs raw — truncate long strings before logging.

## Two modes — pick by where the data comes from, not by language

- **Live** — you're running the pipeline *now* (e.g. inside `Eval()`); wrap each
  stage so spans stream as it executes. This is what `braintrust-eval` uses.
- **Offline / imported** — the runs already happened elsewhere (a HF dump, exported
  logs); rebuild the tree and push it. That's `braintrust-dataset-import`.

Both modes work in every language the SDK supports.

---

## Live tracing

Inside an `Eval()` task you're already in a root span, so just open **child** spans
per stage; they nest automatically.

**Python:**
```python
from braintrust import start_span

def task(input):
    with start_span(name="retrieve", type="task") as span:
        docs = retrieve(input)
        span.log(input=input, output=docs, metrics={"n_docs": len(docs)})
    with start_span(name="generate", type="llm") as span:
        answer = call_model(input, docs)
        span.log(input={"question": input, "docs": docs}, output=answer.text,
                 metadata={"model": "claude-opus-4-8"},
                 metrics={"prompt_tokens": answer.usage.input, "completion_tokens": answer.usage.output})
    return answer.text
```

**TypeScript:**
```ts
import { traced } from "braintrust";

const docs = await traced(async (span) => {
  const out = await retrieve(input);
  span.log({ input, output: out, metrics: { n_docs: out.length } });
  return out;
}, { name: "retrieve", type: "task" });
```

For a standalone script (outside `Eval()`), open the root yourself: `init_logger(...)`
then a root `start_span(name="call", type="task")` (Python) / `initLogger(...)` +
`traced(..., {type:"task"})` (TS), with child spans as above.

## Offline / imported

The runs already happened; you rebuild the tree and push it. The key trick is
**deterministic IDs** so re-importing the same session *upserts* instead of
duplicating:

```python
import uuid
root_id  = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"root:{session_id}"))
child_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"child:{session_id}:{i}"))
```

Each span carries `id`/`span_id`/`root_span_id`/`span_parents`, `is_root`,
`input`/`output`, `metadata`, `metrics`, and `span_attributes: {name, type,
exec_counter}` — root `type:"task"`, children `type:"llm"`. Write to JSONL and
`bt sync push`. The pattern is identical in any language; the battle-tested Python
builder is `braintrust_logs.py` in the `hf_bt_cookbook` — reuse it via the
`braintrust-dataset-import` skill rather than hand-rolling.

---

## Quick reference — span fields

| Field | What goes in it |
|---|---|
| `name` | the stage (`retrieve`, `generate`, `tool:lookup`) |
| `type` | `task` (root / generic), `llm` (model call), `tool`, `score` |
| `input` / `output` | this span's own in/out (truncate long strings) |
| `metadata` | model name, params, flags |
| `metrics` | `prompt_tokens`, `completion_tokens`, timing |
| `error` | set on the child *and* summarize on the root |
