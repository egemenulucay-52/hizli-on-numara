from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import binom

from analysis.model import NUMBER_COUNT, combination_inclusion_probability
from analysis.tail_metrics import benjamini_hochberg


TRIPLE_COMBINATIONS = np.asarray(
    list(combinations(range(NUMBER_COUNT), 3)), dtype=np.int16
)
TRIPLE_INDEX_TABLE = np.full(
    (NUMBER_COUNT, NUMBER_COUNT, NUMBER_COUNT), -1, dtype=np.int32
)
TRIPLE_INDEX_TABLE[
    TRIPLE_COMBINATIONS[:, 0],
    TRIPLE_COMBINATIONS[:, 1],
    TRIPLE_COMBINATIONS[:, 2],
] = np.arange(len(TRIPLE_COMBINATIONS), dtype=np.int32)
DRAW_TRIPLE_POSITIONS = np.asarray(list(combinations(range(20), 3)), dtype=np.int8)


def draw_triple_indices(draw_indices):
    values = np.sort(np.asarray(draw_indices, dtype=int))
    triples = values[DRAW_TRIPLE_POSITIONS]
    return TRIPLE_INDEX_TABLE[triples[:, 0], triples[:, 1], triples[:, 2]]


def triple_indices_for_sets(triples):
    values = np.sort(np.asarray(triples, dtype=int), axis=-1)
    return TRIPLE_INDEX_TABLE[values[..., 0], values[..., 1], values[..., 2]]


def regularized_relation_scores(counts, draw_count, group_size, minimum_support, clip):
    probability = combination_inclusion_probability(group_size)
    expected = draw_count * probability
    deviation = np.sqrt(draw_count * probability * (1.0 - probability))
    z_scores = (np.asarray(counts, dtype=float) - expected) / deviation
    support_weight = np.asarray(counts, dtype=float) / (
        np.asarray(counts, dtype=float) + minimum_support
    )
    return np.clip(z_scores, -clip, clip) * support_weight


def triple_score_vector(triple_counts, draw_count, minimum_support=3, clip=4.0):
    return regularized_relation_scores(
        triple_counts, draw_count, 3, minimum_support, clip
    )


def context_triple_scores(triple_counts, draw_count, latest_draw, minimum_support=3, clip=4.0):
    pair_positions = np.asarray(list(combinations(range(len(latest_draw)), 2)), dtype=int)
    latest_pairs = np.asarray(latest_draw, dtype=int)[pair_positions]
    candidates = np.arange(NUMBER_COUNT)[:, None]
    first = np.broadcast_to(latest_pairs[:, 0], (NUMBER_COUNT, len(latest_pairs)))
    second = np.broadcast_to(latest_pairs[:, 1], (NUMBER_COUNT, len(latest_pairs)))
    stacked = np.stack((np.broadcast_to(candidates, first.shape), first, second), axis=-1)
    sorted_triples = np.sort(stacked, axis=-1)
    valid = (
        (sorted_triples[..., 0] != sorted_triples[..., 1])
        & (sorted_triples[..., 1] != sorted_triples[..., 2])
    )
    indices = TRIPLE_INDEX_TABLE[
        sorted_triples[..., 0], sorted_triples[..., 1], sorted_triples[..., 2]
    ]
    queried_counts = np.asarray(triple_counts)[np.maximum(indices, 0)]
    gathered = np.where(
        valid,
        regularized_relation_scores(
            queried_counts,
            draw_count,
            group_size=3,
            minimum_support=minimum_support,
            clip=clip,
        ),
        np.nan,
    )
    return np.nanmean(gathered, axis=1)


def significant_triple_diagnostics(triple_counts, draw_count, alpha=0.05, minimum_support=3):
    probability = combination_inclusion_probability(3)
    counts = np.asarray(triple_counts, dtype=int)
    p_values = binom.sf(counts - 1, draw_count, probability)
    q_values = benjamini_hochberg(p_values)
    mask = (counts >= minimum_support) & (q_values <= alpha)
    selected = TRIPLE_COMBINATIONS[mask] + 1
    return pd.DataFrame(
        {
            "Triple": [" ".join(map(str, triple)) for triple in selected],
            "Observed": counts[mask],
            "Expected": draw_count * probability,
            "p-value": p_values[mask],
            "q-value": q_values[mask],
        }
    ).sort_values(["q-value", "Observed"], ascending=[True, False])
