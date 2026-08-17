import numpy as np
import pandas as pd

from analysis.benchmark import expected_random_hits
from analysis.config import MODEL_NAMES


EVALUATED_MODELS = (*MODEL_NAMES, "Ensemble")
SELECTION_SIZES = (4, 5, 6)


def evaluate_ranking(ranking, actual_numbers):
    ranking = np.asarray(ranking, dtype=int)
    actual = set(np.asarray(actual_numbers, dtype=int).tolist())
    return {
        size: len(set(ranking[:size].tolist()) & actual)
        for size in SELECTION_SIZES
    }


def summarize_backtest(results, last=None):
    if results.empty:
        return pd.DataFrame()
    selected = results.tail(last) if last is not None else results
    rows = []
    for model in EVALUATED_MODELS:
        row = {"Model": model, "Evaluation Count": len(selected)}
        for size in SELECTION_SIZES:
            values = selected[f"{model} Hit@{size}"]
            mean = float(values.mean())
            row[f"Mean Hit@{size}"] = mean
            row[f"Median Hit@{size}"] = float(values.median())
            row[f"Std Hit@{size}"] = float(values.std(ddof=0))
            row[f"Cumulative Hit@{size}"] = int(values.sum())
            row[f"Lift@{size}"] = mean / expected_random_hits(size)
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_backtest_windows(results, windows=(25, 50, 100, 250)):
    """Aynı backtest için tüm geçmiş ve sabit son dönem özetlerini birleştirir."""

    summaries = []
    all_history = summarize_backtest(results)
    if not all_history.empty:
        all_history.insert(0, "Window", "All")
        summaries.append(all_history)

    for window in windows:
        if window > len(results):
            continue
        summary = summarize_backtest(results, last=window)
        summary.insert(0, "Window", f"Last {window}")
        summaries.append(summary)
    return pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
