# src/crawler/pipelines.py

from typing import Dict, Any
import logfire
from crawler.database import db_manager
from twisted.internet import defer

class DatabasePipeline:
    """Pipeline for storing URLs in the database"""
    
    def __init__(self):
        self.db_initialized = False
    
    @defer.inlineCallbacks
    def open_spider(self, spider):
        """Initialize database connection"""
        if not self.db_initialized:
            yield db_manager.initialize()
            self.db_initialized = True
            logfire.info("Database pipeline initialized")
    
    @defer.inlineCallbacks
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Store URL in frontier database"""
        try:
            url_id = yield db_manager.store_frontier_url(
                url=item["url"],
                category=item["category"],
                type_=item["type"],
                depth=item.get("depth", 0),
                is_target=item["is_target"]
            )
            
            if url_id:
                logfire.info(
                    "Stored URL in frontier",
                    url=item["url"],
                    type=item["type"],
                    is_target=item["is_target"]
                )
            
            return item
            
        except Exception as e:
            logfire.error(
                "Error storing URL in database",
                url=item["url"],
                error=str(e)
            )
            raise
    
    @defer.inlineCallbacks
    def close_spider(self, spider):
        """Close database connection"""
        if self.db_initialized:
            yield db_manager.close()
            logfire.info("Database pipeline closed")