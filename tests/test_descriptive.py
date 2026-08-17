import unittest

import pandas as pd

from analysis.descriptive import (
    block_summary,
    ending_digit_summary,
    number_frequency_summary,
)
from veri_modeli import SAYI_KOLONLARI


def sample_draws(draw_count=20):
    rows = []
    for offset in range(draw_count):
        numbers = [((number + offset - 1) % 80) + 1 for number in range(1, 21)]
        rows.append(dict(zip(SAYI_KOLONLARI, numbers)))
    return pd.DataFrame(rows)


class DescriptiveAnalysisTests(unittest.TestCase):
    def test_number_summary_contains_all_numbers_and_neutral_momentum(self):
        result = number_frequency_summary(sample_draws(), SAYI_KOLONLARI, 5, 20)

        self.assertEqual(result["Number"].tolist(), list(range(1, 81)))
        self.assertAlmostEqual(result["Short Expected"].iloc[0], 1.25)
        self.assertAlmostEqual(result["Long Expected"].iloc[0], 5.0)
        self.assertIn("Frequency Momentum", result.columns)

    def test_block_observed_and_expected_totals_match_draw_size(self):
        result = block_summary(sample_draws(), SAYI_KOLONLARI, window=20)

        self.assertEqual(len(result), 8)
        self.assertEqual(result["Observed"].sum(), 20 * 20)
        self.assertAlmostEqual(result["Expected"].sum(), 20 * 20)

    def test_ending_digit_groups_cover_all_drawn_numbers(self):
        result = ending_digit_summary(sample_draws(), SAYI_KOLONLARI, window=20)

        self.assertEqual(len(result), 10)
        self.assertEqual(result["Observed"].sum(), 20 * 20)
        self.assertAlmostEqual(result["Expected per Draw"].iloc[0], 2.0)


if __name__ == "__main__":
    unittest.main()
