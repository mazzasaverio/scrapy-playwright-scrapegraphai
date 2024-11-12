# src/crawler/spiders/frontier_spider.py

import scrapy
import logfire
from crawler.utils.config_utils import load_crawler_config
from crawler.utils.crawl_manager_utils import CrawlManager
from crawler.items import ConfigUrlLogItem
from crawler.utils.playwright_utils import PlaywrightPageManager
from crawler.utils.logging_utils import setup_logging

class FrontierSpider(scrapy.Spider):
    name = "frontier_spider"
    
    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "args": [
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
            "headless": False,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setup_logging()
        self.config = load_crawler_config()
        
    def start_requests(self):
        """Generate initial requests from config"""
        logfire.info("Starting crawler process")
        
        for category in self.config.get('categories', []):
            category_name = category['name']
            
            for url_config in category.get('urls', []):
                url = url_config['url']
                url_type = url_config['type']
                
                # Type 1 and 2 require DOM manipulation, use Playwright
                if url_type in (1, 2):
                    logfire.info(f"Creating Playwright request for {url}", type=url_type)
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_with_playwright,
                        meta={
                            'playwright': True,
                            'playwright_include_page': True,
                            'playwright_page_methods': PlaywrightPageManager.get_default_page_methods(),
                            'category': category_name,
                            'url_config': url_config,
                            'depth': 0
                        }
                    )
                else:
                    # Type 0 is direct URL processing
                    logfire.info(f"Creating direct request for {url}", type=url_type)
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_direct,
                        meta={
                            'category': category_name,
                            'url_config': url_config,
                        }
                    )

    async def parse_with_playwright(self, response):
        """Parse response using Playwright for dynamic content"""
        page = response.meta['playwright_page']
        category = response.meta['category']
        url_config = response.meta['url_config']
        current_depth = response.meta.get('depth', 0)
        
        try:
            page_manager = PlaywrightPageManager(page)
            await page_manager.initialize_page()

            # Extract links using Scrapy's selectors from rendered content
            content = await page.content()
            sel = scrapy.Selector(text=content)
            found_links = []
            for href in sel.css('a::attr(href)').getall():
                abs_url = response.urljoin(href)
                if abs_url:
                    found_links.append(abs_url)
            
            # Process links
            crawl_manager = CrawlManager(category, url_config)
            items = crawl_manager.process_url(response.url, found_links, current_depth)
            
            # Update config URL log
            yield ConfigUrlLogItem(
                url=response.url,
                category=category,
                type=url_config['type'],
                success=True,
                status='completed'
            )
            
            # Yield found items
            for item in items:
                yield item
                
            logfire.info(
                "Processed page with Playwright", 
                url=response.url, 
                found_links=len(found_links),
                items=len(items)
            )
            
        except Exception as e:
            logfire.error(
                "Error processing page with Playwright",
                url=response.url,
                error=str(e)
            )
            yield ConfigUrlLogItem(
                url=response.url,
                category=category,
                type=url_config['type'],
                success=False,
                status=str(e)
            )
        finally:
            await page_manager.cleanup()

    async def parse_direct(self, response):
        """Parse direct URLs (Type 0) without Playwright"""
        category = response.meta['category']
        url_config = response.meta['url_config']
        
        try:
            crawl_manager = CrawlManager(category, url_config)
            items = crawl_manager.process_url(response.url, [], 0)
            
            yield ConfigUrlLogItem(
                url=response.url,
                category=category,
                type=url_config['type'],
                success=True,
                status='completed'
            )
            
            for item in items:
                yield item
                
            logfire.info(
                "Processed direct URL", 
                url=response.url, 
                items=len(items)
            )
            
        except Exception as e:
            logfire.error(
                "Error processing direct URL",
                url=response.url,
                error=str(e)
            )
            yield ConfigUrlLogItem(
                url=response.url,
                category=category,
                type=url_config['type'],
                success=False,
                status=str(e)
            )

    def closed(self, reason):
        if reason == 'finished':
            logfire.info("Crawler process completed successfully")
        else:
            logfire.error("Crawler process failed", reason=reason)