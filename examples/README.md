# Open evals you can inspect and run

Original studies of models and agents on real tasks. Every example publishes the methodology and the code behind the result: dataset or dataset builder, task, scorers, and runnable harness.

Use them three ways:

- **Read the result** to understand what changed and where the conclusion holds.
- **Inspect the method** to see how the dataset, scoring, controls, and traces fit together.
- **Run it yourself** against the published setup or adapt it to your own models and data.

## Studies

### GLM-5.2 long-context retrieval

Do open-source models fall apart once the context gets long? We ask GLM-5.2 exact, machine-checkable questions over 25K and 50K tokens of CPython source. Questions and answer keys come from the AST, and perturbation rows change the supplied source to test retrieval instead of memorization.

| Context | AST semantic match | Substring match | Mean cost/trace |
| --- | ---: | ---: | ---: |
| 25K tokens | 83.3% | 76.7% | $0.0208 |
| 50K tokens | 84.5% | 76.5% | $0.0415 |

**What is included:** deterministic dataset generation, question-aware scorers, an optional audit judge, repeated-prefix latency traces, and published aggregate results.

[Open the GLM-5.2 eval →](glm-5.2-long-context/)

### RAG-only enforcement for coding agents

Can a coding agent produce a correct patch while ignoring a rule about how it must find the code? We run 30 real SWE-bench Django tasks under four enforcement conditions, from an unconstrained baseline to hook-based lockdown, and compare output scores with behavior scores over the trajectory.

**What is included:** the 30-task dataset, behavior specification, deterministic trajectory scorer, LLM behavior judge, Claude Code hooks, vector-search tool, and full eval harness.

[Open the RAG-only enforcement eval →](rag-only-enforcement/)

## Run an eval

Each study has its own setup and smoke-test command. You will generally need a Python environment and `BRAINTRUST_API_KEY`; provider credentials and agent runtimes vary by study.

These evals call models and may cost money. Start with the documented smoke path, inspect the expected number of rows, trials, and model calls, then scale up.

## Add a study

A useful example does more than demonstrate an SDK call. It answers a real question and exposes the evidence behind the answer: a scoring approach that is hard to picture from prose, a control that changes the conclusion, a harness pattern worth reusing, or a result that challenges an intuition.

1. Keep the study in one self-contained directory.
2. State the question, method, result, limitations, setup, and exact commands in its `README.md`.
3. Pin the models, dataset version, configuration, and date needed to reproduce the claim.
4. Include the dataset or a deterministic builder. Publish compact results when the raw artifacts are too large.
5. Include no credentials or absolute paths from your machine.
6. Add the study here and to the root [README](../README.md).

Full contributor rules are in [CONTRIBUTING.md](../CONTRIBUTING.md).
