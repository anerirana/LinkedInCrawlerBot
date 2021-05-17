# LinkedInCrawlerBot

Collects LinkedIn profiles by searching keywords on google and sraps each profile to collect publicly available data.

## Installation
Prerequisite: Python v3.x and pip needs to be installed

To install all the required packages run `pip install -r requirements.txt`

## Collect LinkedIn Profiles
To collect LinkedIn profile URLs from google, run `python3 do_url_scraping.py`

This code was meant to analyse skill set distribution in fintech industry. So the google query searches for a combination of skills and company names. But the code is reusable for any keyword search on google.

Collected profiles will be stored in `cloud_profiles_data.txt`

## Collect Profile Data
To scrap each LinkedIn profile run `python3 do_scraping.py`
To execute in headless mode provide `HEADLESS` option while running the command.


A configurator will be initialised to accept console inputs for
1. LinkedIn username
2. LinkedIn password
3. Input file name - Containing list of profiles urls
4. Output file name - For storing collected data
5. Append timestamp (Y/N)

This collects following information:
1. Name
2. Skills
3. Jobs
4. Location

Can be reconfigured to collect any publicly available data on the profile with a simple java script modification.

Program runs faster in `HEADLESS` mode as mulit-threading is utilised, but it will terminate if a bot check is evoked from linkedin. Otherwise, selenium driver will launch a chrome instance to run the bot. Periodically monitor the chrome page for bot checks. The program pauses and waits for user input to clear the bot test.

