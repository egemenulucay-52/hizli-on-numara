import unittest

from analysis.model import (
    COMBINATION_SIZES,
    category_count_moments,
    combination_inclusion_probability,
    combination_occurrence_moments,
)


class TeorikModelTestleri(unittest.TestCase):
    def test_kombinasyon_kapsami_ikiden_dorde_kadardir(self):
        self.assertEqual(COMBINATION_SIZES, (2, 3, 4))

    def test_tek_sayi_ve_ikili_olasiliklari_kesindir(self):
        self.assertAlmostEqual(combination_inclusion_probability(1), 20 / 80)
        self.assertAlmostEqual(
            combination_inclusion_probability(2),
            (20 / 80) * (19 / 79),
        )

    def test_ikili_tekrar_momentleri_binom_modelini_kullanir(self):
        probability = (20 / 80) * (19 / 79)
        moments = combination_occurrence_moments(150, 2)

        self.assertAlmostEqual(moments.expected, 150 * probability)
        self.assertAlmostEqual(moments.variance, 150 * probability * (1 - probability))

    def test_blok_ve_son_basamak_beklenen_degerleri(self):
        block = category_count_moments(150, 10)
        ending_digit = category_count_moments(150, 8)

        self.assertAlmostEqual(block.expected, 150 * 2.5)
        self.assertAlmostEqual(ending_digit.expected, 150 * 2.0)
        self.assertGreater(block.standard_deviation, 0)

    def test_gecersiz_parametreler_reddedilir(self):
        with self.assertRaises(ValueError):
            combination_inclusion_probability(0)
        with self.assertRaises(ValueError):
            combination_occurrence_moments(-1, 2)
        with self.assertRaises(ValueError):
            category_count_moments(10, 81)


if __name__ == "__main__":
    unittest.main()
