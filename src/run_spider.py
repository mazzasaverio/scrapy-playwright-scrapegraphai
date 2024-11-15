import os
import sys
from pathlib import Path
import asyncio
import argparse
from scrapy.utils.reactor import install_reactor
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
import logfire
from dotenv import load_dotenv

def setup_environment():
    """Setup environment variables and paths"""
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))
    os.chdir(project_root)
    load_dotenv()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run the frontier spider')
    parser.add_argument('--url_seed_root_id', 
                       type=int,
                       help='Specific url_seed_root_id to process from config',
                       required=False)
    parser.add_argument('--log_level',
                       choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                       default='INFO',
                       help='Set logging level (default: INFO)')
    return parser.parse_args()

def main():
    try:
        args = parse_arguments()
        setup_environment()
        
        # Set logging level from command line argument
        os.environ['LEVEL_DEEP_LOGGING'] = args.log_level
        
        install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
        
        from crawler.utils.logging_utils import setup_logging
        setup_logging()
        from crawler.database import db_manager
        
        db_manager.initialize()
        configure_logging(install_root_handler=False)
        
        settings = get_project_settings()
        process = CrawlerProcess(settings)
        
        from crawler.spiders.frontier_spider import FrontierSpider
        
        logfire.info("Starting crawler process", 
                    url_seed_root_id=args.url_seed_root_id if args.url_seed_root_id is not None else "all",
                    log_level=args.log_level)
        process.crawl(FrontierSpider, url_seed_root_id=args.url_seed_root_id)
        process.start()
        
    except Exception as e:
        logfire.error(f"Failed to run crawler: {e}")
        raise

if __name__ == "__main__":
    main()