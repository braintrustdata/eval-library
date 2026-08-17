#!/usr/bin/env python3
"""Build deterministic long-context retrieval rows from a CPython 3.13 Lib tree."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import tiktoken

QUESTION_DIFFICULTY = {
    "RT": "easy",
    "CL": "easy",
    "BC": "easy",
    "FC": "hard",
    "DC": "hard",
    "DS": "hard",
}
EXCLUDED_PARTS = {"test", "tests", "__pycache__", ".venv", "venv", ".git", "node_modules"}
PINNED_CPYTHON_VERSION = "3.13.5"


@dataclass(frozen=True)
class Candidate:
    question_type: str
    question: str
    expected: str
    source_file: str
    source_line: int
    ast_node_type: str
    function_name: str | None = None
    definition_prefix: str | None = None

    @property
    def difficulty(self) -> str:
        return QUESTION_DIFFICULTY[self.question_type]


def collect_python_files(lib_path: Path) -> list[Path]:
    return [
        path
        for path in sorted(lib_path.rglob("*.py"))
        if not any(part in EXCLUDED_PARTS or part.startswith(".") for part in path.parts)
    ]


def validate_cpython_version(lib_path: Path) -> str:
    patchlevel = lib_path.parent / "Include" / "patchlevel.h"
    if not patchlevel.is_file():
        raise ValueError(
            f"{lib_path} does not look like a CPython source checkout "
            "(Include/patchlevel.h is missing)"
        )
    match = re.search(r'^#define PY_VERSION "([^"]+)"', patchlevel.read_text(), re.MULTILINE)
    if not match:
        raise ValueError(f"Could not read the CPython version from {patchlevel}")
    version = match.group(1)
    if version != PINNED_CPYTHON_VERSION:
        raise ValueError(
            f"Expected CPython {PINNED_CPYTHON_VERSION}, found {version}. "
            "Use the pinned v3.13.5 tag so the generated answer key is reproducible."
        )
    return version


def build_corpus(lib_path: Path, files: list[Path], token_budget: int) -> tuple[str, str]:
    encoding = tiktoken.get_encoding("cl100k_base")
    chunks: list[str] = []
    used = 0
    for path in files:
        text = f"\n# === {path.relative_to(lib_path)} ===\n" + path.read_text(
            encoding="utf-8", errors="replace"
        )
        tokens = encoding.encode(text)
        remaining = token_budget - used
        if remaining <= 0:
            break
        if len(tokens) > remaining:
            break
        chunks.append(text)
        used += len(tokens)
    corpus = "".join(chunks)
    return corpus, hashlib.sha256(corpus.encode()).hexdigest()


def corpus_files(corpus: str) -> set[str]:
    return {
        line.removeprefix("# === ").removesuffix(" ===")
        for line in corpus.splitlines()
        if line.startswith("# === ") and line.endswith(" ===")
    }


def unparse(node: ast.AST | None) -> str:
    return ast.unparse(node) if node is not None else "None"


def module_name(relative_path: Path) -> str:
    parts = list(relative_path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def extract_candidates(lib_path: Path, files: list[Path]) -> list[Candidate]:
    candidates: list[Candidate] = []
    for path in files:
        relative = path.relative_to(lib_path)
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        module = module_name(relative)
        module_functions = [
            node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        candidates.append(
            Candidate(
                "FC",
                f"How many functions are defined at module level in {module}?",
                str(len(module_functions)),
                str(relative),
                1,
                "Module.FunctionDef.count",
            )
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = ", ".join(unparse(base) for base in node.bases) or "object"
                candidates.extend(
                    [
                        Candidate(
                            "CL",
                            f"In which file is class {node.name} defined?",
                            str(relative),
                            str(relative),
                            node.lineno,
                            "ClassDef.location",
                        ),
                        Candidate(
                            "BC",
                            f"What base classes does {node.name} inherit from?",
                            bases,
                            str(relative),
                            node.lineno,
                            "ClassDef.bases",
                        ),
                    ]
                )

            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            return_type = unparse(node.returns)
            if return_type != "None":
                candidates.append(
                    Candidate(
                        "RT",
                        f"What return type does {node.name} in {module} declare?",
                        return_type,
                        str(relative),
                        node.lineno,
                        "FunctionDef.returns",
                        node.name,
                        prefix,
                    )
                )
            decorators = ", ".join(unparse(item) for item in node.decorator_list)
            if decorators:
                candidates.append(
                    Candidate(
                        "DC",
                        f"What decorators are applied to {node.name} in {module}?",
                        decorators,
                        str(relative),
                        node.lineno,
                        "FunctionDef.decorator_list",
                        node.name,
                        prefix,
                    )
                )
            docstring = ast.get_docstring(node, clean=False)
            first_line = (
                docstring.strip().splitlines()[0].strip()
                if docstring and docstring.strip()
                else ""
            )
            if first_line:
                candidates.append(
                    Candidate(
                        "DS",
                        f"What is the first line of the docstring for {node.name} in {module}?",
                        first_line,
                        str(relative),
                        node.lineno,
                        "FunctionDef.docstring.first_line",
                        node.name,
                        prefix,
                    )
                )
    return candidates


def sample(
    candidates: list[Candidate], rows: int, easy_ratio: float, rng: random.Random
) -> list[Candidate]:
    easy_count = round(rows * easy_ratio)
    pools = {
        "easy": [candidate for candidate in candidates if candidate.difficulty == "easy"],
        "hard": [candidate for candidate in candidates if candidate.difficulty == "hard"],
    }
    targets = {"easy": easy_count, "hard": rows - easy_count}
    selected: list[Candidate] = []
    for difficulty, pool in pools.items():
        if len(pool) < targets[difficulty]:
            raise ValueError(
                f"Need {targets[difficulty]} {difficulty} candidates; found {len(pool)}"
            )
        selected.extend(rng.sample(pool, targets[difficulty]))
    rng.shuffle(selected)
    return selected


def make_rows(
    selected: list[Candidate], corpus: str, tier: str, perturbations: int, rng: random.Random
) -> list[dict]:
    rows: list[dict] = []
    perturbable = [index for index, item in enumerate(selected) if item.function_name]
    rng.shuffle(perturbable)
    perturbable = perturbable[:perturbations]

    for index, candidate in enumerate(selected, 1):
        context = corpus
        question = candidate.question
        metadata = {
            "question_id": f"{tier}_{index:03d}",
            "question_type": candidate.question_type,
            "difficulty": candidate.difficulty,
            "source_file": candidate.source_file,
            "source_line": candidate.source_line,
            "ast_node_type": candidate.ast_node_type,
            "is_perturbation": False,
        }
        if index - 1 in perturbable:
            old = candidate.function_name
            new = f"{old}_v2"
            signature = f"{candidate.definition_prefix} {old}("
            if signature in context:
                context = context.replace(signature, f"{candidate.definition_prefix} {new}(", 1)
                question = question.replace(old, new)
                metadata["is_perturbation"] = True
                metadata["perturbation"] = {"old_symbol": old, "new_symbol": new}
        rows.append(
            {
                "input": {
                    "question": question,
                    "context": context,
                    "tier": tier,
                    "question_type": candidate.question_type,
                    "ast_node_type": candidate.ast_node_type,
                },
                "expected": candidate.expected,
                "metadata": metadata,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lib-path", type=Path, required=True, help="CPython 3.13.5 Lib directory")
    parser.add_argument("--tier", choices=("T25", "T50"), default="T25")
    parser.add_argument("--rows", type=int, default=100)
    parser.add_argument("--easy-ratio", type=float, default=0.6)
    parser.add_argument("--perturbations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if not 0 < args.easy_ratio < 1:
        raise ValueError("--easy-ratio must be between 0 and 1")
    if args.rows <= 0 or args.perturbations < 0:
        raise ValueError("--rows must be positive and --perturbations cannot be negative")
    lib_path = args.lib_path.resolve()
    if not lib_path.is_dir():
        raise FileNotFoundError(lib_path)
    cpython_version = validate_cpython_version(lib_path)

    budget = {"T25": 25_000, "T50": 50_000}[args.tier]
    files = collect_python_files(lib_path)
    corpus, corpus_sha = build_corpus(lib_path, files, budget)
    included = corpus_files(corpus)
    candidates = [
        item for item in extract_candidates(lib_path, files) if item.source_file in included
    ]
    rng = random.Random(args.seed)
    selected = sample(candidates, args.rows, args.easy_ratio, rng)
    rows = make_rows(selected, corpus, args.tier, args.perturbations, rng)

    output = args.output or Path("datasets") / f"cpython-stdlib-{args.tier}.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "dataset_version": f"cpython-v{cpython_version}-seed-{args.seed}",
        "cpython_ref": f"v{cpython_version}",
        "tier": args.tier,
        "token_budget": budget,
        "tokenizer": "cl100k_base",
        "seed": args.seed,
        "row_count": len(rows),
        "corpus_sha256": corpus_sha,
        "question_type_counts": Counter(row["metadata"]["question_type"] for row in rows),
        "candidate_schema": list(asdict(selected[0]).keys()) if selected else [],
    }
    output.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
