# Finding an existing HuggingFace dataset

Used in Phase 3 when an existing dataset probably already covers what the user
wants to eval. Goal: surface 2–3 real candidates with enough detail to pick one,
then hand the choice to `braintrust-dataset-import`.

## 1. Search the Hub API

```bash
curl "https://huggingface.co/api/datasets?search=<query>&sort=downloads&direction=-1&limit=20&full=true"
```

Returns dataset ids, tags, downloads, likes, and `cardData`. Rank by relevance +
downloads; downloads is a decent proxy for "this one actually works."

## 2. Check gating BEFORE recommending

Many strong eval/ASR sets are **gated** and 401 without an `HF_TOKEN`. Check the
dataset info and don't recommend one the user can't access without flagging it:

```bash
curl "https://huggingface.co/api/datasets/<id>"   # look for "gated": true / license
```

`HF_TOKEN` in `.env` is also worth setting for higher rate limits even on ungated
sets; it's required for gated or private ones.

## 3. Inspect via the dataset viewer REST API (not the `datasets` lib)

Pull the shape straight from the viewer API — avoids `datasets`/torchcodec/decoding
headaches, and shows exactly what a row looks like:

```bash
curl "https://datasets-server.huggingface.co/splits?dataset=<id>"                        # configs + splits
curl "https://datasets-server.huggingface.co/size?dataset=<id>"                          # row counts
curl "https://datasets-server.huggingface.co/first-rows?dataset=<id>&config=<cfg>&split=<split>"  # real rows
```

Read the columns and judge how they map to Braintrust's `{input, expected,
metadata}`: which column is the prompt, which is the golden answer, what's left for
metadata.

## 4. Present candidates

For each of 2–3 candidates give:
- **id + size/splits** (e.g. `openai/gsm8k` — test, 1.3k rows)
- **one-line why it fits** the user's eval
- **gated/license** status (flag if it needs a token)
- **rough mapping** — "`question` → input, `answer` → expected"

Recommend one, note the tradeoff, and **wait for the user to pick.** Then hand the
chosen `{repo, config, split, column mapping}` to **`braintrust-dataset-import`**.

## Provenance — why is this dataset reputable?

Once the user picks, gather evidence it's trustworthy and log a short blurb to
`ANALYSIS-SUMMARY.md` (this ends up in the blog-ready writeup):

- **HF stats:** `curl https://huggingface.co/api/datasets/<id>` → `downloads`,
  `likes`, and the owning org (a known lab/company beats an anonymous account).
- **Paper:** check cardData/README for an arXiv link; note venue (e.g. NAACL,
  NeurIPS D&B) and rough citation count (Semantic Scholar API:
  `https://api.semanticscholar.org/graph/v1/paper/arXiv:<id>?fields=citationCount,venue,year`).
- **Code/community:** GitHub stars on the companion repo
  (`https://api.github.com/repos/<org>/<repo>` → `stargazers_count`), plus any
  leaderboard/benchmark usage or news mentions from a quick web search.

Blurb shape: *"Built by <lab>; <n> HF downloads, <n> likes; introduced in <paper,
venue, year> with <n> citations; companion repo <n>★; used by <who else>."* If the
evidence is thin, log that as a caveat instead of overselling the source.

## Caution

A dataset's "answer" column is a *reference*, not guaranteed ground truth
(read-aloud, auto-transcribed, and crowd-sourced sets all carry label noise).
Prefer LLM-judge or similarity scoring over exact-match unless the answers are
genuinely canonical — carry this into Phase 4.
