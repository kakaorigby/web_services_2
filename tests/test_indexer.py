"""
Unit tests for the indexing module.

Tests cover:
- Word tokenization
- Inverted index creation
- Word statistics (frequency, positions)
- Case-insensitive indexing
- Search functionality
- Index statistics
"""

import unittest
from src.indexer import InvertedIndex


class TestInvertedIndex(unittest.TestCase):
    """Test cases for InvertedIndex class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.index = InvertedIndex()
    
    def test_index_initialization(self):
        """Test InvertedIndex initialization."""
        self.assertEqual(len(self.index), 0)
        self.assertEqual(len(self.index.all_words), 0)
        self.assertEqual(len(self.index.index), 0)
    
    def test_tokenization_basic(self):
        """Test basic word tokenization."""
        text = "Hello world this is a test"
        tokens = self.index._tokenize(text)
        
        self.assertEqual(tokens, ["hello", "world", "this", "is", "a", "test"])
    
    def test_tokenization_case_insensitive(self):
        """Test tokenization converts to lowercase."""
        text = "Hello WORLD ThIs Is A TeSt"
        tokens = self.index._tokenize(text)
        
        self.assertTrue(all(token.islower() for token in tokens))
    
    def test_tokenization_removes_punctuation(self):
        """Test tokenization removes punctuation."""
        text = "Hello, world! This is a test."
        tokens = self.index._tokenize(text)
        
        self.assertNotIn("hello,", tokens)
        self.assertNotIn("world!", tokens)
        self.assertNotIn("test.", tokens)
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)
    
    def test_tokenization_handles_special_chars(self):
        """Test tokenization with special characters."""
        text = "It's a well-known fact about C++"
        tokens = self.index._tokenize(text)
        
        # Should tokenize but handle hyphens
        self.assertIn("it", tokens)
        self.assertIn("s", tokens)  # apostrophe removed
        self.assertIn("well-known", tokens)  # Hyphens are preserved in words
    
    def test_tokenization_empty_string(self):
        """Test tokenization of empty string."""
        tokens = self.index._tokenize("")
        self.assertEqual(tokens, [])
    
    def test_index_single_page(self):
        """Test indexing a single page."""
        url = "https://example.com/page1"
        content = "The quick brown fox jumps over the lazy dog"
        
        self.index.index_page(url, content)
        
        # Should have indexed words
        self.assertGreater(len(self.index), 0)
        self.assertIn("the", self.index.all_words)
        self.assertIn("fox", self.index.all_words)
    
    def test_index_word_frequency(self):
        """Test word frequency counting."""
        url = "https://example.com/page1"
        content = "the cat sat on the mat the cat"
        
        self.index.index_page(url, content)
        
        pages = self.index.get_word_pages("the")
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]['frequency'], 3)
        
        pages = self.index.get_word_pages("cat")
        self.assertEqual(pages[0]['frequency'], 2)
    
    def test_index_multiple_pages(self):
        """Test indexing multiple pages."""
        pages = {
            "https://example.com/1": "python is great",
            "https://example.com/2": "python programming language",
            "https://example.com/3": "java is also good",
        }
        
        self.index.build_from_pages(pages)
        
        # "python" should appear in 2 pages
        python_pages = self.index.search_single_word("python")
        self.assertEqual(len(python_pages), 2)
        
        # "is" should appear in 2 pages (1 and 3)
        is_pages = self.index.search_single_word("is")
        self.assertEqual(len(is_pages), 2)
    
    def test_search_nonexistent_word(self):
        """Test searching for non-existent word."""
        url = "https://example.com/page1"
        self.index.index_page(url, "hello world")
        
        results = self.index.search_single_word("nonexistent")
        self.assertEqual(results, [])
    
    def test_search_case_insensitive(self):
        """Test case-insensitive search."""
        url = "https://example.com/page1"
        self.index.index_page(url, "Hello World")
        
        # Search in different cases
        results_lower = self.index.search_single_word("hello")
        results_upper = self.index.search_single_word("HELLO")
        results_mixed = self.index.search_single_word("HeLLo")
        
        self.assertEqual(results_lower, results_upper)
        self.assertEqual(results_lower, results_mixed)
        self.assertEqual(len(results_lower), 1)
    
    def test_search_all_words(self):
        """Test AND query (all words)."""
        pages = {
            "https://example.com/1": "python and java are languages",
            "https://example.com/2": "python is great",
            "https://example.com/3": "java is powerful",
        }
        
        self.index.build_from_pages(pages)
        
        # Find pages with both "python" and "java"
        results = self.index.search_all_words(["python", "java"])
        self.assertEqual(len(results), 1)
        self.assertIn("https://example.com/1", results)
        
        # Find pages with both "python" and "is"
        results = self.index.search_all_words(["python", "is"])
        self.assertEqual(len(results), 1)  # Only page 2 has both
    
    def test_search_all_words_empty_result(self):
        """Test AND query with no matching pages."""
        pages = {
            "https://example.com/1": "python",
            "https://example.com/2": "java",
        }
        
        self.index.build_from_pages(pages)
        
        # Both words don't appear together
        results = self.index.search_all_words(["python", "java"])
        self.assertEqual(len(results), 0)
    
    def test_search_all_words_single_word(self):
        """Test AND query with single word."""
        pages = {
            "https://example.com/1": "python is great",
            "https://example.com/2": "java is also good",
        }
        
        self.index.build_from_pages(pages)
        
        results = self.index.search_all_words(["python"])
        self.assertEqual(len(results), 1)
    
    def test_index_statistics(self):
        """Test index statistics calculation."""
        pages = {
            "https://example.com/1": "python is great",
            "https://example.com/2": "python programming",
        }
        
        self.index.build_from_pages(pages)
        
        stats = self.index.get_statistics()
        
        self.assertGreater(stats['unique_words'], 0)
        self.assertEqual(stats['indexed_pages'], 2)
        self.assertGreater(stats['total_word_frequency'], 0)
    
    def test_get_word_pages_empty_index(self):
        """Test getting pages for word in empty index."""
        pages = self.index.get_word_pages("nonexistent")
        self.assertEqual(pages, [])
    
    def test_duplicate_indexing(self):
        """Test re-indexing same page."""
        url = "https://example.com/page1"
        
        # Index same page twice
        self.index.index_page(url, "hello world")
        self.index.index_page(url, "hello world")
        
        # Should create two separate entries (not merge)
        pages = self.index.get_word_pages("hello")
        # This will actually have 2 entries since we index it twice
        self.assertEqual(len(pages), 2)


class TestInvertedIndexEdgeCases(unittest.TestCase):
    """Edge case tests for InvertedIndex."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.index = InvertedIndex()
    
    def test_index_empty_content(self):
        """Test indexing empty content."""
        self.index.index_page("https://example.com/page", "")
        
        # Should not create any index entries
        self.assertEqual(len(self.index), 0)
    
    def test_index_whitespace_only(self):
        """Test indexing whitespace-only content."""
        self.index.index_page("https://example.com/page", "   \n\t  ")
        
        self.assertEqual(len(self.index), 0)
    
    def test_index_single_word(self):
        """Test indexing single word."""
        self.index.index_page("https://example.com/page", "hello")
        
        self.assertEqual(len(self.index), 1)
        self.assertIn("hello", self.index.all_words)
    
    def test_very_long_text(self):
        """Test indexing very long text."""
        long_text = " ".join(["word"] * 1000)
        self.index.index_page("https://example.com/page", long_text)
        
        pages = self.index.get_word_pages("word")
        self.assertEqual(pages[0]['frequency'], 1000)
    
    def test_special_characters_only(self):
        """Test indexing text with only special characters."""
        self.index.index_page("https://example.com/page", "!@#$%^&*()")
        
        self.assertEqual(len(self.index), 0)
    
    def test_numbers_in_text(self):
        """Test tokenization of text with numbers."""
        self.index.index_page("https://example.com/page", "Python 3.11 version")
        
        # Numbers should be tokenized
        self.assertIn("3", self.index.all_words)
        self.assertIn("11", self.index.all_words)


if __name__ == '__main__':
    unittest.main()
