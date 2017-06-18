from scrapy import cmdline
cmdline.execute("scrapy crawl zara -o overall_data_run_2.json -t json --logfile log.txt".split())
