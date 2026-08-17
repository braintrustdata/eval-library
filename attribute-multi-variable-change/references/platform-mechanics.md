<!-- Shared Braintrust mechanics. A copy ships with each skill so the directory works
     standalone; keep copies identical rather than diverging per-skill. -->

# Shared Braintrust mechanics

Every card's `Braintrust` section inherits this file. It is the platform half that would
otherwise be repeated across the suite. Cards reference it and add only what is specific to
their own stage.

Mechanics here are product behavior, not empirical claims — they go stale, so re-check
against the shipped surface before relying on one externally.

## 1. The four objects

**Traces** (behavioral record), **datasets** (sampled population), **scorers** (instruments),
**experiments** (repeated observations). Traces come first; everything else consumes them.

## 2. Reading results safely

Two facts cause most phantom findings, and both present as data problems:

- **Check completed-row count against error count**, never the summary line. An arm can
  report completion while most of its rows errored, and every average it reports is then
  computed over the survivors.
- **Follow the 1,000-row pagination cursor**, and cache locally before analyzing. A truncated
  pull is indistinguishable from a missing stratum. Bulk reads also get throttled.

Pull once and work off the cache — re-fetching makes every pass a fresh reliability risk.

## 3. Pairing is a pinning decision, made before the run

Pin every arm to the **same dataset version**; cross-experiment diffs are then item-paired by
construction. An unpinned experiment **cannot be paired retroactively** — fall back to
unpaired and state the limitation.

A dataset change invalidates cross-experiment comparisons exactly like a scorer change. Treat
the boundary as a wall.

## 4. Metadata is the only slicing surface

Record independent variables and stratification fields in `metadata`: model string, decoding
params, provider/endpoint/tier, cache state, prompt/scorer/tool versions, plus every stratum
you intend to report on.

**A stratum not in metadata does not exist for reporting**, and there is no retroactive fix.
Discovering one missing is an instrumentation finding worth reporting, not a gap to omit
silently.

## 5. Names are join keys

Braintrust groups and auto-diffs **by name**, so naming is not cosmetic.

- **Experiments:** put the variable under test *first*. `v2_model-a` / `v2_model-b` group into
  readable blocks; `model-a_v2` / `model-b_v2` scatter alphabetically. Prefix order determines
  whether arms line up at all.
- **Scorers:** one criterion, one scorer, one stable name — across every experiment and across
  offline and online. A renamed scorer breaks the cross-experiment diff every regression check
  depends on; a differently-named production scorer produces a second, incomparable series.

## 6. The search denominator lives in the experiment list

Keep sweep arms as **separate experiments**, losers included, and count arms from that list
rather than from what anyone remembers trying. **If nothing is marked confirmatory, everything
is exploratory.**

## 7. Run hygiene

- `maxConcurrency` from an **environment variable**, so one fragile provider can be throttled
  alone instead of slowing or confounding the whole matrix.
- **Delete** smoke tests and partially-errored experiments (`DELETE /v1/experiment/{id}`) so
  they are never read as arms or counted in the denominator.
- K runs means K **recorded** trials, kept per-run. A stored mean cannot be un-averaged.

## 8. What is not native

κ, clustered standard errors, confusion heatmaps, `pass^k`, Wilson and rule-of-three upper
bounds, and per-run p95 all need **custom columns or an exported notebook**.

These are also where gates get wired wrong most often: pooling runs before taking p95, gating
on an observed rate instead of its upper bound, or averaging run means in place of `pass^k`.
