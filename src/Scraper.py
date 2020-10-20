from threading import Thread
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import csv
import time
import json
from utils import ComplexEncoder
import random

from webdriver_manager.chrome import ChromeDriverManager

from utils import Profile, ScrapingException, is_url_valid, HumanCheckException, wait_for_loading, wait_for_scrolling, \
    Job, AuthenticationException, Location, ScrapingResult


class Scraper(Thread):

    def __init__(self, linkedin_username, linkedin_password, profiles_urls, output_file_name, headless=False):

        Thread.__init__(self)

        # Creation of a new instance of Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        if headless:
            options.add_argument('--headless')

        self.browser = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)

        self.profiles_urls = profiles_urls

        self.results = []

        self.linkedin_username = linkedin_username
        self.linkedin_password = linkedin_password
        self.output_file_name = output_file_name

        # Count how many profiles were skipped due to expections
        self.omitted_url_count = 0

    def run(self):

        # Login in LinkedIn
        self.browser.get('https://www.linkedin.com/uas/login')

        username_input = self.browser.find_element_by_id('username')
        username_input.send_keys(self.linkedin_username)

        password_input = self.browser.find_element_by_id('password')
        password_input.send_keys(self.linkedin_password)
        password_input.submit()

        if not self.browser.current_url == "https://www.linkedin.com/feed/":
            print(self.browser.current_url)
            time.sleep(40)
            raise AuthenticationException()

        for linkedin_url in self.profiles_urls:

            scraped_profile = self.scrape_profile(linkedin_url)
            self.results.append(
                ScrapingResult(
                    linkedin_url,
                    scraped_profile
                )
            )

            self.write_to_file(scraped_profile)
            self.sleep_randomly()

        # Closing the Chrome instance
        self.browser.quit()

    def scrape_profile(self, linkedin_url, waiting_time=10):
        retry_count = 0
        try:
            profile = self.__scrape_profile(linkedin_url)

        except HumanCheckException:
            print("Please solve the captcha.")
            print("Another try will be performed within 10 seconds...")
            time.sleep(waiting_time)
            
            if retry_count > 4:
                print("Maximum attempts for captcha reached !!!")
                print("Omitting profile " + linkedin_url + " due to HumanException")
                self.omitted_url_count = self.omitted_url_count + 1
                profile = None
            else:
                retry_count = retry_count + 1
                profile = self.scrape_profile(linkedin_url, int(waiting_time*1.5))

        except ScrapingException:
            print("Omitting profile " + linkedin_url + " due to ScrapingException")
            self.omitted_url_count = self.omitted_url_count + 1
            profile = None

        return profile

    def __scrape_profile(self, profile_linkedin_url):

        if not is_url_valid(profile_linkedin_url):
            raise ScrapingException

        self.browser.get(profile_linkedin_url)

        # Check correct loading of profile and eventual Human Check
        current_url = str(self.browser.current_url).strip()
        if not current_url == profile_linkedin_url.strip():
            if current_url == 'https://www.linkedin.com/in/unavailable/':
                raise ScrapingException
            elif current_url.find(profile_linkedin_url.strip()) != -1:
                # Url was slightly modified by the browser, so it is ok to continue crawling
                print("URL modified")
                pass
            else:
                raise HumanCheckException

        self.load_full_page()

        # SCRAPING

        profile_name = self.scrape_profile_name()

        # email = self.scrape_email()

        location = self.scrape_location()

        job = self.scrape_job() 

        skills = self.scrape_skills()

        return Profile(
            url = profile_linkedin_url,
            name = profile_name,
            location = location,
            skills = skills,
            job = job
        )

    def scrape_profile_name(self):
        return self.browser.execute_script(
            "return document.getElementsByClassName('pv-top-card--list')[0].children[0].innerText")

    def scrape_email(self):
        # > click on 'Contact info' link on the page
        self.browser.execute_script(
            "(function(){try{for(i in document.getElementsByTagName('a')){let el = document.getElementsByTagName("
            "'a')[i]; if(el.innerHTML.includes('Contact info')){el.click();}}}catch(e){}})()")
        wait_for_loading()

        # > gets email from the 'Contact info' popup
        try:
            email = self.browser.execute_script(
                "return (function(){try{for (i in document.getElementsByClassName('pv-contact-info__contact-type')){ "
                "let el = document.getElementsByClassName('pv-contact-info__contact-type')[i]; if("
                "el.className.includes( 'ci-email')){ return el.children[2].children[0].innerText; } }} catch(e){"
                "return '';}})()")
        except WebDriverException:
            email = ''

        try:
            self.browser.execute_script("document.getElementsByClassName('artdeco-modal__dismiss')[0].click()")
        except WebDriverException:
            pass

        return email

    def scrape_location(self):
        try:
            location = self.browser.execute_script(
            "return document.getElementsByClassName('pv-top-card--list-bullet')[0].children[0].innerText")
            # location = self.browser.execute_script(
            #     "return (function(){"
            #         "var location = '';"
            #         "var "
            #         "return location;"
            #     "})();"
            # )
            parsed_location = Location(location)
        except WebDriverException:
            parsed_location = Location('')
        return parsed_location

    def scrape_job(self):

        try:
            job = self.browser.execute_script(
                "return (function(){ "
                    "var job = []; "
                    "var els = document.getElementById('experience-section').getElementsByTagName('ul')[0].getElementsByTagName('li')[0]; "
                    "if(els.className!='pv-entity__position-group-role-item'){  " 
                        "  if(els.getElementsByClassName('pv-entity__position-group-role-item').length>0){ "
                        "       role = els.getElementsByClassName('pv-entity__position-group-role-item')[0];  "
                        "       company = els.getElementsByClassName('pv-entity__company-summary-info')[0];  "
                        "       try { position = role.getElementsByClassName('pv-entity__summary-info-v2')[0].getElementsByTagName('h3')[0].getElementsByTagName('span')[1].innerText;  "     
                        "       } catch(err) { position = ''; } "
                        "       try { company_name = company.getElementsByTagName('h3')[0].getElementsByTagName('span')[1].innerText; "
                        "       } catch (err) { company_name = ''; }  "    
                        "       try { date_ranges = role.getElementsByClassName('pv-entity__date-range')[0].getElementsByTagName('span')[1].innerText;  "
                        "       } catch (err) { date_ranges = ''; }  "
                        "       try { job_location = role.getElementsByClassName('pv-entity__location')[0].getElementsByTagName('span')[1].innerText;  "
                        "       } catch (err) {job_location = ''; }  "    
                        "       job = [position, company_name, date_ranges, job_location];  "
                        " } else { "
                        "      try { position = els.getElementsByClassName('pv-entity__summary-info')[0].getElementsByTagName('h3')[0].innerText;  "     
                        "       } catch(err) { position = ''; } "
                        "       try { company_name = els.getElementsByClassName('pv-entity__summary-info')[0].getElementsByClassName('pv-entity__secondary-title')[0].innerText; "
                        "       } catch (err) { company_name = ''; }  "    
                        "       try { date_ranges = els.getElementsByClassName('pv-entity__summary-info')[0].getElementsByClassName('pv-entity__date-range')[0].getElementsByTagName('span')[1].innerText;  "
                        "       } catch (err) { date_ranges = ''; }  "
                        "       try { job_location = els.getElementsByClassName('pv-entity__summary-info')[0].getElementsByClassName('pv-entity__location')[0].getElementsByTagName('span')[1].innerText;  "
                        "       } catch (err) {job_location = ''; } "    
                        "       job = [position, company_name, date_ranges, job_location];  "
                        "} "  
                    "}"
                "   return job; "
                "})();"
            )

        except WebDriverException:
            print("Found WebDriverException while scrapping Job !!")
            job = []
            parsed_job = Job(
                    position='',
                    company='',
                    date_range='',
                    location=Location('')
                )
            return parsed_job

        parsed_job = Job(
                    position=job[0],
                    company=job[1],
                    date_range=job[2],
                    location=Location(job[3])
                )

        return parsed_job

    def scrape_company_details(self, company_url):

        self.browser.get(company_url)

        try:
            company_employees = self.browser.execute_script(
                "return document.querySelector('a[data-control-name" +
                '="topcard_see_all_employees"' +
                "]').innerText.split(' employees')[0].split(' ').lastObject;"
            )
        except WebDriverException:
            company_employees = ''

        try:
            company_industry = self.browser.execute_script(
                "return document.getElementsByClassName('org-top-card-summary-info-list__info-item')[0].innerText")
        except WebDriverException:
            company_industry = ''

        return company_industry, company_employees

    def scrape_skills(self):
        try:
            self.browser.execute_script(
                "document.getElementsByClassName('pv-skills-section__additional-skills')[0].click()")
        except WebDriverException:
            return []

        wait_for_loading()

        try:
            return self.browser.execute_script(
                "return (function(){els = document.getElementsByClassName('pv-skill-category-entity');results = ["
                "];for (var i=0; i < els.length; i++){results.push(els[i].getElementsByClassName("
                "'pv-skill-category-entity__name-text')[0].innerText);}return results;})()")
        except WebDriverException:
            return []

    def load_full_page(self):
        window_height = self.browser.execute_script("return window.innerHeight")
        scrolls = 1
        while scrolls * window_height < self.browser.execute_script("return document.body.offsetHeight"):
            self.browser.execute_script('window.scrollTo(0, ' + str(window_height * scrolls) + ');')
            wait_for_scrolling()
            scrolls += 1

        for i in range(self.browser.execute_script(
                "return document.getElementsByClassName('pv-profile-section__see-more-inline').length")):
            try:
                self.browser.execute_script(
                    "document.getElementsByClassName('pv-profile-section__see-more-inline')[" + str(
                        i) + "].click()")
            except WebDriverException:
                pass

            wait_for_loading()

    def write_to_file(self, scraping_result):

        if scraping_result.is_error():
            data = ['Error'] * len(headers)
        else:
            p = scraping_result
            data = [
                p.url,
                p.name,
                ",".join(p.skills)
            ]

            data.append(json.dumps(p.job.reprJSON(), cls=ComplexEncoder))
            data.append(json.dumps(p.location.reprJSON(), cls=ComplexEncoder))

        with open(self.output_file_name, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(data)

    def sleep_randomly(self):
        # make array of random numbers
        # generate random number and mulitply with array
        # choose randomly from array

        random_array = [3, 7, 1, 9, 4, 8]
        random_number = random.uniform(1,5)
        random_array = [i * random_number for i in random_array]
        
        true_random_number = random.choice(random_array)
        time.sleep(true_random_number )
