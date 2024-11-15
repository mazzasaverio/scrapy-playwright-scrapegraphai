# src/crawler/settings.py

import os
from pathlib import Path
import logfire

# Basic Scrapy Settings
BOT_NAME = "crawler"
SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"


TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DOWNLOAD_HANDLERS = {
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Database Pipeline
ITEM_PIPELINES = {
    "crawler.pipelines.DatabasePipeline": 300,
}

# Playwright Settings
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,
    "args": [
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
    ],
}

# Performance Settings
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Retry Settings 
RETRY_ENABLED = True
RETRY_TIMES = 1
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Default Headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

# Security and Cache Settings
ROBOTSTXT_OBEY = False
COOKIES_ENABLED = True
TELNETCONSOLE_ENABLED = False
# src/crawler/settings.py
# Read LEVEL_DEEP_LOGGING from environment
LEVEL_DEEP_LOGGING = os.getenv('LEVEL_DEEP_LOGGING', 'INFO').upper()

# Validate LEVEL_DEEP_LOGGING
valid_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
if LEVEL_DEEP_LOGGING not in valid_levels:
    LEVEL_DEEP_LOGGING = 'INFO'

# Set Scrapy's log level
LOG_LEVEL = LEVEL_DEEP_LOGGING

# Disable Scrapy's built-in logging if LEVEL_DEEP_LOGGING is ERROR or INFO
if LEVEL_DEEP_LOGGING in ['ERROR', 'INFO']:
    LOG_ENABLED = False
else:
    LOG_ENABLED = True

LOG_FORMAT = '%(asctime)s %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
LOG_STDOUT = True  # Capture standard output
# Export Settings
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"

DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = 30
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000


