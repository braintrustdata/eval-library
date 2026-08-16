#!/usr/bin/env python3
"""
Generate dataset entries from SWE-bench Lite (Django tasks).

This script:
1. Pulls Django tasks from the princeton-nlp/SWE-bench_Lite HuggingFace dataset
2. Filters for manageable tasks (small patches, clear test cases)
3. Outputs dataset entries compatible with run_eval.py

Usage:
    uv run python generate_swebench_dataset.py                    # Generate 25 Django tasks
    uv run python generate_swebench_dataset.py -n 10              # Generate 10 tasks
    uv run python generate_swebench_dataset.py -o my_dataset.json # Custom output file
    uv run python generate_swebench_dataset.py --version 3.0      # Filter by Django version
"""

import json
from pathlib import Path

import click


def load_swebench_django(version: str = None) -> list[dict]:
    """Load Django tasks from SWE-bench Lite."""
    from datasets import load_dataset

    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    django = [x for x in ds if x["repo"] == "django/django"]

    if version:
        django = [x for x in django if x["version"] == version]

    return django


def filter_tasks(tasks: list[dict], max_patch_files: int = 5) -> list[dict]:
    """Filter tasks to find good candidates for evaluation.

    Criteria:
    - Patch modifies a reasonable number of files (not too many)
    - Has clear FAIL_TO_PASS tests
    - Problem statement is descriptive enough
    """
    good = []
    for task in tasks:
        # Parse FAIL_TO_PASS
        fail_to_pass = json.loads(task["FAIL_TO_PASS"])
        if not fail_to_pass:
            continue

        # Check patch size (count files modified)
        patch = task.get("patch", "")
        patch_files = [
            line.split(" b/")[1] if " b/" in line else ""
            for line in patch.split("\n")
            if line.startswith("diff --git")
        ]
        patch_files = [f for f in patch_files if f]

        if len(patch_files) < 1 or len(patch_files) > max_patch_files:
            continue

        # Check problem statement is substantial
        if len(task.get("problem_statement", "")) < 100:
            continue

        task["_patch_files"] = patch_files
        task["_fail_to_pass"] = fail_to_pass
        task["_pass_to_pass"] = json.loads(task.get("PASS_TO_PASS", "[]"))
        good.append(task)

    return good


def derive_test_command(fail_to_pass: list[str], task: dict) -> str:
    """Derive a Django test command from FAIL_TO_PASS test names.

    SWE-bench test names look like:
    - "test_foo (app.tests.TestClass)" -> module is "app"
    - "app.tests.test_module" -> module is "app"

    Django tests are run via: python tests/runtests.py --parallel 1 <module>
    """
    # Extract unique top-level test modules
    test_modules = set()
    for test_name in fail_to_pass:
        if "(" in test_name:
            # Format: "test_method (module.path.TestClass)"
            _, class_path = test_name.split(" (")
            class_path = class_path.rstrip(")")
            # Top-level module: e.g., "test_utils.tests.Foo" -> "test_utils"
            test_modules.add(class_path.split(".")[0])
        else:
            test_modules.add(test_name.split(".")[0])

    modules_str = " ".join(sorted(test_modules))
    return f"PYTHONPATH=. python3 tests/runtests.py --parallel 1 {modules_str}"


def make_dataset_entry(task: dict) -> dict:
    """Convert a SWE-bench task to our eval dataset format."""
    instance_id = task["instance_id"]
    # Convert django__django-10914 -> django-10914
    short_id = instance_id.replace("django__django-", "django-")

    fail_to_pass = task["_fail_to_pass"]
    pass_to_pass = task["_pass_to_pass"]

    return {
        "id": short_id,
        "repo_url": "https://github.com/django/django",
        "instance_id": instance_id,
        "commit_before": task["base_commit"],
        "version": task["version"],
        "prompt": task["problem_statement"],
        "test_patch": task["test_patch"],
        "gold_patch": task["patch"],
        "fail_to_pass": fail_to_pass,
        "pass_to_pass": pass_to_pass,
        "test_command": derive_test_command(fail_to_pass, task),
        "patch_files": task["_patch_files"],
        # Compatibility fields for run_eval.py
        "test_files": [],
        "expected_fix_file": task["_patch_files"][0] if task["_patch_files"] else "",
        "expected_fix_line": 0,
    }


@click.command()
@click.option("-n", "--count", default=25, help="Number of dataset entries to generate")
@click.option("-o", "--output", default="dataset_swebench.json", help="Output file")
@click.option("--version", default=None, help="Filter by Django version (e.g., 3.0, 3.1)")
@click.option(
    "--max-patch-files",
    default=5,
    help="Maximum number of files in the gold patch (filters out huge PRs)",
)
def main(count: int, output: str, version: str, max_patch_files: int):
    """Generate SWE-bench Django dataset for eval."""
    print("Loading SWE-bench Lite dataset...")
    tasks = load_swebench_django(version)
    print(f"Found {len(tasks)} Django tasks" + (f" (version {version})" if version else ""))

    print("Filtering for good candidates...")
    filtered = filter_tasks(tasks, max_patch_files=max_patch_files)
    print(f"Filtered to {len(filtered)} candidates")

    if not filtered:
        print("No suitable tasks found!")
        return

    # Take the requested count
    selected = filtered[:count]
    entries = [make_dataset_entry(t) for t in selected]

    print(f"\nGenerated {len(entries)} dataset entries:")
    for entry in entries:
        ftp_count = len(entry["fail_to_pass"])
        files_count = len(entry["patch_files"])
        print(f"  {entry['id']} (v{entry['version']}) - {ftp_count} fail_to_pass tests, {files_count} patch files")

    # Write output
    output_path = Path(output)
    with open(output_path, "w") as f:
        json.dump(entries, f, indent=2)

    print(f"\nWrote dataset to {output_path}")


if __name__ == "__main__":
    main()
