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
        items = []
        target_count = 0
        seed_count = 0

        try:
            if self.type == 0:
                # Tipo 0: URL target diretto
                items.append(self._create_target_item(url))
                target_count += 1

            elif self.type == 1:
                # Tipo 1: Estrai URL target
                target_items = self._process_target_links(found_links, current_depth)
                items.extend(target_items)
                target_count = len(target_items)

            elif self.type == 2:
                if current_depth < self.max_depth:
                    # Estrai sia target che seed URL
                    target_items = self._process_target_links(found_links, current_depth)
                    seed_items = self._process_seed_links(found_links, current_depth)
                    items.extend(target_items)
                    items.extend(seed_items)
                    target_count = len(target_items)
                    seed_count = len(seed_items)
                elif current_depth == self.max_depth:
                    # Estrai solo target URL
                    target_items = self._process_target_links(found_links, current_depth)
                    items.extend(target_items)
                    target_count = len(target_items)
                    # Non estrarre seed URL al livello massimo di profondità
                else:
                    # Profondità massima raggiunta, non fare nulla
                    pass

            # Logga i risultati
            logfire.info(
                f"Processed URLs at depth {current_depth}",
                url=url,
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
        



    def _process_target_links(self, links: List[str], current_depth: int) -> List[UrlItem]:
        items = []
        for link in links:
            if not is_valid_url(link):
                continue
                
            if matches_pattern(link, self.target_patterns):
                logfire.info(f"Found target URL at depth {current_depth}: {link}")
                items.append(UrlItem(
                    url=link,
                    category=self.category,
                    type=self.type,
                    depth=current_depth,
                    is_target=True,
                    max_depth=self.max_depth,
                    target_patterns=self.target_patterns,
                    seed_pattern=self.seed_pattern
                ))
        return items

    def _process_seed_links(self, links: List[str], current_depth: int) -> List[UrlItem]:
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
                    is_target=False,
                    max_depth=self.max_depth,
                    target_patterns=self.target_patterns,
                    seed_pattern=self.seed_pattern
                ))
        return items