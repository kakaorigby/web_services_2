"""
Advanced retrieval tests for phrase, boolean, and TF-IDF ranking behavior.
"""

import unittest
from src.indexer import InvertedIndex
from src.search import SearchEngine


class TestAdvancedSearch(unittest.TestCase):
    def setUp(self):
        self.index = InvertedIndex()
        self.search = SearchEngine(self.index)
        pages = {
            "https://example.com/1": "good friends are always good",
            "https://example.com/2": "good people and friends together",
            "https://example.com/3": "life is good but death is inevitable",
            "https://example.com/4": "friendship and kindness in life",
        }
        self.index.build_from_pages(pages)

    def test_phrase_search(self):
        results = self.search.find('"good friends"')
        self.assertEqual(results, ["https://example.com/1"])

    def test_or_query(self):
        results = self.search.find("friendship OR death")
        self.assertEqual(set(results), {"https://example.com/3", "https://example.com/4"})

    def test_and_not_query(self):
        results = self.search.find("life AND NOT death")
        self.assertEqual(results, ["https://example.com/4"])

    def test_implicit_and_with_parentheses(self):
        results = self.search.find("good AND (friends OR people)")
        self.assertEqual(set(results), {"https://example.com/1", "https://example.com/2"})

    def test_ranked_results_descending(self):
        ranked = self.search.find_ranked("good friends")
        self.assertGreaterEqual(len(ranked), 2)
        scores = [item["score"] for item in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(ranked[0]["url"], "https://example.com/1")

    def test_rank_output_contains_scores(self):
        output = self.search.format_rank_output("good friends")
        self.assertIn("score=", output)
        self.assertIn("Ranked results", output)


if __name__ == "__main__":
    unittest.main()
