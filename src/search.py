"""
Search functionality module for querying the inverted index.

This module provides search operations including single-word lookup,
multi-word queries, and detailed index inspection.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Search engine that operates on an inverted index.
    
    Attributes:
        index: Reference to an InvertedIndex object
    """
    
    def __init__(self, index):
        """
        Initialize search engine with an inverted index.
        
        Args:
            index: An InvertedIndex object to search
        """
        self.index = index
    
    def find(self, query: str) -> List[str]:
        """
        Search for pages containing query terms.
        
        Supports:
        - Single word: "python" returns pages with "python"
        - Multiple words: "good friends" returns pages with BOTH words (AND query)
        
        Args:
            query: Search query string
            
        Returns:
            List of URLs matching the query
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        # Split query into words and remove empty strings
        words = [w.strip() for w in query.split() if w.strip()]
        
        if not words:
            return []
        
        # Case-insensitive search
        words_lower = [w.lower() for w in words]
        
        # Use AND logic for multiple words
        results = self.index.search_all_words(words_lower)
        
        logger.info(f"Search query: '{query}' returned {len(results)} results")
        
        return results
    
    def print_word(self, word: str) -> Dict:
        """
        Print detailed information about a word in the index.
        
        Args:
            word: The word to inspect
            
        Returns:
            Dictionary with word statistics
        """
        pages = self.index.get_word_pages(word)
        
        if not pages:
            logger.info(f"Word '{word}' not found in index")
            return {
                'word': word.lower(),
                'found': False,
                'pages': []
            }
        
        result = {
            'word': word.lower(),
            'found': True,
            'total_occurrences': sum(p['frequency'] for p in pages),
            'pages_containing': len(pages),
            'pages': []
        }
        
        # Sort pages by frequency (most frequent first)
        sorted_pages = sorted(pages, key=lambda p: p['frequency'], reverse=True)
        
        for page in sorted_pages:
            result['pages'].append({
                'url': page['url'],
                'frequency': page['frequency'],
                'position_count': len(page['positions'])
            })
        
        return result
    
    def format_print_output(self, word: str) -> str:
        """
        Format the output for the print command.
        
        Args:
            word: The word to display
            
        Returns:
            Formatted string for display
        """
        data = self.print_word(word)
        
        if not data['found']:
            return f"Word '{word}' not found in index"
        
        lines = [
            f"Word: {data['word']}",
            f"Total Occurrences: {data['total_occurrences']}",
            f"Pages Containing Word: {data['pages_containing']}",
            "",
            "Pages:"
        ]
        
        for page_info in data['pages']:
            lines.append(f"  - {page_info['url']}")
            lines.append(f"    Frequency: {page_info['frequency']}")
        
        return "\n".join(lines)
    
    def format_find_output(self, query: str) -> str:
        """
        Format the output for the find command.
        
        Args:
            query: The search query
            
        Returns:
            Formatted string for display
        """
        results = self.find(query)
        
        if not results:
            return f"No pages found containing: {query}"
        
        lines = [f"Results for query: '{query}' ({len(results)} pages):", ""]
        
        for i, url in enumerate(results, 1):
            lines.append(f"{i}. {url}")
        
        return "\n".join(lines)
