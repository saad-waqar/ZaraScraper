import scrapy


class ZarascraperItem(scrapy.Item):
    """
    Items fields describing the attributes of an item that are going to be fetched during scrapping.
    All these attributes will be acquired and will be set equal to its value regardless of the page structure
    being followed.
    """
    id = scrapy.Field()
    type = scrapy.Field()
    kind = scrapy.Field()
    name = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()
    colors = scrapy.Field()
    videos = scrapy.Field()
    sizes = scrapy.Field()
    relatedProducts = scrapy.Field()
    detailedComposition = scrapy.Field()
    categories = scrapy.Field()
    image_urls = scrapy.Field()
    url = scrapy.Field()
    timestamp_utc = scrapy.Field()
    care = scrapy.Field()
    country_code = scrapy.Field()
    currency = scrapy.Field()
