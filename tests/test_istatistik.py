import unittest

import pandas as pd

import istatistik


class IstatistikTestleri(unittest.TestCase):
    def test_markov_gecmisten_gelecege_hesaplanir(self):
        # Veri sırası: en yeni (2), ardından daha eski (1).
        df = pd.DataFrame({"Sayi_1": [2, 1]})

        matris = istatistik.markov_zinciri_matrisi(df, ["Sayi_1"])

        self.assertEqual(matris[0, 1], 1.0)
        self.assertEqual(matris[1, 0], 0.0)

    def test_gecikmeye_ulasma_olasiligi_kuyruk_olasiligidir(self):
        df = pd.DataFrame({"Sayi_1": [2, 3, 1]})

        sonuc = istatistik.gecikme_derinligi_analizi(df, ["Sayi_1"])

        self.assertEqual(sonuc.loc[1, "gecikme"], 2)
        self.assertAlmostEqual(sonuc.loc[1, "olasilik"], 0.75**2)


if __name__ == "__main__":
    unittest.main()
