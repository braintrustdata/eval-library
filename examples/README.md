# examples/

Runnable evals built with the skills in [../skills/](../skills/) — dataset, task,
scorers, and a harness you can execute, not snippets.

## What's here

| Example | Question it answers | Techniques on display |
| --- | --- | --- |
| **[glm-5.2-long-context](glm-5.2-long-context/)** | Can GLM-5.2 retrieve exact facts from 25K–50K tokens of code, and how do cold and warm latencies differ? | AST-derived ground truth, perturbation controls, question-aware deterministic scoring, repeated-prefix latency spans |
| **[rag-only-enforcement](rag-only-enforcement/)** | Does behavior-based scoring catch what `test_passed` misses when a coding agent is told to find code by vector search only? | Behavior scorers vs. output scorers, four enforcement variants, SWE-bench-derived dataset, subprocess agent tracing, hook-based tool gating |

## Running one

Each example carries its own README with setup and commands. You will need a Braintrust
API key (`BRAINTRUST_API_KEY`) and a Python environment; dependencies differ per example.

**These cost money to run** — they call models, sometimes many times per row. Check the
example's README for scale first, and use the smoke path where one is offered.

## Adding an example

An example earns its place by demonstrating something a skill card can only describe.
Good candidates: a scoring approach that is hard to picture from prose, a harness pattern
worth copying, a result that contradicts an intuition.

1. One directory, self-contained, with its own `README.md` covering the question, the
   setup, the commands, and what the results showed.
2. Pin what a reader needs to reproduce it — models, dataset version, date.
3. No credentials, and no absolute paths from your machine.
4. Add a row to the table above, and link it from the Examples section of the root
   [README](../README.md).
