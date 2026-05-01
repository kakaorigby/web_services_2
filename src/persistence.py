"""
Persistence module for saving and loading inverted indices.

This module handles serialization and deserialization of the inverted index
to/from the file system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class IndexPersistence:
    """
    Handles saving and loading of inverted indices.
    
    Attributes:
        index_path (Path): Path to save/load index files
    """
    
    def __init__(self, index_dir: str = "data"):
        """
        Initialize persistence handler.
        
        Args:
            index_dir: Directory to store index files (default: data/)
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        self.index_file = self.index_dir / "index.json"
    
    def save_index(self, index) -> bool:
        """
        Save an inverted index to disk.
        
        Args:
            index: InvertedIndex object to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Prepare data for JSON serialization
            data = {
                'index': index.index,
                'all_words': sorted(list(index.all_words))
            }
            
            # Write to file
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Index saved to {self.index_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False
    
    def load_index(self, index) -> bool:
        """
        Load an inverted index from disk.
        
        Args:
            index: InvertedIndex object to populate
            
        Returns:
            True if load was successful, False otherwise
        """
        try:
            if not self.index_file.exists():
                logger.error(f"Index file not found: {self.index_file}")
                return False
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore index data
            index.index = data['index']
            index.all_words = set(data['all_words'])
            
            logger.info(f"Index loaded from {self.index_file}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding index file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def index_exists(self) -> bool:
        """
        Check if an index file exists.
        
        Returns:
            True if index file exists, False otherwise
        """
        return self.index_file.exists()
    
    def get_index_info(self) -> Optional[Dict]:
        """
        Get information about the saved index without loading it fully.
        
        Returns:
            Dictionary with index metadata, or None if not found
        """
        try:
            if not self.index_file.exists():
                return None
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'file_path': str(self.index_file),
                'file_size': self.index_file.stat().st_size,
                'unique_words': len(data.get('all_words', [])),
                'indexed_pages': len(set(
                    page['url'] 
                    for word_data in data.get('index', {}).values()
                    for page in word_data.get('pages', [])
                ))
            }
            
        except Exception as e:
            logger.error(f"Error getting index info: {e}")
            return None
    
    def delete_index(self) -> bool:
        """
        Delete the saved index file.
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if self.index_file.exists():
                self.index_file.unlink()
                logger.info(f"Index file deleted: {self.index_file}")
            return True
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False
