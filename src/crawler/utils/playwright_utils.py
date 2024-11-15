import logfire
import traceback
from typing import List, Optional
from playwright.async_api import Page
from scrapy_playwright.page import PageMethod


# src/crawler/utils/playwright_utils.py

class PlaywrightPageManager:
    def __init__(self, page):
        self.page = page

    @staticmethod
    def get_default_page_methods():
        """Returns default page methods for initial request"""
        return [
            PageMethod("wait_for_load_state", "domcontentloaded"),
            PageMethod("wait_for_timeout", 5000),  # Increased timeout
        ]

    # src/crawler/utils/playwright_utils.py

    async def _wait_for_page_ready(self):
        """Enhanced page ready check with detailed logging"""
        try:
            logfire.debug("Waiting for page to be ready", url=self.page.url)
            
            # Wait for DOM content
            await self.page.wait_for_load_state('domcontentloaded')
            logfire.debug("DOM content loaded", url=self.page.url)
            
            # Wait for network idle
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            logfire.debug("Network idle", url=self.page.url)
            
            # Additional wait for dynamic content
            await self.page.wait_for_timeout(5000)
            logfire.debug("Additional wait completed", url=self.page.url)
            
        except Exception as e:
            logfire.error(
                "Error during page ready check",
                url=self.page.url,
                error=str(e),
                traceback=traceback.format_exc()
            )
            raise

    async def _handle_cookie_consent(self):
        """Enhanced cookie consent handling with detailed logging"""
        try:
            await self.page.wait_for_timeout(2000)  # Wait for cookie banner to appear
            
            # Check for cookie banner
            cookie_banner = await self.page.query_selector('#chefcookie-root')
            
            if not cookie_banner:
                return
                
            # Try to click using JavaScript first
            try:
                await self.page.evaluate("""() => {
                    const button = document.querySelector('[data-cc-accept-all]');
                    if (button) button.click();
                }""")
                await self.page.wait_for_timeout(2000)
                
                # Check if banner is gone
                banner_exists = await self.page.query_selector('#chefcookie-root')
                if not banner_exists:
                    return
                else:
                    logfire.debug("Cookie banner still present after JavaScript click")
            except Exception as e:
                logfire.warning("JavaScript click failed", error=str(e))
            
            # UniBo specific selectors with detailed attributes
            unibo_selectors = [
                {
                    'selector': '[data-cc-accept-all]',
                    'description': 'Accept all button by data attribute'
                },
                {
                    'selector': '.chefcookie__button--accept_all',
                    'description': 'Accept all button by class'
                },
                {
                    'selector': 'a[href="#chefcookie__accept_all"]',
                    'description': 'Accept all link by href'
                },
                {
                    'selector': 'button:has-text("Accetta tutti i cookie")',
                    'description': 'Accept button by text'
                },
                {
                    'selector': '.chefcookie__button-accept-all',
                    'description': 'Accept button alternative class'
                }
            ]
            
            # Try each selector
            for selector_info in unibo_selectors:
                selector = selector_info['selector']
                description = selector_info['description']
                
                try:
                    logfire.debug(f"Trying cookie selector: {description}", selector=selector)
                    
                    # Wait for element
                    button = await self.page.wait_for_selector(
                        selector,
                        state="visible",
                        timeout=5000
                    )
                    
                    if button:
                        logfire.debug(f"Found cookie button", 
                                   selector=selector, 
                                   description=description)
                        
        
                        # Try different click methods
                        methods = [
                            ('standard', lambda: button.click()),
                            ('force', lambda: button.click(force=True)),
                            ('js', lambda: self.page.evaluate(f'document.querySelector("{selector}").click()')),
                            ('dispatch', lambda: self.page.evaluate(f'''
                                document.querySelector("{selector}").dispatchEvent(
                                    new MouseEvent('click', {{
                                        bubbles: true,
                                        cancelable: true,
                                        view: window
                                    }})
                                )
                            '''))
                        ]
                        
                        for method_name, click_method in methods:
                            try:
                                await click_method()
                                await self.page.wait_for_timeout(2000)
                                
                                banner_exists = await self.page.query_selector('#chefcookie-root')
                                if not banner_exists:
                                  
                                    return
                                else:
                                    logfire.debug(f"Cookie banner still present after {method_name} click")
                            except Exception as e:
                                logfire.warning(f"{method_name} click failed", error=str(e))
                                continue
                            
                except Exception as e:
                    logfire.debug(
                        f"Failed with selector {selector}",
                        error=str(e),
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc()
                    )
                    continue
            
            logfire.error("Failed to handle cookie consent with all selectors")
            
            # Take screenshot if all methods fail
            try:
                screenshot_path = "cookie_banner_failed.png"
                await self.page.screenshot(path=screenshot_path)
              
            except Exception as e:
                logfire.error("Failed to save screenshot", error=str(e))
            
        except Exception as e:
            logfire.error(
                "Error handling cookie consent",
                url=self.page.url,
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )

    async def initialize_page(self):
        """Initialize page with common settings and handlers"""
        try:
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Wait for page ready
            await self._wait_for_page_ready()
            
            # Handle cookie consent
            await self._handle_cookie_consent()
            
            # Handle dynamic elements
            await self._handle_dynamic_elements()
            
        except Exception as e:
            logfire.error(
                "Failed to initialize page",
                url=self.page.url,
                error=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            raise

    async def _handle_dynamic_elements(self):
        """Handle dynamic page elements"""
        try:

            # Wait for any animations
            await self.page.wait_for_timeout(1000)
            
            # Scroll to bottom and back
            await self.page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
                window.scrollTo(0, 0);
            """)
            
            # Wait for network idle
            await self.page.wait_for_load_state('networkidle')

        except Exception as e:
            logfire.warning(
                "Error handling dynamic elements",
                error=str(e),
                traceback=traceback.format_exc()
            )

    async def cleanup(self):
        """Cleanup resources"""
        try:
           
            await self.page.close()
           
        except Exception as e:
            logfire.error("Error during cleanup", 
                          error=str(e),
                          traceback=traceback.format_exc())