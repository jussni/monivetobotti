import os
import pickle
import numpy as np

from compute import (
    get_initial_scores_and_probs,
    match_to_multiscore_probs,
    filter_goal_limits,
    calc_evs_and_odds,
    kelly_restriction
)
from optimize import Optimizer
from scrape_oddsportal import OddsPortalScraper
from veikkaus_api import VeikkausAPI
from config import (
    ODDSPORTAL_URLS,
    VEIKKAUS_LIST_INDEX,
    HEADLESS_BROWSER,
    COMPUTE_MULTISCORES,
    WAGER
)

from const import PATH_TO_HISTORICAL_DATA
from veikkaus_config import USER, PASSWORD

HISTORICAL_DATA = pickle.load(open(PATH_TO_HISTORICAL_DATA, "rb"))


def main_compute(v_api):
    if COMPUTE_MULTISCORES or not os.path.isfile(f"data/{v_api.draw_id}/multiscores_and_probs.p"):
        oddsportal_probs = []

        for i, base_url in enumerate(ODDSPORTAL_URLS):
            print(f"Match #{i + 1}:")
            op_scraper = OddsPortalScraper(base_url, HEADLESS_BROWSER)
            op_prob = op_scraper.calc_and_combine()
            oddsportal_probs.append(op_prob)
            print("." * 40)

        if not os.path.exists(f"data/{v_api.draw_id}/"):
            os.mkdir(f'data/{v_api.draw_id}/')

        print('Initializing scores and probabilities...')

        initial_scores_and_probs = get_initial_scores_and_probs(oddsportal_probs, HISTORICAL_DATA)
        scores_and_probs = []

        print('Optimizing scores and probabilities...')
        for match_idx, op_prob in enumerate(oddsportal_probs):
            initial_sap = initial_scores_and_probs[match_idx]
            opt = Optimizer(initial_sap, *op_prob[:-2])
            result = opt.run()
            scores_and_probs.append(result)

        print('Computing multiscore-probabilities...')
        multiscores_and_probs_wo_limits = match_to_multiscore_probs(scores_and_probs)
        multiscores_and_probs = filter_goal_limits(multiscores_and_probs_wo_limits, v_api.goal_limits)

        for f in ["oddsportal_probs", "multiscores_and_probs", "scores_and_probs"]:
            pickle.dump(eval(f), open(f"data/{v_api.draw_id}/{f}.p", "wb"))

    else:
        multiscores_and_probs = pickle.load(open(f"data/{v_api.draw_id}/multiscores_and_probs.p", "rb"))

    print('Fetching Veikkaus-data...')
    veikkaus_data = v_api.fetch(sorted(multiscores_and_probs.keys()))
    multiscores_and_evs, multiscores_and_odds = calc_evs_and_odds(multiscores_and_probs, veikkaus_data, v_api.betsize)

    for f in ["multiscores_and_evs", "multiscores_and_odds"]:
        pickle.dump(eval(f), open(f"data/{v_api.draw_id}/{f}.p", "wb"))

    return multiscores_and_probs, multiscores_and_evs


def main_wager(v_api, suggested_wagers):
    max_wagers = int(input("Enter # of wagers (default = max): ") or len(suggested_wagers))
    if max_wagers == 0:
        exit()
    wagers = suggested_wagers[:max_wagers]

    print('Logging in...')
    session = v_api.login(USER, PASSWORD)

    print('Placing wagers...')
    v_api.place_wagers(session, wagers)
    pickle.dump(wagers, open(f"data/{v_api.draw_id}/placed_wagers.p", "wb"))
    return


if __name__ == "__main__":
    v_api = VeikkausAPI(VEIKKAUS_LIST_INDEX)
    multiscores_and_probs, multiscores_and_evs = main_compute(v_api)

    print('Filtering by Kelly and EV-threshold...')
    suggested_wagers = kelly_restriction(v_api.betsize, multiscores_and_probs, multiscores_and_evs)
    suggested_wagers_and_evs = {w: multiscores_and_evs[w] for w in suggested_wagers}
    pickle.dump(suggested_wagers_and_evs, open(f"data/{v_api.draw_id}/suggested_wagers_and_evs.p", "wb"))

    avg_ev = np.mean(list(suggested_wagers_and_evs.values()))
    wager_count = len(suggested_wagers)
    print(f"# of suggested wagers: {wager_count} | {v_api.betsize * 0.01 * wager_count:.2f}€ (avg ev: {avg_ev:.2f}).")

    if WAGER:
        main_wager(v_api, suggested_wagers)
    print("Finished.")
