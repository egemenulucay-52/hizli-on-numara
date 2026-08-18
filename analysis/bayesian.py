import numpy as np

from analysis.model import NUMBER_COUNT, NUMBERS_PER_DRAW


BASE_RATE = NUMBERS_PER_DRAW / NUMBER_COUNT


def posterior_transition_moments(counts, exposure, prior_strength=40.0):
    counts = np.asarray(counts, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    alpha = counts + prior_strength * BASE_RATE
    beta = exposure[..., None] - counts + prior_strength * (1.0 - BASE_RATE)
    total = alpha + beta
    mean = alpha / total
    variance = alpha * beta / (total * total * (total + 1.0))
    reliability = exposure / (exposure + prior_strength)
    return mean, variance, reliability


def bayesian_smoothed_context_score(counts, exposure, context, prior_strength=40.0):
    active = np.asarray(context, dtype=int)
    active = active[np.asarray(exposure)[active] > 0]
    if active.size == 0:
        return np.zeros(NUMBER_COUNT)
    mean, _, reliability = posterior_transition_moments(
        np.asarray(counts)[active], np.asarray(exposure)[active], prior_strength
    )
    return ((mean - BASE_RATE) * reliability[:, None]).mean(axis=0)


def m8_bayesian_conditional_score(counts, exposure, context, prior_strength=40.0, clip=4.0):
    active = np.asarray(context, dtype=int)
    active = active[np.asarray(exposure)[active] > 0]
    if active.size == 0:
        return np.zeros(NUMBER_COUNT)
    mean, variance, reliability = posterior_transition_moments(
        np.asarray(counts)[active], np.asarray(exposure)[active], prior_strength
    )
    posterior_z = (mean - BASE_RATE) / np.sqrt(np.maximum(variance, 1e-12))
    return (np.clip(posterior_z, -clip, clip) * reliability[:, None]).mean(axis=0)
