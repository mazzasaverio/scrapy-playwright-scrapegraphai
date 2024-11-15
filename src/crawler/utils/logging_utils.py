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
