# Monivetobotti
Monivetobotti (veikkaus.fi) uses odds from Oddsportal.com to estimate the probabiliteties for each match and calculates multigame-EVs for all conceivable combination. Finally it places selected wagers with given thresholds.

User must modify config.py to include correct Moniveto-number and Oddportal URLs. In order to place the wagers, veikkaus_config.py needs to be updated.

Bot will fetch following odds: multiway, asian handicap, over/under and correct score. Odds are scraped with Selenium and Chromedriver. Path to chromedriver.exe needs to be set at const.py. 

Single match probabilities are based on scraped odds and historical football data. Historical data has been downloaded from https://www.football-data.co.uk/. Path to historical data needs to be set at const.py. Bot uses Scipy's minimize function and SLSQP-method to optimize the probabilities.

Veikkaus data is fetched asynchronously with asyncio and aiohttp. Once the EVs for all combinations are calculated, the bot employs an EV-threshold and a mutually exclusive Kelly-restriction system to determine the optimal wagers. Users also have the option to specify the number of wagers they desire.

User can review placed wager using check_results.py. Different combinations can be filtered using command line arguments such as:

![check-results-img-s](https://github.com/jussni/monivetobotti/assets/33765119/76b6cf4d-214d-42b2-aa89-410d6406907d)
