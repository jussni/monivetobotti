import argparse
import pickle
from veikkaus_api import VeikkausAPI
from config import VEIKKAUS_LIST_INDEX
from functions import modify_arg, check_results

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Check results for Moniveto.',
        epilog="ex. format: python check_results.py 0-3,0-3 1-2,1-2 0,0"
    )
    parser.add_argument("match1")
    parser.add_argument("match2")
    parser.add_argument("match3", nargs="?")
    parser.add_argument("match4", nargs="?")

    args = parser.parse_args()
    args = [eval(modify_arg(getattr(args, arg))) for arg in vars(args) if getattr(args, arg) is not None]

    return args

if __name__ == "__main__":
    args = parse_arguments()
    v_api = VeikkausAPI(VEIKKAUS_LIST_INDEX)
    draw_id = v_api.draw_id

    with open(f"data/{draw_id}/placed_wagers.p", "rb") as file:
        wagers = pickle.load(file)

    with open(f"data/{draw_id}/multiscores_and_probs.p", "rb") as file:
        multiscores_and_probs = pickle.load(file)

    with open(f"data/{draw_id}/multiscores_and_evs.p", "rb") as file:
        multiscores_and_evs = pickle.load(file)

    probs_evs_euramts = {
        k: (v, multiscores_and_evs[k],  multiscores_and_evs[k] / v) for k, v in multiscores_and_probs.items() if k in wagers
    }

    print_output, wager_count = check_results(probs_evs_euramts, *args)
    print(print_output)
    print(f"Wager count: {wager_count}")
