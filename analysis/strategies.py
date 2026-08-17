import numpy as np

from analysis.config import AnalysisConfig, MODEL_NAMES
from analysis.model import (
    NUMBER_COUNT,
    NUMBERS_PER_DRAW,
    category_count_moments,
    combination_inclusion_probability,
)


THEORETICAL_NUMBER_RATE = NUMBERS_PER_DRAW / NUMBER_COUNT


def _require_history(state):
    if state.draw_count == 0 or state.latest_draw is None:
        raise ValueError("Strateji skoru için en az bir geçmiş çekiliş gerekir.")


def frequency_momentum_score(state):
    short_size = state.window_size("short")
    long_size = state.window_size("long")
    return (
        state.window_counts("short") / short_size
        - state.window_counts("long") / long_size
    )


def frequency_deviation_score(state):
    window_size = state.window_size("deviation")
    expected = window_size * THEORETICAL_NUMBER_RATE
    standard_deviation = np.sqrt(
        window_size
        * THEORETICAL_NUMBER_RATE
        * (1.0 - THEORETICAL_NUMBER_RATE)
    )
    return (state.window_counts("deviation") - expected) / standard_deviation


def pair_association_score(state, z_clip):
    pair_probability = combination_inclusion_probability(2)
    expected = state.draw_count * pair_probability
    standard_deviation = np.sqrt(
        state.draw_count * pair_probability * (1.0 - pair_probability)
    )
    pair_z = (state.pair_counts - expected) / standard_deviation
    pair_z = np.clip(pair_z, -z_clip, z_clip)

    scores = np.empty(NUMBER_COUNT, dtype=float)
    for candidate in range(NUMBER_COUNT):
        partners = state.latest_draw[state.latest_draw != candidate]
        scores[candidate] = pair_z[partners, candidate].mean()
    return scores


def markov_transition_score(state, z_clip):
    scores = np.zeros(NUMBER_COUNT, dtype=float)
    active_rows = state.latest_draw[state.transition_exposure[state.latest_draw] > 0]
    if active_rows.size == 0:
        return scores

    exposure = state.transition_exposure[active_rows, None]
    expected = exposure * THEORETICAL_NUMBER_RATE
    standard_deviation = np.sqrt(
        exposure * THEORETICAL_NUMBER_RATE * (1.0 - THEORETICAL_NUMBER_RATE)
    )
    transition_z = (
        state.transition_counts[active_rows, :] - expected
    ) / standard_deviation
    return np.clip(transition_z, -z_clip, z_clip).mean(axis=0)


def delay_recency_score(state):
    return np.power(1.0 - THEORETICAL_NUMBER_RATE, state.gaps.astype(float))


def structural_score(state):
    window_size = state.structural_window_size
    block_moments = category_count_moments(window_size, 10)
    digit_moments = category_count_moments(window_size, 8)
    block_z = (
        state.structural_block_counts - block_moments.expected
    ) / block_moments.standard_deviation
    digit_z = (
        state.structural_digit_counts - digit_moments.expected
    ) / digit_moments.standard_deviation

    numbers = np.arange(1, NUMBER_COUNT + 1)
    return 0.5 * block_z[(numbers - 1) // 10] + 0.5 * digit_z[numbers % 10]


def calculate_raw_scores(state, config=None):
    """M1-M6 için 1-80 sırasındaki ham skor dizilerini döndürür."""

    _require_history(state)
    config = config or state.config or AnalysisConfig()
    scores = {
        "M1": frequency_momentum_score(state),
        "M2": frequency_deviation_score(state),
        "M3": pair_association_score(state, config.z_clip),
        "M4": markov_transition_score(state, config.z_clip),
        "M5": delay_recency_score(state),
        "M6": structural_score(state),
    }
    if tuple(scores) != MODEL_NAMES:
        raise AssertionError("Model skor sırası config ile uyuşmuyor.")
    if any(values.shape != (NUMBER_COUNT,) for values in scores.values()):
        raise AssertionError("Her model 1-80 için tam skor üretmelidir.")
    if any(not np.isfinite(values).all() for values in scores.values()):
        raise ValueError("Model skorlarında sonlu olmayan değer oluştu.")
    return scores
