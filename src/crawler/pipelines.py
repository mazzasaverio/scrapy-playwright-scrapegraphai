# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class CrawlerPipeline:
    def process_item(self, item, spider):
        return item


# src/crawler/pipelines.py

import asyncio
from typing import Dict, Any
import logfire
from crawler.database import db_manager

class DatabasePipeline:
    """Pipeline for storing URLs in the database"""
    
    async def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Store URL in frontier database"""
        try:
            url_id = await db_manager.store_frontier_url(
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
            
    async def open_spider(self, spider):
        """Initialize database connection"""
        await db_manager.initialize()
        
    async def close_spider(self, spider):
        """Close database connection"""
        await db_manager.close()