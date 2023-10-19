import json
import math
import requests
import asyncio
import aiohttp

from const import HEADERS, URL_WAGER, URL_LOGIN, URL_INFO


class VeikkausAPI:
    def __init__(self, list_index):
        self.list_index = list_index
        self.draw_id = self.find_id()
        self.betsize = self.find_betsize()
        self.n_games = self.find_n_games()
        self.goal_limits = self.find_goal_limits()

    def find_id(self):
        '''
        returns gameid
        '''
        r = requests.get(URL_INFO, verify=True, headers=HEADERS)
        j = r.json()
        for row in j:
            if row['listIndex'] == str(self.list_index):
                return row['id']

    def find_betsize(self):
        '''
        returns (minimum) betsize
        '''
        r = requests.get(URL_INFO, verify=True, headers=HEADERS)
        j = r.json()
        for row in j:
            if row['listIndex'] == str(self.list_index):
                return row['gameRuleSet']['minStake']

    def find_goal_limits(self):
        '''
        returns (min, max) goal amounts
        '''
        r = requests.get(URL_INFO, verify=True, headers=HEADERS)
        j = r.json()
        for row in j:
            if row['listIndex'] == str(self.list_index):
                return row['rows'][0]['score']['min'], row['rows'][0]['score']['max']
            
    def find_n_games(self):
        '''
        returns number of games
        '''
        r = requests.get(URL_INFO, verify=True, headers=HEADERS)
        j = r.json()
        for row in j:
            if row['listIndex'] == str(self.list_index):
                return len(row['rows'])        

    def login(self, username, password):
        """
        logs in to veikkaus
        returns logged in session.
        """
        
        payload = json.dumps({
            "type": "STANDARD_LOGIN",
            "login": username,
            "password": password
        })

        session = requests.Session()
        r = session.post(URL_LOGIN, data=payload, verify=True, headers=HEADERS)
        if r.status_code != 200:
            raise Exception(f"Authentication failed: {r.status_code}")
        print("Login Succesful")
        return session
    
    def place_wagers(self, session, wagers):
        '''
        places wagers with given list-index.
        '''

        payloads = [{
            "listIndex": self.list_index,
            "gameName": "MULTISCORE",
            "price": self.betsize,
            "boards": [{
                "betType": "Regular",
                "stake": self.betsize,
                "selections": [
                    {
                        "homeScores": [home_score],
                        "awayScores": [away_score]
                    }
                    for i, (home_score, away_score) in enumerate(wager)]}]
            } for wager in wagers]

        for payload in payloads:
            r = session.post(URL_WAGER, data=json.dumps(payload), verify=True, headers=HEADERS)
            if r.status_code != 200:
                raise ValueError(f'Bad response: {r}')

        print(f"{len(wagers)} wagers placed succesfully.")
        return

    def fetch(self, multiscores):
        '''
        fetches VeikkausAPI data with given score amounts and list index.
        returns multiscore odds and exchange amount.
        '''

        score_amounts_by_team = []
        for _ in range(self.n_games):
            score_amounts_by_team.append([set(), set()])
            
        for multiscore in multiscores:
            for i, game_score in enumerate(multiscore):
                score_amounts_by_team[i][0].add(game_score[0])
                score_amounts_by_team[i][1].add(game_score[1])

        total_combinations = 1.0
        for match in score_amounts_by_team:
            for team in match:
                total_combinations *= len(team)

        n_pages = math.ceil(total_combinations / 100 + 0.0001)  # how many pages is needed to scrape

        url_fetch = f"https://www.veikkaus.fi/api/sport-odds/v1/games/MULTISCORE/draws/{self.draw_id}/odds"
        
        selections = [
            {
                "rowId": i,
                "systemBetType": "SYSTEM",
                "homeScores": sorted(team_score[0]),
                "awayScores": sorted(team_score[1]),
            }
            for i, team_score in enumerate(score_amounts_by_team)
        ]

        payloads = [json.dumps({
                "selections": selections,
                "page": page_idx
            }) for page_idx in range(n_pages)]
        data = []

        async def fetch_page(session, url_fetch, payload):
            async with session.post(url_fetch, data=payload) as resp:
                res = await resp.json()
                return res

        async def fetch_all():
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                tasks = [
                    asyncio.ensure_future(fetch_page(session, url_fetch, payload)) for payload in payloads
                ]
                results = await asyncio.gather(*tasks)
                data.append(results)

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(fetch_all())

        if len(data) == 1:
            data = data[0]
        else:
            print(f"VeikkausAPI data len > 1")

        return data
    
