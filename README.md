# Apparel Scraper

One Paragraph of project description goes here

### Prerequisites

Clone the repo at your end and make a virtual environment. Then activate the virtual environment and run:

```
pip install -r requirements.txt
```

### Regions
The zara spider currently has 49 regions mentioned in the following list:
```
'au', 'be', 'bg', 'ca', 'tw', 'hk', 'mo', 'cz', 'dk', 'de', 'ee', 'es', 'ic', 'fi', 'fr', 'gr', 'hr', 'hu', 'in', 'ie', 'it', 'jp', 'lv', 'lt', 'lu', 'my', 'mt', 'mx', 'mc', 'nl', 'nz', 'no', 'at', 'pl', 'pt', 'ro', 'ru', 'sg', 'sk', 'si', 'kr', 'se', 'ch', 'th', 'tr', 'uk', 'us', 'vn', 'cn'
```
Whenever a region outside of this is detected a critical message is generated in the logs.

To add a new region for example a region is found named: om (OMAN)
add the following code:
```
# Oman
class OMCrawlSpider(ZaraSpider):
    name = 'zara-om'
    start_urls = ['https://www.zara.com/om/']
```
to the bottom of the file and then you can start crawling the region

### Running
After you've setup the environment, activate the environment and run the following command while in the repo directory.
```
scrapy crawl zara-us -o output_file_name.jsonl -t jsonlines --logfile logfile_name.txt
```

similarly if you want to crawl another region lets say china you run:
```
scrapy crawl zara-cn -o output_file_name.jsonl -t jsonlines --logfile logfile_name.txt
```

The output types that are supported for scrapy are:
- JSON
- JSON lines
- CSV
- XML
