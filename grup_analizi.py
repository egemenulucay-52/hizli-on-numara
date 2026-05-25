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
    
    # --- 1. MODELLER: ONLUK BLOK GRUPLARI (1-10, 11-20...) ---
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

    # --- 2. MODEL: SON BASAMAK GRUPLARI (Ending Digits) ---
    basamak_rapor = []
    for b in range(10):
        grup_sayilari = [x for x in range(1, 81) if x % 10 == b]
        s5_b_adet = df.head(5)[sayi_kolonlari].isin(grup_sayilari).sum().sum() / 5
        s20_b_adet = df.head(20)[sayi_kolonlari].isin(grup_sayilari).sum().sum() / 20
        ivme = "📈 Yükselişte" if s5_b_adet > s20_b_adet else "📉 Düşüşte"
        basamak_rapor.append({"Son Basamak": f"Sonu {b} Olanlar", "Son 5 Ort": round(s5_b_adet, 2), "Son 20 Ort": round(s20_b_adet, 2), "İvme": ivme})
    df_basamak = pd.DataFrame(basamak_rapor).sort_values(by="Son 5 Ort", ascending=False)

    # --- 3. MODEL: EN SIK BERABER ÇIKAN İKİLİ ÇETELER (Top 10 Pairs) ---
    pair_counts = {}
    for _, row in df.head(50)[sayi_kolonlari].iterrows():
        nums = sorted(row.values.astype(int))
        for idx, i in enumerate(nums):
            for j in nums[idx+1:]:
                pair = (i, j)
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
                
    top_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    cete_rapor = [{"İkili Sayı Grubu": f"[{p[0][0]} - {p[0][1]}]", "Son 50 Turda Beraber Çıkma": p[1]} for p in top_pairs]
    df_cete = pd.DataFrame(cete_rapor)

    # --- CSV OLARAK KAYDET ---
    df_blok.to_csv(RAPOR_CSV, index=False)
    
    # --- GITHUB MARKDOWN RAPORU ---
    md_content = f"""# 📊 Hızlı On Numara Kuantum Grup Raporu
> **Son Güncellenme:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (TR)  
> **Analiz Edilen Son Çekiliş No:** `{son_cekilis_no}` | **Tarih:** `{son_cekilis_tarih}`

---

### 🧱 1. Onluk Blok Dağılım Matrisi
*Teorik Denge Sınırı: Tur başına **2.50** adettir. Kurak olan bloklar geometrik olarak patlamaya en yakın alanlardır.*

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
    # Hataya sebep olan o tehlikeli parça buradan tamamen temizlendi:
    for _, r in df_basamak.iterrows():
        md_content += f"| {r['Son Basamak']} | {r['Son 5 Ort']} | {r['Son 20 Ort']} | {r['İvme']} |\n"

    md_content += """
---

### 🕸️ 3. Son 50 Çekilişin En Sadık İkili Sayı Grupları (Çeteler)
*Birbirini en çok tetikleyen ve slottan beraber ayrılmayan kilit mikroskobik kombinasyonlar.*

| İkili Sayı Grubu | Son 50 Turda Beraber Görülme Sıklığı |
| :--- | :---: |
"""
    for _, r in df_cete.iterrows():
        md_content += f"| `{r['İkili Sayı Grubu']}` | **{r['Son 50 Turda Beraber Çıkma']} Kez** |\n"

    md_content += "\n\n_Bu rapor otonom işçi tarafından her 10 dakikada bir sıfır gecikmeyle üretilir._"

    with open(RAPOR_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print("🚀 Dandirik ama ışık hızındaki GitHub Raporu başarıyla basıldı!")

if __name__ == "__main__":
    grup_analizini_calistir()
