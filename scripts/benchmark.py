"""
Benchmark script for indexing and retrieval operations.

Usage:
    python3 scripts/benchmark.py
"""

import random
import statistics
import time
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.indexer import InvertedIndex
from src.search import SearchEngine


logging.getLogger().setLevel(logging.WARNING)


def generate_pages(page_count: int):
    base_terms = [
        "search", "engine", "crawler", "index", "ranking", "query",
        "python", "web", "services", "quotes", "friends", "wisdom",
        "life", "learning", "testing", "retrieval", "boolean", "phrase"
    ]

    pages = {}
    for i in range(page_count):
        words = random.choices(base_terms, k=120)
        words.extend(["good", "friends"] if i % 7 == 0 else ["life", "wisdom"])
        pages[f"https://bench.local/{i}"] = " ".join(words)
    return pages


def run_benchmark(page_count: int = 1500, query_runs: int = 200):
    pages = generate_pages(page_count)

    idx = InvertedIndex()
    start_build = time.perf_counter()
    idx.build_from_pages(pages)
    build_time = time.perf_counter() - start_build

    engine = SearchEngine(idx)

    queries = [
        "good friends",
        '"good friends"',
        "life AND wisdom",
        "life AND NOT friends",
        "good OR wisdom",
    ]

    simple_times = []
    ranked_times = []

    for _ in range(query_runs):
        q = random.choice(queries)

        t0 = time.perf_counter()
        engine.find(q)
        simple_times.append(time.perf_counter() - t0)

        t1 = time.perf_counter()
        engine.find_ranked(q)
        ranked_times.append(time.perf_counter() - t1)

    print("Benchmark Results")
    print("=================")
    print(f"Pages indexed: {page_count}")
    print(f"Index build time: {build_time:.4f}s")
    print(f"Mean query latency: {statistics.mean(simple_times) * 1000:.3f} ms")
    print(f"P95 query latency: {statistics.quantiles(simple_times, n=20)[18] * 1000:.3f} ms")
    print(f"Mean ranked latency: {statistics.mean(ranked_times) * 1000:.3f} ms")
    print(f"P95 ranked latency: {statistics.quantiles(ranked_times, n=20)[18] * 1000:.3f} ms")


if __name__ == "__main__":
    random.seed(42)
    run_benchmark()
