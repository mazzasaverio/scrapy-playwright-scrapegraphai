# src/run_spider.py

import os
import sys
from pathlib import Path
import asyncio
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

def main():
    try:
        # Setup environment
        setup_environment()
        
        # Install asyncio reactor
        install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
        
        # Configure logging
        configure_logging()
        
        # Get settings
        settings = get_project_settings()
        

        # Create process
        process = CrawlerProcess(settings)
        
        # Import spider only after reactor is set
        from crawler.spiders.frontier_spider import FrontierSpider
        
        # Start crawling
        logfire.info("Starting crawler process")
        process.crawl(FrontierSpider)
        process.start()
        
    except Exception as e:
        logfire.error(f"Failed to run crawler: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logfire.info("Crawler stopped by user")
    except Exception as e:
        logfire.error(f"Crawler failed: {e}")
        raise