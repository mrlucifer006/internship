from dataclasses import dataclass
from typing import List, Dict, Any, Generator
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Default pagination settings
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 0.1  # seconds


@dataclass
class PaginationResult:
    """Container for paginated query results with metadata."""
    data: List[Dict[str, Any]]
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'data': self.data,
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_prev': self.has_prev
        }
