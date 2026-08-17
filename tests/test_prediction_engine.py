import unittest

import numpy as np
import pandas as pd

from analysis.backtest import chronological_standard_draws, walk_forward_backtest
from analysis.benchmark import (
    expected_random_hits,
    random_hit_distribution,
)
from analysis.config import AnalysisConfig, MODEL_NAMES
from analysis.ensemble import robust_percentile_rank, score_state
from analysis.evaluation import summarize_backtest_windows
from analysis.state import IncrementalAnalysisState
from veri_modeli import SAYI_KOLONLARI


def generated_draw(index, offset=0):
    return ((np.arange(20) * 3 + index * 7 + offset) % 80) + 1


def generated_frame(draw_count=20):
    rows = []
    for index in range(draw_count):
        row = {"CekilisNo": str(10000 + index)}
        row.update(
            {
                column: int(value)
                for column, value in zip(SAYI_KOLONLARI, generated_draw(index))
            }
        )
        rows.append(row)
    # Üretim CSV'si gibi yeni->eski veriyoruz.
    return pd.DataFrame(rows[::-1])


class PredictionEngineTests(unittest.TestCase):
    def test_config_weights_are_fixed_and_hashed(self):
        config = AnalysisConfig(minimum_training_size=5)
        self.assertEqual(tuple(config.weights), MODEL_NAMES)
        self.assertAlmostEqual(sum(config.weights.values()), 1.0)
        self.assertEqual(len(config.config_hash), 64)

    def test_all_models_produce_finite_normalized_rankings(self):
        config = AnalysisConfig(
            minimum_training_size=5,
            short_window=3,
            long_window=5,
            deviation_window=5,
            structural_window=4,
        )
        state = IncrementalAnalysisState(config)
        for index in range(8):
            state.update(generated_draw(index), str(10000 + index))

        raw, normalized, ensemble, rankings = score_state(state, config)
        for model in MODEL_NAMES:
            self.assertEqual(raw[model].shape, (80,))
            self.assertTrue(np.isfinite(raw[model]).all())
            self.assertTrue(((normalized[model] >= 0) & (normalized[model] <= 1)).all())
            self.assertEqual(len(set(rankings[model].tolist())), 80)
        self.assertTrue(np.isfinite(ensemble).all())
        self.assertEqual(len(set(rankings["Ensemble"].tolist())), 80)

    def test_constant_scores_normalize_to_neutral(self):
        normalized = robust_percentile_rank(np.ones(80))
        np.testing.assert_allclose(normalized, 0.5)

    def test_random_benchmark_is_exact(self):
        self.assertEqual(expected_random_hits(4), 1.0)
        self.assertEqual(expected_random_hits(5), 1.25)
        self.assertEqual(expected_random_hits(6), 1.5)
        self.assertAlmostEqual(sum(random_hit_distribution(6).values()), 1.0)

    def test_nonstandard_id_is_excluded_and_time_is_ascending(self):
        frame = generated_frame(8)
        legacy = frame.iloc[[0]].copy()
        legacy["CekilisNo"] = "202605222219"
        prepared = chronological_standard_draws(pd.concat([frame, legacy]))
        self.assertEqual(len(prepared), 8)
        ids = prepared["CekilisNo"].astype(int).tolist()
        self.assertEqual(ids, sorted(ids))

    def test_missing_draw_is_not_markov_transition_or_backtest_target(self):
        config = AnalysisConfig(
            minimum_training_size=5,
            short_window=3,
            long_window=5,
            deviation_window=5,
            structural_window=4,
        )
        state = IncrementalAnalysisState(config)
        state.update(generated_draw(0), "10000")
        state.update(generated_draw(2), "10002")
        self.assertEqual(int(state.transition_exposure.sum()), 0)
        self.assertEqual(int(state.transition_counts.sum()), 0)

        frame = generated_frame(9)
        frame = frame[frame["CekilisNo"] != "10006"]
        results = walk_forward_backtest(frame, config=config)
        self.assertNotIn("10007", results["Target Draw"].tolist())
        self.assertIn("10008", results["Target Draw"].tolist())

    def test_walk_forward_does_not_see_target(self):
        config = AnalysisConfig(
            minimum_training_size=5,
            short_window=3,
            long_window=5,
            deviation_window=5,
            structural_window=4,
        )
        first = generated_frame(9)
        changed = first.copy()
        target_id = "10005"
        target_index = changed.index[changed["CekilisNo"] == target_id][0]
        changed.loc[target_index, SAYI_KOLONLARI] = generated_draw(5, offset=1)

        result_a = walk_forward_backtest(first, config=config)
        result_b = walk_forward_backtest(changed, config=config)
        first_a = result_a.iloc[0]
        first_b = result_b.iloc[0]
        self.assertEqual(first_a["Target Draw"], target_id)
        self.assertEqual(first_a["Train End Draw"], "10004")
        for model in (*MODEL_NAMES, "Ensemble"):
            self.assertEqual(first_a[f"{model} Top6"], first_b[f"{model} Top6"])

        summary = summarize_backtest_windows(result_a, windows=(2, 4))
        self.assertEqual(set(summary["Window"]), {"All", "Last 2", "Last 4"})


if __name__ == "__main__":
    unittest.main()
