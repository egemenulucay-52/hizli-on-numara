from hashlib import sha256

import numpy as np
import pandas as pd

from analysis.benchmark import random_hit_probability
from analysis.config import MODEL_NAMES


TAIL_OBJECTIVES = {
    "Exact": {4: 4, 5: 5, 6: 6},
    "NearPerfect": {4: 3, 5: 4, 6: 5},
}
DEFAULT_EVALUATED_MODELS = (*MODEL_NAMES, "Ensemble")


def exact_random_rate(selection_size):
    return random_hit_probability(selection_size, selection_size)


def near_perfect_random_rate(selection_size):
    threshold = selection_size - 1
    return sum(
        random_hit_probability(selection_size, hit)
        for hit in range(threshold, selection_size + 1)
    )


def objective_random_rate(objective, selection_size):
    if objective == "Exact":
        return exact_random_rate(selection_size)
    if objective == "NearPerfect":
        return near_perfect_random_rate(selection_size)
    raise ValueError(f"Bilinmeyen tail objective: {objective}")


def clopper_pearson_interval(successes, trials, confidence=0.95):
    from scipy.stats import beta

    if trials < 1 or not 0 <= successes <= trials:
        raise ValueError("Başarı ve deneme sayıları geçersiz.")
    alpha = 1.0 - confidence
    lower = 0.0 if successes == 0 else beta.ppf(alpha / 2, successes, trials - successes + 1)
    upper = 1.0 if successes == trials else beta.ppf(1 - alpha / 2, successes + 1, trials - successes)
    return float(lower), float(upper)


def benjamini_hochberg(p_values):
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or np.any((values < 0) | (values > 1)):
        raise ValueError("p-value dizisi 0-1 aralığında olmalıdır.")
    order = np.argsort(values)
    ranked = values[order]
    adjusted_ranked = ranked * len(values) / np.arange(1, len(values) + 1)
    adjusted_ranked = np.minimum.accumulate(adjusted_ranked[::-1])[::-1]
    adjusted = np.empty_like(adjusted_ranked)
    adjusted[order] = np.clip(adjusted_ranked, 0.0, 1.0)
    return adjusted


def _stable_seed(*parts):
    digest = sha256("|".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _monte_carlo_p_value(observed, trials, probability, samples, seed_parts):
    if samples < 1:
        return np.nan
    rng = np.random.default_rng(_stable_seed(*seed_parts))
    simulated = rng.binomial(trials, probability, size=samples)
    return float((1 + np.count_nonzero(simulated >= observed)) / (samples + 1))


def summarize_tail_metrics(
    results,
    models=DEFAULT_EVALUATED_MODELS,
    windows=(None, 25, 50, 100, 250),
    monte_carlo_samples=50_000,
):
    """Exact ve near-perfect tail metriklerini model/pencere bazında özetler."""

    from scipy.stats import binom

    if results.empty:
        return pd.DataFrame()
    rows = []
    for window in windows:
        if window is not None and window > len(results):
            continue
        selected = results if window is None else results.tail(window)
        window_label = "All" if window is None else f"Last {window}"
        trials = len(selected)
        for objective, thresholds in TAIL_OBJECTIVES.items():
            for selection_size, threshold in thresholds.items():
                random_rate = objective_random_rate(objective, selection_size)
                for model in models:
                    hits = selected[f"{model} Hit@{selection_size}"].to_numpy(dtype=int)
                    observed = int(np.count_nonzero(hits >= threshold))
                    rate = observed / trials
                    ci_low, ci_high = clopper_pearson_interval(observed, trials)
                    exact_p = float(binom.sf(observed - 1, trials, random_rate))
                    rows.append(
                        {
                            "Window": window_label,
                            "Objective": objective,
                            "Selection Size": selection_size,
                            "Model": model,
                            "Evaluation Count": trials,
                            "Observed Count": observed,
                            "Observed Rate": rate,
                            "Random Rate": random_rate,
                            "Expected Count": trials * random_rate,
                            "Lift": rate / random_rate,
                            "Rate CI Low": ci_low,
                            "Rate CI High": ci_high,
                            "Lift CI Low": ci_low / random_rate,
                            "Lift CI High": ci_high / random_rate,
                            "Exact p-value": exact_p,
                            "Monte Carlo p-value": _monte_carlo_p_value(
                                observed,
                                trials,
                                random_rate,
                                monte_carlo_samples,
                                (window_label, objective, selection_size, model),
                            ),
                            f"Mean Hit@{selection_size}": float(hits.mean()),
                        }
                    )

    summary = pd.DataFrame(rows)
    summary["q-value"] = np.nan
    family_columns = ["Window", "Objective", "Selection Size"]
    for _, family in summary.groupby(family_columns, sort=False):
        summary.loc[family.index, "q-value"] = benjamini_hochberg(
            family["Exact p-value"].to_numpy()
        )

    def evidence_status(row):
        if row["Expected Count"] < 5:
            return "Insufficient tail sample"
        if row["q-value"] <= 0.05 and row["Lift CI Low"] > 1.0:
            return "Statistically supported historical signal"
        if row["Lift"] > 1.0:
            return "Promising historical signal - insufficient evidence"
        return "No historical evidence"

    summary["Evidence Status"] = summary.apply(evidence_status, axis=1)
    return summary
