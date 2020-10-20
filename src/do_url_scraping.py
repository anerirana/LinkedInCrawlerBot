import sys
from UrlScraper import UrlScraper

# Setting the execution mode
headless_option = len(sys.argv) >= 2 and sys.argv[1].upper() == 'HEADLESS'

# Launch UrlScraper
s = UrlScraper(headless=headless_option)
s.start()

s.join()

