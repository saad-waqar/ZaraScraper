from scrapy import cmdline
cmdline.execute("scrapy crawl zara -o debug.json -t json".split())
# cmdline.execute("scrapy crawl zara -o etoro_data.json -t json".split())
