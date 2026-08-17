#!/usr/bin/env python3
"""Run the GLM-5.2 long-context retrieval eval and log it to Braintrust."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from scorers import ASTSemanticMatch, SubstringMatch, make_factuality_judge

load_dotenv()

PROJECT_NAME = "GLM-5.2 Long-Context Retrieval"
MODEL = "zai-org/GLM-5.2"
BASETEN_BASE_URL = "https://inference.baseten.co/v1"
SYSTEM_PROMPT = (
    "You are a code analysis assistant. "
    "Answer strictly from the provided code. Be concise—one line."
)


def load_dataset(path: Path, limit: int | None) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not {"input", "expected"} <= row.keys():
                raise ValueError(f"Invalid eval row at {path}:{line_number}")
            rows.append(row)
            if limit is not None and len(rows) >= limit:
                break
    if not rows:
        raise ValueError(f"No eval rows found in {path}")
    return rows


def load_manifest(dataset_path: Path) -> dict:
    path = dataset_path.with_suffix(".manifest.json")
    return json.loads(path.read_text()) if path.is_file() else {}


def numeric_metrics(metrics: dict[str, Any]) -> dict[str, float | int]:
    return {
        key: value
        for key, value in metrics.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def make_task(api_key: str, repetitions: int):
    from braintrust import start_span, wrap_openai
    from openai import AsyncOpenAI

    client = wrap_openai(
        AsyncOpenAI(
            api_key=api_key,
            base_url=BASETEN_BASE_URL,
            max_retries=6,
            timeout=300,
        )
    )

    async def task(input: dict, hooks=None) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"[CONTEXT]\n{input['context']}\n\n[QUESTION]\n{input['question']}",
            },
        ]
        runs = []
        for run_number in range(1, repetitions + 1):
            with start_span(name=f"llm-call-run-{run_number}") as span:
                started = time.monotonic()
                first_token_at = None
                answer = ""

                async def collect() -> None:
                    nonlocal answer, first_token_at
                    stream = await client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        temperature=0,
                        max_tokens=128,
                        stream=True,
                        stream_options={"include_usage": True},
                    )
                    async for chunk in stream:
                        content = chunk.choices[0].delta.content if chunk.choices else None
                        if content:
                            first_token_at = first_token_at or time.monotonic()
                            answer += content

                await asyncio.wait_for(collect(), timeout=180)
                total_ms = (time.monotonic() - started) * 1000
                ttft_ms = (first_token_at - started) * 1000 if first_token_at else None
                first_ttft = runs[0]["ttft_ms"] if runs else None
                cache_hit_heuristic = bool(
                    run_number > 1
                    and ttft_ms is not None
                    and first_ttft is not None
                    and ttft_ms < first_ttft * 0.3
                )
                span.log(
                    metrics=numeric_metrics({"ttft_ms": ttft_ms, "total_latency_ms": total_ms}),
                    metadata={
                        "model": MODEL,
                        "run_number": run_number,
                        "run_kind": "cold" if run_number == 1 else "warm",
                        "cache_hit_heuristic": cache_hit_heuristic,
                    },
                )
                runs.append(
                    {
                        "answer": answer.strip(),
                        "ttft_ms": ttft_ms,
                        "total_latency_ms": total_ms,
                    }
                )

        if hooks is not None and getattr(hooks, "metadata", None) is not None:
            hooks.metadata["latency_runs"] = runs
        return runs[0]["answer"]

    return task


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path, default=Path("datasets/cpython-stdlib-T25.jsonl")
    )
    parser.add_argument("--limit", type=int, help="Run only the first N rows")
    parser.add_argument("--trial-count", type=int, default=1)
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Sequential calls per row; only the first answer is scored",
    )
    parser.add_argument("--judge", action="store_true", help="Add the Baseten-hosted LLM judge")
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit must be positive")
    if args.trial_count <= 0 or args.repetitions <= 0:
        raise ValueError("--trial-count and --repetitions must be positive")

    rows = load_dataset(args.dataset, args.limit)
    manifest = load_manifest(args.dataset)
    tier = rows[0]["input"].get("tier", "unknown")
    experiment_name = f"glm-5.2-{tier}"
    if args.dry_run:
        print(
            f"Validated {len(rows)} rows; would run {experiment_name} with "
            f"trial_count={args.trial_count}, repetitions={args.repetitions}, judge={args.judge}"
        )
        return

    missing = [name for name in ("BRAINTRUST_API_KEY", "BASETEN_API_KEY") if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    from braintrust import Eval

    api_key = os.environ["BASETEN_API_KEY"]
    scores = [ASTSemanticMatch, SubstringMatch]
    if args.judge:
        scores.append(make_factuality_judge(api_key, BASETEN_BASE_URL))

    Eval(
        PROJECT_NAME,
        experiment_name=experiment_name,
        data=rows,
        task=make_task(api_key, args.repetitions),
        scores=scores,
        trial_count=args.trial_count,
        max_concurrency=1,
        update=args.update,
        metadata={
            "model": MODEL,
            "provider": "baseten",
            "dataset_version": manifest.get("dataset_version", "unknown"),
            "corpus_sha256": manifest.get("corpus_sha256", "unknown"),
            "tier": tier,
            "sequential_calls_per_row": args.repetitions,
        },
    )


if __name__ == "__main__":
    main()
