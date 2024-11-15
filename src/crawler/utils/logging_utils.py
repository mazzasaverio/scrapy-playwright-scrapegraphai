# src/crawler/utils/logging_utils.py

import logging
import os
import logfire

def setup_logging():
    """Configure logging with logfire."""
    # Get LEVEL_DEEP_LOGGING from environment
    LEVEL_DEEP_LOGGING = os.getenv('LEVEL_DEEP_LOGGING', 'INFO').upper()

    # Validate LEVEL_DEEP_LOGGING
    valid_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
    if LEVEL_DEEP_LOGGING not in valid_levels:
        LEVEL_DEEP_LOGGING = 'INFO'

    min_log_level = getattr(logging, LEVEL_DEEP_LOGGING, logging.INFO)

    # Configure logfire
    logfire.configure(
        console=logfire.ConsoleOptions(
            span_style="indented",
            min_log_level=LEVEL_DEEP_LOGGING.lower(),
            verbose=True,
            show_project_link=False,
            include_timestamps=True
        )
    )

    # Configure logging based on LEVEL_DEEP_LOGGING
    if LEVEL_DEEP_LOGGING in ['ERROR', 'INFO']:
        # Disable all other loggers
        logging.getLogger().setLevel(logging.CRITICAL)
        loggers_to_disable = [
            'scrapy',
            'playwright',
            'scrapy_playwright',
            'scrapy-playwright',
            'twisted',
            'asyncio',
            'urllib3',
            'filelock',
            'parso',
            'asyncio.python',
            'scrapy.utils.log',
            'scrapy.middleware',
            'scrapy.core.engine',
            'scrapy.core.scraper',
            'scrapy.utils.signal',
            'twisted.internet.protocol',
            'twisted.internet.defer',
            'scrapy.statscollectors',
            'scrapy.logformatter',
            'scrapy.crawler',
            'scrapy.dupefilters',
            'scrapy.spidermiddlewares',
            'scrapy.extensions',
            'scrapy.core'
        ]

        for logger_name in loggers_to_disable:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.CRITICAL)
            logger.propagate = False
            logger.disabled = True
            logger.handlers = []
    else:
        # Set logging level for root logger
        logging.getLogger().setLevel(min_log_level)
        # Optionally, adjust logging levels for specific loggers
        logging.getLogger('scrapy').setLevel(min_log_level)
        logging.getLogger('playwright').setLevel(min_log_level)
        logging.getLogger('scrapy_playwright').setLevel(min_log_level)
        logging.getLogger('scrapy-playwright').setLevel(min_log_level)
        logging.getLogger('twisted').setLevel(min_log_level)
        # Add any other loggers you wish to configure

    # Configure the formatter for the logs you want to see
    handler = logfire.LogfireLoggingHandler()

    # Configure basic logging
    logging.basicConfig(
        handlers=[handler],
        format="%(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        level=min_log_level  # Set to the level determined by LEVEL_DEEP_LOGGING
    )

# Export logfire for use in other modules
logger = logfire


def write_to_log(filename: str, content: dict, current_depth: int, page_url: str):
    """Write crawling results to log file
    
    Args:
        filename: Log file path
        content: Dict containing found_links, target_urls and seed_urls
        current_depth: Current crawling depth
        page_url: URL of current page
    """
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\n\n{'='*50}\n")
        f.write(f"DEPTH {current_depth} - PAGE: {page_url}\n")
        f.write(f"{'='*50}\n\n")
        
        f.write("ALL FOUND LINKS:\n")
        f.write("-" * 20 + "\n")
        for i, link in enumerate(content['found_links'], 1):
            f.write(f"{i}. {link}\n")

        f.write(f"\nTARGET URLS FOUND ({len(content['target_urls'])}):\n")
        f.write("-" * 20 + "\n")
        for i, url in enumerate(content['target_urls'], 1):
            f.write(f"{i}. {url}\n")
            
        f.write(f"\nSEED URLS FOUND ({len(content['seed_urls'])}):\n")
        f.write("-" * 20 + "\n")
        for i, url in enumerate(content['seed_urls'], 1):
            f.write(f"{i}. {url}\n")
        
        f.write("\n" + "="*50 + "\n")