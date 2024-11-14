# 1. Update src/crawler/crud/frontier_crud.py

from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import logfire

from crawler.crud.basic_crud import BaseCRUD
from crawler.models.frontier_model import (
    FrontierUrl, 
    FrontierStatistics, 
    UrlType,
    UrlState
)

class FrontierCRUD(BaseCRUD):
    """CRUD operations for frontier_url table using aiosql queries"""
    
    def __init__(self, conn, queries):
        super().__init__(conn, queries)
        self.table = "frontier_url"

    def create_url(self, frontier_url: FrontierUrl) -> int:
        """Create new URL in frontier"""
        try:
            # Convert model to dict for query params
            data = {
                'url': str(frontier_url.url),
                'category': frontier_url.category,
                'url_type': frontier_url.url_type.value,
                'depth': frontier_url.depth,
                'max_depth': frontier_url.max_depth,
                'main_domain': urlparse(str(frontier_url.url)).netloc,
                'target_patterns': frontier_url.target_patterns,
                'seed_pattern': frontier_url.seed_pattern,
                'is_target': frontier_url.is_target,
                'parent_url': str(frontier_url.parent_url) if frontier_url.parent_url else None,
                'url_state': UrlState.PENDING.value
            }

            # Execute insert query
            result = self.queries.insert_frontier_url(self.conn, **data)
            # Adjust how you extract the id
            if result:
                if isinstance(result, dict):
                    url_id = result['id']
                elif isinstance(result, tuple):
                    url_id = result[0]
                else:
                    url_id = result  # If result is an int
            else:
                url_id = None

            
            self.conn.commit()

            return url_id

        except Exception as e:
            logfire.error(
                "Error creating frontier URL",
                url=str(frontier_url.url),
                error=str(e)
            )
            raise

    def get_unprocessed_urls(self, limit: int = 100) -> List[FrontierUrl]:
        """Get batch of unprocessed URLs"""
        try:
            results = self.queries.get_unprocessed_urls(
                self.conn,
                limit=limit
            )
            
            urls = []
            for row in results:
                # Convert state and url_type to enums
                row['url_state'] = UrlState(row['url_state'])
                row['url_type'] = UrlType(row['url_type'])
                urls.append(FrontierUrl.model_validate(row))
                
            return urls

        except Exception as e:
            logfire.error(
                "Error getting unprocessed URLs",
                error=str(e)
            )
            return []

    def mark_url_processed(
        self,
        url_id: int,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Mark URL as processed or failed"""
        try:
            self.queries.mark_url_processed(
                self.conn,
                url_id=url_id,
                success=success,
                error_message=error_message
            )
            
            state = 'processed' if success else 'failed'
            logfire.debug(
                f"Marked URL as {state}",
                url_id=url_id,
                success=success
            )

        except Exception as e:
            logfire.error(
                "Error marking URL processed",
                url_id=url_id,
                error=str(e)
            )
            raise
        

    def exists_in_frontier(self, url: str) -> bool:
        """Check if URL exists in frontier"""
        try:
            result = self.execute_query(
                "SELECT EXISTS(SELECT 1 FROM frontier_url WHERE url = %(url)s) AS exists",
                {'url': url},
                fetch=True,
                fetch_one=True
            )
            return result['exists'] if result else False

        except Exception as e:
            logfire.error(
                "Error checking URL existence",
                url=url,
                error=str(e)
            )
            return False


    def get_frontier_statistics(self, category: str) -> Optional[FrontierStatistics]:
        """Get statistics for frontier URLs in category"""
        try:
            result = self.execute_query("""
                SELECT 
                    COUNT(*) as total_urls,
                    SUM(CASE WHEN is_target THEN 1 ELSE 0 END) as target_urls,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_urls,
                    SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed_urls,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_urls,
                    COUNT(DISTINCT main_domain) as unique_domains,
                    MAX(depth) as max_reached_depth,
                    MIN(insert_date) as first_url_date,
                    MAX(last_update) as last_update_date
                FROM frontier_url
                WHERE category = %s
            """, (category,), fetch=True)

            if not result or not result[0]['total_urls']:
                return None

            stats = result[0]
            
            # Calculate success rate
            total_processed = stats['processed_urls'] + stats['failed_urls']
            success_rate = (
                (stats['processed_urls'] / total_processed * 100)
                if total_processed > 0 else 0
            )

            return FrontierStatistics(
                category=category,
                success_rate=success_rate,
                **stats
            )

        except Exception as e:
            logfire.error(
                "Error getting frontier statistics",
                category=category,
                error=str(e)
            )
            return None