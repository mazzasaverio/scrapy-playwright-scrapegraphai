# src/crawler/items.py

import scrapy
from typing import Optional

class UrlItem(scrapy.Item):
    """Item representing a URL found during crawling"""
    url = scrapy.Field()
    category = scrapy.Field()
    type = scrapy.Field()
    depth = scrapy.Field()
    is_target = scrapy.Field()
    found_on = scrapy.Field()  # URL where this was found

class ConfigUrlLogItem(scrapy.Item):
    """Item representing a log entry for config URLs"""
    url = scrapy.Field()
    category = scrapy.Field()
    type = scrapy.Field()
    success = scrapy.Field()
    status = scrapy.Field()