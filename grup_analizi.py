import pandas as pd
import os

from analiz_motoru import (
    blok_analizi,
    ikili_frekans_farki,
    kombinasyon_ozeti,
    son_basamak_analizi,
)
from veri_modeli import (
    SAYI_KOLONLARI,
    cekilisleri_sirala,
    veri_cercevesini_dogrula,
    veri_cercevesini_normalize_et,
)

CSV_DOSYASI = "hizli_on_numara.csv"
RAPOR_MD = "grup_raporu.md"
RAPOR_CSV = "grup_analizi.csv"


def ilk_dolu_deger(satir, kolonlar, varsayilan="Bilinmiyor"):
    for kolon in kolonlar:
        deger = satir.get(kolon)
        if pd.notna(deger) and str(deger).strip():
            return str(deger)
    return varsayilan


def grup_analizini_calistir():
    if not os.path.exists(CSV_DOSYASI):
        print("⚠️ Ham veri dosyası bulunamadı!")
        return

    df = pd.read_csv(CSV_DOSYASI, dtype={"CekilisNo": str})
    df = veri_cercevesini_normalize_et(df)
    veri_cercevesini_dogrula(df)
    df = cekilisleri_sirala(df)
    sayi_kolonlari = SAYI_KOLONLARI
    
    if len(df) < 5:
        print("⚠️ Yetersiz veri!")
        return

    # En taze çekiliş bilgileri
    son_cekilis_no = df.iloc[0]['CekilisNo']
    son_cekilis_tarih = ilk_dolu_deger(df.iloc[0], ["CekilisTarihi"])
    if son_cekilis_tarih == "Bilinmiyor":
        son_cekilis_tarih = ilk_dolu_deger(df.iloc[0], ["ToplanmaTarihi"])
        zaman_etiketi = "CSV'deki Son Toplanma Zamanı"
    else:
        zaman_etiketi = "Son Çekiliş Zamanı"

    df_blok = blok_analizi(df, sayi_kolonlari)
    df_basamak = son_basamak_analizi(df, sayi_kolonlari)
    df_k_summary = kombinasyon_ozeti(df, sayi_kolonlari)
    df_cete_macd = ikili_frekans_farki(df, sayi_kolonlari)

    # --- CSV OLARAK YEDEKLE ---
    df_blok.to_csv(RAPOR_CSV, index=False)
    
    # --- GITHUB MARKDOWN RAPORU OLUŞTURMA ---
    md_content = f"""# 📊 Hızlı On Numara Grup Raporu
> **{zaman_etiketi}:** {son_cekilis_tarih}
> **Analiz Edilen Son Çekiliş No:** `{son_cekilis_no}`

---

### 🧱 1. Onluk Blok Dağılım Matrisi
| Onluk Bölge | Son 5 Tur Ortalaması | Son 20 Tur Ortalaması | Durum |
| :--- | :---: | :---: | :--- |
"""
    for _, r in df_blok.iterrows():
        md_content += f"| **{r['Grup']}** | {r['Son 5 Tur Ort']} | {r['Son 20 Tur Ort']} | {r['Mevcut Durum']} |\n"

    md_content += """
---

### 🔢 2. Son Basamak (Ending Digits) Grup Kümelenmesi
| Sayı Grubu Kökü | Son 5 Tur Ort | Son 20 Tur Ort | Trend İvmesi |
| :--- | :---: | :---: | :--- |
"""
    for _, r in df_basamak.iterrows():
        md_content += f"| {r['Son Basamak']} | {r['Son 5 Ort']} | {r['Son 20 Ort']} | {r['İvme']} |\n"

    md_content += """
---

### 📐 3. İkili-Beşli Kombinasyon Kümelenmesi (Son 150 Çekiliş)
*Sayı gruplarının detayına inmeden önce, çekilen 20 sayı içinden kaçarlı ortak grupların doğduğunu ve bunların tekrarlanma istatistiklerini veren makro tablodur.*

| Ortaklık Tipi | En Az 1 Kez Çıkan (Benzersiz) | En Az 2 Kez Çıkan (Tekrarlayan) | En Az 3 Kez Çıkan | Tarihsel En Yüksek Tekrar |
| :--- | :---: | :---: | :---: | :---: |
"""
    for _, r in df_k_summary.iterrows():
        md_content += f"| **{r['Grup Tipi']}** | {r['En Az 1 Kez Çıkan (Benzersiz)']} | {r['En Az 2 Kez Çıkan (Tekrarlayan)']} | {r['En Az 3 Kez Çıkan']} | **{r['Maksimum Tekrar']} Kez** |\n"

    md_content += """
---

### 🕸 4. İkili Sayı Grupları Kısa-Uzun Dönem Frekans Farkı
| İkili Sayı Grubu | Son 15 Tur Ort (Kısa) | Son 150 Tur Ort (Uzun) | Frekans Farkı | Toplam Beraber Çıkma |
| :--- | :---: | :---: | :---: | :---: |
"""
    for _, r in df_cete_macd.iterrows():
        emoji = "📈 Yüksek Pozitif" if r['Frekans_Farki'] > 0.05 else ("↗️ Pozitif" if r['Frekans_Farki'] > 0 else "↘️ Negatif")
        md_content += f"| `{r['Grup']}` | {r['Son 15 Ort']} | {r['Son 150 Ort']} | **{r['Frekans_Farki']}** ({emoji}) | {r['Toplam_Hit']} Kez |\n"

    md_content += "\n\n_Bu rapor zamanlanmış GitHub Actions işi tarafından güncellenir; çalışma zamanı kesin değildir._"

    with open(RAPOR_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print("🚀 Kombinasyon matrisi entegreli yeni GitHub Raporu başarıyla basıldı!")

if __name__ == "__main__":
    grup_analizini_calistir()
