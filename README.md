# eval-library

A library of Claude Code skills for running and analyzing evals in Braintrust.

## Skills

- **[braintrust-eval](braintrust-eval/)** — Run an independent, end-to-end eval in Braintrust: from a plain-English idea to a scored, compared experiment (dataset sourcing, scorer design, hygienic experiment runs).
- **[bt-analyze-eval-results](bt-analyze-eval-results/)** — Turn eval results into a defensible ship / no-ship decision: confidence intervals, run-to-run variance, subgroup breakdowns, paired comparisons, and a stats-grounded release gate.
- **[braintrust-graph-styles](braintrust-graph-styles/)** — Apply Braintrust brand colors, typography, and styling to matplotlib/seaborn graphs when generating, restyling, or auditing data visualizations.

Each skill is a directory containing a `SKILL.md` (and any supporting `references/` or `scripts/`). Drop a skill directory into `~/.claude/skills/` to use it.

## Examples

- **[rag-only-enforcement](rag-only-enforcement/)** — A runnable end-to-end eval (not a skill): does behavior-based scoring catch what `test_passed` misses when a coding agent is given a "locate code via vector search only" rule? Four enforcement variants over SWE-bench Django tasks, with output and behavior scorers side by side.
