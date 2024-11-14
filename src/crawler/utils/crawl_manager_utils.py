# src/crawler/utils/crawl_manager.py

from typing import Optional, List, Dict, Any
from crawler.utils.url_utils import matches_pattern, is_valid_url
from crawler.items import UrlItem, ConfigUrlLogItem
import logfire

class CrawlManager:
    def __init__(self, category: str, url_config: Dict[str, Any]):
        self.category = category
        self.url_config = url_config
        self.type = url_config.get('type')
        self.target_patterns = url_config.get('target_patterns', [])
        self.seed_pattern = url_config.get('seed_pattern')
        self.max_depth = url_config.get('max_depth', 0)
        
    def process_url(self, url: str, found_links: List[str], current_depth: int = 0) -> List[UrlItem]:
        items = []
        if self.type == 0:
            # Type 0: Direct target URL
            items.append(self._create_target_item(url))
        elif self.type == 1:
            # Type 1: Extract target URLs
            items.extend(self._process_target_links(found_links))
        elif self.type == 2 and current_depth < self.max_depth:
            # Type 2: Extract target and seed URLs
            items.extend(self._process_target_links(found_links))
            items.extend(self._process_seed_links(found_links, current_depth))
        return items
    
    def _create_target_item(self, url: str) -> UrlItem:
        return UrlItem(
            url=url,
            category=self.category,
            type=self.type,
            depth=0,
            is_target=True
        )
        
    def _process_target_links(self, links: List[str]) -> List[UrlItem]:
        """Process links to find target URLs"""
        items = []
        for link in links:
            if not is_valid_url(link):
                continue
                
            if matches_pattern(link, self.target_patterns):
                items.append(UrlItem(
                    url=link,
                    category=self.category, 
                    type=self.type,
                    depth=0,
                    is_target=True
                ))
        return items
        
    def _process_seed_links(self, links: List[str], current_depth: int) -> List[UrlItem]:
        """Process links to find seed URLs"""
        items = []
        for link in links:
            if not is_valid_url(link):
                continue
                
            if self.seed_pattern and matches_pattern(link, [self.seed_pattern]):
                items.append(UrlItem(
                    url=link,
                    category=self.category,
                    type=self.type, 
                    depth=current_depth + 1,
                    is_target=False
                ))
        return items