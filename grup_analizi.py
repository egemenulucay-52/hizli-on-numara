import pandas as pd
import numpy as np
import os
from datetime import datetime

CSV_DOSYASI = "hizli_on_numara.csv"
RAPOR_MD = "grup_raporu.md"
RAPOR_CSV = "grup_analizi.csv"

def grup_analizini_calistir():
    if not os.path.exists(CSV_DOSYASI):
        print("⚠️ Ham veri dosyası bulunamadı!")
        return

    df = pd.read_csv(CSV_DOSYASI)
    sayi_kolonlari = [f"Sayi_{i}" for i in range(1, 21)]
    
    if len(df) < 5:
        print("⚠️ Yetersiz veri!")
        return

    # En taze çekiliş bilgileri
    son_cekilis_no = df.iloc[0]['CekilisNo']
    son_cekilis_tarih = df.iloc[0].get('Tarih', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # --- 1. MODELLER: ONLUK BLOK GRUPLARI ---
    bloklar = {
        "Grup_1_10": range(1, 11), "Grup_11_20": range(11, 21),
        "Grup_21_30": range(21, 31), "Grup_31_40": range(31, 41),
        "Grup_41_50": range(41, 51), "Grup_51_60": range(51, 61),
        "Grup_61_70": range(61, 71), "Grup_71_80": range(71, 81)
    }
    
    blok_rapor = []
    for ad, aralik in bloklar.items():
        s5_adet = df.head(5)[sayi_kolonlari].isin(aralik).sum().sum() / 5
        s20_adet = df.head(20)[sayi_kolonlari].isin(aralik).sum().sum() / 20
        durum = "🔥 YOĞUN" if s5_adet > 2.8 else ("❄️ KURAK (Aday)" if s5_adet < 2.1 else "⚖️ DENGELİ")
        blok_rapor.append({"Grup": ad.replace("Grup_", ""), "Son 5 Tur Ort": round(s5_adet, 2), "Son 20 Tur Ort": round(s20_adet, 2), "Mevcut Durum": durum})
    df_blok = pd.DataFrame(blok_rapor)

    # --- 2. MODEL: SON BASAMAK GRUPLARI ---
    basamak_rapor = []
    for b in range(10):
        grup_sayilari = [x for x in range(1, 81) if x % 10 == b]
        s5_b_adet = df.head(5)[sayi_kolonlari].isin(grup_sayilari).sum().sum() / 5
        s20_b_adet = df.head(20)[sayi_kolonlari].isin(grup_sayilari).sum().sum() / 20
        ivme = "📈 Yükselişte" if s5_b_adet > s20_b_adet else "📉 Düşüşte"
        basamak_rapor.append({"Son Basamak": f"Sonu {b} Olanlar", "Son 5 Ort": round(s5_b_adet, 2), "Son 20 Ort": round(s20_b_adet, 2), "İvme": ivme})
    df_basamak = pd.DataFrame(basamak_rapor).sort_values(by="Son 5 Ort", ascending=False)

    # --- 3. MODEL: İKİLİ ÇETELER VE GRUP MACD MOMENTUM HESABI (YENİ SİLAH) ---
    # Potansiyel güçlü adayları belirlemek için önce geniş kapsamlı (son 150 tur) çift haritası çıkarıyoruz
    df_len = len(df)
    short_horizon = min(15, df_len)
    long_horizon = min(150, df_len)
    
    def cete_frekansi_hesapla(data_slice):
        counts = {}
        for _, row in data_slice[sayi_kolonlari].iterrows():
            nums = sorted(row.values.astype(int))
            for idx, i in enumerate(nums):
                for j in nums[idx+1:]:
                    counts[(i, j)] = counts.get((i, j), 0) + 1
        return counts

    counts_total = cete_frekansi_hesapla(df.head(long_horizon))
    counts_short = cete_frekansi_hesapla(df.head(short_horizon))
    
    # En az 4 kez beraber çıkmış popüler ikilileri süzüyoruz ki gürültü (noise) elensin
    populer_ikililer = [pair for pair, count in counts_total.items() if count >= 4]
    
    cete_macd_rapor = []
    for pair in populer_ikililer:
        # Kısa ve uzun vadeli normalize edilmiş frekanslar
        f_short = counts_short.get(pair, 0) / short_horizon
        f_long = counts_total.get(pair, 0) / long_horizon
        
        grup_macd = f_short - f_long
        toplam_birliktelik = counts_total.get(pair, 0)
        
        cete_macd_rapor.append({
            "Grup": f"[{pair[0]} - {pair[1]}]",
            "Son 15 Ort": round(f_short, 3),
            "Son 150 Ort": round(f_long, 3),
            "Grup_MACD": round(grup_macd, 4),
            "Toplam_Hit": toplam_birliktelik
        })
        
    df_cete_macd = pd.DataFrame(cete_macd_rapor).sort_values(by="Grup_MACD", ascending=False).head(15)

    # --- CSV OLARAK YEDEKLE ---
    df_blok.to_csv(RAPOR_CSV, index=False)
    
    # --- GITHUB MARKDOWN RAPORU OLUŞTURMA ---
    md_content = f"""# 📊 Hızlı On Numara Kuantum Grup Raporu
> **Son Güncellenme:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (TR)  
> **Analiz Edilen Son Çekiliş No:** `{son_cekilis_no}` | **Tarih:** `{son_cekilis_tarih}`

---

### 🧱 1. Onluk Blok Dağılım Matrisi
*Teorik Denge Sınırı: Tur başına **2.50** adettir. Kurak olan bloklar patlamaya en yakın alanlardır.*

| Onluk Bölge | Son 5 Tur Ortalaması | Son 20 Tur Ortalaması | Kuantum Durum |
| :--- | :---: | :---: | :--- |
"""
    for _, r in df_blok.iterrows():
        md_content += f"| **{r['Grup']}** | {r['Son 5 Tur Ort']} | {r['Son 20 Tur Ort']} | {r['Mevcut Durum']} |\n"

    md_content += """
---

### 🔢 2. Son Basamak (Ending Digits) Grup Kümelenmesi
*Sayıların son hanelerine göre çekilme yoğunluğu (En popülerden en uyuza doğru sıralı).*

| Sayı Grubu Kökü | Son 5 Tur Ort | Son 20 Tur Ort | Trend İvmesi |
| :--- | :---: | :---: | :--- |
"""
    for _, r in df_basamak.iterrows():
        md_content += f"| {r['Son Basamak']} | {r['Son 5 Ort']} | {r['Son 20 Ort']} | {r['İvme']} |\n"

    md_content += """
---

### 🕸️ 3. İkili Sayı Grupları (Çeteler) Kombinasyonel MACD İvme Tablosu
*Sayı gruplarının kısa vadeli (15 tur) momentumu ile makro (150 tur) trendi arasındaki farktır. Skoru **en yüksek** olan gruplar eş zamanlı yükseliş ivmesindedir ve rötara karşı en dayanıklı ortak takımlardır.*

| İkili Sayı Grubu | Son 15 Tur Ort (Kısa) | Son 150 Tur Ort (Uzun) | Grup MACD Skoru | Toplam Beraber Çıkma |
| :--- | :---: | :---: | :---: | :---: |
"""
    for _, r in df_cete_macd.iterrows():
        # Skorun gücüne göre görsel emoji desteği ekledik
        emoji = "🚀 Şiddetli" if r['Grup_MACD'] > 0.05 else ("📈 Pozitif" if r['Grup_MACD'] > 0 else "📉 Zayıf")
        md_content += f"| `{r['Grup']}` | {r['Son 15 Ort']} | {r['Son 150 Ort']} | **{r['Grup_MACD']}** ({emoji}) | {r['Toplam_Hit']} Kez |\n"

    md_content += "\n\n_Bu rapor otonom işçi tarafından her 10 dakikada bir sıfır gecikmeyle üretilir._"

    with open(RAPOR_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print("🚀 Grup MACD entegreli GitHub Raporu başarıyla basıldı!")

if __name__ == "__main__":
    grup_analizini_calistir()
