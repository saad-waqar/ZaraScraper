from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ZaraScraper.items import ZarascraperItem
import json
from datetime import datetime
from itertools import chain
import re
import scrapy
# product_ids = []
# class ZaraSpider(scrapy.Spider):
#     name = 'zara'
#     download_delay = 0.25
#     allowed_domains = ['zara.com']
#     start_urls = ['https://www.zara.com/vn/vi/nam/qu%E1%BA%A7n/xem-t%E1%BA%A5t-c%E1%BA%A3/qu%C3%A2%CC%80n-da%CC%81ng-carrot-fit-c719514p4900642.html'
#                     ,'https://www.zara.com/ie/en/kids/mini-%7C-0-12-months/shop-by-look/-c810511p4383542.html'
#                     ,'https://www.zara.com/ie/en/kids/baby-girl-%7C-3-months-4-years/shop-by-look/-c719506p4594526.html'
#                     ,'https://www.zara.com/il/en/kids/mini-%7C-0-12-months/shop-by-look/-c810511p4521674.html'
#                     ,'https://www.zara.com/il/en/kids/mini-%7C-0-12-months/shop-by-look/-c810511p4521683.html'
#                     ,'https://www.zara.com/il/en/kids/mini-%7C-0-12-months/organic-cotton/-c802506p4334032.html'
#                     ,'https://www.zara.com/il/en/kids/baby-boy-%7C-3-months---4-years/shop-by-look/-c719507p4497098.html'
#                     ,'https://www.zara.com/il/en/kids/girl-%7C-4-14-years/shop-by-look/-c810509p4433021.html'
#                     ,'https://www.zara.com/il/en/kids/girl-%7C-4-14-years/holidays-collection/-c816004p4763344.html'
#                   ]
product_ids = []


class ZaraSpider(CrawlSpider):
    name = "zara"
    download_delay = 0.25
    # allowed_domains = ["zara.com"]
    start_urls = ["https://www.zara.com"]

    rules = (
        Rule(LinkExtractor(allow=(), restrict_css=('select#country a',)), follow=True),
        Rule(LinkExtractor(allow=(), restrict_css=('#menu>ul>li:nth_child(3)>ul a, #menu>ul>li:nth_child(4)>ul a, #menu>ul>li:nth_child(5)>ul a, #menu>ul>li:nth_child(6)>ul a',)),
             follow=True),
        Rule(LinkExtractor(allow=(), restrict_css=('a.name._item',)), callback="parse_item"),
    )

    def parse_item(self, response):
        data = response.xpath("//script[@data-compress='true']")[3]
        json_input = data.re('"product":(.*),"parent')[0]
        country_code = data.re("countryCode: *'(.*?)'")[0]
        currency = data.re('currencyCode":"(.*?)"')[0] or None
        if self.is_json(json_input):
            product_metadata = json.loads(json_input)
        else:
            temp = [{'before': x, 'after': re.sub(r'[^\\]"', '\\"', x)} for x in
             re.findall(r'"\w+" *: *"(.*?)"[},]', json_input, flags=re.UNICODE)]
            for entry in temp:
                json_input = json_input.replace(entry['before'], entry['after'])
            product_metadata = json.loads(json_input)
        if product_metadata['detail']['bundleProducts']:
            for product in product_metadata['detail']['bundleProducts']:
                yield self.compile_item(product, response, country_code, currency)
        else:
            yield self.compile_item(product_metadata, response, country_code, currency)

    def filter_sizes(self, size_lists):
        result = []
        for color in size_lists:
            for size in color['sizes']:
                result.append({'sku': size['sku'], 'name': size['name'], 'availability': size['availability']})
        return result

    def filter_color_objects(self, color_list):
        result = []
        for color in color_list:
            if 'colorImage' in color and 'colorCutImg' in color:
                url = color['colorImageUrl'].replace(color['colorImage']['name'], color['colorCutImg']['name'])
            else:
                url = color['colorImageUrl'].replace('.jpg', '_1.jpg')
            result.append({'id': color['id'], 'name': color['name'], 'url': url})
        return result

    def compile_item(self, product_metadata, response, country_code, currency):
        if product_metadata['id'] not in product_ids:
            product_ids.append(product_metadata['id'])
            item = ZarascraperItem()
            item['id'] = product_metadata['id']
            item['type'] = product_metadata['type']
            item['kind'] = product_metadata['kind']
            if 'description' in product_metadata:
                item['description'] = product_metadata['description']
            item['price'] = product_metadata['price']
            item['tags'] = product_metadata['tags']
            item['relatedProducts'] = [related_product['id'] for related_product in
                                       product_metadata['detail']['relatedProducts']]
            item['categories'] = product_metadata['detail']['categories']
            item['url'] = response.url
            item['timestamp'] = datetime.utcnow()
            item['name'] = product_metadata['name']
            item['image_urls'] = ['https:' + x for x in response.css('._seoImg::attr(href)').extract()]
            item['sizes'] = self.filter_sizes(product_metadata['detail']['colors'])
            item['colors'] = self.filter_color_objects(product_metadata['detail']['colors'])
            if 'detailedComposition' in product_metadata['detail']:
                item['detailedComposition'] = product_metadata['detail']['detailedComposition']
            item['care'] = product_metadata['detail']['care']
            item['videos'] = list(
                chain.from_iterable([videos['videos'] for videos in product_metadata['detail']['colors']]))
            item['country_code'] = country_code
            item['currency'] = currency
            return item

    def is_json(self, myjson):
        try:
            json_object = json.loads(myjson)
        except ValueError, e:
            return False
        return True

