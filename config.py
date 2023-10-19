ODDSPORTAL_URLS = [
    "https://www.oddsportal.com/football/brazil/serie-a/cruzeiro-flamengo-rj-CAAnZE6C/",
    "https://www.oddsportal.com/football/brazil/serie-a/palmeiras-atletico-mg-Qg8zxHMg/",
    "https://www.oddsportal.com/football/brazil/serie-a/santos-bragantino-4p7vyyx0/",
]

VEIKKAUS_LIST_INDEX = 2

EV_THRESHOLD = 1.20
ONE_WINCLASS = True  # usually Moniveto has only one winclass, however Supermoniveto has two.
WAGER = True
BANKROLL_EUR = 100000
BANKROLL = BANKROLL_EUR * 100
HIST_SCORES_SAMPLE = 7000  # sample size for historical scores used to generate initial_scores_and_probs.

HEADLESS_BROWSER = True
COMPUTE_MULTISCORES = False  # if False, OddsPortal data is scraped and multiscore-probs
# are computed only if no such data already exists

ODDSPORTAL_URLS = [url + '/' if url[-1] != '/' else url for url in ODDSPORTAL_URLS]
