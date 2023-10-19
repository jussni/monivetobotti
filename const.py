PATH_TO_CHROMEDRIVER = 'chromedriver.exe'
PATH_TO_HISTORICAL_DATA = 'historical-football-data.p'

HEADERS = {
    'Content-type': 'application/json',
    'Accept': 'application/json',
    'X-ESA-API-Key': 'ROBOT'
}

URL_LOGIN = "https://www.veikkaus.fi/api/bff/v1/sessions"
URL_WAGER = "https://www.veikkaus.fi/api/sport-interactive-wager/v1/tickets"
URL_INFO = "https://www.veikkaus.fi/api/sport-open-games/v1/games/MULTISCORE/draws"

ODDSPORTAL_OPTIONS = {
    'Multiway': {
        'xpath': '//*[@id="app"]/div/div[1]/div/main/div[2]/div[3]/div[1]/div',
        'url-suffix': ''
    },
    'Asian Handicap': {
        'xpath': '//*[@id="app"]/div/div[1]/div/main/div[2]/div[3]',
        'url-suffix': '#ah;2'
    },
    'Over/Under': {
        'url-suffix': '#over-under;2'
    },
    'Correct Score': {
        'url-suffix': '#cs;2'
    }
}

ODDSPORTAL_OPTIONS['Over/Under']['xpath'] = ODDSPORTAL_OPTIONS['Asian Handicap']['xpath']
ODDSPORTAL_OPTIONS['Correct Score']['xpath'] = ODDSPORTAL_OPTIONS['Asian Handicap']['xpath']
