#!/usr/bin/env python3
"""
Content-addressable vector search over a codebase using ChromaDB + OpenAI embeddings.

This implementation uses content hashing to enable efficient per-commit indexing:
- Each code chunk is hashed by its content
- Embeddings are cached globally by content hash
- Per-commit indexes just reference the cached embeddings
- Unchanged files across commits reuse the same embeddings

Usage:
    # Index a repository at a specific commit
    uv run python vector_search.py index /path/to/repo --commit abc123

    # Search a repository at a specific commit
    uv run python vector_search.py search --repo /path/to/repo --commit abc123 "your query here"

    # Pre-index multiple commits (for eval)
    uv run python vector_search.py preindex /path/to/repo commit1 commit2 commit3
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
import numpy as np

# Default paths
CACHE_DIR = Path.home() / ".cache" / "agent-search-eval" / "vector_cache"
EMBEDDINGS_CACHE_DIR = CACHE_DIR / "embeddings"  # Global content-addressed embeddings
COMMIT_INDEX_DIR = CACHE_DIR / "commit_indexes"  # Per-commit indexes

# File extensions to index
EXTENSIONS = {".go", ".py"}

# Directories to skip
SKIP_DIRS = {"_submodules", ".git", "testdata", "node_modules", "vendor"}

MAX_CHUNK_CHARS = 6000  # Stay well under 8192 token limit
EMBEDDING_DIM = 1536  # text-embedding-3-small dimension


def get_openai_client():
    """Get OpenAI client for embeddings.
    
    Uses OPENAI_API_KEY if set, otherwise falls back to Braintrust proxy.
    """
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return OpenAI(api_key=api_key)

    # Fall back to Braintrust proxy
    bt_key = os.environ.get("BRAINTRUST_API_KEY")
    if bt_key:
        return OpenAI(
            api_key=bt_key,
            base_url="https://api.braintrust.dev/v1/proxy",
        )

    raise ValueError("Neither OPENAI_API_KEY nor BRAINTRUST_API_KEY is set")


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content for content-addressing."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_repo_name(repo_path: str) -> str:
    """Get a safe repo name for directory naming."""
    repo_name = Path(repo_path).name
    return "".join(c if c.isalnum() else "_" for c in repo_name)


def get_embedding_path(content_hash: str) -> Path:
    """Get path for a cached embedding by content hash."""
    # Use first 2 chars as subdirectory for better filesystem performance
    return EMBEDDINGS_CACHE_DIR / content_hash[:2] / f"{content_hash}.npy"


def get_commit_index_path(repo_path: str, commit: str) -> Path:
    """Get path for a commit's index file."""
    repo_name = get_repo_name(repo_path)
    return COMMIT_INDEX_DIR / repo_name / f"{commit}.json"


def load_embedding(content_hash: str) -> Optional[np.ndarray]:
    """Load a cached embedding by content hash."""
    path = get_embedding_path(content_hash)
    if path.exists():
        return np.load(path)
    return None


def save_embedding(content_hash: str, embedding: np.ndarray):
    """Save an embedding to the cache."""
    path = get_embedding_path(content_hash)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, embedding)


def compute_embeddings_batch(texts: List[str], client) -> List[np.ndarray]:
    """Compute embeddings for a batch of texts using OpenAI API."""
    response = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [np.array(item.embedding) for item in response.data]


def chunk_file(
    filepath: str, repo_path: str, chunk_size: int = 800, overlap: int = 100
) -> List[Dict]:
    """Split a file into overlapping chunks with content hashes."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return []

    if not content.strip():
        return []

    # Get relative path
    rel_path = os.path.relpath(filepath, repo_path)

    chunks = []
    lines = content.split("\n")
    current_chunk = []
    current_size = 0
    chunk_start_line = 1

    for i, line in enumerate(lines, 1):
        current_chunk.append(line)
        current_size += len(line) + 1

        if current_size >= chunk_size:
            chunk_text = "\n".join(current_chunk)
            # Truncate if still too large
            if len(chunk_text) > MAX_CHUNK_CHARS:
                chunk_text = chunk_text[:MAX_CHUNK_CHARS]

            # Content-addressable ID
            content_hash = compute_content_hash(chunk_text)

            chunks.append(
                {
                    "content_hash": content_hash,
                    "text": chunk_text,
                    "metadata": {
                        "filepath": rel_path,
                        "start_line": chunk_start_line,
                        "end_line": i,
                    },
                }
            )
            # Overlap: keep last few lines
            overlap_lines = int(overlap / 50)  # rough estimate
            current_chunk = current_chunk[-overlap_lines:] if overlap_lines > 0 else []
            current_size = sum(len(line) + 1 for line in current_chunk)
            chunk_start_line = i - len(current_chunk) + 1

    # Don't forget the last chunk
    if current_chunk:
        chunk_text = "\n".join(current_chunk)
        if len(chunk_text) > MAX_CHUNK_CHARS:
            chunk_text = chunk_text[:MAX_CHUNK_CHARS]
        content_hash = compute_content_hash(chunk_text)
        chunks.append(
            {
                "content_hash": content_hash,
                "text": chunk_text,
                "metadata": {
                    "filepath": rel_path,
                    "start_line": chunk_start_line,
                    "end_line": len(lines),
                },
            }
        )

    return chunks


def should_skip(path: Path) -> bool:
    """Check if path should be skipped."""
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    return False


def get_current_commit(repo_path: str) -> str:
    """Get the current HEAD commit SHA."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get current commit: {result.stderr}")
    return result.stdout.strip()[:9]  # Short SHA


def checkout_commit(repo_path: str, commit: str):
    """Checkout a specific commit."""
    # First, clean any changes
    subprocess.run(["git", "checkout", "."], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "clean", "-fd"], cwd=repo_path, capture_output=True)
    # Checkout the commit
    result = subprocess.run(
        ["git", "checkout", commit, "--", "."],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to checkout {commit}: {result.stderr}")


@click.group()
def cli():
    """Content-addressable vector search tool for code repositories."""
    pass


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--commit", "-c", default=None, help="Commit to index (default: current HEAD)")
@click.option("--force", "-f", is_flag=True, help="Force re-index even if already indexed")
def index(repo_path: str, commit: str, force: bool):
    """Index a repository at a specific commit.

    REPO_PATH is the path to the repository to index.
    """
    repo_path = os.path.abspath(repo_path)

    # Get or checkout commit
    if commit:
        checkout_commit(repo_path, commit)
        commit_sha = commit
    else:
        commit_sha = get_current_commit(repo_path)

    index_path = get_commit_index_path(repo_path, commit_sha)

    if index_path.exists() and not force:
        print(f"Commit {commit_sha} already indexed at {index_path}")
        return

    print(f"Indexing {repo_path} at commit {commit_sha}...")

    # First, count files to show progress
    print("  Scanning for files...")
    files_to_process = [
        filepath
        for filepath in Path(repo_path).rglob("*")
        if filepath.is_file() and filepath.suffix in EXTENSIONS and not should_skip(filepath)
    ]
    print(f"  Found {len(files_to_process)} files to index")

    # Collect all chunks with progress bar
    from tqdm import tqdm

    all_chunks = []

    for filepath in tqdm(files_to_process, desc="  Chunking files", unit="files"):
        chunks = chunk_file(str(filepath), repo_path)
        all_chunks.extend(chunks)

    print(f"  Total: {len(files_to_process)} files, {len(all_chunks)} chunks")

    # Check which embeddings we need to compute
    chunks_needing_embedding = []
    for chunk in all_chunks:
        if load_embedding(chunk["content_hash"]) is None:
            chunks_needing_embedding.append(chunk)

    cached_count = len(all_chunks) - len(chunks_needing_embedding)
    print(f"  {cached_count} chunks already cached, {len(chunks_needing_embedding)} need embedding")

    # Compute new embeddings in batches (parallel with progress bar)
    if chunks_needing_embedding:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from tqdm import tqdm

        client = get_openai_client()
        batch_size = 20
        max_workers = 8  # Parallel API requests

        # Split into batches
        batches = []
        for i in range(0, len(chunks_needing_embedding), batch_size):
            batches.append(chunks_needing_embedding[i : i + batch_size])

        def process_batch(batch):
            """Process a single batch: compute embeddings and save."""
            texts = [c["text"] for c in batch]
            embeddings = compute_embeddings_batch(texts, client)
            for chunk, embedding in zip(batch, embeddings):
                save_embedding(chunk["content_hash"], embedding)
            return len(batch)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_batch, batch) for batch in batches]
            with tqdm(
                total=len(chunks_needing_embedding),
                desc="  Computing embeddings",
                unit="chunks",
            ) as pbar:
                for future in as_completed(futures):
                    pbar.update(future.result())

    # Save commit index (just content hashes and metadata, not embeddings)
    index_data = {
        "commit": commit_sha,
        "repo_path": repo_path,
        "chunks": [
            {
                "content_hash": c["content_hash"],
                "filepath": c["metadata"]["filepath"],
                "start_line": c["metadata"]["start_line"],
                "end_line": c["metadata"]["end_line"],
            }
            for c in all_chunks
        ],
    }

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w") as f:
        json.dump(index_data, f)

    print(f"Saved index to {index_path}")
    print("Done indexing!")


@cli.command()
@click.argument("query")
@click.option(
    "--repo",
    "-r",
    required=True,
    type=click.Path(exists=True),
    help="Path to the repository to search",
)
@click.option("--commit", "-c", default=None, help="Commit to search (default: current HEAD)")
@click.option("-n", "--num-results", default=10, help="Number of results to return")
def search(query: str, repo: str, commit: str, num_results: int):
    """Search a repository for relevant code.

    QUERY is the search query (e.g., "nil pointer dereference in completions").
    """
    repo_path = os.path.abspath(repo)

    # Get commit
    if commit:
        commit_sha = commit
    else:
        commit_sha = get_current_commit(repo_path)

    index_path = get_commit_index_path(repo_path, commit_sha)

    if not index_path.exists():
        print(
            f"Error: Commit {commit_sha} not indexed. Run 'index {repo_path} --commit {commit_sha}' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load index
    with open(index_path) as f:
        index_data = json.load(f)

    chunks = index_data["chunks"]
    print(f"Searching {len(chunks)} chunks at commit {commit_sha}...")

    # Load embeddings for all chunks
    embeddings = []
    valid_chunks = []
    for chunk in chunks:
        emb = load_embedding(chunk["content_hash"])
        if emb is not None:
            embeddings.append(emb)
            valid_chunks.append(chunk)
        else:
            print(
                f"Warning: Missing embedding for {chunk['content_hash'][:8]}...",
                file=sys.stderr,
            )

    if not embeddings:
        print("Error: No embeddings found!", file=sys.stderr)
        sys.exit(1)

    # Compute query embedding
    client = get_openai_client()
    query_embedding = compute_embeddings_batch([query], client)[0]

    # Compute cosine similarities
    embeddings_matrix = np.vstack(embeddings)
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    embeddings_norm = embeddings_matrix / np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
    similarities = embeddings_norm @ query_norm

    # Get top results
    top_indices = np.argsort(similarities)[::-1][: num_results * 2]  # Get extra for deduping

    # Format results (dedupe by file)
    formatted = []
    seen_files = set()

    for idx in top_indices:
        if len(formatted) >= num_results:
            break

        chunk = valid_chunks[idx]
        filepath = chunk["filepath"]

        # Dedupe by file (keep first/best match per file)
        if filepath not in seen_files:
            seen_files.add(filepath)

            # We need to get the text - load from the file if it exists at this commit
            full_path = Path(repo_path) / filepath
            snippet = ""
            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        start = max(0, chunk["start_line"] - 1)
                        end = min(len(lines), chunk["end_line"])
                        snippet = "".join(lines[start:end])[:500]
                except Exception:
                    snippet = "(could not load snippet)"

            formatted.append(
                {
                    "rank": len(formatted) + 1,
                    "filepath": filepath,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "similarity": float(similarities[idx]),
                    "snippet": snippet,
                }
            )

    # Print results
    print(f"\nTop results for: {query}\n")
    print("-" * 80)
    for r in formatted:
        print(
            f"{r['rank']}. {r['filepath']} (lines {r['start_line']}-{r['end_line']}, sim: {r['similarity']:.3f})"
        )
        print(f"   {r['snippet'][:200]}...")
        print()


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
@click.argument("commits", nargs=-1, required=True)
@click.option("--force", "-f", is_flag=True, help="Force re-index even if already indexed")
def preindex(repo_path: str, commits: tuple, force: bool):
    """Pre-index multiple commits for efficient eval.

    REPO_PATH is the path to the repository.
    COMMITS are the commit SHAs to index.
    """
    repo_path = os.path.abspath(repo_path)

    print(f"Pre-indexing {len(commits)} commits for {repo_path}...")

    # Save current HEAD to restore later
    original_head = get_current_commit(repo_path)

    try:
        for i, commit in enumerate(commits, 1):
            print(f"\n[{i}/{len(commits)}] Indexing commit {commit}...")

            index_path = get_commit_index_path(repo_path, commit)
            if index_path.exists() and not force:
                print("  Already indexed, skipping")
                continue

            # Checkout and index
            checkout_commit(repo_path, commit)

            # Call index logic directly
            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                index,
                [repo_path, "--commit", commit, "--force"]
                if force
                else [repo_path, "--commit", commit],
            )
            if result.exit_code != 0:
                print(f"  Error indexing: {result.output}")
    finally:
        # Restore original HEAD
        print(f"\nRestoring to original HEAD {original_head}...")
        checkout_commit(repo_path, original_head)

    print("\nPre-indexing complete!")


@cli.command()
def stats():
    """Show cache statistics."""
    # Count embeddings
    embedding_count = 0
    embedding_size = 0
    if EMBEDDINGS_CACHE_DIR.exists():
        for npy_file in EMBEDDINGS_CACHE_DIR.rglob("*.npy"):
            embedding_count += 1
            embedding_size += npy_file.stat().st_size

    # Count commit indexes
    index_count = 0
    if COMMIT_INDEX_DIR.exists():
        for json_file in COMMIT_INDEX_DIR.rglob("*.json"):
            index_count += 1

    print("Vector Cache Statistics")
    print("-" * 40)
    print(f"Cached embeddings: {embedding_count}")
    print(f"Embedding cache size: {embedding_size / 1024 / 1024:.2f} MB")
    print(f"Commit indexes: {index_count}")
    print(f"Cache directory: {CACHE_DIR}")


if __name__ == "__main__":
    cli()
