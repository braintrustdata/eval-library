---
name: braintrust-attribute-multi-variable-change
description: >-
  Attribute an observed change when several things moved at once — model plus prompt plus tools, a
  provider migration, a framework upgrade, or a vendor swap that bundles serving stack with model.
  Use when asked which part of a change caused the result, when a comparison's arms differ in more
  than one way, when a treatment has no uniform implementation across vendors, or when a
  serving-stack difference is confounded with a model difference. Do not use for a clean
  single-variable comparison, or to design an experiment that has not yet run.
---

# Attribute a multi-variable change

Contract: `references/interaction-contract.md`. Calibration, templates, provenance: `references/isolation-designs.md`.

## Trigger

- "We upgraded the model and rewrote the prompt — which one helped?"
- A vendor or provider migration bundling model, serving stack, and tool surface.
- Arms that differ in more than one respect, discovered after results exist.

## Do

1. Enumerate what actually differs between arms with the inventory in `reference.md`, including
   the variables hiding inside apparently atomic ones: the serving path behind a model string, the
   tool manifest behind "the agent."
2. State honestly what the existing data can and cannot separate. Two arms differing in three ways
   support **one** claim about the bundle and **no** claim about any component. Say that before
   analyzing anything.
3. Choose the cheapest design that isolates what the decision needs — ablation ladder,
   one-factor-at-a-time from the new baseline, or full factorial only when interactions are the
   actual question.
4. Where a factor cannot be held constant — a vendor with no equivalent parameter — record the
   per-arm implementation as a published table and **exclude that arm from the component claim**
   rather than scoring it "no benefit."
5. Report bundle effect and component effects as **separate rows**, each with its own uncertainty.

## Avoid

- Do not attribute a bundle's gain to its most interesting component because it is the one you
  care about.
- Do not treat a provider swap as a model comparison; precision, batching, and hardware shift
  outputs independent of weights.
- Do not fix arms mid-comparison to make them match — restart, or finish and document the
  confound.
- Do not reach for this on a clean single-variable comparison; ordinary paired analysis is
  both simpler and more sensitive.

## Check

- Full difference inventory per arm, including serving path and tool manifest.
- An explicit statement of which claims the current data cannot support.
- Isolation design chosen with its cost, and the factor each run isolates.
- Per-arm implementation table for any non-uniform treatment.
- Bundle and component effects reported separately, never merged.

## Risk

- The most common outcome is that the data supports no component claim at all, and **saying so is
  the correct deliverable** — an attribution invented from a confounded comparison is worse than
  none.
- Interactions are real: two changes can each help alone and hurt together, so
  one-factor-at-a-time results do not simply add.
- Serving-stack variation is the confound teams most often leave unnamed, because it rides inside
  a model string that looks like a single value.

## Braintrust

Shared mechanics: `references/platform-mechanics.md`. Attribution leans hardest on **§4
metadata** — the per-arm record of model string, decoding params, provider/endpoint/tier, cache
state, and prompt/scorer/tool versions *is* the difference inventory, recoverable months later.
Without it, attribution is guesswork. **§7 hygiene** matters more here than elsewhere too, since
a throttled provider left unthrottled becomes one more confound in a comparison already carrying
several.

Name for the factor being toggled, **most-significant first**, so an ablation ladder reads down
the experiment list in order.

Use cross-experiment diffs for item-paired component estimates, and group by `metadata` to check
whether a component effect is concentrated in one stratum; a component helping only one slice is
a stratification finding, not a main effect.
