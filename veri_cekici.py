import time
import pandas as pd
import os
import requests

CSV_DOSYASI = "hizli_on_numara.csv"

def canli_cekilis_takip_et():
    print("🚀 GITHUB BULUT BOTU PROFESYONEL API MODUNDA ATEŞLENDİ!")
    
    # Zaman aşımını engellemek için doğrudan tarih bazlı en kararlı ana API ucunu hedefliyoruz
    API_URL = "https://www.millipiyangoonline.com/api/v1/games/results/hizli-on-numara"
    
    # Sunucuyu ikna etmek için tam donanımlı tarayıcı kimliği (Headers)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.millipiyangoonline.com",
        "Referer": "https://www.millipiyangoonline.com/hizli-on-numara/sonuclar",
        "Connection": "keep-alive"
    }
    
    try:
        # Oturum hafızası oluşturarak çerezleri ve bağlantıyı canlı tutuyoruz
        session = requests.Session()
        session.headers.update(headers)
        
        print("⏳ Milli Piyango sunucusundan veriler güvenli modda talep ediliyor (Sabırla Bekleniyor)...")
        
        # Timeout süresini 30 saniyeye çıkartarak sunucuya nefes alma alanı tanıyoruz
        response = session.get(API_URL, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Sunucu cevap vermedi, Durum Kodu: {response.status_code}")
            return
            
        data = response.json()
        
        # Farklı API mimarilerine karşı esnek veri yakalama hazneleri
        cekilisler = []
        if isinstance(data, dict):
            cekilisler = data.get("data") or data.get("results") or data.get("draws") or []
        elif isinstance(data, list):
            cekilisler = data

        if not cekilisler:
            print("⚠️ Siteden dönen çekiliş listesi boş. Format değişmiş olabilir.")
            return
            
        mevcut_cekilisler = set()
        if os.path.exists(CSV_DOSYASI):
            try:
                eski_df = pd.read_csv(CSV_DOSYASI)
                if "CekilisNo" in eski_df.columns:
                    mevcut_cekilisler = set(eski_df["CekilisNo"].astype(str).tolist())
            except: pass

        yeni_eklenen_ler = []
        
        for c in cekilisler:
            try:
                # Çekiliş ID'sini kazıma
                c_no = str(c.get("drawId") or c.get("id") or c.get("cekilisNo") or "")
                if not c_no or c_no in mevcut_cekilisler: continue
                
                # Sayı bloklarını ayıklama
                toplar = c.get("numbers") or c.get("result") or c.get("kazananSayilar") or c.get("items")
                if not toplar or not isinstance(toplar, list): continue
                
                gecici_sayilar = [int(n) for n in toplar if str(n).isdigit() and 1 <= int(n) <= 80]
                
                if len(gecici_sayilar) == 20:
                    gecici_sayilar.sort()
                    satir_verisi = {"Tarih": time.strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                    for i, s in enumerate(gecici_sayilar, start=1):
                        satir_verisi[f"Sayi_{i}"] = s
                    yeni_eklenen_ler.append(satir_verisi)
                    print(f"✨ API'den Çekiliş Başarıyla Süzüldü: {c_no}")
            except: continue
            
        # --- VERİ TABANINI KAYDETME VE BİRLEŞTİRME ---
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
            print(f"💾 CSV API Sayesinde Güncellendi! Toplam satır sayısı: {len(toplam_df)}")
        else:
            print("💤 Havuzda olmayan yeni veya farklı bir çekiliş bulunamadı.")
            
    except Exception as e:
        print(f"❌ API Bağlantı Hatası: {e}")

if __name__ == "__main__":
    canli_cekilis_takip_et()
