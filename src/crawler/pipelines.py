# src/crawler/pipelines.py

import logfire
from crawler.items import UrlItem, ConfigUrlLogItem
from crawler.models.frontier_model import FrontierUrl, UrlState, UrlType
from crawler.models.config_url_log_model import ConfigUrlLog, ConfigState
from crawler.crud.config_url_log_crud import ConfigUrlLogCRUD
from crawler.crud.frontier_crud import FrontierCRUD
from crawler.database import db_manager

class DatabasePipeline:
    def __init__(self):
        # Initialize database manager
        if not db_manager.pool:
            db_manager.initialize()
        self.conn = db_manager.pool.getconn()
        self.queries = db_manager.queries
        self.config_crud = ConfigUrlLogCRUD(self.conn, self.queries)
        self.frontier_crud = FrontierCRUD(self.conn, self.queries)
        self.stats_cache = {}

    def close_spider(self, spider):
        # Release database connection
        db_manager.pool.putconn(self.conn)

    def process_item(self, item, spider):
        if isinstance(item, UrlItem):
            self._process_url_item(item)
        elif isinstance(item, ConfigUrlLogItem):
            self._process_config_log_item(item)
        return item

    def _process_config_log_item(self, item: ConfigUrlLogItem):
        try:
            category = item['category']
            url = item['url']
            status = item['status']
            
            log_entry = ConfigUrlLog(
                url=url,
                category=category,
                url_type=item['type'],
                config_state=ConfigState(status),
                max_depth=item.get('max_depth', 0),
                target_patterns=item.get('target_patterns'),
                seed_pattern=item.get('seed_pattern'),
                error_message=item.get('error_message'),
                target_urls_found=item.get('target_count', 0),
                seed_urls_found=item.get('seed_count', 0)
            )

            # CHANGED: Always create/update log entry
            log_id = self.config_crud.create_log(log_entry)
            if not log_id:
                logfire.error("Failed to create/update log entry", url=url, category=category)
                return
                
            # Update state if not pending
            if status != 'pending':
                self.config_crud.update_state(
                    log_id=log_id,
                    state=ConfigState(status),
                    error_message=item.get('error_message'),
                    target_count=item.get('target_count', 0),
                    seed_count=item.get('seed_count', 0)
                )

        except Exception as e:
            logfire.error(f"Error processing ConfigUrlLogItem: {e}", item=item)
            raise

    def _process_url_item(self, item: UrlItem):
        try:
            # Check if URL exists
            if not self.frontier_crud.exists_in_frontier(str(item['url'])):
                # Convert item to FrontierUrl model
                frontier_url = FrontierUrl(
                    url=item['url'],
                    category=item['category'],
                    url_type=UrlType(item['type']),
                    depth=item['depth'],
                    is_target=item['is_target'],
                    parent_url=item.get('parent_url'),
                    target_patterns=item.get('target_patterns'),
                    seed_pattern=item.get('seed_pattern'),
                    max_depth=item['max_depth'],
                    url_state=UrlState.PENDING
                )
                
                # Create URL in frontier
                url_id = self.frontier_crud.create_url(frontier_url)
                if url_id:
                    logfire.debug(
                        "Created new frontier URL",
                        url=str(frontier_url.url),
                        category=frontier_url.category,
                        is_target=frontier_url.is_target
                    )
                else:
                    logfire.error(
                        "Failed to create frontier URL",
                        url=str(frontier_url.url)
                    )

        except Exception as e:
            logfire.error(
                "Error storing URL",
                url=str(item['url']),
                error=str(e)
            )
            raise
