import pandas as pd


SAYI_KOLONLARI = [f"Sayi_{i}" for i in range(1, 21)]
ZAMAN_KOLONLARI = ["CekilisTarihi", "ToplanmaTarihi"]


def veri_cercevesini_normalize_et(df):
    sonuc = df.copy()
    if "ToplanmaTarihi" not in sonuc.columns and "Tarih" in sonuc.columns:
        sonuc = sonuc.rename(columns={"Tarih": "ToplanmaTarihi"})
    if "CekilisTarihi" not in sonuc.columns:
        sonuc["CekilisTarihi"] = pd.NA
    if "ToplanmaTarihi" not in sonuc.columns:
        sonuc["ToplanmaTarihi"] = pd.NA

    ana_kolonlar = [*ZAMAN_KOLONLARI, "CekilisNo", *SAYI_KOLONLARI]
    kalan_kolonlar = [kolon for kolon in sonuc.columns if kolon not in ana_kolonlar]
    return sonuc[ana_kolonlar + kalan_kolonlar]


def veri_cercevesini_dogrula(df):
    gerekli_kolonlar = {"CekilisNo", *SAYI_KOLONLARI}
    eksik_kolonlar = gerekli_kolonlar - set(df.columns)
    if eksik_kolonlar:
        raise ValueError(f"Eksik CSV kolonları: {sorted(eksik_kolonlar)}")

    sayilar = df[SAYI_KOLONLARI].apply(pd.to_numeric, errors="raise")
    if not sayilar.apply(lambda row: row.between(1, 80).all(), axis=1).all():
        raise ValueError("CSV içinde 1-80 aralığı dışında sayı var.")
    if not sayilar.nunique(axis=1).eq(20).all():
        raise ValueError("Her çekilişte 20 benzersiz sayı bulunmalıdır.")


def cekilisleri_sirala(df):
    sonuc = df.copy()
    sonuc["CekilisNo"] = sonuc["CekilisNo"].astype(str)
    sonuc["_standart_id"] = sonuc["CekilisNo"].str.fullmatch(r"\d{5,6}")
    sonuc["_sayisal_id"] = pd.to_numeric(sonuc["CekilisNo"], errors="coerce").fillna(-1)
    return sonuc.sort_values(
        by=["_standart_id", "_sayisal_id"], ascending=[False, False]
    ).drop(columns=["_standart_id", "_sayisal_id"]).reset_index(drop=True)
