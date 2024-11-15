# src/crawler/utils/crawl_manager.py

from typing import  List, Dict, Any
from crawler.utils.url_utils import matches_pattern, is_valid_url
from crawler.items import UrlItem
import logfire

class CrawlManager:
    def __init__(self, category: str, url_config: Dict[str, Any]):
        self.category = category
        self.url_config = url_config
        self.type = url_config.get('type')
        self.target_patterns = url_config.get('target_patterns', [])
        self.seed_pattern = url_config.get('seed_pattern')
        self.max_depth = url_config.get('max_depth', 0)
        
    # src/crawler/utils/crawl_manager_utils.py

    def process_url(self, url: str, found_links: List[str], current_depth: int = 0) -> List[UrlItem]:
        """Process URLs and return items"""
        items = []
        target_count = 0
        seed_count = 0

        try:
            if self.type == 0:
                # Type 0: Direct target URL
                items.append(self._create_target_item(url))
                target_count += 1
                
            elif self.type == 1:
                # Type 1: Extract target URLs
                target_items = self._process_target_links(found_links)
                items.extend(target_items)
                target_count = len(target_items)
                
            elif self.type == 2 and current_depth < self.max_depth:
                # Type 2: Extract target and seed URLs
                target_items = self._process_target_links(found_links)
                seed_items = self._process_seed_links(found_links, current_depth)
                items.extend(target_items)
                items.extend(seed_items)
                target_count = len(target_items)
                seed_count = len(seed_items)

            logfire.info(
                f"Processed URLs at depth {current_depth}",
                url_type=self.type,
                target_count=target_count,
                seed_count=seed_count
            )
            
            return items

        except Exception as e:
            logfire.error(
                "Error processing URLs",
                url=url,
                error=str(e),
                url_type=self.type
            )
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
                    is_target=True,
                    max_depth=self.max_depth,  
                    target_patterns=self.target_patterns,  
                    seed_pattern=self.seed_pattern 
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