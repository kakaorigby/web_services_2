"""
Web crawler module for crawling quotes.toscrape.com with politeness window.

This module crawls a website, extracts text from each page, and returns
page information suitable for indexing. It respects a minimum 6-second
politeness window between successive requests.
"""

import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Set, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebCrawler:
    """
    A web crawler that respects politeness windows and extracts text content.
    
    Attributes:
        base_url (str): The base URL to crawl
        politeness_window (float): Minimum seconds between requests
        visited_urls (Set[str]): Set of already visited URLs
        timeout (int): Timeout for requests in seconds
    """
    
    def __init__(self, base_url: str, politeness_window: float = 6.0, timeout: int = 10):
        """
        Initialize the web crawler.
        
        Args:
            base_url: The starting URL to crawl
            politeness_window: Minimum seconds between successive requests (default: 6)
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url
        self.politeness_window = politeness_window
        self.timeout = timeout
        self.visited_urls: Set[str] = set()
        self.last_request_time: float = 0
        self.domain = urlparse(base_url).netloc
    
    def _respect_politeness_window(self) -> None:
        """Enforce the politeness window by waiting if necessary."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.politeness_window:
            sleep_time = self.politeness_window - elapsed
            logger.info(f"Waiting {sleep_time:.2f}s to respect politeness window")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and belongs to the same domain.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and same domain, False otherwise
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain
        except Exception:
            return False
    
    def _extract_text_from_page(self, html: str) -> str:
        """
        Extract readable text content from HTML.
        
        Args:
            html: HTML content as string
            
        Returns:
            Extracted text content
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up text: remove extra whitespace and empty lines
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return ""
    
    def _get_next_urls(self, html: str, current_url: str) -> List[str]:
        """
        Extract all links from a page.
        
        Args:
            html: HTML content as string
            current_url: Current page URL for resolving relative links
            
        Returns:
            List of absolute URLs found on the page
        """
        urls = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.find_all('a', href=True):
                url = urljoin(current_url, link['href'])
                # Remove fragment identifiers
                url = url.split('#')[0]
                if self._is_valid_url(url):
                    urls.append(url)
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
        
        return urls
    
    def fetch_page(self, url: str) -> Tuple[str, str]:
        """
        Fetch a single page while respecting politeness window.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (url, html_content). Returns ("", "") on error.
        """
        if url in self.visited_urls:
            return ("", "")
        
        self._respect_politeness_window()
        
        try:
            logger.info(f"Fetching: {url}")
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            self.visited_urls.add(url)
            return (url, response.text)
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return ("", "")
    
    def crawl(self, start_url: str = None, max_pages: int = None) -> Dict[str, str]:
        """
        Crawl the website starting from start_url.
        
        Args:
            start_url: Starting URL (uses base_url if not provided)
            max_pages: Maximum number of pages to crawl (None = no limit)
            
        Returns:
            Dictionary mapping URLs to their text content
        """
        if start_url is None:
            start_url = self.base_url
        
        pages: Dict[str, str] = {}
        to_visit: List[str] = [start_url]
        pages_crawled = 0
        
        while to_visit and (max_pages is None or pages_crawled < max_pages):
            url = to_visit.pop(0)
            
            if url in self.visited_urls:
                continue
            
            # Fetch the page
            fetched_url, html = self.fetch_page(url)
            
            if not fetched_url:
                continue
            
            # Extract text content
            text_content = self._extract_text_from_page(html)
            
            if text_content:
                pages[fetched_url] = text_content
                pages_crawled += 1
                logger.info(f"Crawled page {pages_crawled}: {fetched_url}")
            
            # Extract and queue new URLs
            new_urls = self._get_next_urls(html, fetched_url)
            for new_url in new_urls:
                if new_url not in self.visited_urls and new_url not in to_visit:
                    to_visit.append(new_url)
        
        logger.info(f"Crawling complete. Total pages crawled: {pages_crawled}")
        return pages
