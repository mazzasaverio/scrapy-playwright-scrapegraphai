# src/crawler/spiders/frontier_spider.py
import scrapy
from crawler.utils.logging import logger, setup_logging

class FrontierSpider(scrapy.Spider):
    name = "frontier_spider"
    allowed_domains = ["google.com"]
    start_urls = ["https://google.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setup_logging()  # Inizializza il logging all'avvio dello spider

    def start_requests(self):
        logger.info("Crawler process started")
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def closed(self, reason):
        if reason == 'finished':
            logger.info("Crawler process completed successfully")
        else:
            logger.error(f"Crawler process failed: {reason}")

    def parse(self, response):
        # Logica di parsing qui
        pass