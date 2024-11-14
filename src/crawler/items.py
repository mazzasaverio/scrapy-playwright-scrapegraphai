# src/crawler/items.py

import scrapy
from typing import Optional, List

class UrlItem(scrapy.Item):
    url = scrapy.Field()
    category = scrapy.Field() 
    type = scrapy.Field()
    depth = scrapy.Field()
    is_target = scrapy.Field()
    parent_url = scrapy.Field()
    target_patterns = scrapy.Field()
    seed_pattern = scrapy.Field()
    max_depth = scrapy.Field()
    error = scrapy.Field()
    

class ConfigUrlLogItem(scrapy.Item):
    url = scrapy.Field()
    category = scrapy.Field()
    type = scrapy.Field()
    status = scrapy.Field()
    max_depth = scrapy.Field()
    target_patterns = scrapy.Field()
    seed_pattern = scrapy.Field()
    target_count = scrapy.Field()
    seed_count = scrapy.Field()
    error_message = scrapy.Field()
