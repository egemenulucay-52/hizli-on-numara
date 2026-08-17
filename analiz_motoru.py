import itertools
from collections import Counter

import numpy as np
import pandas as pd


KOMBINASYON_BOYUTLARI = (2, 3, 4, 5)


def cok_boyutlu_skorlar(df, sayi_kolonlari):
    if df.empty:
        raise ValueError("Skor üretmek için en az bir çekiliş gerekir.")

    df_len = len(df)
    short_len = min(15, df_len)
    long_len = min(150, df_len)
    short_freq = (
        pd.Series(df.head(short_len)[sayi_kolonlari].values.flatten())
        .value_counts()
        .reindex(range(1, 81), fill_value=0)
        / short_len
    )
    long_freq = (
        pd.Series(df.head(long_len)[sayi_kolonlari].values.flatten())
        .value_counts()
        .reindex(range(1, 81), fill_value=0)
        / long_len
    )

    birlikte_cikma = np.zeros((80, 80))
    for _, row in df.head(100)[sayi_kolonlari].iterrows():
        nums = row.values.astype(int) - 1
        birlikte_cikma[np.ix_(nums, nums)] += 1
        birlikte_cikma[nums, nums] -= 1

    son_cekilis = df.iloc[0][sayi_kolonlari].values.astype(int)
    iliski_skorlari = birlikte_cikma[:, son_cekilis - 1].sum(axis=1)

    gecikme_skorlari = []
    for num in range(1, 81):
        gorulmeler = np.where((df[sayi_kolonlari] == num).any(axis=1))[0]
        if len(gorulmeler) > 0:
            mevcut_gecikme = float(gorulmeler[0])
            gecmis_oran = len(gorulmeler) / df_len
            skor = 1.0 - np.exp(-gecmis_oran * mevcut_gecikme)
        else:
            skor = 1.0
        gecikme_skorlari.append(skor)

    son_10 = df.head(10)
    bolge_sayilari = pd.Series(
        (son_10[sayi_kolonlari].values.flatten() - 1) // 10
    ).value_counts().reindex(range(8), fill_value=0)
    beklenen_bolge_adedi = len(son_10) * len(sayi_kolonlari) / 8
    bolge_skorlari = [
        float(beklenen_bolge_adedi - bolge_sayilari[(num - 1) // 10])
        for num in range(1, 81)
    ]

    return pd.DataFrame({
        "Sayı": range(1, 81),
        "Frekans_Farki": (short_freq - long_freq).values,
        "Iliski_Agi_Skoru": iliski_skorlari,
        "Gecikme_Skoru": gecikme_skorlari,
        "Bolge_Yogunluk_Eksigi": bolge_skorlari,
    })


def blok_analizi(df, sayi_kolonlari):
    bloklar = {
        "1_10": range(1, 11),
        "11_20": range(11, 21),
        "21_30": range(21, 31),
        "31_40": range(31, 41),
        "41_50": range(41, 51),
        "51_60": range(51, 61),
        "61_70": range(61, 71),
        "71_80": range(71, 81),
    }
    son_5_uzunluk = min(5, len(df))
    son_20_uzunluk = min(20, len(df))
    rapor = []
    for ad, aralik in bloklar.items():
        son_5 = df.head(son_5_uzunluk)[sayi_kolonlari].isin(aralik).sum().sum() / son_5_uzunluk
        son_20 = df.head(son_20_uzunluk)[sayi_kolonlari].isin(aralik).sum().sum() / son_20_uzunluk
        durum = "🔥 YOĞUN" if son_5 > 2.8 else ("❄️ KURAK (Aday)" if son_5 < 2.1 else "⚖️ DENGELİ")
        rapor.append({
            "Grup": ad,
            "Son 5 Tur Ort": round(son_5, 2),
            "Son 20 Tur Ort": round(son_20, 2),
            "Mevcut Durum": durum,
        })
    return pd.DataFrame(rapor)


def son_basamak_analizi(df, sayi_kolonlari):
    son_5_uzunluk = min(5, len(df))
    son_20_uzunluk = min(20, len(df))
    rapor = []
    for basamak in range(10):
        sayilar = [x for x in range(1, 81) if x % 10 == basamak]
        son_5 = df.head(son_5_uzunluk)[sayi_kolonlari].isin(sayilar).sum().sum() / son_5_uzunluk
        son_20 = df.head(son_20_uzunluk)[sayi_kolonlari].isin(sayilar).sum().sum() / son_20_uzunluk
        rapor.append({
            "Son Basamak": f"Sonu {basamak} Olanlar",
            "Son 5 Ort": round(son_5, 2),
            "Son 20 Ort": round(son_20, 2),
            "İvme": "📈 Yükselişte" if son_5 > son_20 else "📉 Düşüşte",
        })
    return pd.DataFrame(rapor).sort_values(by="Son 5 Ort", ascending=False)


def kombinasyon_ozeti(df, sayi_kolonlari, ufuk=150):
    cekilisler = df.head(min(ufuk, len(df)))[sayi_kolonlari].values.astype(int)
    rapor = []
    for boyut in KOMBINASYON_BOYUTLARI:
        sayac = Counter()
        for row in cekilisler:
            sayac.update(itertools.combinations(sorted(row), boyut))
        rapor.append({
            "Grup Tipi": f"{boyut}'lı Ortak Gruplar",
            "En Az 1 Kez Çıkan (Benzersiz)": len(sayac),
            "En Az 2 Kez Çıkan (Tekrarlayan)": sum(adet >= 2 for adet in sayac.values()),
            "En Az 3 Kez Çıkan": sum(adet >= 3 for adet in sayac.values()),
            "Maksimum Tekrar": max(sayac.values(), default=0),
        })
    return pd.DataFrame(rapor)


def ikili_frekans_farki(df, sayi_kolonlari, kisa_ufuk=15, uzun_ufuk=150, minimum_hit=4, limit=15):
    def ikili_sayaci(data_slice):
        sayac = Counter()
        for _, row in data_slice[sayi_kolonlari].iterrows():
            sayac.update(itertools.combinations(sorted(row.values.astype(int)), 2))
        return sayac

    kisa_uzunluk = min(kisa_ufuk, len(df))
    uzun_uzunluk = min(uzun_ufuk, len(df))
    uzun_sayac = ikili_sayaci(df.head(uzun_uzunluk))
    kisa_sayac = ikili_sayaci(df.head(kisa_uzunluk))
    rapor = []
    for ikili, toplam_hit in uzun_sayac.items():
        if toplam_hit < minimum_hit:
            continue
        kisa_oran = kisa_sayac.get(ikili, 0) / kisa_uzunluk
        uzun_oran = toplam_hit / uzun_uzunluk
        rapor.append({
            "Grup": f"[{ikili[0]} - {ikili[1]}]",
            "Son 15 Ort": round(kisa_oran, 3),
            "Son 150 Ort": round(uzun_oran, 3),
            "Frekans_Farki": round(kisa_oran - uzun_oran, 4),
            "Toplam_Hit": toplam_hit,
        })
    kolonlar = ["Grup", "Son 15 Ort", "Son 150 Ort", "Frekans_Farki", "Toplam_Hit"]
    return pd.DataFrame(rapor, columns=kolonlar).sort_values(
        by="Frekans_Farki", ascending=False
    ).head(limit)
