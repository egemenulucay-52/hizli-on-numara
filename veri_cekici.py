import time
import pandas as pd
import os
import requests

CSV_DOSYASI = "hizli_on_numara.csv"

def canli_cekilis_takip_et():
    print("🚀 GITHUB BULUT BOTU API MODUNDA ATEŞLENDİ!")
    
    # Sitenin arkada verileri çekmek için kullandığı resmi, gizli API adresi
    API_URL = "https://www.millipiyangoonline.com/api/v1/games/results/hizli-on-numara"
    
    # Sitenin bizi bot olarak algılamaması için tarayıcı süsü (Header) veriyoruz
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.millipiyangoonline.com",
        "Referer": "https://www.millipiyangoonline.com/hizli-on-numara/sonuclar"
    }
    
    try:
        # Doğrudan sitenin veri tabanı linkine istek atıyoruz
        response = requests.get(API_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Siteye bağlanılamadı, Durum Kodu: {response.status_code}")
            return
            
        data = response.json()
        
        # Eğer API'den boş veri döndüyse alternatif alt kırılımı dene
        if "data" in data:
            cekilisler = data["data"]
        elif "results" in data:
            cekilisler = data["results"]
        else:
            cekilisler = data if isinstance(data, list) else []
            
        if not cekilisler:
            print("⚠️ Siteden çekiliş listesi boş döndü veya yapı değişti.")
            return
            
        mevcut_cekilisler = set()
        if os.path.exists(CSV_DOSYASI):
            try:
                eski_df = pd.read_csv(CSV_DOSYASI)
                if "CekilisNo" in eski_df.columns:
                    mevcut_cekilisler = set(eski_df["CekilisNo"].astype(str).tolist())
            except: pass

        yeni_eklenen_ler = []
        
        # Siteden gelen her bir çekiliş verisini döngüye alıyoruz
        for c in cekilisler:
            try:
                # API verisindeki çekiliş numarası ve şanslı sayıların yerini buluyoruz
                c_no = str(c.get("drawId") or c.get("id") or c.get("cekilisNo") or "")
                if not c_no or c_no in mevcut_cekilisler: continue
                
                # Sayıları ayıklama
                toplar = c.get("numbers") or c.get("result") or c.get("kazananSayilar")
                if not toplar or not isinstance(toplar, list): continue
                
                # Sadece 1-80 arasındaki geçerli sayıları filtrele
                gecici_sayilar = [int(n) for n in toplar if str(n).isdigit() and 1 <= int(n) <= 80]
                
                # 20 sayı tamam ise veri tabanına hazırla
                if len(gecici_sayilar) == 20:
                    gecici_sayilar.sort()
                    satir_verisi = {"Tarih": time.strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                    for i, s in enumerate(gecici_sayilar, start=1):
                        satir_verisi[f"Sayi_{i}"] = s
                    yeni_eklenen_ler.append(satir_verisi)
                    print(f"✨ API'den Yeni Çekiliş Yakalandı: {c_no}")
            except: continue
            
        # --- VERİ TABANINI GÜNCELLEME VE KAYDETME ---
        if yeni_eklenen_ler:
            yeni_df = pd.DataFrame(yeni_eklenen_ler)
            if os.path.exists(CSV_DOSYASI):
                eski_df = pd.read_csv(CSV_DOSYASI)
                toplam_df = pd.concat([eski_df, yeni_df], ignore_index=True)
            else:
                toplam_df = yeni_df
                
            toplam_df["CekilisNo"] = toplam_df["CekilisNo"].astype(str)
            toplam_df = toplam_df.drop_duplicates(subset=["CekilisNo"]).sort_values(by="CekilisNo", ascending=False)
            toplam_df.to_csv(CSV_DOSYASI, index=False, encoding='utf-8')
            print(f"💾 CSV API Verileriyle Güncellendi! Toplam satır sayısı: {len(toplam_df)}")
        else:
            print("💤 Havuzda olmayan yeni bir çekiliş verisi bulunamadı.")
            
    except Exception as e:
        print(f"❌ API Hatası: {e}")

if __name__ == "__main__":
    canli_cekilis_takip_et()
