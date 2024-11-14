# src/crawler/crud/config_url_log_crud.py

from typing import Optional, Dict, Any
from datetime import datetime
import logfire

from crawler.crud.basic_crud import BaseCRUD
from crawler.models.config_url_log_model import ConfigUrlLog, ConfigState
class ConfigUrlLogCRUD(BaseCRUD):
    """CRUD operations for config_url_log table using aiosql queries"""

    def __init__(self, conn, queries):
        super().__init__(conn, queries)
        self.table = "config_url_log"

    def create_log(self, log: ConfigUrlLog) -> Optional[int]:
        """Create or update a config URL log entry"""
        try:
            # Convert model to dict for query params
            data = {
                'url': str(log.url),
                'category': log.category,
                'url_type': log.url_type,
                'config_state': log.config_state.value,
                'max_depth': log.max_depth,
                'target_patterns': log.target_patterns,
                'seed_pattern': log.seed_pattern,
                'start_time': datetime.now()
            }

            result = self.queries.upsert_config_log(self.conn, **data)
            
            if result:
                if isinstance(result, dict):
                    return result['id']
                elif isinstance(result, tuple):
                    return result[0]  
                return result  # If result is just an int
                
            return None

        except Exception as e:
            logfire.error(
                "Error creating/updating ConfigUrlLog entry",
                url=str(log.url),
                error=str(e)
            )
            raise



    def update_state(
        self,
        log_id: int,
        state: ConfigState,
        error_message: Optional[str] = None,
        target_count: int = 0,
        seed_count: int = 0
    ) -> None:
        """Update config URL state and counts"""
        try:
            # Prepare parameters for the query
            params = {
                'log_id': log_id,
                'config_state': state.value,
                'error_message': error_message,
                'target_count': target_count,
                'seed_count': seed_count,
                'end_time': datetime.now()
            }

            # Execute the update query
            self.queries.update_config_state(self.conn, **params)

        except Exception as e:
            logfire.error(
                "Error updating ConfigUrlLog state",
                log_id=log_id,
                error=str(e)
            )
            raise

    def get_log_id(self, url: str, category: str) -> Optional[int]:
        """Get the log ID for a given URL and category"""
        try:
            result = self.execute_query(
                "SELECT id FROM config_url_log WHERE url = %(url)s AND category = %(category)s",
                {'url': url, 'category': category},
                fetch=True,
                fetch_one=True
            )
            return result['id'] if result else None
        except Exception as e:
            logfire.error(
                "Error getting ConfigUrlLog ID",
                url=url,
                category=category,
                error=str(e)
            )
            return None

    def start_processing(self, log_id: int) -> None:
        """Mark config URL as starting processing"""
        try:
            self.queries.start_config_processing(
                self.conn,
                log_id=log_id
            )

            logfire.debug(
                "Started processing ConfigUrlLog entry",
                log_id=log_id
            )

        except Exception as e:
            logfire.error(
                "Error starting processing of ConfigUrlLog entry",
                log_id=log_id, 
                error=str(e)
            )
            raise

    def increment_counters(
        self,
        log_id: int,
        target_count: int = 0,
        seed_count: int = 0,
        failed_count: int = 0
    ) -> None:
        """Increment counters in the ConfigUrlLog entry"""
        try:
            # Build the SET clause dynamically based on which counts are being incremented
            set_clauses = []
            params = {'log_id': log_id}
            if target_count:
                set_clauses.append("target_urls_found = target_urls_found + %(target_count)s")
                params['target_count'] = target_count
            if seed_count:
                set_clauses.append("seed_urls_found = seed_urls_found + %(seed_count)s")
                params['seed_count'] = seed_count
            if failed_count:
                set_clauses.append("failed_urls = failed_urls + %(failed_count)s")
                params['failed_count'] = failed_count

            if not set_clauses:
                # Nothing to update
                return

            query = f"""
                UPDATE config_url_log
                SET {', '.join(set_clauses)},
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %(log_id)s
            """

            self.execute_query(query, params)

            logfire.debug(
                "Incremented counters in ConfigUrlLog entry",
                log_id=log_id,
                increments=params
            )

        except Exception as e:
            logfire.error(
                "Error incrementing counters in ConfigUrlLog entry",
                log_id=log_id,
                error=str(e)
            )
            raise

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get overall processing statistics"""
        try:
            result = self.execute_query("""
                SELECT
                    COUNT(*) as total_configs,
                    SUM(CASE WHEN config_state = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN config_state = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(target_urls_found) as total_targets,
                    SUM(seed_urls_found) as total_seeds,
                    SUM(failed_urls) as total_failures,
                    AVG(processing_duration) as avg_duration,
                    MAX(processing_duration) as max_duration
                FROM config_url_log
            """, fetch=True, fetch_one=True)

            return result if result else {}

        except Exception as e:
            logfire.error(
                "Error getting processing statistics from ConfigUrlLog",
                error=str(e)
            )
            return {}
