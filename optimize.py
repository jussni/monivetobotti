import numpy as np
from scipy.optimize import minimize


class Optimizer:
    def __init__(self, initial_scores_and_probs, probs_mw, probs_ou, probs_ah, probs_cs_max, method='SLSQP'):
        self.initial_scores_and_probs = initial_scores_and_probs
        self.n_vars = len(initial_scores_and_probs)
        self.scores = sorted(initial_scores_and_probs.keys())
        self.probs_ah = probs_ah
        self.probs_cs_max = probs_cs_max
        self.probs_mw = probs_mw
        self.probs_ou = probs_ou
        self.method = method

    @staticmethod
    def apply_sum_constraint(inputs):
        return 1.0 - np.sum(inputs)
    
    def loss(self, x0):
        scores_and_probs = {s: x0[i] for i, s in enumerate(self.scores)}
        err = self.calculate_error(scores_and_probs)
        return err
    
    def run(self):
        x0 = np.array([self.initial_scores_and_probs[score] for score in self.scores])
        constraints = ({'type': 'eq', "fun": self.apply_sum_constraint})
        res = minimize(self.loss, x0, method=self.method, constraints=constraints,
                       bounds=[(0.0, 1.0) for _ in range(self.n_vars)])
        scores_and_probs_updated = {s: res.x[i] for i, s in enumerate(self.scores)}
        return scores_and_probs_updated
    
    def calculate_error(self, scores_and_probs):
        ou_estimated = {k: 0.0 for k in self.probs_ou.keys()}
        ah_estimated = {k: 0.0 for k in self.probs_ah.keys()}
        mw_estimated = {k: 0.0 for k in self.probs_mw.keys()}
        cs_errs = []

        for score, prob in scores_and_probs.items():
            diff = float(score[0] - score[1])
            total = sum(score)
            if diff > 0:
                res = 0
            elif diff < 0:
                res = 2
            else:
                res = 1
            mw_estimated[res] += prob

            for line in self.probs_ou.keys():
                if total > line:
                    ou_estimated[line] += prob
            for line in self.probs_ah.keys():
                if diff > -1 * line:
                    ah_estimated[line] += prob
            
            if self.probs_cs_max.get(score):
                err_cs = max(prob - self.probs_cs_max[score], 0)
                cs_errs.append(err_cs)

        mw_e = np.sum([abs(prob - mw_estimated[line])*2 for line, prob in self.probs_mw.items()])
        ou_e = np.sum([abs(prob - ou_estimated[line]) for line, prob in self.probs_ou.items()])
        ah_e = np.sum([abs(prob - ah_estimated[line]) for line, prob in self.probs_ah.items()])
        cs_e = np.sum([x*1.0 for x in cs_errs])
        return (ou_e + ah_e + mw_e + cs_e) * 1
