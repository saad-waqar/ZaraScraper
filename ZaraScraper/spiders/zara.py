from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from datetime import datetime
from itertools import chain
from ZaraScraper.items import ZarascraperItem
from ZaraScraper import constants
import json
import re

product_ids = []


class ZaraSpider(CrawlSpider):
    name = "zara"
    download_delay = 0.25
    # allowed_domains = ["zara.com"]
    start_urls = ["https://www.zara.com"]

    rules = (
        Rule(LinkExtractor(allow=(), restrict_css=(constants.country_locator,)), follow=True),
        Rule(LinkExtractor(allow=(), restrict_css=(constants.subcategory_locator,)),
             follow=True),
        Rule(LinkExtractor(allow=(), restrict_css=(constants.product_locator,)), callback="parse_item"),
    )

    def parse_item(self, response):
        data = response.xpath(constants.script_tag_data_extract)[3]
        json_input = data.re(constants.product_re)[0]
        country_code = data.re(constants.countrycode_re)[0]
        currency = data.re(constants.currencycode_re)[0] or None
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
        """
        This method validates the json passed to the method is a valid json or is an invalid one.
        :param myjson: json passed as a param that needs to be verified
        :return: boolean
        """
        try:
            json_object = json.loads(myjson)
        except ValueError, e:
            return False
        return True
