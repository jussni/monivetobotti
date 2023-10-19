import operator
import itertools
import numpy as np

from config import BANKROLL, HIST_SCORES_SAMPLE, ONE_WINCLASS, EV_THRESHOLD


def get_initial_scores_and_probs(oddsportal_probs, hist):
    initial_scores_and_probs = []
    for match_idx, op_prob in enumerate(oddsportal_probs):
        mw_probs, o_probs, *_ = op_prob
        scores_hist = []
        for diff in range(100):
            mw_diff = 0.1 + diff / 100
            ou_diff = mw_diff * 0.25

            fav_mw_probs = max(mw_probs[0], mw_probs[2])
            if mw_probs[0] > mw_probs[2]:
                fav = 'h'
            else:
                fav = 'a'

            scores_hist = []
            for row in hist:
                score_hist, mw_probs_hist, ou25_hist = row
                o25_hist = ou25_hist[0]
                fav_mw_probs_hist = max(mw_probs_hist[0], mw_probs_hist[-1])

                if not (fav_mw_probs - mw_diff < fav_mw_probs_hist < fav_mw_probs + mw_diff):
                    continue
                if not (o_probs[2.5] - ou_diff < o25_hist < o_probs[2.5] + ou_diff):
                    continue

                if mw_probs_hist[0] > mw_probs_hist[-1]:
                    fav_hist = 'h'
                else:
                    fav_hist = 'a'
                if fav_hist != fav:
                    scores_hist.append(score_hist[::-1])
                else:
                    scores_hist.append(score_hist)
            if len(scores_hist) >= HIST_SCORES_SAMPLE:
                break
        else:
            print(f'Not enough sample for GameID: {match_idx}')

        if scores_hist:
            initial_scores_and_probs.append(
                {
                    score: scores_hist.count(score) / len(scores_hist) for score in set(scores_hist)
                }
            )
    return initial_scores_and_probs


def match_to_multiscore_probs(list_of_probs):
    multiscores_and_probs = {
        multiscore: np.prod([list_of_probs[j][r] for j, r in enumerate(multiscore)])
        for multiscore in list(itertools.product(*list_of_probs))
    }
    return multiscores_and_probs


def filter_goal_limits(multiscores_and_probs, goal_limits):
    filtered = {}
    for multiscore, probs in multiscores_and_probs.items():
        min_max = None
        for score in multiscore:
            if min_max is None:
                min_max = [min(score), max(score)]
            else:
                if min(score) < min_max[0]:
                    min_max[0] = min(score)
                if max(score) > min_max[1]:
                    min_max[1] = max(score)
        if min_max[0] >= goal_limits[0] and min_max[1] <= goal_limits[1]:
            filtered[multiscore] = probs
    return filtered


def veikkaus_data_to_odds(veikkaus_data):
    '''
    converts veikkaus json to odds dict
    '''
    veikkaus_odds = {}
    for page in veikkaus_data:
        for odds in page['odds']:
            multiscore = []
            for selection in odds['selections']:
                h = int(selection['homeScores'][0])
                a = int(selection['awayScores'][0])
                multiscore.append((h, a))
            multiscore = tuple(multiscore)
            o = int(odds['value'])
            veikkaus_odds[multiscore] = o
    return veikkaus_odds


def calc_evs_and_odds(multiscores_and_probs, veikkaus_data, betsize):
    veikkaus_odds = veikkaus_data_to_odds(veikkaus_data)

    if ONE_WINCLASS:
        winshare = 0.7
    else:
        winshare = 0.5

    v_exchange = max(d['exchange'] for d in veikkaus_data)
    v_n_bets_if_bet = {k: 1 + round((betsize * winshare * v_exchange) / v) if v > 0 else 1 for k, v in veikkaus_odds.items()}
    veikkaus_odds_if_bet = {k: int((betsize * winshare * v_exchange) / v_n_bets_if_bet[k]) for k, v in veikkaus_odds.items()}

    evs, odds = {}, {}
    for k, v in multiscores_and_probs.items():
        if veikkaus_odds_if_bet.get(k):
            evs[k] = 0.01 * 0.01 * betsize * veikkaus_odds_if_bet[k] * v
            odds[k] = veikkaus_odds_if_bet[k]
    return evs, odds


def kelly_restriction(betsize, multiscore_probs, multiscore_evs):
    sorted_evs = sorted(multiscore_evs.items(), key=operator.itemgetter(1), reverse=True)
    wagers_scores = []
    rr = 1.0
    for i, wager in enumerate(sorted_evs):
        ev = wager[-1]
        if ev > rr and ev >= EV_THRESHOLD:
            s = wager[0]
            wagers_scores.append(s)
            wager_probs = np.array([multiscore_probs[score] for score in wagers_scores])
            wager_evs = np.array([multiscore_evs[score] for score in wagers_scores])
            sum_wager_probs = np.sum(wager_probs)
            sum_wager_probs_div_by_wager_evs = np.sum(wager_probs / wager_evs)
            new_rr = (1 - sum_wager_probs) / (1 - sum_wager_probs_div_by_wager_evs)
            optimal_betsize = multiscore_probs[s] - (new_rr * multiscore_probs[s]) / ev
            if optimal_betsize > betsize / BANKROLL:
                rr = new_rr
            else:
                del wagers_scores[-1]

    return wagers_scores
