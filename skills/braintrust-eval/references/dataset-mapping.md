# Dataset mapping (source → `{input, expected, metadata}`)

The Dataset path of the import. The whole job is the `to_record` function — everything
else (pull, preview, push) is boilerplate around it.

## The EDIT ME block + the mapping

```python
HF_REPO, HF_SUBSET, HF_SPLIT = "openai/gsm8k", "main", "test"
BT_PROJECT, BT_DATASET = "hf-imports", "gsm8k"

def to_record(row, i):
    return {
        "id": str(row.get("task_id") or i),      # stable id → re-import upserts
        "input": row["question"],
        "expected": row["answer"],                # optional
        "metadata": {"hf_dataset": HF_REPO, "hf_subset": HF_SUBSET, "hf_split": HF_SPLIT},
    }
```

Run without `--push` to print the first few records and see the exact shape; flip
`--push` when it looks right. The loop is always **edit mapping → preview → push**.

## Common variations

- **Chat-formatted input** (a column that's a list of `{role, content}`):
  ```python
  "input": normalize_messages(parse_messages(row["messages"]))
  ```
- **Several columns into metadata** (for later grouping/slicing in analysis):
  ```python
  "metadata": {"category": row["category"], "difficulty": row["level"]}
  ```
- **Traces-as-expected** — build a gradable benchmark out of recorded runs: lift the
  trace's task into `input` and its final answer into `expected`. Grade with a judge or
  similarity scorer, not exact-match — a recorded answer is a reference, not ground truth.

## Pulling HF rows

Use the dataset **viewer REST API**, not the `datasets` lib (avoids torchcodec/decoding
headaches). Each row gives you the fields directly:

```bash
curl "https://datasets-server.huggingface.co/first-rows?dataset=<id>&config=<cfg>&split=<split>"
```

`HF_TOKEN` in `.env` raises rate limits and is required for gated/private sets. Normalize
any binary/media columns to a uniform format before logging.

## Push

- **Dataset:** insert the mapped records via the Braintrust SDK/REST into
  `BT_PROJECT / BT_DATASET`. Nothing writes until `--push`.
- Re-running is safe: same `id` → upsert, no duplicates.

## What keeps it safe
Credentials read from env only + secret-shape redaction; long strings truncated;
metadata byte-capped (largest keys dropped, recorded); malformed message JSON kept as
raw text. Preview (no writes) is the default — an upload happens only with `--push`.
