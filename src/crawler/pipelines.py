# src/crawler/pipelines.py
import logfire
from crawler.items import UrlItem, ConfigUrlLogItem
from crawler.models.frontier_model import (
    FrontierUrl, 
    UrlState, 
    UrlType
)
from crawler.models.config_url_log_model import (
    ConfigUrlLog, 
)

class DatabasePipeline:
    
    def process_item(self, item, spider):
        if isinstance(item, UrlItem):
            self._process_url_item(item)
        elif isinstance(item, ConfigUrlLogItem):
            self._process_config_log_item(item)
        return item

    def _process_config_log_item(self, item: ConfigUrlLogItem):
        category = item['category']
        url = item['url']
        status = item['status']
        log_entry = ConfigUrlLog(
            url=url,
            category=category,
            url_type=item['type'],
            config_state=status,
            max_depth=item.get('max_depth', 0),
            target_patterns=item.get('target_patterns'),
            seed_pattern=item.get('seed_pattern'),
            error_message=item.get('error_message'),
            target_urls_found=item.get('target_count', 0),
            seed_urls_found=item.get('seed_count', 0)
        )

        if status == 'pending':
            # Create a new log entry
            self.config_crud.create_log(log_entry)
        else:
            # Update existing log entry
            self.config_crud.update_state(
                url=url,
                category=category,
                state=status,
                error_message=item.get('error_message'),
                target_count=item.get('target_count', 0),
                seed_count=item.get('seed_count', 0)
            )

    def _process_url_item(self, item: UrlItem):
        """Process URL items using FrontierCRUD"""
        try:
            # Update stats cache
            category = item['category']
            if category not in self.stats_cache:
                self.stats_cache[category] = {
                    'target_count': 0,
                    'seed_count': 0
                }
                
            if item['is_target']:
                self.stats_cache[category]['target_count'] += 1
            else:
                self.stats_cache[category]['seed_count'] += 1

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

            # Check if URL exists
            if not self.frontier_crud.exists_in_frontier(str(frontier_url.url)):
                self.frontier_crud.create_url(frontier_url)
                logfire.debug(
                    "Created new frontier URL", 
                    url=str(frontier_url.url),
                    category=frontier_url.category
                )
                
        except Exception as e:
            logfire.error(f"Error storing URL: {e}", url=str(item['url']))
            raise

