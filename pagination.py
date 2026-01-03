import sqlite3
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


@contextmanager
def safe_db_connection(db_name: str):
    """
    Context manager for safe database connections with retry logic.
    Prevents database failures when handling multiple concurrent requests.
    """
    conn = None
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            conn = sqlite3.connect(db_name, timeout=30.0)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
            yield conn
            return
        except sqlite3.OperationalError as e:
            last_error = e
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"DB connection attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"DB connection failed after {MAX_RETRIES} attempts: {e}")
                raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


def paginate_query(
    conn: sqlite3.Connection,
    base_query: str,
    count_query: str,
    params: tuple = (),
    page: int = 1,
    per_page: int = DEFAULT_PAGE_SIZE
) -> PaginationResult:
    """
    Execute a paginated query with metadata.
    
    Args:
        conn: Database connection
        base_query: SQL query WITHOUT LIMIT/OFFSET (will be added)
        count_query: SQL query to count total rows
        params: Query parameters (applied to both queries)
        page: Current page number (1-indexed)
        per_page: Items per page
        
    Returns:
        PaginationResult with data and pagination metadata
    """
    # Validate and sanitize inputs
    page = max(1, int(page))
    per_page = min(max(1, int(per_page)), MAX_PAGE_SIZE)
    
    try:
        # Get total count
        cursor = conn.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Calculate pagination metadata
        total_pages = max(1, (total + per_page - 1) // per_page)  # Ceiling division
        
        # Adjust page if out of bounds
        if page > total_pages:
            page = total_pages
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Execute paginated query
        paginated_query = f"{base_query} LIMIT ? OFFSET ?"
        cursor = conn.execute(paginated_query, params + (per_page, offset))
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        data = [dict(row) for row in rows]
        
        return PaginationResult(
            data=data,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except sqlite3.Error as e:
        logger.error(f"Pagination query failed: {e}")
        # Return empty result on error
        return PaginationResult(
            data=[],
            page=1,
            per_page=per_page,
            total=0,
            total_pages=1,
            has_next=False,
            has_prev=False
        )


def batch_fetch(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = (),
    batch_size: int = 100
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Fetch large datasets in batches to prevent memory issues.
    
    Args:
        conn: Database connection
        query: SQL query to execute
        params: Query parameters
        batch_size: Number of rows to fetch at a time
        
    Yields:
        Batches of rows as list of dicts
    """
    cursor = conn.execute(query, params)
    
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        yield [dict(row) for row in rows]


def get_pagination_info(total: int, page: int, per_page: int) -> Dict[str, Any]:
    """
    Calculate pagination metadata without executing query.
    
    Args:
        total: Total number of items
        page: Current page (1-indexed)
        per_page: Items per page
        
    Returns:
        Dict with pagination info
    """
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(max(1, page), total_pages)
    
    return {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'start_index': (page - 1) * per_page + 1,
        'end_index': min(page * per_page, total)
    }
