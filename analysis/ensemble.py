import numpy as np
import pandas as pd

from analysis.config import AnalysisConfig, MODEL_NAMES
from analysis.model import NUMBER_COUNT
from analysis.strategies import calculate_raw_scores


def robust_percentile_rank(values):
    """Aşırı uçları kırpıp skorları deterministik olarak 0-1 aralığına taşır."""

    values = np.asarray(values, dtype=float)
    if values.shape != (NUMBER_COUNT,):
        raise ValueError(f"Skor dizisi {NUMBER_COUNT} elemanlı olmalıdır.")
    if not np.isfinite(values).all():
        raise ValueError("Skor dizisi yalnız sonlu değerler içermelidir.")

    lower, upper = np.quantile(values, [0.05, 0.95])
    clipped = np.clip(values, lower, upper)
    if np.allclose(clipped, clipped[0]):
        return np.full(NUMBER_COUNT, 0.5)

    ranks = pd.Series(clipped).rank(method="average").to_numpy(dtype=float)
    return (ranks - 1.0) / (NUMBER_COUNT - 1.0)


def normalize_scores(raw_scores):
    if tuple(raw_scores) != MODEL_NAMES:
        raise ValueError(f"Beklenen model sırası: {MODEL_NAMES}")
    return {
        model: robust_percentile_rank(raw_scores[model]) for model in MODEL_NAMES
    }


def weighted_ensemble_score(normalized_scores, config=None):
    config = config or AnalysisConfig()
    return sum(
        normalized_scores[model] * config.weights[model] for model in MODEL_NAMES
    )


def rank_numbers(scores):
    """Skor azalan, eşitlikte sayı artan deterministik sıralama."""

    scores = np.asarray(scores, dtype=float)
    if scores.shape != (NUMBER_COUNT,):
        raise ValueError(f"Skor dizisi {NUMBER_COUNT} elemanlı olmalıdır.")
    numbers = np.arange(1, NUMBER_COUNT + 1)
    return numbers[np.lexsort((numbers, -scores))]


def score_state(state, config=None):
    """Ham/normalize skorları ve ensemble sıralamasını tek seferde üretir."""

    config = config or state.config or AnalysisConfig()
    raw = calculate_raw_scores(state, config)
    normalized = normalize_scores(raw)
    ensemble = weighted_ensemble_score(normalized, config)
    rankings = {model: rank_numbers(normalized[model]) for model in MODEL_NAMES}
    rankings["Ensemble"] = rank_numbers(ensemble)
    return raw, normalized, ensemble, rankings


def score_table(state, config=None):
    raw, normalized, ensemble, _ = score_state(state, config)
    table = pd.DataFrame({"Number": np.arange(1, NUMBER_COUNT + 1)})
    for model in MODEL_NAMES:
        table[f"{model} Raw"] = raw[model]
        table[f"{model} Score"] = normalized[model]
    table["Final Score"] = ensemble
    return table.sort_values(
        ["Final Score", "Number"], ascending=[False, True]
    ).reset_index(drop=True)
