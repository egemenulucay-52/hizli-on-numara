import unittest

import pandas as pd

from analysis.tail_metrics import (
    benjamini_hochberg,
    clopper_pearson_interval,
    exact_random_rate,
    near_perfect_random_rate,
    summarize_tail_metrics,
)


class TailMetricTests(unittest.TestCase):
    def test_random_rates_use_hypergeometric_distribution(self):
        self.assertAlmostEqual(exact_random_rate(4), 0.003063392303899699)
        self.assertAlmostEqual(exact_random_rate(6), 0.00012898493911156627)
        self.assertAlmostEqual(near_perfect_random_rate(4), 0.046311283653055804)
        self.assertAlmostEqual(near_perfect_random_rate(6), 0.0032246234777891565)

    def test_confidence_interval_and_bh_are_bounded(self):
        low, high = clopper_pearson_interval(2, 100)
        self.assertLess(low, 0.02)
        self.assertGreater(high, 0.02)
        adjusted = benjamini_hochberg([0.001, 0.02, 0.5])
        self.assertEqual(len(adjusted), 3)
        self.assertTrue(all(0 <= value <= 1 for value in adjusted))

    def test_summary_contains_exact_and_near_metrics(self):
        rows = []
        for index in range(20):
            row = {}
            for model in ("M1", "M2", "M3", "M4", "M5", "M6", "Ensemble"):
                row[f"{model} Hit@4"] = 4 if index == 0 else 1
                row[f"{model} Hit@5"] = 5 if index == 0 else 1
                row[f"{model} Hit@6"] = 6 if index == 0 else 1
            rows.append(row)
        summary = summarize_tail_metrics(
            pd.DataFrame(rows), windows=(None,), monte_carlo_samples=100
        )
        self.assertEqual(len(summary), 7 * 3 * 2)
        exact6 = summary[
            (summary["Model"] == "M1")
            & (summary["Objective"] == "Exact")
            & (summary["Selection Size"] == 6)
        ].iloc[0]
        self.assertEqual(exact6["Observed Count"], 1)
        self.assertIn("q-value", summary.columns)


if __name__ == "__main__":
    unittest.main()
