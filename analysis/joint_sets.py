from itertools import combinations

import numpy as np

from analysis.hypergraph import TRIPLE_INDEX_TABLE
from analysis.search import deterministic_beam_search


def _mean_or_zero(values):
    return float(np.mean(values)) if len(values) else 0.0


class JointSetScorer:
    def __init__(
        self,
        individual,
        pair_matrix,
        triple_scores,
        conditional,
        structural,
        bayesian,
        weights,
    ):
        self.individual = np.asarray(individual, dtype=float)
        self.pair_matrix = np.asarray(pair_matrix, dtype=float)
        self.triple_scores = np.asarray(triple_scores, dtype=float)
        self.conditional = np.asarray(conditional, dtype=float)
        self.structural = np.asarray(structural, dtype=float)
        self.bayesian = np.asarray(bayesian, dtype=float)
        self.weights = dict(weights)

    def components(self, number_set):
        indices = np.asarray(number_set, dtype=int) - 1
        pairs = list(combinations(indices, 2))
        triples = list(combinations(indices, 3))
        pair_values = [self.pair_matrix[a, b] for a, b in pairs]
        triple_values = []
        for a, b, c in triples:
            triple_values.append(self.triple_scores[TRIPLE_INDEX_TABLE[a, b, c]])
        return {
            "individual": float(self.individual[indices].mean()),
            "pair": _mean_or_zero(pair_values),
            "triple": _mean_or_zero(triple_values),
            "conditional": float(self.conditional[indices].mean()),
            "structural": float(self.structural[indices].mean()),
            "bayesian": float(self.bayesian[indices].mean()),
        }

    def score(self, number_set):
        components = self.components(number_set)
        return sum(self.weights[name] * components[name] for name in self.weights)


def optimize_joint_sets(candidate_numbers, scorer, beam_width=50):
    return deterministic_beam_search(
        candidate_numbers, scorer.score, max_size=6, beam_width=beam_width
    )


def optimize_hypergraph_sets(candidate_numbers, pair_matrix, triple_scores, beam_width=50):
    pair_matrix = np.asarray(pair_matrix, dtype=float)
    triple_scores = np.asarray(triple_scores, dtype=float)

    def score(number_set):
        indices = np.asarray(number_set, dtype=int) - 1
        pairs = [pair_matrix[a, b] for a, b in combinations(indices, 2)]
        triples = [
            triple_scores[TRIPLE_INDEX_TABLE[a, b, c]]
            for a, b, c in combinations(indices, 3)
        ]
        return 0.45 * _mean_or_zero(pairs) + 0.55 * _mean_or_zero(triples)

    return deterministic_beam_search(
        candidate_numbers, score, max_size=6, beam_width=beam_width
    )
