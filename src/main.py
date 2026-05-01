"""
Main module providing the command-line interface for the search tool.

Commands:
    build - Crawl the website and build the index
    load - Load a previously built index
    print - Display index information for a word
    find - Search for pages containing word(s)
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from crawler import WebCrawler
from indexer import InvertedIndex
from search import SearchEngine
from persistence import IndexPersistence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class SearchTool:
    """
    Main search tool combining crawling, indexing, and searching.
    
    Attributes:
        index: InvertedIndex object
        crawler: WebCrawler object
        search_engine: SearchEngine object
        persistence: IndexPersistence object
    """
    
    TARGET_URL = "https://quotes.toscrape.com/"
    
    def __init__(self):
        """Initialize the search tool."""
        self.index = InvertedIndex()
        self.crawler = WebCrawler(self.TARGET_URL)
        self.search_engine = SearchEngine(self.index)
        self.persistence = IndexPersistence()
        self.index_loaded = False
    
    def cmd_build(self, args: list = None) -> None:
        """
        Build the index by crawling the website.
        
        Usage: build
        """
        logger.info("Building index...")
        logger.info(f"Crawling {self.TARGET_URL}")
        logger.info("This may take several minutes due to politeness window.")
        
        try:
            # Crawl the website
            pages = self.crawler.crawl()
            
            if not pages:
                logger.error("No pages were crawled. Check the URL and network connection.")
                return
            
            logger.info(f"\nCrawled {len(pages)} pages")
            
            # Build the index
            self.index.build_from_pages(pages)
            
            # Get statistics
            stats = self.index.get_statistics()
            logger.info(f"\nIndex Statistics:")
            logger.info(f"  Unique Words: {stats['unique_words']}")
            logger.info(f"  Indexed Pages: {stats['indexed_pages']}")
            logger.info(f"  Total Word Occurrences: {stats['total_word_frequency']}")
            
            # Save index
            if self.persistence.save_index(self.index):
                logger.info("\n✓ Index built and saved successfully!")
            else:
                logger.error("Failed to save index")
            
            self.index_loaded = True
            
        except Exception as e:
            logger.error(f"Error during build: {e}")
    
    def cmd_load(self, args: list = None) -> None:
        """
        Load a previously built index from disk.
        
        Usage: load
        """
        logger.info("Loading index...")
        
        try:
            if not self.persistence.index_exists():
                logger.error("Index file not found. Run 'build' command first.")
                return
            
            if self.persistence.load_index(self.index):
                self.index_loaded = True
                stats = self.index.get_statistics()
                logger.info(f"✓ Index loaded successfully!")
                logger.info(f"  Unique Words: {stats['unique_words']}")
                logger.info(f"  Indexed Pages: {stats['indexed_pages']}")
            else:
                logger.error("Failed to load index")
                
        except Exception as e:
            logger.error(f"Error during load: {e}")
    
    def cmd_print(self, args: list) -> None:
        """
        Print inverted index information for a word.
        
        Usage: print <word>
        """
        if not self._check_index_loaded():
            return
        
        if not args or len(args) < 1:
            logger.error("Usage: print <word>")
            return
        
        word = args[0]
        
        try:
            output = self.search_engine.format_print_output(word)
            print(output)
        except Exception as e:
            logger.error(f"Error printing word: {e}")
    
    def cmd_find(self, args: list) -> None:
        """
        Find pages containing search terms (AND query).
        
        Usage: find <word> [word2 word3 ...]
        """
        if not self._check_index_loaded():
            return
        
        if not args or len(args) < 1:
            logger.error("Usage: find <word> [word2 word3 ...]")
            return
        
        query = " ".join(args)
        
        try:
            output = self.search_engine.format_find_output(query)
            print(output)
        except Exception as e:
            logger.error(f"Error searching: {e}")
    
    def _check_index_loaded(self) -> bool:
        """
        Check if an index has been loaded or built.
        
        Returns:
            True if index is loaded, False otherwise
        """
        if not self.index_loaded and len(self.index) == 0:
            logger.error("Index not loaded. Run 'load' or 'build' command first.")
            return False
        return True
    
    def run(self) -> None:
        """Run the interactive shell."""
        logger.info("Search Tool - Interactive Shell")
        logger.info("Type 'help' for available commands, 'quit' to exit\n")
        
        while True:
            try:
                # Get user input
                prompt = "> "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Parse command and arguments
                parts = user_input.split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Execute command
                if command == "quit" or command == "exit":
                    logger.info("Goodbye!")
                    break
                
                elif command == "help":
                    self._print_help()
                
                elif command == "build":
                    self.cmd_build(args)
                
                elif command == "load":
                    self.cmd_load(args)
                
                elif command == "print":
                    self.cmd_print(args)
                
                elif command == "find":
                    self.cmd_find(args)
                
                else:
                    logger.error(f"Unknown command: {command}")
                    logger.info("Type 'help' for available commands")
                
            except KeyboardInterrupt:
                logger.info("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
    
    def _print_help(self) -> None:
        """Print help information."""
        help_text = """
Available Commands:

  build               Crawl the website and build the inverted index
                     This may take several minutes.

  load                Load a previously built index from disk

  print <word>        Print index information for a specific word
                     Example: print nonsense

  find <words>        Find pages containing all specified words (AND query)
                     Examples:
                       find indifference
                       find good friends

  help                Show this help message

  quit                Exit the program

Note: Use 'load' or 'build' before running print/find commands.
"""
        print(help_text)


def main():
    """Main entry point for the search tool."""
    tool = SearchTool()
    tool.run()


if __name__ == "__main__":
    main()
