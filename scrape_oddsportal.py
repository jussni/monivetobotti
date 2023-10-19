from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from const import ODDSPORTAL_OPTIONS, PATH_TO_CHROMEDRIVER


class OddsPortalScraper:
    def __init__(self, base_url, headless=True, timeout=20):
        self.base_url = base_url
        self.headless = headless
        self.timeout = timeout
        self.browser = None

    @staticmethod
    def start_browser(headless):
        options = Options()
        options.add_argument("--log-level=3")
        if headless:
            options.add_argument('headless')

        service = Service(PATH_TO_CHROMEDRIVER)
        browser = webdriver.Chrome(service=service, options=options)
        return browser

    def close_browser(self):
        self.browser.quit()

    @staticmethod
    def odds_to_probs(odds):
        s = sum(1 / x for x in odds)
        return [1 / (x * s) for x in odds]    

    def wait_and_find(self, xpath, src, title):
        '''
        waits till odds element is visible and scrapes it.
        '''

        if 'My Predictions' in src:
            print(f"{title} | OddsPortal: logged in")
        else:
            print(f"{title} | OddsPortal: NOT logged in")
        try:
            WebDriverWait(self.browser, self.timeout).until(
                EC.visibility_of_element_located((
                    By.XPATH, xpath
                )))
        except TimeoutException:
            print(f"{title} | Timed out waiting for page to load.")
            self.browser.quit()
        odds_element = self.browser.find_elements(By.XPATH, xpath + '/*')
        return odds_element

    def scrape_elements(self, title):
        '''
        scrapes multiway Selenium elements
        '''

        if self.browser is not None:
            self.close_browser()

        self.browser = self.start_browser(self.headless)
        self.browser.get(self.base_url + ODDSPORTAL_OPTIONS[title]['url-suffix'])
        self.browser.refresh()
        
        src = self.browser.page_source
        odds_elements = self.wait_and_find(ODDSPORTAL_OPTIONS[title]['xpath'], src, title)
        return odds_elements

    @staticmethod
    def get_multiway_odds_from_elements(odds_elements):
        '''
        returns multiway odds from scraped Selenium elements
        return format: (bookmaker, odds_home, odds_tie, odds_away)
        '''
        
        odds_data = []
        for el in odds_elements[1:]:
            text_str = el.text
            if '%' not in text_str:
                continue
            if 'Betting Exchanges'.lower() in text_str.lower():
                continue
            if 'BONUS'.lower() in text_str.lower():
                bookmaker, _, odds_home, odds_tie, odds_away, _ = text_str.split("\n")
            else:
                bookmaker, odds_home, odds_tie, odds_away, _ = text_str.split("\n")

            try:
                odds_home = float(odds_home)
                odds_tie = float(odds_tie)
                odds_away = float(odds_away)
            except (ValueError, TypeError):
                continue
                
            odds_data.append((bookmaker, odds_home, odds_tie, odds_away))
        return odds_data

    @staticmethod
    def get_ou_odds_from_elements(odds_elements):
        odds_data = []
        for el in odds_elements:
            text_str = el.text
            if 'Over/Under' not in text_str:
                continue
            ou_line, n_bookies, odds_over, odds_under, _ = text_str.split("\n")
            ou_line = ou_line.replace("Over/Under", "").strip()

            try:
                odds_under = float(odds_under)
                odds_over = float(odds_over)
                n_bookies = int(n_bookies)
            except ValueError:
                continue
            odds_data.append((ou_line, odds_over, odds_under, n_bookies))

        return odds_data
    
    @staticmethod
    def get_ah_odds_from_elements(odds_elements):
        odds_data = []
        for el in odds_elements:
            
            text_str = el.text

            if 'Asian Handicap' not in text_str:
                continue

            ah_line, n_bookies, odds_home, odds_away, _ = text_str.split("\n")
            ah_line = ah_line.replace("Asian Handicap", "").strip()

            try:
                odds_home = float(odds_home)
                odds_away = float(odds_away)
                n_bookies = int(n_bookies)
            except ValueError:
                continue
            odds_data.append((ah_line, odds_home, odds_away, n_bookies))
        return odds_data
    
    @staticmethod
    def get_cs_odds_from_elements(odds_elements):
        odds_data = []
        for el in odds_elements:
            text_str = el.text
            if ':' not in text_str:
                continue
            score, n_bookies, odds = text_str.split("\n")
            try:
                odds = float(odds)
                n_bookies = int(n_bookies)
            except ValueError:
                continue
            odds_data.append((score, odds, n_bookies))

        return odds_data

    def multiway_odds_to_probs(self, odds_data):
        dict_probs_data = {}
        for row in odds_data:
            probs = self.odds_to_probs(row[1:])
            dict_probs_data[row[0]] = tuple(probs)

        if dict_probs_data.get('Pinnacle'):
            p = dict_probs_data.get('Pinnacle')
        else:
            p = dict_probs_data.get('Average')
        return {i: val for i, val in enumerate(p)}
        
    def ah_and_ou_odds_to_probs(self, odds_data):
        dict_probs_data = {}
        for row in odds_data:
            probs = self.odds_to_probs(row[1:-1])
            dict_probs_data[row[0]] = tuple(probs)
        return dict_probs_data

    @staticmethod
    def cs_odds_to_max_probs(odds_data):
        '''
        correct score odds to MAX probs (estimated probs cannot exceed correct score probabilities)
        '''

        dict_probs_data = {(int(row[0].split(":")[0]), int(row[0].split(":")[1])): 1 / row[1] for row in odds_data}

        return dict_probs_data

    @staticmethod
    def simplify_ou_probs(ou_probs):
        '''
        returns only .5-totals (as float) and over-prob.
        '''
        simplified = {}
        for line, prob in ou_probs.items():
            if line.endswith('.5'):
                simplified[float(line[1:])] = prob[0]
        return simplified

    @staticmethod
    def simplify_ah_probs(ah_probs):
        '''
        returns only .5-handicaps (as float) and home-prob.
        '''
        simplified = {}
        for line, prob in ah_probs.items():
            if line.endswith('.5'):
                simplified[float(line)] = prob[0]
        return simplified

    def calc_and_combine(self):
        ou_el = self.scrape_elements('Over/Under')
        ou_odds = self.get_ou_odds_from_elements(ou_el)
        ou_probs = self.ah_and_ou_odds_to_probs(ou_odds)

        ah_el = self.scrape_elements('Asian Handicap')
        ah_odds = self.get_ah_odds_from_elements(ah_el)
        ah_probs = self.ah_and_ou_odds_to_probs(ah_odds)

        cs_el = self.scrape_elements('Correct Score')
        cs_odds = self.get_cs_odds_from_elements(cs_el)
        cs_max_probs = self.cs_odds_to_max_probs(cs_odds)

        mw_el = self.scrape_elements('Multiway')
        mw_odds = self.get_multiway_odds_from_elements(mw_el)
        mw_probs = self.multiway_odds_to_probs(mw_odds)

        simp_ou_probs = self.simplify_ou_probs(ou_probs)
        simp_ah_probs = self.simplify_ah_probs(ah_probs)

        self.close_browser()

        return mw_probs, simp_ou_probs, simp_ah_probs, cs_max_probs, ou_probs, ah_probs
