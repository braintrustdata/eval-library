# eval-library

Agent Skills for evaluating LLM applications and agents, built around [Braintrust](https://www.braintrust.dev).

Most eval tooling helps you *run* an eval. The harder problem is knowing whether the
result means anything — whether the dataset represents your users, whether the judge
agrees with a human, whether a 3-point gain survives run-to-run noise, and whether the
claim you are about to publish is one the design supports.

This library encodes that as **24 skills**: one per stage of the eval lifecycle, each
narrow enough to invoke on its own, each naming the skill that consumes its output next.

## Install

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

Each skill directory is self-contained, so copying works too.

## Start here

**Don't know which one you need?** Invoke `braintrust-plan-agent-eval`. It reads your
project, inventories what already exists, and names the *earliest* missing artifact —
which is usually not the one you were about to build.

**Want to just run an eval?** `braintrust-eval` takes you from "I want to eval X" to a
scored, compared experiment, with approval gates before anything costs money.

**Already have results and want to know if they're real?**
`braintrust-analyze-eval-experiment`.

## Compatibility

Skills follow the [Agent Skills open standard](https://agentskills.io), so they work in
Claude Code, Codex CLI, and other tools that adopted it.

They assume Braintrust as the platform. The methodology in each card is
platform-independent; the `Braintrust` section at the end is where the platform-specific
mechanics live.

---

## What's covered

Twenty-four skills, grouped by lifecycle stage. Full catalog with descriptions, plus the
routing tables for choosing between them, in **[skills/README.md](skills/README.md)**.

| Stage | Covers |
| --- | --- |
| **Workflow** | Running an eval end to end against a live project |
| **Foundation** | Planning, trace instrumentation, behavior specs |
| **What to measure** | Objectives, metric bundles, evidence maps |
| **Human knowledge** | Eliciting criteria from experts, review workflows and golden sets |
| **Datasets** | Sourcing, sampling, label audits, splits, sizing and power |
| **Scorers** | Writing one, validating it against humans, deploying it to live traffic |
| **Experiments** | Design, analysis, multi-variable attribution, release gates |
| **Diagnostics** | Capability and variability probes, failure discovery, topics, red teaming |
| **Reporting** | Calibrated writeups, production monitoring |

## Examples

Runnable evals built with these skills, in [examples/](examples/):

- **[rag-only-enforcement](examples/rag-only-enforcement/)** — Does behavior-based scoring catch what `test_passed` misses when a coding agent is told to locate code via vector search only? Four enforcement variants over SWE-bench Django tasks, with output and behavior scorers side by side.

## Contributing

Adding a skill or an example: [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Apache 2.0](LICENSE).
