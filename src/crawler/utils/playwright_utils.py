# src/crawler/utils/playwright_utils.py

from playwright.async_api import Page
import logfire
from typing import List, Optional, Dict, Any
import asyncio

class PlaywrightPageManager:
    """Manages common Playwright page operations and dynamic content handling"""
    
    def __init__(self, page: Page):
        self.page = page
        self.logger = logfire.logger
    
    @staticmethod
    def get_default_page_methods():
        """Returns default page methods for initial request"""
        from scrapy_playwright.page import PageMethod
        
        return [
            PageMethod("wait_for_load_state", "domcontentloaded"),
            PageMethod("wait_for_load_state", "networkidle"),
            PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
            PageMethod("wait_for_timeout", 1000),
        ]
    
    async def initialize_page(self):
        """Initialize page with common settings and handlers"""
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        await self._wait_for_page_ready()
        await self._handle_dynamic_elements()
    
    async def _wait_for_page_ready(self):
        """Wait for page to be completely loaded and stable."""
        try:
            # Wait for basic load
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Wait for network idle
            await self.page.wait_for_load_state('networkidle')
            
            # Wait for full page load
            await self.page.wait_for_load_state('load')
            
            # Scroll for lazy content
            await self.page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
                window.scrollTo(0, 0);
            """)
            
            # Short pause for JS reactions
            await self.page.wait_for_timeout(1000)

        except Exception as e:
            self.logger.warning(
                "Error waiting for page ready",
                error=str(e)
            )

    async def _handle_dynamic_elements(self):
        """Handle common dynamic page elements like popups, cookies, and load more buttons."""
        try:
            # Handle cookie and privacy banners
            await self._handle_cookie_banners()
            
            # Handle load more buttons
            await self._handle_load_more_buttons()
            
            # Handle modals
            await self._handle_modals()
            
        except Exception as e:
            self.logger.warning(f"Error handling dynamic elements: {str(e)}")

    async def _handle_cookie_banners(self):
        """Handle common cookie consent banners"""
        cookie_selectors = [
            '[id*="cookie"]', 
            '[id*="privacy"]',
            '[id*="gdpr"]',
            'button:has-text("Accetta")',
            'button:has-text("Accept")',
            'button[onclick*="cookiesPolicy"]'
        ]
        
        for selector in cookie_selectors:
            try:
                button = await self.page.wait_for_selector(selector, timeout=2000)
                if button:
                    await button.click()
                    self.logger.debug(f"Clicked cookie/privacy button: {selector}")
                    await self.page.wait_for_timeout(1000)
                    break
            except:
                continue

    async def _handle_load_more_buttons(self, max_clicks: int = 5):
        """Handle load more buttons with safety limits"""
        load_more_selectors = [
            'button:has-text("carica")', 
            'button:has-text("load")',
            'button:has-text("più")',
            'button:has-text("more")',
            '[class*="load-more"]',
            'text="carica altri"'
        ]
        
        clicks = 0
        while clicks < max_clicks:
            clicked = False
            for selector in load_more_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=2000)
                    if button and await button.is_visible():
                        await button.scroll_into_view_if_needed()
                        await button.click()
                        await self.page.wait_for_load_state('networkidle', timeout=5000)
                        clicked = True
                        clicks += 1
                        self.logger.debug(f"Clicked load more button: {selector}")
                        break
                except:
                    continue
            if not clicked:
                break

    async def _handle_modals(self):
        """Handle common modal dialogs"""
        modal_close_selectors = [
            '[class*="modal"] button[class*="close"]',
            '[class*="modal"] button[class*="dismiss"]',
            '[class*="dialog"] button[class*="close"]'
        ]
        
        for selector in modal_close_selectors:
            try:
                button = await self.page.wait_for_selector(selector, timeout=1000)
                if button and await button.is_visible():
                    await button.click()
                    self.logger.debug(f"Closed modal using selector: {selector}")
            except:
                continue
    
    async def extract_links(self, pattern: Optional[str] = None) -> List[str]:
        """Extract all links from the current page, optionally filtered by pattern"""
        links = await self.page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a'))
                .map(a => a.href)
                .filter(href => href && href.startsWith('http'));
        }''')
        
        if pattern:
            import re
            links = [link for link in links if re.search(pattern, link)]
            
        return list(set(links))

    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.page.close()
        except Exception as e:
            self.logger.error(f"Error during page cleanup: {str(e)}")