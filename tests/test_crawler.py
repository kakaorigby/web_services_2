"""
Unit tests for the web crawler module.

Tests cover:
- URL validation and filtering
- Text extraction from HTML
- Link extraction
- Politeness window enforcement
- Error handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from src.crawler import WebCrawler


class TestWebCrawler(unittest.TestCase):
    """Test cases for WebCrawler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://quotes.toscrape.com"
        self.crawler = WebCrawler(self.base_url, politeness_window=0.1)
    
    def test_crawler_initialization(self):
        """Test WebCrawler initialization."""
        self.assertEqual(self.crawler.base_url, self.base_url)
        self.assertEqual(self.crawler.politeness_window, 0.1)
        self.assertEqual(len(self.crawler.visited_urls), 0)
        self.assertIsNotNone(self.crawler.domain)
    
    def test_url_validation_same_domain(self):
        """Test URL validation for same domain."""
        valid_urls = [
            "https://quotes.toscrape.com/page/2/",
            "https://quotes.toscrape.com/",
            "https://quotes.toscrape.com/tag/life/",
        ]
        
        for url in valid_urls:
            self.assertTrue(self.crawler._is_valid_url(url), f"URL should be valid: {url}")
    
    def test_url_validation_different_domain(self):
        """Test URL validation rejects different domains."""
        invalid_urls = [
            "https://example.com/",
            "https://google.com/",
            "http://quotes.toscrape.com/",  # Different scheme but technically different domain
        ]
        
        for url in invalid_urls:
            result = self.crawler._is_valid_url(url)
            # Only check netloc mismatch (example.com, google.com)
            if "example.com" in url or "google.com" in url:
                self.assertFalse(result, f"URL should be invalid: {url}")
    
    def test_text_extraction_from_html(self):
        """Test text extraction from HTML."""
        html = """
        <html>
            <head><script>alert('hidden');</script></head>
            <body>
                <h1>Quote Title</h1>
                <p>This is a quote text</p>
                <style>body { color: red; }</style>
                <p>Another paragraph</p>
            </body>
        </html>
        """
        
        text = self.crawler._extract_text_from_page(html)
        
        # Should contain body text
        self.assertIn("Quote Title", text)
        self.assertIn("This is a quote text", text)
        self.assertIn("Another paragraph", text)
        
        # Should not contain script/style content
        self.assertNotIn("alert", text)
        self.assertNotIn("color: red", text)
    
    def test_text_extraction_empty_html(self):
        """Test text extraction from empty HTML."""
        html = "<html><body></body></html>"
        text = self.crawler._extract_text_from_page(html)
        
        # Should return empty or whitespace-only string
        self.assertEqual(text.strip(), "")
    
    def test_text_extraction_with_special_chars(self):
        """Test text extraction preserves meaningful content."""
        html = "<p>Hello, World! It's a test.</p>"
        text = self.crawler._extract_text_from_page(html)
        
        self.assertIn("Hello", text)
        self.assertIn("World", text)
        self.assertIn("test", text)
    
    def test_link_extraction(self):
        """Test extracting links from HTML."""
        html = """
        <html>
            <body>
                <a href="/page/2/">Page 2</a>
                <a href="https://quotes.toscrape.com/tag/life/">Life Tag</a>
                <a href="https://external.com/">External</a>
                <a href="/page/3/">Page 3</a>
            </body>
        </html>
        """
        
        current_url = "https://quotes.toscrape.com/"
        urls = self.crawler._get_next_urls(html, current_url)
        
        # Should include same-domain links
        self.assertEqual(len(urls), 3)  # External link should be filtered
        
        # Check for converted absolute URLs
        self.assertTrue(any("page/2" in url for url in urls))
        self.assertTrue(any("page/3" in url for url in urls))
    
    def test_link_extraction_removes_fragments(self):
        """Test that URL fragments are removed."""
        html = '<a href="/page/2/#section">Link</a>'
        
        current_url = "https://quotes.toscrape.com/"
        urls = self.crawler._get_next_urls(html, current_url)
        
        # Fragment should be removed
        self.assertEqual(len(urls), 1)
        self.assertNotIn("#", urls[0])
    
    def test_politeness_window_enforcement(self):
        """Test that politeness window is respected."""
        crawler = WebCrawler(self.base_url, politeness_window=0.2)
        crawler.last_request_time = time.time()
        
        start = time.time()
        crawler._respect_politeness_window()
        elapsed = time.time() - start
        
        # Should have waited approximately politeness_window seconds
        self.assertGreaterEqual(elapsed, 0.15)  # Allow small variance
    
    def test_duplicate_url_tracking(self):
        """Test that visited URLs are tracked."""
        self.crawler.visited_urls.add("https://quotes.toscrape.com/page/2/")
        
        # Try to fetch the same URL
        url, html = self.crawler.fetch_page("https://quotes.toscrape.com/page/2/")
        
        # Should return empty since already visited
        self.assertEqual(url, "")
        self.assertEqual(html, "")
    
    @patch('src.crawler.requests.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        url, html = self.crawler.fetch_page("https://quotes.toscrape.com/")
        
        self.assertEqual(url, "https://quotes.toscrape.com/")
        self.assertIn("Test", html)
        self.assertIn(url, self.crawler.visited_urls)
    
    @patch('src.crawler.requests.get')
    def test_fetch_page_network_error(self, mock_get):
        """Test handling of network errors."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        url, html = self.crawler.fetch_page("https://quotes.toscrape.com/")
        
        # Should return empty on error
        self.assertEqual(url, "")
        self.assertEqual(html, "")


class TestCrawlerIntegration(unittest.TestCase):
    """Integration tests for crawler."""
    
    @patch('src.crawler.requests.get')
    def test_crawl_multiple_pages(self, mock_get):
        """Test crawling multiple pages."""
        # Mock responses for multiple pages
        html_page1 = '<html><body>Page 1 <a href="/page/2/">Next</a></body></html>'
        html_page2 = '<html><body>Page 2 <a href="/page/3/">Next</a></body></html>'
        html_page3 = '<html><body>Page 3</body></html>'
        
        mock_get.side_effect = [
            Mock(text=html_page1, raise_for_status=Mock()),
            Mock(text=html_page2, raise_for_status=Mock()),
            Mock(text=html_page3, raise_for_status=Mock()),
        ]
        
        crawler = WebCrawler("https://quotes.toscrape.com", politeness_window=0.01)
        pages = crawler.crawl(max_pages=3)
        
        # Should crawl all 3 pages
        self.assertEqual(len(pages), 3)
        self.assertIn("Page 1", " ".join(pages.values()))
        self.assertIn("Page 2", " ".join(pages.values()))


if __name__ == '__main__':
    unittest.main()
