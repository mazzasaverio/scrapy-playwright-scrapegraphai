
import logging
import logfire

def setup_logging():
    """Configure logging with logfire."""
    # Configura logfire
    logfire.configure(
        console=logfire.ConsoleOptions(
            min_log_level='info',
            verbose=True,
            show_project_link=False,
            include_timestamps=True
        )
    )

    # Disabilita TUTTI i log di sistema
    logging.getLogger().setLevel(logging.WARNING)
    loggers_to_disable = [
        'scrapy',
        'playwright',
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

    # Configura il formatter per i log che vuoi vedere
    handler = logfire.LogfireLoggingHandler()
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    
    # Configura il logging di base
    logging.basicConfig(
        handlers=[handler],
        format='%(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.WARNING  # Importante: metti WARNING qui per sopprimere i log di sistema
    )

# Esporta logfire per l'uso in altri moduli
logger = logfire