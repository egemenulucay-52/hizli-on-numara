import pandas as pd

from analysis.benchmark import expected_random_hits
from analysis.config import AnalysisConfig, MODEL_NAMES
from analysis.ensemble import score_state
from analysis.evaluation import SELECTION_SIZES, evaluate_ranking
from analysis.state import IncrementalAnalysisState
from veri_modeli import SAYI_KOLONLARI, veri_cercevesini_dogrula


def chronological_standard_draws(df):
    """Standart çekilişleri backtest için kesin olarak eski->yeni sıralar."""

    veri_cercevesini_dogrula(df)
    result = df.copy()
    result["CekilisNo"] = result["CekilisNo"].astype(str)
    result = result[result["CekilisNo"].str.fullmatch(r"\d{5,6}")].copy()
    result["_numeric_draw_id"] = pd.to_numeric(result["CekilisNo"], errors="raise")
    if result["_numeric_draw_id"].duplicated().any():
        raise ValueError("Backtest verisinde yinelenen çekiliş numarası var.")
    result = result.sort_values("_numeric_draw_id", ascending=True)
    if not result["_numeric_draw_id"].is_monotonic_increasing:
        raise AssertionError("Backtest zaman yönü eski->yeni kurulamadı.")
    return result.drop(columns="_numeric_draw_id").reset_index(drop=True)


def walk_forward_backtest(df, config=None, last=None):
    """Her hedefi görmeden skorlayan expanding-window walk-forward testi."""

    config = config or AnalysisConfig()
    draws = chronological_standard_draws(df)
    if len(draws) <= config.minimum_training_size:
        raise ValueError("Backtest için minimum eğitimden daha fazla çekiliş gerekir.")
    if last is not None and (
        isinstance(last, bool) or not isinstance(last, int) or last < 1
    ):
        raise ValueError("last pozitif bir tam sayı veya None olmalıdır.")

    numeric_ids = draws["CekilisNo"].astype(int).to_numpy()
    eligible_targets = [
        index
        for index in range(config.minimum_training_size, len(draws))
        if numeric_ids[index] == numeric_ids[index - 1] + 1
    ]
    if not eligible_targets:
        raise ValueError("Değerlendirilebilecek ardışık hedef çekiliş bulunamadı.")
    if last is not None:
        eligible_targets = eligible_targets[-last:]
    first_target = eligible_targets[0]

    state = IncrementalAnalysisState(config)
    for index in range(first_target):
        row = draws.iloc[index]
        state.update(row[SAYI_KOLONLARI].to_numpy(dtype=int), row["CekilisNo"])

    records = []
    for target_index in range(first_target, len(draws)):
        target = draws.iloc[target_index]
        training_last = draws.iloc[target_index - 1]
        if state.latest_draw_id != str(training_last["CekilisNo"]):
            raise AssertionError("Look-ahead koruması: eğitim sonu hedefle uyuşmuyor.")
        if state.draw_count != target_index:
            raise AssertionError("Look-ahead koruması: hedef state'e erken eklenmiş.")

        actual = target[SAYI_KOLONLARI].to_numpy(dtype=int)
        if numeric_ids[target_index] != numeric_ids[target_index - 1] + 1:
            # Eksik çekilişin üzerinden geçiş veya geriye dönük tahmin üretilmez.
            state.update(actual, target["CekilisNo"])
            continue

        _, _, _, rankings = score_state(state, config)
        record = {
            "Train End Draw": str(training_last["CekilisNo"]),
            "Target Draw": str(target["CekilisNo"]),
            "Training Size": state.draw_count,
            "Strategy Version": config.strategy_version,
            "Config Version": config.config_version,
            "Config Hash": config.config_hash,
        }
        for model in (*MODEL_NAMES, "Ensemble"):
            ranking = rankings[model]
            record[f"{model} Top6"] = " ".join(map(str, ranking[:6]))
            hits = evaluate_ranking(ranking, actual)
            for size in SELECTION_SIZES:
                record[f"{model} Hit@{size}"] = hits[size]
        for size in SELECTION_SIZES:
            record[f"Random Expected Hit@{size}"] = expected_random_hits(size)
        records.append(record)

        # Hedef ancak tahmin ve değerlendirme tamamlandıktan sonra geçmişe eklenir.
        state.update(actual, target["CekilisNo"])

    return pd.DataFrame(records)
