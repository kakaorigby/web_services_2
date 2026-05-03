"""
Lightweight performance and scaling tests.

These tests are intentionally conservative to avoid flakiness on shared machines.
"""

import time
import unittest
import logging

from src.indexer import InvertedIndex
from src.search import SearchEngine


logging.getLogger().setLevel(logging.WARNING)


class TestPerformance(unittest.TestCase):
    def test_large_index_search_latency(self):
        index = InvertedIndex()

        pages = {}
        for i in range(800):
            pages[f"https://example.com/{i}"] = (
                "python web services indexing search engine "
                + ("ranked retrieval " * (i % 5))
                + f"document {i}"
            )

        start_build = time.perf_counter()
        index.build_from_pages(pages)
        build_time = time.perf_counter() - start_build

        search = SearchEngine(index)

        start_query = time.perf_counter()
        results = search.find("python AND search")
        query_time = time.perf_counter() - start_query

        self.assertGreater(len(results), 0)
        self.assertLess(build_time, 3.5)
        self.assertLess(query_time, 0.1)

    def test_ranked_query_latency(self):
        index = InvertedIndex()
        pages = {
            f"https://example.com/{i}": "good friends life wisdom and kindness " + ("good " * (i % 6))
            for i in range(600)
        }
        index.build_from_pages(pages)
        search = SearchEngine(index)

        start_rank = time.perf_counter()
        ranked = search.find_ranked('"good friends" OR wisdom')
        rank_time = time.perf_counter() - start_rank

        self.assertGreater(len(ranked), 0)
        self.assertLess(rank_time, 0.2)


if __name__ == "__main__":
    unittest.main()
