---
name: braintrust-eval
description: >-
  Run an independent, end-to-end eval in Braintrust — from a plain-English idea
  to a scored, compared experiment. Guides dataset sourcing (existing vs.
  synthetic), scorer design, and a hygienic experiment run. Use when the user
  wants to run a Braintrust eval, run an experiment, eval or compare
  models/prompts, score model outputs, or "set up an eval" for a task.
---

# Braintrust Eval

Take the user from "I want to eval X" to a clean, comparable Braintrust
experiment. This skill owns the **judgment-heavy** parts of an eval — what the
dataset should be, which scorers to use and how they're written, and running the
experiment without the reliability/hygiene traps. It is deliberately interactive:
ask, propose, get approval, then spend money.

## When to use / when not
- **Use this** to design and run a new eval or model/prompt comparison.
- **Getting data into Braintrust** (mapping a HuggingFace / CSV / trace source into
  a BT dataset)? Handled in Phase 3 via `references/dataset-import.md`.
- **Pulling or plotting results** from experiments that already ran? Hand off to
  the **`braintrust-analyze`** skill.

Work through the phases in order. Do not skip the approval gates — the whole point
is that the user signs off on the dataset and the scorers before a paid run.

---

## Phase 1 — Preflight (before anything else)

**1a. Ask which org.** Braintrust API keys are org-scoped, so this decides which
credential the run uses — and it's a data-governance decision.

> "Which org should this run in — **Personal** or **Braintrust**?"

Governance default, state it if relevant: *if the eval involves sensitive,
customer, or proprietary data, default to the Personal org unless the user says
otherwise.*

**1b. Select + verify the key.** Keys live in **one canonical file**:
`/Users/jess/Documents/Coding Projects/Braintrust/.env` (fall back to the current
project's `.env` only if the canonical file doesn't exist). Map the org to its key:
- Personal → `BRAINTRUST_API_KEY_PERSONAL`
- Braintrust → `BRAINTRUST_API_KEY_BRAINTRUST`

**Do not hunt for keys** across sub-project `.env` files — that trips credential-
scanning guards. If the chosen key is missing or empty: create/append the stub
line to the canonical `.env`, tell the user exactly which variable to fill in
(key from Braintrust app → Settings → API Keys, per org), and wait. **Never ask
the user to paste a key into the chat, and never print one.** Verify the filled
key by listing the org's **projects** via the API (not `/v1/organization` — it can
return empty for member keys). (See `references/bt-auth.md`.)

**1c. Ask which project**, then confirm it exists in that org via the API. If it
doesn't exist, offer to create it.

## Phase 2 — Intake

Three open prompts (answer in prose), plus one quick config pick:

1. **What do you want to eval?** (They'll usually name the model and/or prompt
   variant here — that's the thing under test.)
2. **Describe what the dataset should be.** (~3 sentences: the inputs, what a good
   answer looks like, any domains/edge cases to cover.)
3. **Describe what scores you'd like to see.** (What does "good" mean here? What
   failures matter most?)
4. **Which language should the eval be written in?** Braintrust ships full SDKs —
   tracing, the `Eval()` framework, and scorers — in **Python, TypeScript, Go,
   Java, Ruby, and C#**. Surface all six and **default to Python** unless the user
   picks another. This drives the scorer and trace code that gets generated.

Read the answers back as a short restatement so the user can correct you before
you plan anything.

## Phase 3 — Dataset planning → **APPROVAL GATE**

From the intake, decide the sourcing route and propose it:

- **Existing dataset likely exists** → search Hugging Face and surface 2–3
  candidates, each with a one-line "why this fits" and its size/split. (See
  `references/hf-dataset-search.md`.)
- **Niche / sensitive / synthetic-friendly** → propose generating it
  synthetically, and include a **clean control bucket** (inputs whose correct
  answer is true by construction) so at least one slice has unimpeachable labels.

Recommend one route, explain the tradeoff in a sentence, and **wait for the user
to pick.** Then map + push the chosen source per `references/dataset-import.md`.

**Provenance check (after the pick, before import).** For a sourced dataset,
spend a couple of minutes establishing *why it's trustworthy* and log it to
`ANALYSIS-SUMMARY.md`: who built it (org/lab), HF downloads + likes, the
associated paper and where it was published/cited, GitHub stars, and whether
other benchmarks/leaderboards use it. If the trail is thin, say so — a
low-provenance dataset is usable but the writeup should carry that caveat.
(Recipe: `references/hf-dataset-search.md` § Provenance.)

> **Ground-truth caution:** a "reference" answer isn't always correct. Prefer
> LLM-judge or similarity scoring over exact-match unless the answers are
> genuinely canonical.

## Phase 4 — Score planning → **TWO APPROVAL GATES**

**Gate 1 — the lineup.** Propose scorers as a table and let the user
add/drop/change before you write any code:

> | Scorer | Type | What it checks |
> |---|---|---|
> | `entity_recall` | Deterministic | % of expected entities present in the output |
> | `exact_match` | Deterministic | Output equals `expected` |
> | `answer_quality` | LLM judge | Does the answer resolve the request? (binary) |
> | `policy_adherence` | LLM judge | Did it follow the stated policy? (binary) |

**Gate 2 — the implementation.** For each approved scorer, show the *actual*
thing before it runs — the **rubric/prompt** for a judge, or the **logic** for a
deterministic scorer — and get sign-off.

**New scorers always re-open the gates.** Any scorer introduced after Gate 1 —
mid-eval, for a new track, or as a "small addition" — gets the same treatment
before it runs: **explicitly alert the user that a new scorer is being added,
show what it measures and how (prompt/logic verbatim), and wait for sign-off.**
Never let a new metric slip into an experiment inside a bigger change. A few defaults worth keeping:
- **Measure the thing the change actually moves.** A broad overall score can hide
  a targeted effect; scope the metric to the slice under test.
- LLM judges: **binary labels, temperature 0, explanations on.** (Binary per
  example still yields a continuous aggregate across the dataset.)
- **"Deterministic" means code-computed, not pass/fail.** When quality is graded
  (similarity, recall, overlap), return a continuous 0–1 score — reserve binary
  for true guards (rendered / didn't). Say this when presenting the lineup so
  "Deterministic" isn't read as "exact match."
- **Don't tune a scorer to flatter results — document the artifact instead.**
- **Datasets and scorers are versioned Braintrust artifacts.** Data always lands
  as a BT Dataset (never inline in code). Push scorers so they're visible in the
  UI: LLM-judge prompts as pushed scorer functions; heavy code scorers (browser,
  torch, etc.) run locally but record their file + git/content hash in experiment
  metadata so every run points at an exact scorer version.

## Phase 5 — Run loop

Run the experiment(s) over the dataset. One `Eval()` per variant in the matrix.

**Model as a variable (offer it).** Default the agent/task model to
**claude-sonnet-5** (cheap enough to iterate, strong enough to be interesting)
— but once a track has baseline results, **proactively suggest a
model-comparison rerun** (e.g. same rows/trials on a stronger model like
Fable 5) as a follow-up experiment. Model changes are a new variable: new
experiment names carrying a model slug, smoke + gate as usual, and cost
estimated up front (stronger models can be several × the per-run cost).

**Small dataset → trials.** If **n < 30**, run **3 trials per row**
(`Eval(trial_count=3)`) so per-row noise doesn't masquerade as a variant
effect; report scores as means across trials. State the trial count in the
experiment metadata and the results table. (Trials multiply cost and quota —
include them in the quota-preflight math.)

**Naming (do this every time).** Name each experiment `v1_<model>` /
`v2_<model>` so runs group and sort cleanly and Braintrust auto-diffs against the
previous same-named run. Good/bad examples + the rename recipe:
`references/experiment-hygiene.md`.

**Headless subprocess agents: brainstorm the tool allowlist deliberately.**
A headless `claude -p` agent **cannot answer permission prompts** — any call to
an un-allowlisted tool makes it stall mid-run asking for approval that never
comes, producing an empty-output failure that *looks like a variant defect*.
`--permission-mode acceptEdits` covers file edits and trivially-safe reads
only; **Bash is NOT allowed by default.** Before the first smoke, run a
dedicated brainstorm: "what would a resourceful human reach for mid-task?" —
e.g. image-heavy tasks → Bash (Python/PIL color sampling, cropping, base64
encoding), asset tasks → download/encode tools, plus Read/Write/Edit and the
`mcp__<server>` entries under test. Allowlist each need or *consciously
exclude it and record the exclusion as a harness condition*. Keep the
allowlist **identical across variants** and **pin it in experiment metadata**
so failures can be attributed later. Failure signature to watch for: run ends
with the agent asking a question ("Could you approve…") and no output file.

**Quota preflight (before any full agentic run).** If the task depends on an
external service — an MCP server, a third-party API, a rate-limited provider —
**check its plan/quota limits before launching the batch**, not after rows
start failing. Do the math out loud: `rows × variants × est. calls per run`
vs. the plan's limit (remember smoke runs and deleted reruns spend the same
quota). If the budget doesn't clearly fit: ask the user to upgrade, shrink the
subset, or split the run across quota windows. Then **preflight one real
mutation call** through the service (read-only calls succeeding proves
nothing — quotas often gate writes only). Quota exhaustion mid-batch
invalidates the variant: stop, delete the partial, rerun when quota allows.

**Smoke first, then delete it.** Run a **5-example smoke experiment** first
(named e.g. `smoke_<variant>`) purely to confirm the pipeline runs end-to-end
with **0 errors**. A smoke run is never a result — **delete the smoke experiment
before the full run** so it can't pollute comparisons.

**→ HARD GATE between smoke and full run.** After presenting smoke results,
**stop and wait**. Give the user room to ask questions, inspect scorer outputs,
and request tweaks — then ask explicitly ("ready to start the full pass?") via a
clickable confirmation (AskUserQuestion) and **do not launch the full run until
they say yes.** Never roll from smoke into the full run in one motion, even when
the smoke is clean.

**Throttle + retry.** Default to bounded concurrency (`maxConcurrency` /
`EVAL_CONCURRENCY`) and 429 backoff honoring `Retry-After`; drop concurrency for
free-tier / rate-limited providers.

**Structure the trace.** Log spans the way these projects settled on:
root span `type:"task"` carrying the overall input/output/metadata; one named
child span per stage (or per LLM call) with its own input/output + `metrics`
(tokens, timing); surface errors/tool-failures onto the root so Topics/Issues can
cluster on them. **Media lives in the trace:** any image/audio the task consumes
or produces (input images, rendered screenshots, artifacts) goes on the span as
an `Attachment` so the trace view shows it inline — never just a local file path.
(See `references/trace-structure.md`.)
For **agentic evals running `claude -p` subprocesses**: enable the
`trace-claude-code` plugin per run so each agent's full internal trace (every
tool/MCP call) lands in the project's **Logs**, and put an `agent_trace_url`
permalink (`.../logs?r=<session_id>`) in the experiment span's metadata.
Deliver the env config via `--settings` file (user settings.json env overrides
subprocess env!) and **verify spans actually landed** — hooks fail silently.
Full recipe + failure catalog: `references/subprocess-tracing.md`.

**Verify completion — don't trust "completed."** A run that reports success can be
mostly errored. Check `ok = roots − errored` before believing any aggregate; a
rate-limited run can log the rows but have most of them error out.

**One variable at a time.** Keep the dataset/inputs fixed across variants so the
comparison is clean. Don't slip in an extra fix mid-run — rerun all variants
together or not at all.

## Phase 6 — Batch summary & sanity check

After the batch finishes, don't just report a number — summarize and pressure-test
it, because a first implementation is usually not fully correct.

1. **Results table.** One row per experiment in the batch, headline scores side by
   side so variants compare at a glance:

   > | Experiment | n (ok) | answer_quality | policy | avg latency |
   > |---|---|---|---|---|
   > | `v1_gpt-4o` | 30 | 0.82 | 0.90 | 1.2s |
   > | `v1_claude-opus-4-8` | 30 | 0.88 | 0.93 | 1.6s |

2. **Scan the traces.** Open a sample of traces — especially low-scoring and any
   errored ones — and look for signs the *run itself* is wrong: empty/garbled
   outputs, tool failures, a scorer that never fires, mangled inputs. **Flag likely
   problems explicitly** instead of reporting scores as if they're final.
   Red flags worth chasing: a score **identical across variants on every row**
   (scorer measuring something the variants can't affect, or a ceiling both
   saturate); and in agentic evals, **the agent not using the capability under
   test** (log tool usage per run and check it — a comparison where the variable
   is never exercised is Sonnet-vs-Sonnet).

3. **Analysis.** Give a 3–5 sentence read of what the scores say — which variant
   won, where it's failing, and whether anything looks like a harness bug vs. a
   real model difference.

## Phase 7 — Hand off to deeper analysis
For plots and heavier slicing, point the user to the **`braintrust-analyze`** skill
(BTQL, cached pulls, Braintrust-styled charts) — it continues the running log below.

**Turning the log into a blog?** That's a separate step, and not everyone wants
it — hand off to the **`braintrust-eval-blog`** skill, which owns the
research-blog structure, the jargon rule, and drafting through the voice skills.

**Agentic-eval analysis menu** (stats worth computing beyond score means —
pick what the experiment makes interesting):
- **Reliability**: failed/zero-score trials per variant with a failure
  taxonomy (API drop / agent stall / tool quota / render fail — read the
  agents' final messages); scores recomputed excluding failures, so
  "worse quality" vs "worse survival" separate cleanly.
- **Efficiency**: duration, cost, and tool calls per run; cost per quality
  point across variants.
- **Behavior**: tool-mix histograms; self-correction loops (e.g.
  screenshots/run) and their **correlation with quality scores** (scatter —
  a weak correlation is a finding); iteration granularity (few-big-writes vs
  many-small-edits).
- **Markup/output forensics**: semantic-tag usage, div ratios, output size,
  technique adoption greps (e.g. backdrop-filter) per variant/prompt.
- **Judge forensics**: grade distributions; recurring loss-themes in judge
  reasons; CLIP-vs-judge agreement.
- **Slices**: per-row win matrix, score-by-design-category, score vs. launch
  order (drift/quota degradation over a batch).

## Running log — `ANALYSIS-SUMMARY.md`
Keep an `ANALYSIS-SUMMARY.md` at the project root and append to it *as you go*, so
the eval ends up blog-ready without reconstructing it later. Log the **methodology**
(what's tested, dataset, scorers, run conditions), the **dataset provenance blurb**
(who built it, downloads/stars, paper + citations — see Phase 3), and **only the big learnings** —
**Every behavioral or structural claim needs at least one concrete example
pulled from a specific trace/log** — an actual output snippet, tool-call
sequence, or judge explanation, cited by experiment + row. "Variant A writes
more conventional markup" is an assertion; a side-by-side of the two outputs'
`<body>` openings from the same row is evidence. If no example can be found,
the claim doesn't go in.
surprising results, confounds you found, decisions and why. Skip routine steps and
raw dumps. `braintrust-analyze` continues this same file with the deeper analysis.

---

## Overridable defaults (sticky for the session, say so to override)
- Before a full run that leans on an external service: check the plan's quota,
  do the rows×calls math, and preflight one mutation call.
- Run a 5-example smoke test first, confirm 0 errors, **then delete the smoke
  experiment** before the full set.
- **Pause after every smoke**: present results, take questions/tweaks, and get
  an explicit clickable "yes" before launching the full run.
- **n < 30 → 3 trials per row** (`trial_count=3`); means across trials.
- Before re-running a same-named experiment, **delete the prior partial/smoke
  run automatically; confirm before deleting a completed run.**
- **Failed runs: attribute before you retry — failures can be signal, not
  noise.** Classify each failure first: (a) *transient infrastructure* (API
  drops) → retry and purge the dead original, disclosing the retry count;
  (b) *harness-caused* (missing tool permission, config bug) → fix the
  harness, disclose, excludable; (c) *variant-caused* (agent stalls, gives
  up, its tool quota/API fails) → **keep it — that IS the product
  experience**. Retry policy must be **symmetric across variants**. Always
  report both all-runs and successful-only scores plus the survival rate as
  its own metric — the decomposition is often the finding.
- If you do retry, **dedupe — don't delete signal**: `Eval(update=True)`
  **appends — it does not replace the dead row**. When a retried row now
  *succeeds*, purge only its **superseded dead original** (delete that one
  event) so the case isn't double-counted. **Never purge a failure that is
  still a failure** — keep it and let it count toward the survival rate; that
  decomposition is often the finding. Re-pull the summary after; aggregates
  that still count the duplicate can flip a comparison's apparent winner.
- **`ANALYSIS-SUMMARY.md` mirrors the live experiments — it is a summary of
  current learnings, not an append-only log.** When the user asks to delete a
  completed experiment or rerun a new version of it, **ask them first: archive
  the analysis or remove it?** (AskUserQuestion — archive moves results +
  learnings to a clearly-marked ARCHIVED block, quotable as "from the deleted
  run"; remove leaves only a one-line pointer to what replaced it.) Episodes
  with narrative value — a confound caught, a diagnosis story — usually
  deserve the archive. Either way, remove the numbers from the *live*
  sections in the same breath. Remember Braintrust experiments are
  unrecoverable once deleted — settle the archive question and capture the
  doc content BEFORE deleting, and keep any plots/caches wanted for the story.
- Smoke tests verify it *runs* — never conclude "which is better" from n=5.
- One variable at a time; dataset fixed across variants.
- Append methodology + big learnings to `ANALYSIS-SUMMARY.md` as you go.

## Troubleshooting
- **`BRAINTRUST_API_KEY_* not set`** → the chosen org's key is missing from `.env`;
  see `references/bt-auth.md`.
- **`ModuleNotFoundError: braintrust` (but an import check passed earlier)** → the
  workspace root's `braintrust/` repo clone shadows the SDK. Use a per-eval venv
  and `.venv/bin/python`; never test SDK presence from the workspace root.
- **Nested `claude -p` returns 401 (agentic evals)** — check in this order:
  1. An **invalid `ANTHROPIC_API_KEY`** shadowing the claude.ai login. It can hide
     in `~/.zshrc`/`~/.bashrc` AND `~/.claude/settings.local.json` (`env` block —
     applies even with a clean process env). Remove it everywhere.
  2. **Parent-session env leakage**: a harness running inside Claude Code exports
     `ANTHROPIC_BASE_URL` + `CLAUDE_CODE_*` OAuth vars that break a child `claude`.
     Always scrub these from the subprocess env (see `SCRUB_ENV` in
     `paper-vs-figma-mcp-eval/run_eval.py`).
  3. **Stale CLI OAuth token**: the desktop app rotates refresh tokens, orphaning
     the CLI's keychain copy. Only the user can fix this — have them run
     `claude /login` in a fresh terminal. A smoke run costing $0.00 with 0 tokens
     is the signature of all three.
- **ECONNRESET / connection storm at scale** → concurrency too high; lower
  `EVAL_CONCURRENCY`.
- **Run "completed" but averages look off** → check `ok = roots − errored`; likely
  most rows errored (rate limits).
- **Aggregate score barely moves after a targeted change** → likely the wrong
  metric; scope the score to the slice the change actually affects.
- **Agentic eval: rows suddenly produce empty output, no agent_error, normal
  turn counts** → read the agents' final messages before blaming the harness —
  a third-party tool quota (e.g. an MCP server's weekly limit) may have run
  out mid-batch. Budget tool-call quota like tokens before launching (rows ×
  calls/row vs. the plan's limit), preflight one *mutation* call per MCP, and
  treat mid-run exhaustion as invalidating the variant: stop, delete the
  partial, rerun when quota allows.

## References
Authored inside this skill folder, loaded on demand:
- `references/experiment-hygiene.md` — naming (good/bad examples), rename, delete,
  verify-completion, and the batch results-summary table
- `references/trace-structure.md` — the span-tree convention
- `references/hf-dataset-search.md` — finding an existing HF dataset
- `references/dataset-import.md` — landing a chosen source as a BT Dataset/Logs
- `references/dataset-mapping.md` — the `to_record` mapping recipes
- `references/subprocess-tracing.md` — full agent-internals tracing for
  `claude -p` subprocess evals (trace-claude-code plugin recipe + failure catalog)
- `references/bt-setup.md`, `references/bt-auth.md` — install + org-scoped keys

**Sibling skill:** `braintrust-eval-blog` — turns the finished `ANALYSIS-SUMMARY.md`
into a publishable blog post (research-blog structure, jargon rule, voice skills).
