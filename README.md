# eval-library

A library of Claude Code skills for running and analyzing evals in Braintrust.

## Skills

- **[braintrust-eval](braintrust-eval/)** — Run an independent, end-to-end eval in Braintrust: from a plain-English idea to a scored, compared experiment (dataset sourcing, scorer design, hygienic experiment runs).
- **[bt-analyze-eval-results](bt-analyze-eval-results/)** — Turn eval results into a defensible ship / no-ship decision: confidence intervals, run-to-run variance, subgroup breakdowns, paired comparisons, and a stats-grounded release gate.

Each skill is a directory containing a `SKILL.md` (and any supporting `references/`). Drop a skill directory into `~/.claude/skills/` to use it.
