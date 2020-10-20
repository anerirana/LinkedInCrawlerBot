import sys
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent

import time
import random

from webdriver_manager.chrome import ChromeDriverManager
from utils import is_url_valid

class UrlScraper(Thread):

    

    # cloud skills = "cloud computing", "cloud applications", "Cloud Development", "Google Cloud Platform", "GCP", "AWS"

    def __init__(self, headless=False):

        Thread.__init__(self)

        # Creation of a new instance of Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        if headless:
            options.add_argument('--headless')

        

        self.browser = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
        
        self.skills = ["Google Cloud Platform", "GCP", "AWS", "Cloud Applications", "Cloud Development"]
        self.companies = ["Citi", "Deutsche", "Credit Suisse", "DBS", "JP Morgan", "UBS", "Wells Fargo", "Goldman Sachs", "Google", "Microsoft"]
        # "HSBC", "Barclays", "Citi", "Deutsche", "Credit Suisse", "DBS", "JP Morgan", "UBS", "Wells Fargo", "Goldman Sachs", "Google", "Microsoft"
        # "Cloud Computing", "Google Cloud Platform", "GCP", "AWS", "Cloud Applications", "Cloud Development"
        # self.universities = []

        self.urls = []

    def run(self):
        self.ua = UserAgent()

        # combine keywords to narrow the search query
        for skill in self.skills:
            for keyword in self.companies:
                self.send_google_query(skill, keyword)
                # time.sleep(60)
                self.sleep_randomly()
    
        # Closing the Chrome instance
        self.browser.quit()

    def send_google_query(self, skill: str, keyword: str):
        print("Searching for " + skill + " skill and " + keyword + " keyword.")

        # Rotate user-agents to doge anti-bot policies
        user_agent = self.ua.random
        self.browser.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": '"' + user_agent + '"'})
        # options.add_argument(f'user-agent={user_agent}')


        # Open Google browser
        self.browser.get('https://www.google.com/')

        # locate search form by_name
        search_query = self.browser.find_element_by_name('q')

        # send_keys() to simulate the search text key strokes
        search_query.send_keys('site:linkedin.com/in/ AND "India" AND "' + skill + '" AND "' + keyword + '"')
        # e.g. site:linkedin.com/in/ AND "India" AND "cloud computing" AND "citi"

        # .send_keys() to simulate the return key 
        search_query.send_keys(Keys.RETURN)

        self.scan_google_pages(0, keyword)
        # page_count = 0
        # while True:
        #     try:
        #         page_count = page_count + 1
        #         # print("scanning page: " + str(page_count))
        #         self.scrape_urls()
        #         # time.sleep(30) 
        #         self.sleep_randomly()
        #         next_button = self.browser.find_element_by_id('pnnext')
        #         next_button.click()

        #     except:
        #         last_url = ""
        #         if len(urls) > 0
        #             last_url = self.urls[-1]
        #         print("last url written for keyword " + keyword + " is: " + last_url)
        #         self.write_to_file()
        #         print("End of search reached. Scanned " +  str(page_count) + " pages")

    def scan_google_pages(self, page_count, keyword):

        try:
            page_count = page_count + 1
            # print("scanning page: " + str(page_count))
            self.scrape_urls()
            # time.sleep(30) 
            self.sleep_randomly()
            next_button = self.browser.find_element_by_id('pnnext')
            next_button.click()
            self.scan_google_pages(page_count, keyword)

        except:
            if str(self.browser.current_url).find('https://www.google.com/sorry/') != -1:
                    print("Please solve the captcha !!!")
                    time.sleep(60)
                    age_count = page_count - 1
                    self.scan_google_pages(page_count, keyword)
            else:
                if len(self.urls) > 0:
                    print("last url written for keyword " + keyword + " is: " + self.urls[-1])
                    self.write_to_file()
                    print("End of search reached. Scanned " +  str(page_count) + " pages")

    def scrape_urls(self):
        divisions = self.browser.find_elements_by_class_name('g')

        for div in divisions:
            url = div.find_element_by_tag_name('a').get_attribute("href")
            # Need these modifications to make a valid url
            url = url.replace("://in", "://www") + "/"
            if not is_url_valid(url):
                print("invalid url found !!", url)
            else:
                self.urls.append(url)

    def sleep_randomly(self):
        # make array of random numbers
        # generate random number and mulitply with array
        # choose randomly from array

        random_array = [3, 7, 1, 9, 4, 8]
        random_number = random.uniform(1,5)
        random_array = [i * random_number for i in random_array]
        
        true_random_number = random.choice(random_array)
        time.sleep(true_random_number )

    def write_to_file(self):
        f = open("cloud_profiles_data.txt", "a")
        for url in self.urls:
            f.write(url + "\n")

        self.urls = []
        f.close()