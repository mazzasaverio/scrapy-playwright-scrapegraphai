from urllib.parse import urljoin

from crawler.utils.url_utils import is_valid_url

import scrapy
import traceback
import logfire
from crawler.utils.config_utils import load_crawler_config
from crawler.utils.crawl_manager_utils import CrawlManager
from crawler.items import ConfigUrlLogItem, UrlItem
from crawler.utils.playwright_utils import PlaywrightPageManager
from crawler.utils.logging_utils import setup_logging
setup_logging()
class FrontierSpider(scrapy.Spider):
    name = "frontier_spider"
    
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,  # Must be True in Docker
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        },
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
  
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = load_crawler_config()
     
    def start_requests(self):
        """Generate initial requests from config"""

        try:
            for category in self.config.get('categories', []):
                category_name = category['name']

                for url_config in category.get('urls', []):
                    url = url_config['url']
                    url_type = url_config['type']
                    
                    if url_type == 0:
                        # Type 0: Direct target URL
                        yield scrapy.Request(
                            url=url,
                            callback=self.parse_direct,
                            errback=self.errback_direct,
                            meta={
                                'category': category_name,
                                'url_config': url_config,
                                'depth': 0
                            },
                            dont_filter=True  # Important if you want to revisit URLs
                        )
                    
                    elif url_type in (1, 2):
                        # Type 1 and 2 require DOM manipulation, use Playwright
                        yield scrapy.Request(
                            url=url,
                            callback=self.parse_with_playwright,
                            errback=self.errback_playwright,
                            meta={
                                'playwright': True,
                                'playwright_include_page': True,
                                'full_page': True,
                                'category': category_name,
                                'url_config': url_config,
                                'depth': 0
                            },
                            dont_filter=True  # Important if you want to revisit URLs
                        )
                    else:
                        logfire.warning(f"Unsupported URL type: {url_type}", url=url)
           
        except Exception as e:
            logfire.error(
                "Error during start_requests",
                error=str(e),
                traceback=traceback.format_exc()
            )

    def parse_direct(self, response):
        """Parse direct requests (Type 0)"""
        category = response.meta.get('category')
        url_config = response.meta.get('url_config')
        url = response.url

        # Mark URL as running
        yield ConfigUrlLogItem(
            url=url,
            category=category,
            type=url_config['type'],
            status='running'
        )

        # Create UrlItem
        yield UrlItem(
            url=url,
            category=category,
            type=url_config['type'],
            depth=0,
            is_target=True,
            max_depth=url_config.get('max_depth', 0),
            target_patterns=url_config.get('target_patterns'),
            seed_pattern=url_config.get('seed_pattern')
        )

        # Update ConfigUrlLog to completed
        yield ConfigUrlLogItem(
            url=url,
            category=category,
            type=url_config['type'],
            status='completed',
            target_count=1,
            seed_count=0
        )

    def errback_direct(self, failure):
        """Handle exceptions in direct requests"""
        logfire.error(
            "Direct request failed",
            url=failure.request.url,
            error=str(failure.value),
            traceback=failure.getTraceback().decode()
        )
        
        # Update ConfigUrlLog with failure
        category = failure.request.meta.get('category')
        url_config = failure.request.meta.get('url_config')
        yield ConfigUrlLogItem(
            url=failure.request.url,
            category=category,
            type=url_config['type'],
            status='failed',
            error_message=str(failure.value)
        )

    async def parse_with_playwright(self, response):
        """Parse response using Playwright for dynamic content"""
        page = response.meta.get('playwright_page')
        if not page:
            logfire.error("No Playwright page in response meta", url=response.url)
            return

        category = response.meta.get('category')
        url_config = response.meta.get('url_config')
        current_depth = response.meta.get('depth', 0)
        parent_url = response.meta.get('parent_url')
        
        target_count = 0
        seed_count = 0
        
        try:
           
            # Create initial log entry
            if current_depth == 0:
                yield ConfigUrlLogItem(
                    url=response.url,
                    category=category,
                    type=url_config['type'],
                    status='running',
                    max_depth=url_config.get('max_depth', 0),
                    target_patterns=url_config.get('target_patterns'),
                    seed_pattern=url_config.get('seed_pattern')
                )

            # Initialize page manager and process page
            page_manager = PlaywrightPageManager(page)
            await page_manager.initialize_page()
            
            content = await page.content()
            base_url = page.url
            
            # Extract and process links
            sel = scrapy.Selector(text=content, base_url=base_url)
            found_links = sel.css('a::attr(href)').getall()
            found_links = [urljoin(base_url, href) for href in found_links if href]
            found_links = [link for link in found_links if is_valid_url(link)]
            
            logfire.debug(
                "Found links",
                url=response.url,
                link_count=len(found_links)
            )

            # Process links
            crawl_manager = CrawlManager(category, url_config)
            items = crawl_manager.process_url(
                response.url, found_links, current_depth
            )
            
            for item in items:
                if isinstance(item, UrlItem):
                    item['parent_url'] = parent_url
                    item['max_depth'] = url_config.get('max_depth', 0)
                    item['target_patterns'] = url_config.get('target_patterns')
                    item['seed_pattern'] = url_config.get('seed_pattern')
                    
                    if item['is_target']:
                        target_count += 1
                    else:
                        seed_count += 1
                        
                    yield item
                    
                    # Generate new requests for seed URLs
                    if not item['is_target'] and current_depth + 1 <= url_config.get('max_depth', 0):
                        yield scrapy.Request(
                            url=item['url'],
                            callback=self.parse_with_playwright,
                            errback=self.errback_playwright,
                            meta={
                                'playwright': True,
                                'playwright_include_page': True,
                                'category': category,
                                'url_config': url_config,
                                'depth': current_depth + 1,
                                'parent_url': response.url
                            },
                            dont_filter=True
                        )
        
            
            # Update final status
            if current_depth == 0:
                logfire.info(
                    "Completing config log",
                    url=response.url,
                    category=category,
                    target_count=target_count,
                    seed_count=seed_count
                )
                yield ConfigUrlLogItem(
                    url=response.url,
                    category=category,
                    type=url_config['type'],
                    status='completed',
                    target_count=target_count,
                    seed_count=seed_count
                )

        except Exception as e:
            logfire.error(
                "Error processing page",
                url=response.url,
                error=str(e),
                traceback=traceback.format_exc()
            )
            
            if current_depth == 0:
                yield ConfigUrlLogItem(
                    url=response.url,
                    category=category,
                    type=url_config['type'],
                    status='failed',
                    error_message=str(e)
                )
                
        finally:
            try:
                await page_manager.cleanup()
            except Exception as e:
                logfire.error(f"Error during cleanup: {e}")

    async def errback_playwright(self, failure):
        """Handle Playwright failures"""
        logfire.error(
            "Playwright request failed",
            url=failure.request.url,
            meta=failure.request.meta,
            error_type=str(type(failure.value)),
            error_details=str(failure.value),
            error_repr=repr(failure.value),
            traceback=failure.getTraceback().decode()
        )
        
        # Try to close the page if it exists
        try:
            page = failure.request.meta.get('playwright_page')
            if page:
                await page.close()
        except Exception as e:
            logfire.error(f"Error closing page in errback: {str(e)}")
        
        # Update ConfigUrlLog with failure if at depth 0
        if failure.request.meta.get('depth', 0) == 0:
            category = failure.request.meta.get('category')
            url_config = failure.request.meta.get('url_config')
            yield ConfigUrlLogItem(
                url=failure.request.url,
                category=category,
                type=url_config['type'],
                status='failed',
                error_message=str(failure.value)
            )

    def closed(self, reason):
        """Called when the spider is closed"""
        logfire.info("Spider closing", reason=reason)