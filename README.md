# Eval Library

Open eval methodology, published datasets, runnable studies, and the skills to design good evals of your own.

This repository has two parts:

- **[Evals](examples/)** — original, open-source studies of models and agents on real tasks. Each example includes the dataset or the code to build it, the task, the scorers, and a harness you can run.
- **[Skills](skills/)** — practical eval methods packaged as plain `SKILL.md` files your coding agent can use. They cover the work around the run itself: deciding what to measure, building representative datasets, validating judges, analyzing results, finding failures, and setting release gates.

The goal is not just to produce a score. It is to produce evidence you can inspect, challenge, and use to make a decision.

## Original, open-source evals

Read the methodology and results, inspect the data, or rerun a study on your own setup.

### GLM-5.2 long-context retrieval

Do open-source models fall apart once the context gets long? This eval gives GLM-5.2 mechanically generated questions over 25K and 50K tokens of CPython source, then grades each answer against AST-derived ground truth.

| Context | AST semantic match | Mean cost/trace |
| --- | ---: | ---: |
| 25K tokens | 83.3% | $0.0208 |
| 50K tokens | 84.5% | $0.0415 |

[Read the methodology, inspect the results, and run the eval →](examples/glm-5.2-long-context/)

### RAG-only enforcement for coding agents

Can a coding agent pass the tests while breaking an important process rule? This eval runs real SWE-bench Django tasks under four search-enforcement setups and scores both the patch and the agent's behavior.

[Inspect the dataset, behavior spec, hooks, and eval harness →](examples/rag-only-enforcement/)

[See all evals →](examples/)

## Run evals like this

Each skill packages a focused eval method into instructions your coding agent can read. Point your agent at a skill, then ask it to do what the skill describes: validate a judge against expert labels, build a representative dataset, investigate hidden failure modes, or analyze whether a model change is real.

### Start here

- **Planning an eval?** Use [`braintrust-plan-agent-eval`](skills/braintrust-plan-agent-eval/). It inventories what already exists and finds the earliest missing piece.
- **Ready to run?** Use [`braintrust-eval`](skills/braintrust-eval/). It takes a live project through setup, smoke tests, scoring, comparison, and logging.
- **Already have results?** Use [`braintrust-analyze-eval-experiment`](skills/braintrust-analyze-eval-experiment/). It checks run integrity, uncertainty, paired differences, subgroups, and fragility.
- **Not sure whether the scorer is trustworthy?** Use [`braintrust-validate-eval-scorer`](skills/braintrust-validate-eval-scorer/). It tests agreement with expert-reviewed reference data and looks for dangerous shortcuts.

[Browse all 24 skills →](skills/)

## Install the skills

```bash
git clone https://github.com/braintrustdata/eval-library.git

# Claude Code
mkdir -p ~/.claude/skills
for d in eval-library/skills/braintrust-*/; do
  ln -sfn "$(cd "$d" && pwd)" ~/.claude/skills/"$(basename "$d")"
done

# Codex CLI
mkdir -p ~/.codex/skills
for d in eval-library/skills/braintrust-*/; do
  ln -sfn "$(cd "$d" && pwd)" ~/.codex/skills/"$(basename "$d")"
done
```

Each skill directory is self-contained, so copying one directory works too.

Skills follow the [Agent Skills open standard](https://agentskills.io) and work in Claude Code, Codex CLI, and other compatible agents. The methodology is platform-independent; sections labeled `Braintrust` contain the product-specific mechanics.

## What the skills cover

| Stage | What you can do |
| --- | --- |
| **Run** | Execute an eval end to end against a live project |
| **Frame** | Define the decision, behavior, instrumentation, and evidence you need |
| **Build data** | Source, sample, label, audit, split, size, and refresh datasets |
| **Score** | Write narrow scorers, validate them against people, and deploy them safely |
| **Experiment** | Design comparisons, analyze uncertainty, attribute changes, and set gates |
| **Investigate** | Probe capability and variability, discover failures, cluster traces, and red-team agents |
| **Operate** | Report claims at the strength the evidence supports and monitor production behavior |

## Contributing

Have an eval with a result worth sharing, or a method that would help someone avoid a common eval mistake? See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Apache 2.0](LICENSE).
