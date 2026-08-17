import unittest

import pandas as pd

from analiz_motoru import (
    KOMBINASYON_BOYUTLARI,
    blok_analizi,
    cok_boyutlu_skorlar,
    ikili_frekans_farki,
    kombinasyon_ozeti,
)
from veri_modeli import SAYI_KOLONLARI, veri_cercevesini_normalize_et


def ornek_veri():
    satirlar = []
    for sira in range(8):
        sayilar = [((sayi + sira - 1) % 80) + 1 for sayi in range(1, 21)]
        satir = {"Tarih": "2026-08-17 21:00:00", "CekilisNo": str(10008 - sira)}
        satir.update({kolon: sayi for kolon, sayi in zip(SAYI_KOLONLARI, sayilar)})
        satirlar.append(satir)
    return veri_cercevesini_normalize_et(pd.DataFrame(satirlar))


class AnalizMotoruTestleri(unittest.TestCase):
    def test_ortak_skor_motoru_80_sayi_dondurur(self):
        sonuc = cok_boyutlu_skorlar(ornek_veri(), SAYI_KOLONLARI)

        self.assertEqual(len(sonuc), 80)
        self.assertEqual(
            set(sonuc.columns),
            {"Sayı", "Frekans_Farki", "Iliski_Agi_Skoru", "Gecikme_Skoru", "Bolge_Yogunluk_Eksigi"},
        )

    def test_kombinasyon_boyutlari_yalniz_iki_ile_dort_arasidir(self):
        sonuc = kombinasyon_ozeti(ornek_veri(), SAYI_KOLONLARI)

        self.assertEqual(KOMBINASYON_BOYUTLARI, (2, 3, 4))
        self.assertEqual(
            sonuc["Grup Tipi"].tolist(),
            ["2'lı Ortak Gruplar", "3'lı Ortak Gruplar", "4'lı Ortak Gruplar"],
        )

    def test_rapor_fonksiyonlari_bos_olmayan_tablo_dondurur(self):
        df = ornek_veri()

        self.assertEqual(len(blok_analizi(df, SAYI_KOLONLARI)), 8)
        self.assertFalse(ikili_frekans_farki(df, SAYI_KOLONLARI).empty)


if __name__ == "__main__":
    unittest.main()
