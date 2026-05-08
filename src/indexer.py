"""
Indexing module for creating and managing inverted indices.

This module creates an inverted index that maps words to their occurrences
across pages, including statistics like frequency and position information.
Case-insensitive indexing is used for search simplicity.
"""

import re
import math
from typing import Dict, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class InvertedIndex:
    """
    An inverted index data structure that maps words to page occurrences.
    
    Structure:
        {
            word: {
                'pages': [
                    {
                        'url': str,
                        'frequency': int,
                        'positions': [int, int, ...]  # word positions in text
                    },
                    ...
                ]
            },
            ...
        }
    
    Attributes:
        index (dict): The inverted index dictionary
        all_words (set): Set of all indexed words
    """
    
    def __init__(self):
        """Initialize an empty inverted index."""
        self.index: Dict[str, Dict] = {}
        self.all_words: Set[str] = set()
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Converts to lowercase, removes punctuation, and splits into words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of lowercase word tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and split on whitespace
        # Keep only alphanumeric characters and hyphens
        words = re.findall(r'\b[a-z0-9]+(?:-[a-z0-9]+)*\b', text)
        
        return words
    
    def index_page(self, url: str, content: str) -> None:
        """
        Add a page's content to the inverted index.
        
        Args:
            url: The page's URL
            content: The page's text content
        """
        # Tokenize content
        words = self._tokenize(content)
        
        if not words:
            logger.warning(f"No words extracted from {url}")
            return
        
        # Lowercase content for position finding
        content_lower = content.lower()
        
        # Count word frequencies and track token positions.
        # Use a mutable list [freq, positions] to avoid O(n²) list copies.
        word_data: Dict[str, List] = {}

        for position, word in enumerate(words):
            if word not in word_data:
                word_data[word] = [0, []]
            word_data[word][0] += 1
            word_data[word][1].append(position)
        
        # Add to index
        for word, (frequency, positions) in word_data.items():  # type: ignore[assignment]
            self.all_words.add(word)
            
            if word not in self.index:
                self.index[word] = {'pages': []}
            
            # Add page entry for this word
            page_entry = {
                'url': url,
                'frequency': frequency,
                'positions': positions
            }
            
            self.index[word]['pages'].append(page_entry)
        
        logger.info(f"Indexed page: {url} ({len(word_data)} unique words)")
    
    def build_from_pages(self, pages: Dict[str, str]) -> None:
        """
        Build the index from a dictionary of pages.
        
        Args:
            pages: Dictionary mapping URLs to page content
        """
        logger.info(f"Building index from {len(pages)} pages")
        
        for url, content in pages.items():
            self.index_page(url, content)
        
        logger.info(f"Index built. Total unique words: {len(self.all_words)}")
    
    def get_word_pages(self, word: str) -> List[Dict]:
        """
        Get all pages containing a specific word.
        
        Args:
            word: The word to search for (case-insensitive)
            
        Returns:
            List of page entries with their statistics
        """
        word_lower = word.lower()
        
        if word_lower not in self.index:
            return []
        
        return self.index[word_lower]['pages']
    
    def search_single_word(self, word: str) -> List[str]:
        """
        Find all pages containing a single word.
        
        Args:
            word: The word to search for
            
        Returns:
            List of URLs containing the word
        """
        pages = self.get_word_pages(word)
        return [page['url'] for page in pages]
    
    def search_all_words(self, words: List[str]) -> List[str]:
        """
        Find pages containing ALL of the given words (AND query).
        
        Args:
            words: List of words to search for
            
        Returns:
            List of URLs containing all words
        """
        if not words:
            return []
        
        # Get pages for first word
        result_urls = set(self.search_single_word(words[0]))
        
        # Intersect with pages containing other words
        for word in words[1:]:
            word_pages = set(self.search_single_word(word))
            result_urls = result_urls.intersection(word_pages)
            
            if not result_urls:
                break
        
        return sorted(list(result_urls))

    def get_indexed_urls(self) -> Set[str]:
        """Return all unique URLs present in the index."""
        urls: Set[str] = set()
        for word_data in self.index.values():
            for page in word_data['pages']:
                urls.add(page['url'])
        return urls

    def get_page_frequency(self, word: str) -> int:
        """Return how many pages contain the given word."""
        return len(self.get_word_pages(word))

    def get_term_frequency(self, url: str, word: str) -> int:
        """Return the term frequency for a word in a specific URL."""
        word_pages = self.get_word_pages(word)
        for page in word_pages:
            if page['url'] == url:
                return page['frequency']
        return 0

    def get_positions_for_word_in_url(self, word: str, url: str) -> List[int]:
        """Return token positions for a word in a specific URL."""
        word_pages = self.get_word_pages(word)
        for page in word_pages:
            if page['url'] == url:
                return page['positions']
        return []

    def compute_tfidf_scores(self, words: List[str], candidate_urls: Set[str] = None) -> Dict[str, float]:
        """
        Compute TF-IDF scores for candidate URLs over the query words.

        Args:
            words: Query words (assumed lowercase)
            candidate_urls: Optional URL subset to score. If None, score all indexed URLs.

        Returns:
            Mapping of URL to aggregated TF-IDF score.
        """
        all_urls = self.get_indexed_urls()
        if not all_urls:
            return {}

        if candidate_urls is None:
            candidate_urls = all_urls

        doc_count = len(all_urls)
        scores: Dict[str, float] = {url: 0.0 for url in candidate_urls}

        for word in words:
            page_frequency = self.get_page_frequency(word)
            if page_frequency == 0:
                continue

            # Smoothed IDF to avoid zero/inf edge cases.
            idf = math.log((doc_count + 1) / (page_frequency + 1)) + 1.0

            for url in candidate_urls:
                tf = self.get_term_frequency(url, word)
                if tf <= 0:
                    continue
                # Log-scaled TF reduces dominance of repeated terms.
                scores[url] += (1.0 + math.log(tf)) * idf

        return scores
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        total_pages = set()
        total_page_entries = 0
        total_word_frequency = 0
        
        for word, word_data in self.index.items():
            pages = word_data['pages']
            total_page_entries += len(pages)
            for page in pages:
                total_pages.add(page['url'])
                total_word_frequency += page['frequency']
        
        return {
            'unique_words': len(self.all_words),
            'indexed_pages': len(total_pages),
            'total_page_entries': total_page_entries,
            'avg_entries_per_word': total_page_entries / len(self.all_words) if self.all_words else 0,
            'total_word_frequency': total_word_frequency
        }
    
    def __len__(self) -> int:
        """Return the number of unique words in the index."""
        return len(self.all_words)
    
    def __repr__(self) -> str:
        """Return string representation of index."""
        stats = self.get_statistics()
        return f"InvertedIndex(words={stats['unique_words']}, pages={stats['indexed_pages']})"
