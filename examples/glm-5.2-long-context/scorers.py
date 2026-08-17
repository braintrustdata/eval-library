"""Deterministic scorers for AST-derived long-context retrieval questions."""

from __future__ import annotations

import re
from typing import Any


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).lower().strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_type(value: str) -> str:
    return _normalize(value).strip("'\"")


def _normalize_path(value: str) -> str:
    value = _normalize(value).replace("\\", "/")
    for prefix in ("cpython-3.13/lib/", "lib/"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    return value


def _contains_phrase(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    return re.search(rf"(?<![a-z0-9_]){re.escape(needle)}(?![a-z0-9_])", haystack) is not None


def _question_type(input: dict) -> str | None:
    explicit = str(input.get("question_type", "")).upper()
    if explicit in {"RT", "CL", "BC", "FC", "DC", "DS"}:
        return explicit
    question = _normalize(input.get("question"))
    prefixes = {
        "what return type does ": "RT",
        "in which file is class ": "CL",
        "what base classes does ": "BC",
        "how many functions are defined at module level in ": "FC",
        "what decorators are applied to ": "DC",
        "what is the first line of the docstring for ": "DS",
    }
    return next((kind for prefix, kind in prefixes.items() if question.startswith(prefix)), None)


def _optional_to_union(value: str) -> str:
    return re.sub(r"optional\[(.+)\]", r"\1 | none", _normalize_type(value))


def ASTSemanticMatch(input: dict, output: Any, expected: Any) -> dict:
    """Score answers according to the semantics of each AST question family."""
    actual = _normalize(output)
    target = _normalize(expected)
    kind = _question_type(input)
    if not actual or not target:
        return {"name": "ASTSemanticMatch", "score": 0.0}

    if kind == "FC":
        actual_number = re.search(r"\b\d+\b", actual)
        target_number = re.search(r"\b\d+\b", target)
        passed = bool(
            actual_number and target_number and actual_number.group() == target_number.group()
        )
    elif kind == "CL":
        passed = _contains_phrase(_normalize_path(actual), _normalize_path(target))
    elif kind in {"BC", "DC"}:
        terms = [_normalize_type(part) for part in re.split(r"[,;]", target) if part.strip()]
        passed = bool(terms) and all(_contains_phrase(actual, term) for term in terms)
    elif kind == "RT":
        passed = _contains_phrase(_optional_to_union(actual), _optional_to_union(target))
    else:
        passed = target in actual if len(target) > 6 else _contains_phrase(actual, target)

    return {"name": "ASTSemanticMatch", "score": float(passed)}


def SubstringMatch(input: dict, output: Any, expected: Any) -> dict:
    """Lenient diagnostic: does the normalized answer contain the expected text?"""
    del input
    actual = _normalize(output)
    target = _normalize(expected)
    passed = bool(target) and (
        target in actual if len(target) > 6 else _contains_phrase(actual, target)
    )
    return {"name": "SubstringMatch", "score": float(passed)}


FACTUALITY_PROMPT = """\
You are evaluating a code-analysis answer for an AST-derived question.

Question type: {{input.question_type}}
Question: {{input.question}}
Expected (ground truth from an AST parse): {{expected}}
Model answer: {{output}}

Score 1.0 for a semantically correct answer, 0.5 for a partially correct answer, and
0.0 for a wrong or unsupported answer. For function counts require exact equality; for
paths allow harmless prefixes; for lists require every expected item, in any order; and
for return types allow equivalent PEP 604 syntax.

Respond with only 1.0, 0.5, or 0.0 followed by one sentence of justification.\
"""


def make_factuality_judge(api_key: str, base_url: str):
    """Build the audit judge used in the published benchmark."""
    from autoevals import LLMClassifier

    return LLMClassifier(
        name="FactualityJudge",
        prompt_template=FACTUALITY_PROMPT,
        choice_scores={"1.0": 1.0, "0.5": 0.5, "0.0": 0.0},
        model="nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B",
        use_cot=False,
        api_key=api_key,
        base_url=base_url,
    )
