"""
Search functionality module for querying the inverted index.

This module provides:
- basic single/multi-word search
- phrase search using quoted terms
- boolean query operators (AND, OR, NOT)
- TF-IDF ranked retrieval for relevance ordering
"""

from typing import List, Dict, Set, Tuple
import re
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
    
    OPERATORS = {"AND", "OR", "NOT"}
    PRECEDENCE = {"NOT": 3, "AND": 2, "OR": 1}

    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize query, preserving quoted phrases and parentheses."""
        pattern = r'"[^"]+"|\(|\)|[^()\s]+'
        return re.findall(pattern, query)

    def _normalize_token(self, token: str) -> str:
        """Normalize token case while preserving operators and phrases."""
        upper = token.upper()
        if upper in self.OPERATORS or token in ("(", ")"):
            return upper if upper in self.OPERATORS else token
        return token.lower()

    def _to_rpn(self, tokens: List[str]) -> List[str]:
        """Convert infix boolean expression to Reverse Polish Notation."""
        output: List[str] = []
        stack: List[str] = []

        for token in tokens:
            if token == "(":
                stack.append(token)
            elif token == ")":
                while stack and stack[-1] != "(":
                    output.append(stack.pop())
                if stack and stack[-1] == "(":
                    stack.pop()
            elif token in self.OPERATORS:
                while (
                    stack
                    and stack[-1] in self.OPERATORS
                    and self.PRECEDENCE[stack[-1]] >= self.PRECEDENCE[token]
                ):
                    output.append(stack.pop())
                stack.append(token)
            else:
                output.append(token)

        while stack:
            output.append(stack.pop())

        return output

    def _find_phrase_urls(self, phrase: str) -> Set[str]:
        """Return URLs where all phrase terms appear in consecutive positions."""
        words = [w for w in phrase.lower().split() if w]
        if not words:
            return set()

        candidate_urls = set(self.index.search_all_words(words))
        if len(words) == 1:
            return candidate_urls

        matched: Set[str] = set()
        for url in candidate_urls:
            first_positions = self.index.get_positions_for_word_in_url(words[0], url)
            if not first_positions:
                continue

            subsequent_positions = [
                set(self.index.get_positions_for_word_in_url(word, url))
                for word in words[1:]
            ]

            for pos in first_positions:
                if all((pos + offset + 1) in subsequent_positions[offset] for offset in range(len(subsequent_positions))):
                    matched.add(url)
                    break

        return matched

    def _evaluate_operand(self, token: str) -> Set[str]:
        """Evaluate a single token into a URL set."""
        if token.startswith('"') and token.endswith('"'):
            phrase = token[1:-1].strip()
            return self._find_phrase_urls(phrase)
        return set(self.index.search_single_word(token.lower()))

    def _evaluate_boolean_query(self, query: str) -> Set[str]:
        """Evaluate boolean/phrase query and return matching URL set."""
        raw_tokens = self._tokenize_query(query)
        if not raw_tokens:
            return set()

        normalized = [self._normalize_token(token) for token in raw_tokens]

        # If the query has no explicit operators, preserve original AND semantics.
        has_operator = any(token in self.OPERATORS for token in normalized)
        has_phrase = any(token.startswith('"') and token.endswith('"') for token in normalized)
        if not has_operator and not has_phrase:
            words = [w for w in normalized if w not in ("(", ")")]
            return set(self.index.search_all_words(words))

        # Insert implicit AND between adjacent operands/phrases/close-open groups.
        expanded: List[str] = []
        prev = None
        for token in normalized:
            if prev is not None:
                prev_is_operand = prev not in self.OPERATORS and prev != "("
                prev_is_close = prev == ")"
                token_is_operand = token not in self.OPERATORS and token != ")"
                token_is_open = token == "("
                if (prev_is_operand or prev_is_close) and (token_is_operand or token_is_open):
                    expanded.append("AND")
            expanded.append(token)
            prev = token

        rpn = self._to_rpn(expanded)
        stack: List[Set[str]] = []
        universe = self.index.get_indexed_urls()

        for token in rpn:
            if token not in self.OPERATORS:
                stack.append(self._evaluate_operand(token))
                continue

            if token == "NOT":
                operand = stack.pop() if stack else set()
                stack.append(universe.difference(operand))
            else:
                right = stack.pop() if stack else set()
                left = stack.pop() if stack else set()
                if token == "AND":
                    stack.append(left.intersection(right))
                elif token == "OR":
                    stack.append(left.union(right))

        return stack[-1] if stack else set()

    def find(self, query: str) -> List[str]:
        """
        Search for pages matching the query.

        Supports:
        - Single word: "python"
        - Implicit AND: "good friends" → pages containing both words
        - Phrase: '"good friends"' → consecutive token match
        - Boolean: AND, OR, NOT with optional parentheses

        Args:
            query: Search query string

        Returns:
            List of URLs matching the query, sorted alphabetically
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        results = sorted(list(self._evaluate_boolean_query(query)))
        
        logger.info(f"Search query: '{query}' returned {len(results)} results")
        
        return results

    def find_ranked(self, query: str) -> List[Dict[str, float]]:
        """
        Return TF-IDF ranked results for query.

        Supports phrase and boolean filtering first, then ranks candidates
        with TF-IDF over non-operator query terms.
        """
        if not query or not query.strip():
            logger.warning("Empty ranked query provided")
            return []

        candidate_urls = self._evaluate_boolean_query(query)
        if not candidate_urls:
            return []

        tokens = [self._normalize_token(t) for t in self._tokenize_query(query)]
        scoring_terms: List[str] = []
        for token in tokens:
            if token in self.OPERATORS or token in ("(", ")"):
                continue
            if token.startswith('"') and token.endswith('"'):
                scoring_terms.extend([w for w in token[1:-1].lower().split() if w])
            else:
                scoring_terms.append(token.lower())

        scores = self.index.compute_tfidf_scores(scoring_terms, candidate_urls)
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        return [{"url": url, "score": round(score, 6)} for url, score in ranked if score > 0]
    
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

    def format_rank_output(self, query: str) -> str:
        """Format TF-IDF ranked query output for display."""
        ranked_results = self.find_ranked(query)
        if not ranked_results:
            return f"No ranked results for query: {query}"

        lines = [f"Ranked results for query: '{query}' ({len(ranked_results)} pages):", ""]
        for i, item in enumerate(ranked_results, 1):
            lines.append(f"{i}. {item['url']} (score={item['score']})")
        return "\n".join(lines)
