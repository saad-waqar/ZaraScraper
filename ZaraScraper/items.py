import scrapy


class ZarascraperItem(scrapy.Item):
    id = scrapy.Field()
    type = scrapy.Field()
    kind = scrapy.Field()
    name = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()
    tags = scrapy.Field()
    colors = scrapy.Field()
    videos = scrapy.Field()
    sizes = scrapy.Field()
    relatedProducts = scrapy.Field()
    detailedComposition = scrapy.Field()
    categories = scrapy.Field()
    image_urls = scrapy.Field()
    url = scrapy.Field()
    timestamp = scrapy.Field()
    care = scrapy.Field()
    country_code = scrapy.Field()
    currency = scrapy.Field()
