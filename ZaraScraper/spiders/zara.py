from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from datetime import datetime
from itertools import chain
from ZaraScraper.items import ZarascraperItem
import json
import re

product_ids = []

existing_regions = [
    'au', 'be', 'bg', 'ca', 'tw', 'hk', 'mo', 'cz', 'dk', 'de', 'ee', 'es', 'ic',
    'fi', 'fr', 'gr', 'hr', 'hu', 'in', 'ie', 'it', 'jp', 'lv', 'lt', 'lu', 'my',
    'mt', 'mx', 'mc', 'nl', 'nz', 'no', 'at', 'pl', 'pt', 'ro', 'ru', 'sg', 'sk',
    'si', 'kr', 'se', 'ch', 'th', 'tr', 'uk', 'us', 'vn', 'cn'
]


class ZaraSpider(CrawlSpider):
    download_delay = 0.25

    def start_requests(self):
        yield Request("https://www.zara.com", self.parse_regions)

    def parse_regions(self, response):
        css = 'select#country .openForSale::attr(value)'
        regions = [r.encode('utf-8') for r in response.css(css).extract()]

        if len(regions) != len(existing_regions):
            new_regions = [r for r in regions if r not in existing_regions]

            for new_region_code in new_regions:
                name = response.css('option[value="{}"]::text'.format(new_region_code)).extract_first()
                message_t = 'NEW REGION HAS BEEN ADDED TO THE SITE (THAT WE\'RE NOT SCRAPING) {} CountryCode: {}'
                self.logger.critical(message_t.format(name, new_region_code))

        yield Request(self.start_urls[0], self.parse)

    listings_css = [
        'nav#menu',
        'li.product div.marketing-bundle'
    ]
    product_css = [
        'li.product a.item'
    ]
    raw_product_re = re.compile('window\.zara\.dataLayer *= *({.+})')
    country_code_re = re.compile("countryCode: *'(.*?)'")
    currency_code_re = re.compile("currencyCode: *\"(.*?)\"")

    rules = (
        Rule(LinkExtractor(allow=['woman'], restrict_css=listings_css), callback="parse"),
        Rule(LinkExtractor(restrict_css=product_css), callback="parse_item"),
    )

    def parse_item(self, response):
        """
        This method extracts a single product details after reaching to product detail page.
        :param response: response containing the the product details in raw form
        :return:
        """
        raw_product_s = response.css('script:contains("window.zara.dataLayer")')
        json_input = raw_product_s.re_first(self.raw_product_re)

        locale_s = response.css('script:contains(_mkt_catalogIds)')
        country_code = locale_s.re_first(self.country_code_re)
        currency = locale_s.re_first(self.currency_code_re)

        if self.is_json(json_input):
            product_metadata = json.loads(json_input)
        else:
            temp = [{'before': x, 'after': re.sub(r'[^\\]"', '\\"', x)} for x in
                    re.findall(r'"\w+" *: *"(.*?)"[},]', json_input, flags=re.UNICODE)]

            for entry in temp:
                json_input = json_input.replace(entry['before'], entry['after'])
            product_metadata = json.loads(json_input)

        if product_metadata['product']['detail']['bundleProducts']:
            for product in product_metadata['product']['detail']['bundleProducts']:
                yield self.compile_item(product, response, country_code, currency)
        else:
            yield self.compile_item(product_metadata, response, country_code, currency)

    def filter_sizes(self, size_lists):
        """
        This method extracts the SKUs of a single product.
        :param size_lists: array containing all colors of to that specific product which further contain sizes
        :return:
        """
        result = []
        for color in size_lists:
            for size in color['sizes']:
                result.append({'sku': size['sku'], 'name': size['name'], 'availability': size['availability']})
        return result

    def filter_color_objects(self, color_list):
        """
        This method extracts the data related to color of the product
        :param color_list: array containing colors of the product
        :return:
        """
        result = []
        for color in color_list:
            if 'colorImage' in color and 'colorCutImg' in color:
                url = color['colorImageUrl'].replace(color['colorImage']['name'], color['colorCutImg']['name'])
            else:
                url = color['colorImageUrl'].replace('.jpg', '_1.jpg')
            result.append({'id': color['id'], 'name': color['name'], 'url': url})
        return result

    def compile_item(self, raw_product, response, country_code, currency):
        """
        This method combines all the parsed data and compiles them into a single item object so that it can be
        written to a .json file later on.
        :param raw_product: product details extracted from the response
        :param response: product details in raw form
        :param country_code: country code of the product belonging to
        :param currency: currency defined for the product
        :return:
        """
        product_metadata = raw_product['product']

        if product_metadata['id'] not in product_ids:
            product_ids.append(product_metadata['id'])

            item = ZarascraperItem()
            item['id'] = product_metadata['id']
            item['type'] = product_metadata['type']
            item['kind'] = product_metadata['kind']

            if 'description' in product_metadata:
                item['description'] = product_metadata['description']

            item['price'] = product_metadata['price']
            item['relatedProducts'] = [related_product['id'] for related_product in
                                       product_metadata['detail']['relatedProducts']]
            item['categories'] = [c.get('text') for c in raw_product.get('breadCrumbs') or []][:-1]
            item['url'] = response.url
            item['timestamp_utc'] = datetime.utcnow()
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

    def is_json(self, input_str):
        """
        This method validates the json passed to the method is a valid json or is an invalid one.
        :param input_str: json passed as a param that needs to be verified
        :return: boolean
        """
        try:
            json_object = json.loads(input_str)
        except ValueError, e:
            return False
        return True


# Australia
class AUCrawlSpider(ZaraSpider):
    name = 'zara-au'
    start_urls = ['https://www.zara.com/au/']


# Belgium
class BECrawlSpider(ZaraSpider):
    name = 'zara-be'
    start_urls = ['https://www.zara.com/be/']


# Bulgaria
class BGCrawlSpider(ZaraSpider):
    name = 'zara-bg'
    start_urls = ['https://www.zara.com/bg/']


# Canada
class CACrawlSpider(ZaraSpider):
    name = 'zara-ca'
    start_urls = ['https://www.zara.com/ca/']


# MAINLAND CHINA
class CNCrawlSpider(ZaraSpider):
    name = 'zara-cn'
    start_urls = ['https://www.zara.cn/cn/']


# Taiwan
class TWCrawlSpider(ZaraSpider):
    name = 'zara-tw'
    start_urls = ['https://www.zara.com/tw/']


# Hong Kong SAR
class HKCrawlSpider(ZaraSpider):
    name = 'zara-hk'
    start_urls = ['https://www.zara.com/hk/']


# Macau SAR
class MOCrawlSpider(ZaraSpider):
    name = 'zara-mo'
    start_urls = ['https://www.zara.com/mo/']


# Czech Republic
class CZCrawlSpider(ZaraSpider):
    name = 'zara-cz'
    start_urls = ['https://www.zara.com/cz/']


# Denmark
class DKCrawlSpider(ZaraSpider):
    name = 'zara-dk'
    start_urls = ['https://www.zara.com/dk/']


# Germany
class DECrawlSpider(ZaraSpider):
    name = 'zara-de'
    start_urls = ['https://www.zara.com/de/']


# Estonia
class EECrawlSpider(ZaraSpider):
    name = 'zara-ee'
    start_urls = ['https://www.zara.com/ee/']


# Spain
class ESCrawlSpider(ZaraSpider):
    name = 'zara-es'
    start_urls = ['https://www.zara.com/es/']


# Spain - Canary Islands
class ICCrawlSpider(ZaraSpider):
    name = 'zara-ic'
    start_urls = ['https://www.zara.com/ic/']


# Finland
class FICrawlSpider(ZaraSpider):
    name = 'zara-fi'
    start_urls = ['https://www.zara.com/fi/']


# France
class FRCrawlSpider(ZaraSpider):
    name = 'zara-fr'
    start_urls = ['https://www.zara.com/fr/']


# Greece
class GRCrawlSpider(ZaraSpider):
    name = 'zara-gr'
    start_urls = ['https://www.zara.com/gr/']


# Croatia
class HRCrawlSpider(ZaraSpider):
    name = 'zara-hr'
    start_urls = ['https://www.zara.com/hr/']


# Hungary
class HUCrawlSpider(ZaraSpider):
    name = 'zara-hu'
    start_urls = ['https://www.zara.com/hu/']


# India
class INCrawlSpider(ZaraSpider):
    name = 'zara-in'
    start_urls = ['https://www.zara.com/in/']


# Ireland
class IECrawlSpider(ZaraSpider):
    name = 'zara-ie'
    start_urls = ['https://www.zara.com/ie/']


# Italy
class ITCrawlSpider(ZaraSpider):
    name = 'zara-it'
    start_urls = ['https://www.zara.com/it/']


# Japan
class JPCrawlSpider(ZaraSpider):
    name = 'zara-jp'
    start_urls = ['https://www.zara.com/jp/']


# Latvia
class LVCrawlSpider(ZaraSpider):
    name = 'zara-lv'
    start_urls = ['https://www.zara.com/lv/']


# Lithuania
class LTCrawlSpider(ZaraSpider):
    name = 'zara-lt'
    start_urls = ['https://www.zara.com/lt/']


# Luxembourg
class LUCrawlSpider(ZaraSpider):
    name = 'zara-lu'
    start_urls = ['https://www.zara.com/lu/']


# Malaysia
class MYCrawlSpider(ZaraSpider):
    name = 'zara-my'
    start_urls = ['https://www.zara.com/my/']


# Malta
class MTCrawlSpider(ZaraSpider):
    name = 'zara-mt'
    start_urls = ['https://www.zara.com/mt/']


# Mexico
class MXCrawlSpider(ZaraSpider):
    name = 'zara-mx'
    start_urls = ['https://www.zara.com/mx/']


# Monaco
class MCCrawlSpider(ZaraSpider):
    name = 'zara-mc'
    start_urls = ['https://www.zara.com/mc/']


# Netherlands
class NLCrawlSpider(ZaraSpider):
    name = 'zara-nl'
    start_urls = ['https://www.zara.com/nl/']


# New Zealand
class NZCrawlSpider(ZaraSpider):
    name = 'zara-nz'
    start_urls = ['https://www.zara.com/nz/']


# Norway
class NOCrawlSpider(ZaraSpider):
    name = 'zara-no'
    start_urls = ['https://www.zara.com/no/']


# Austria
class ATCrawlSpider(ZaraSpider):
    name = 'zara-at'
    start_urls = ['https://www.zara.com/at/']


# Poland
class PLCrawlSpider(ZaraSpider):
    name = 'zara-pl'
    start_urls = ['https://www.zara.com/pl/']


# Portugal
class PTCrawlSpider(ZaraSpider):
    name = 'zara-pt'
    start_urls = ['https://www.zara.com/pt/']


# Romania
class ROCrawlSpider(ZaraSpider):
    name = 'zara-ro'
    start_urls = ['https://www.zara.com/ro/']


# Russia
class RUCrawlSpider(ZaraSpider):
    name = 'zara-ru'
    start_urls = ['https://www.zara.com/ru/']


# Singapore
class SGCrawlSpider(ZaraSpider):
    name = 'zara-sg'
    start_urls = ['https://www.zara.com/sg/']


# Slovakia
class SKCrawlSpider(ZaraSpider):
    name = 'zara-sk'
    start_urls = ['https://www.zara.com/sk/']


# Slovenia
class SICrawlSpider(ZaraSpider):
    name = 'zara-si'
    start_urls = ['https://www.zara.com/si/']


# South Korea
class KRCrawlSpider(ZaraSpider):
    name = 'zara-kr'
    start_urls = ['https://www.zara.com/kr/']


# Sweden
class SECrawlSpider(ZaraSpider):
    name = 'zara-se'
    start_urls = ['https://www.zara.com/se/']


# Switzerland
class CHCrawlSpider(ZaraSpider):
    name = 'zara-ch'
    start_urls = ['https://www.zara.com/ch/']


# Thailand
class THCrawlSpider(ZaraSpider):
    name = 'zara-th'
    start_urls = ['https://www.zara.com/th/']


# Turkey
class TRCrawlSpider(ZaraSpider):
    name = 'zara-tr'
    start_urls = ['https://www.zara.com/tr/']


# United Kingdom
class UKCrawlSpider(ZaraSpider):
    name = 'zara-uk'
    start_urls = ['https://www.zara.com/uk/']


# United States
class USCrawlSpider(ZaraSpider):
    name = 'zara-us'
    start_urls = ['https://www.zara.com/us/']


# Vietnam
class VNCrawlSpider(ZaraSpider):
    name = 'zara-vn'
    start_urls = ['https://www.zara.com/vn/']
