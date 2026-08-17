import os
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

import grup_analizi


class GrupAnaliziTestleri(unittest.TestCase):
    def test_yalniz_ikili_uclu_dortlu_kombinasyonlar_rapora_girer(self):
        satirlar = []
        for cekilis_no in range(10005, 10000, -1):
            satir = {"Tarih": "2026-08-17 21:00:00", "CekilisNo": str(cekilis_no)}
            satir.update({f"Sayi_{i}": i for i in range(1, 21)})
            satirlar.append(satir)

        with tempfile.TemporaryDirectory() as gecici_dizin:
            csv_yolu = os.path.join(gecici_dizin, "veri.csv")
            rapor_yolu = os.path.join(gecici_dizin, "rapor.md")
            ozet_yolu = os.path.join(gecici_dizin, "ozet.csv")
            pd.DataFrame(satirlar).to_csv(csv_yolu, index=False)

            with (
                patch.object(grup_analizi, "CSV_DOSYASI", csv_yolu),
                patch.object(grup_analizi, "RAPOR_MD", rapor_yolu),
                patch.object(grup_analizi, "RAPOR_CSV", ozet_yolu),
            ):
                grup_analizi.grup_analizini_calistir()

            with open(rapor_yolu, encoding="utf-8") as rapor_dosyasi:
                rapor = rapor_dosyasi.read()

            self.assertIn("4'lı Ortak Gruplar", rapor)
            self.assertNotIn("5'lı Ortak Gruplar", rapor)
            self.assertNotIn("6'lı Ortak Gruplar", rapor)


if __name__ == "__main__":
    unittest.main()
