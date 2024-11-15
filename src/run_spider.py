# src/run_spider.py

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
    # Get project root
    project_root = Path(__file__).resolve().parent.parent
    
    # Add project paths
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))
    
    # Set working directory
    os.chdir(project_root)
    
    # Load env vars
    load_dotenv()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run the frontier spider')
    parser.add_argument('--url_seed_root_id', 
                       type=int,
                       help='Specific url_seed_root_id to process from config',
                       required=False)
    return parser.parse_args()

def main():
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Setup environment
        setup_environment()
        
        # Install asyncio reactor
        install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
        
        # Import modules that depend on the reactor after it's installed
        from crawler.utils.logging_utils import setup_logging
        setup_logging()
        from crawler.database import db_manager
        
        # Initialize database
        db_manager.initialize()
        
        # Configure logging without installing root handler
        configure_logging(install_root_handler=False)
        
        # Get settings
        settings = get_project_settings()
        
        # Create process
        process = CrawlerProcess(settings)
        
        # Import spider only after reactor is set
        from crawler.spiders.frontier_spider import FrontierSpider
        
        # Start crawling with optional url_seed_root_id
        logfire.info("Starting crawler process", 
                    url_seed_root_id=args.url_seed_root_id if args.url_seed_root_id is not None else "all")
        process.crawl(FrontierSpider, url_seed_root_id=args.url_seed_root_id)
        process.start()
        
    except Exception as e:
        logfire.error(f"Failed to run crawler: {e}")
        raise

if __name__ == "__main__":
    main()