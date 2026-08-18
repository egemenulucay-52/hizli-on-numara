import numpy as np

from analysis.bayesian import bayesian_smoothed_context_score
from analysis.model import NUMBER_COUNT, NUMBERS_PER_DRAW
from analysis.strategies import markov_transition_score


BASE_RATE = NUMBERS_PER_DRAW / NUMBER_COUNT


def _transition_z(counts, exposure):
    counts = np.asarray(counts, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    expected = exposure[..., None] * BASE_RATE
    deviation = np.sqrt(np.maximum(exposure[..., None] * BASE_RATE * (1 - BASE_RATE), 1e-12))
    return (counts - expected) / deviation


def time_decay_score(state):
    context = state.latest_draw
    active = context[state.decayed_exposure[context] > 0]
    if active.size == 0:
        return np.zeros(NUMBER_COUNT)
    rate = state.decayed_counts[active] / state.decayed_exposure[active, None]
    n_eff = state.decayed_exposure[active] ** 2 / np.maximum(
        state.decayed_exposure_sq[active], 1e-12
    )
    z = (rate - BASE_RATE) / np.sqrt(
        BASE_RATE * (1 - BASE_RATE) / np.maximum(n_eff[:, None], 1e-12)
    )
    return np.clip(z, -state.config.relation_clip, state.config.relation_clip).mean(axis=0)


def multi_lag_score(state):
    components = []
    weights = []
    history = list(state.history)
    for lag_index, lag_weight in enumerate(state.config.multi_lag_weights):
        if len(history) <= lag_index:
            continue
        context = history[-(lag_index + 1)][1]
        exposure = state.lag_exposure[lag_index]
        active = context[exposure[context] > 0]
        if active.size == 0:
            continue
        z = _transition_z(state.lag_counts[lag_index][active], exposure[active])
        components.append(np.clip(z, -state.config.relation_clip, state.config.relation_clip).mean(axis=0))
        weights.append(lag_weight)
    if not components:
        return np.zeros(NUMBER_COUNT)
    return np.average(np.asarray(components), axis=0, weights=np.asarray(weights))


def significant_transition_score(state):
    context = state.latest_draw
    exposure = state.baseline.transition_exposure
    active = context[exposure[context] >= state.config.significant_min_support]
    if active.size == 0:
        return np.zeros(NUMBER_COUNT)
    z = _transition_z(state.baseline.transition_counts[active], exposure[active])
    mask = np.abs(z) >= state.config.significant_z_threshold
    return np.where(mask, np.clip(z, -state.config.relation_clip, state.config.relation_clip), 0.0).mean(axis=0)


def reliability_weighted_context_score(state):
    context = state.latest_draw
    exposure = state.baseline.transition_exposure
    active = context[exposure[context] > 0]
    if active.size == 0:
        return np.zeros(NUMBER_COUNT)
    counts = state.baseline.transition_counts[active]
    rates = counts / exposure[active, None]
    noise = BASE_RATE * (1 - BASE_RATE) / exposure[active]
    signal = np.maximum(((rates - BASE_RATE) ** 2).mean(axis=1) - noise, 0.0)
    reliability = exposure[active] / (exposure[active] + 100.0)
    weights = np.sqrt(signal) * reliability
    if np.allclose(weights.sum(), 0.0):
        weights = np.ones_like(weights)
    z = np.clip(
        _transition_z(counts, exposure[active]),
        -state.config.relation_clip,
        state.config.relation_clip,
    )
    return np.average(z, axis=0, weights=weights)


def calculate_m4_variants(state):
    baseline = state.baseline
    return {
        "M4-A": markov_transition_score(baseline, state.config.relation_clip),
        "M4-B": time_decay_score(state),
        "M4-C": bayesian_smoothed_context_score(
            baseline.transition_counts,
            baseline.transition_exposure,
            baseline.latest_draw,
            state.config.bayesian_prior_strength,
        ),
        "M4-D": multi_lag_score(state),
        "M4-E": significant_transition_score(state),
        "M4-F": reliability_weighted_context_score(state),
    }
