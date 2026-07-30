# Reference — scorer validation

Thresholds here are **defaults to justify, not laws**. Quote the hedge with the number.

## Fitness bands

| Agreement (κ or α) vs. golden set | Fit for |
| --- | --- |
| < 0.4 | exploration only; do not report trends |
| 0.4 – 0.7 | may still be fine for **trend monitoring** |
| ≥ ~0.7 | candidate for **release gating** |

The stated bar: *don't gate releases on a judge below κ ≈ 0.7 against the golden set;
between 0.4–0.7 it may still be fine for trend monitoring.* Treat these as defaults to
justify, not laws. `[guide §7.1]`

Agreement alone never licenses gating. A scorer above the bar that misses a severe class
is still unfit — severity beats average.

## The validation recipe

1. **Build the reference set** — ~100+ traces spanning clear successes, clear failures,
   and ambiguous edge cases, reviewed by ≥2 experts with adjudicated labels, built
   construct-first. `[guide §7.1 → Casabianca 2025]`
2. **Compare scorer to humans.** Report κ or α, not raw accuracy.
3. **Examine disagreements by category and severity**, not just overall agreement. A
   scorer confusing "excellent" with "good" may be fine for trend monitoring; one that
   misses harmful outputs or overestimates implementation correctness is unacceptable for
   gating. `[guide §7.1 → Salaudeen et al. 2025]`
4. **Inspect the dangerous cells explicitly** — every case where the scorer said **≥0.8
   and humans said ≤0.3**, and the reverse. These are where a gate would have shipped a
   failure.
5. **Test sensitivity to real change** — the scorer should move when you inject known
   regressions and known improvements. A scorer that cannot detect changes users notice
   is decoration.
6. **Probe for gaming** — does length raise the score independent of quality? Confidence
   independent of correctness? Polish independent of task completion?
   `[guide §7.1 → Zheng et al. 2023; Skalse et al. 2022]`
7. **Propagate scorer error into headline numbers.** If the judge agrees with humans 85%
   of the time, "92% helpful" carries wider uncertainty than the item-count interval
   implies — report it. Generalizability Theory treats judges as one more variance source
   to decompose. `[guide §7.1 → Truong & Koyejo 2026 ch. 5]`
8. **Revalidate** when the product, rubric, model mix, or production distribution
   changes.

## Validate the pattern, not just the score

Single benchmark numbers hide the underlying demand structure of tasks. Validate the
**pattern of relationships** among the bundle's dimensions, not one aggregate. If a
prompt change improves helpfulness while degrading safety, or raises correctness only via
verbosity and latency, that relational pattern **is** the finding.
`[guide §7.2 → Zhou et al. 2026]`

Two confusion heatmaps make it concrete:

- human category × scorer category — the diagonal is agreement; off-diagonal cells show
  which distinct human categories the scorer collapses.
- scorer A × scorer B (e.g. deterministic checker vs. LLM judge) — reveals where they
  capture different aspects of behavior.

`[guide §7.2]`

## Confusion table template

```yaml
alignment_verified: item_and_criterion_level
n_reference_items:
agreement:
  metric: cohens_kappa | krippendorff_alpha
  value:
  ci:
raw_accuracy: <report only alongside kappa, never alone>

dangerous_cells:
  false_accept:              # scorer ≥0.8, human ≤0.3
    - {item_id: , scorer: , human: , why: , severity: }
  false_reject:              # scorer ≤0.3, human ≥0.8
    - {item_id: , scorer: , human: , why: , severity: }

by_severity:
  - {class: harmful_output, n: , missed: , rate: }
  - {class: correctness, n: , missed: , rate: }

by_subgroup:
  - {stratum: , agreement: , n: }

shortcut_probes:
  length_independent_of_quality: pass | fail
  confidence_independent_of_correctness: pass | fail
  polish_independent_of_completion: pass | fail

sensitivity:
  injected_regression_detected: yes | no
  injected_improvement_detected: yes | no
```

## Fitness statement template

```yaml
scorer: <name>@<version>
validated_against: <golden dataset>@<version>
date:
allowed_uses:
  - exploration
  - trend_monitoring
  - release_gating           # only if severity checks also pass
prohibited_uses:
  - <e.g. safety gating — misses 2/9 harmful cases>
known_blind_spots:
  - <understood failure mode>
propagated_uncertainty: <how scorer error widens headline intervals>
revalidation_triggers:
  - rubric change
  - scorer version bump
  - judge model change
  - production distribution shift
```

## The goal

Not to prove a scorer perfect. To establish that, for a specific product context and
decision, it tracks the distinctions the team cares about, **fails in understood ways**,
and is robust enough to be useful. That is what turns a convenient score into a
defensible measurement. `[guide §7.2]`
