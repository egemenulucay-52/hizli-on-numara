import os
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

import veri_cekici
from veri_modeli import veri_cercevesini_dogrula


def cekilis_satiri(cekilis_no, baslangic=1):
    sayilar = list(range(baslangic, baslangic + 20))
    satir = {"Tarih": "2026-08-17 21:00:00", "CekilisNo": str(cekilis_no)}
    satir.update({f"Sayi_{i}": sayi for i, sayi in enumerate(sayilar, start=1)})
    return satir


class VeriCekiciTestleri(unittest.TestCase):
    def test_csv_yazimi_dogrular_ve_standart_idyi_once_siralar(self):
        with tempfile.TemporaryDirectory() as gecici_dizin:
            csv_yolu = os.path.join(gecici_dizin, "veri.csv")
            pd.DataFrame([cekilis_satiri("202605222219")]).to_csv(csv_yolu, index=False)

            with patch.object(veri_cekici, "CSV_DOSYASI", csv_yolu):
                veri_cekici.veri_tabanina_kaydet([cekilis_satiri("49665", 21)])

            sonuc = pd.read_csv(csv_yolu, dtype={"CekilisNo": str})
            self.assertEqual(sonuc.iloc[0]["CekilisNo"], "49665")
            self.assertEqual(len(sonuc), 2)

    def test_yinelenen_sayilar_reddedilir(self):
        satir = cekilis_satiri("49665")
        satir["Sayi_20"] = satir["Sayi_19"]

        with self.assertRaisesRegex(ValueError, "20 benzersiz"):
            veri_cercevesini_dogrula(pd.DataFrame([satir]))

    @patch.object(veri_cekici, "motor_2_stealth_selenium")
    @patch.object(veri_cekici, "motor_1_api", side_effect=ValueError("boş API"))
    def test_api_bozulursa_seleniuma_gecilir(self, _api, selenium):
        veri_cekici.canli_cekilis_takip_et()
        selenium.assert_called_once_with()

    @patch.object(veri_cekici, "motor_2_stealth_selenium", side_effect=RuntimeError("sayfa yok"))
    @patch.object(veri_cekici, "motor_1_api", side_effect=ValueError("boş API"))
    def test_iki_motor_hatasi_islemi_basarisiz_yapar(self, _api, _selenium):
        with self.assertRaisesRegex(RuntimeError, "İki veri motoru"):
            veri_cekici.canli_cekilis_takip_et()


if __name__ == "__main__":
    unittest.main()
