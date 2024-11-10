import scrapy


class FrontierSpiderSpider(scrapy.Spider):
    name = "frontier_spider"
    allowed_domains = ["google.com"]
    start_urls = ["https://google.com"]

    def parse(self, response):
        pass
