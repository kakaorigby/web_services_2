"""
Unit tests for the search module.

Tests cover:
- Single-word searches
- Multi-word searches
- Search output formatting
- Word statistics display
- Edge cases and error handling
"""

import unittest
from src.indexer import InvertedIndex
from src.search import SearchEngine


class TestSearchEngine(unittest.TestCase):
    """Test cases for SearchEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.index = InvertedIndex()
        self.search_engine = SearchEngine(self.index)
        
        # Create sample index
        pages = {
            "https://example.com/1": "the quick brown fox jumps over the lazy dog",
            "https://example.com/2": "the fox is very clever",
            "https://example.com/3": "the dog is loyal and friendly",
            "https://example.com/4": "quick thinking saves the day",
        }
        self.index.build_from_pages(pages)
    
    def test_find_single_word(self):
        """Test finding pages with single word."""
        results = self.search_engine.find("fox")
        
        self.assertEqual(len(results), 2)
        self.assertIn("https://example.com/1", results)
        self.assertIn("https://example.com/2", results)
    
    def test_find_multiple_words(self):
        """Test AND query with multiple words."""
        results = self.search_engine.find("the fox")
        
        self.assertEqual(len(results), 2)
        self.assertIn("https://example.com/1", results)
        self.assertIn("https://example.com/2", results)
    
    def test_find_three_words(self):
        """Test AND query with three words."""
        results = self.search_engine.find("the dog loyal")
        
        self.assertEqual(len(results), 1)
        self.assertIn("https://example.com/3", results)
    
    def test_find_case_insensitive(self):
        """Test case-insensitive search."""
        results_lower = self.search_engine.find("FOX")
        results_mixed = self.search_engine.find("FoX")
        results_normal = self.search_engine.find("fox")
        
        self.assertEqual(results_lower, results_mixed)
        self.assertEqual(results_lower, results_normal)
    
    def test_find_nonexistent_word(self):
        """Test searching for non-existent word."""
        results = self.search_engine.find("nonexistent")
        
        self.assertEqual(results, [])
    
    def test_find_impossible_combination(self):
        """Test AND query with words that don't appear together."""
        results = self.search_engine.find("fox dog loyal")
        
        # No single page has all three
        self.assertEqual(results, [])
    
    def test_find_empty_query(self):
        """Test searching with empty query."""
        results = self.search_engine.find("")
        self.assertEqual(results, [])
        
        results = self.search_engine.find("   ")
        self.assertEqual(results, [])
    
    def test_print_word_found(self):
        """Test printing word that exists in index."""
        result = self.search_engine.print_word("fox")
        
        self.assertTrue(result['found'])
        self.assertEqual(result['word'], 'fox')
        self.assertEqual(result['pages_containing'], 2)
        self.assertGreater(result['total_occurrences'], 0)
    
    def test_print_word_not_found(self):
        """Test printing word that doesn't exist."""
        result = self.search_engine.print_word("nonexistent")
        
        self.assertFalse(result['found'])
        self.assertEqual(result['pages'], [])
    
    def test_print_word_frequency_sorting(self):
        """Test that print results are sorted by frequency."""
        result = self.search_engine.print_word("the")
        
        # "the" appears in multiple pages
        self.assertTrue(result['found'])
        self.assertGreater(len(result['pages']), 1)
        
        # Pages should be sorted by frequency (descending)
        frequencies = [p['frequency'] for p in result['pages']]
        self.assertEqual(frequencies, sorted(frequencies, reverse=True))
    
    def test_format_find_output_single_result(self):
        """Test formatting find output with single result."""
        output = self.search_engine.format_find_output("clever")
        
        self.assertIn("clever", output)
        self.assertIn("1 page", output)
        self.assertIn("https://example.com/2", output)
    
    def test_format_find_output_multiple_results(self):
        """Test formatting find output with multiple results."""
        output = self.search_engine.format_find_output("the")
        
        self.assertIn("the", output)
        self.assertIn("page", output)
        # Should list multiple URLs
        self.assertGreater(output.count("https://"), 1)
    
    def test_format_find_output_no_results(self):
        """Test formatting find output with no results."""
        output = self.search_engine.format_find_output("xyz")
        
        self.assertIn("No pages found", output)
        self.assertIn("xyz", output)
    
    def test_format_print_output_found(self):
        """Test formatting print output for found word."""
        output = self.search_engine.format_print_output("fox")
        
        self.assertIn("fox", output)
        self.assertIn("Frequency", output)
        self.assertIn("https://example.com", output)
    
    def test_format_print_output_not_found(self):
        """Test formatting print output for not found word."""
        output = self.search_engine.format_print_output("xyz")
        
        self.assertIn("not found", output)
        self.assertIn("xyz", output)
    
    def test_search_with_whitespace_padding(self):
        """Test search handles whitespace correctly."""
        results1 = self.search_engine.find("fox")
        results2 = self.search_engine.find("  fox  ")
        results3 = self.search_engine.find("fox \n")
        
        self.assertEqual(results1, results2)
        self.assertEqual(results1, results3)
    
    def test_search_results_sorted(self):
        """Test that search results are sorted consistently."""
        results = self.search_engine.find("the")
        
        # Results should be sorted
        self.assertEqual(results, sorted(results))


class TestSearchEngineEdgeCases(unittest.TestCase):
    """Edge case tests for SearchEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.index = InvertedIndex()
        self.search_engine = SearchEngine(self.index)
    
    def test_search_empty_index(self):
        """Test searching in empty index."""
        results = self.search_engine.find("anything")
        self.assertEqual(results, [])
    
    def test_print_empty_index(self):
        """Test printing in empty index."""
        result = self.search_engine.print_word("anything")
        self.assertFalse(result['found'])
    
    def test_search_special_characters(self):
        """Test search handles special characters."""
        # Index some content with special characters
        self.index.index_page("https://example.com/1", "Hello, World!")
        
        # Search should still work
        results = self.search_engine.find("hello")
        self.assertEqual(len(results), 1)
        
        results = self.search_engine.find("world")
        self.assertEqual(len(results), 1)
    
    def test_multiple_spaces_in_query(self):
        """Test query with multiple spaces."""
        self.index.index_page("https://example.com/1", "a b c d e")
        
        # Query with multiple spaces should work
        results = self.search_engine.find("a   b   c")
        self.assertEqual(len(results), 1)
    
    def test_results_are_unique(self):
        """Test that search results contain no duplicates."""
        self.index.index_page("https://example.com/1", "word word word")
        
        results = self.search_engine.find("word")
        
        # Should return unique URLs only
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results), len(set(results)))
    
    def test_single_word_query_ordering(self):
        """Test that results are in consistent order."""
        pages = {
            "https://z.com": "word",
            "https://a.com": "word",
            "https://m.com": "word",
        }
        
        self.index.build_from_pages(pages)
        
        results = self.search_engine.find("word")
        
        # Should be sorted alphabetically
        self.assertEqual(results, sorted(results))


class TestSearchIntegration(unittest.TestCase):
    """Integration tests for search functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.index = InvertedIndex()
        self.search_engine = SearchEngine(self.index)
    
    def test_realistic_search_scenario(self):
        """Test realistic search scenario with multiple pages."""
        pages = {
            "https://docs.example.com/tutorial": "Python tutorial for beginners",
            "https://docs.example.com/advanced": "Advanced Python programming techniques",
            "https://blog.example.com/python": "Why Python is great for data science",
            "https://blog.example.com/java": "Java vs Python comparison",
        }
        
        self.index.build_from_pages(pages)
        
        # Single word search
        results = self.search_engine.find("Python")
        self.assertEqual(len(results), 4)
        
        # Two word search
        results = self.search_engine.find("Python programming")
        self.assertEqual(len(results), 1)
        
        # Impossible combination
        results = self.search_engine.find("Java beginners")
        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()
