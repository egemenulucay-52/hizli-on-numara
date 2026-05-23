import time
import pandas as pd
import os
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

CSV_DOSYASI = "hizli_on_numara.csv"

def mevcut_cekilisleri_oku():
    mevcut = set()
    if os.path.exists(CSV_DOSYASI):
        try:
            eski_df = pd.read_csv(CSV_DOSYASI)
            if "CekilisNo" in eski_df.columns:
                mevcut = set(eski_df["CekilisNo"].astype(str).tolist())
        except: pass
    return mevcut

def veri_tabanina_kaydet(yeni_eklenen_ler):
    if not yeni_eklenen_ler:
        print("💤 Havuzda olmayan yeni veya farklı bir çekiliş bulunamadı.")
        return
        
    yeni_df = pd.DataFrame(yeni_eklenen_ler)
    if os.path.exists(CSV_DOSYASI):
        eski_df = pd.read_csv(CSV_DOSYASI)
        toplam_df = pd.concat([eski_df, yeni_df], ignore_index=True)
    else:
        toplam_df = yeni_df
        
    toplam_df["CekilisNo"] = toplam_df["CekilisNo"].astype(str)
    toplam_df = toplam_df.drop_duplicates(subset=["CekilisNo"]).sort_values(by="CekilisNo", ascending=False)
    toplam_df.to_csv(CSV_DOSYASI, index=False, encoding='utf-8')
    print(f"💾 CSV Başarıyla Güncellendi! Toplam satır sayısı: {len(toplam_df)}")


def motor_1_api():
    print("🎯 MOTOR 1: Sınırlandırılmış API bağlantısı deneniyor...")
    API_URL = "https://www.millipiyangoonline.com/api/v1/games/results/hizli-on-numara?size=30"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.millipiyangoonline.com",
        "Referer": "https://www.millipiyangoonline.com/hizli-on-numara/sonuclar"
    }
    
    response = requests.get(API_URL, headers=headers, timeout=12)
    if response.status_code != 200:
        raise Exception(f"Sunucu durum kodu: {response.status_code}")
        
    data = response.json()
    cekilisler = data.get("data") or data.get("results") or []
    
    mevcut_cekilisler = mevcut_cekilisleri_oku()
    yeni_eklenen_ler = []
    
    for c in cekilisler:
        try:
            c_no = str(c.get("drawId") or c.get("id") or c.get("cekilisNo") or "")
            if not c_no or c_no in mevcut_cekilisler: continue
            
            toplar = c.get("numbers") or c.get("result") or c.get("kazananSayilar")
            if not toplar or not isinstance(toplar, list): continue
            
            gecici_sayilar = [int(n) for n in toplar if str(n).isdigit() and 1 <= int(n) <= 80]
            if len(gecici_sayilar) == 20:
                gecici_sayilar.sort()
                satir_verisi = {"Tarih": time.strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                for i, s in enumerate(gecici_sayilar, start=1):
                    satir_verisi[f"Sayi_{i}"] = s
                yeni_eklenen_ler.append(satir_verisi)
                print(f"✨ API'den Çekiliş Süzüldü: {c_no}")
        except: continue
        
    veri_tabanina_kaydet(yeni_eklenen_ler)


def motor_2_stealth_selenium():
    print("🚀 MOTOR 2: Akıllı Görsel Saf Metin Tarayıcı Başlatılıyor...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,1600")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    try:
        driver.get("https://www.millipiyangoonline.com/hizli-on-numara/sonuclar")
        time.sleep(12)
        
        # Sayfayı kaydırıp içeriğin tam yüklenmesini sağlıyoruz
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(3)
        
        # Sayfadaki tüm ham yazıyı tek parça halinde çekiyoruz
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        print("\n--- 📄 CANLI SAYFA METNİ ÖRNEĞİ (İLK 1000 KARAKTER) ---")
        print(body_text[:1000])
        print("-----------------------------------------------------\n")
        
        mevcut_cekilisler = mevcut_cekilisleri_oku()
        yeni_eklenen_ler = []
        
        # Metni 2026 ile başlayan çekiliş numaralarına göre dilimliyoruz
        segments = re.split(r'\b(2026\d{7,12})\b', body_text)
        
        if len(segments) > 1:
            print(f"🔮 Sayfa metninde {len(segments)//2} adet potansiyel çekiliş bloku izole edildi.")
            for i in range(1, len(segments), 2):
                c_no = segments[i]
                post_text = segments[i+1] # Çekiliş numarasından sonra gelen metin alanı (tarih ve toplar)
                
                if c_no in mevcut_cekilisler: continue
                
                # Metin bloğu içindeki tüm 1-2 basamaklı şanslı sayı adaylarını topluyoruz
                aday_sayilar = [int(n) for n in re.findall(r'\b\d{1,2}\b', post_text) if 1 <= int(n) <= 80]
                
                # Eğer blokta en az 20 sayı varsa, tarih verilerinden sıyrılmak için en sondaki 20 sayıyı (topları) alıyoruz
                if len(aday_sayilar) >= 20:
                    sansli_toplar = aday_sayilar[-20:]
                    sansli_toplar.sort()
                    
                    satir_verisi = {"Tarih": time.strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                    for idx, s in enumerate(sansli_toplar, start=1):
                        satir_verisi[f"Sayi_{idx}"] = s
                        
                    yeni_eklenen_ler.append(satir_verisi)
                    print(f"✨ Saf Metin Analiziyle Çekiliş Kilidi Kırıldı: {c_no}")
        
        veri_tabanina_kaydet(yeni_eklenen_ler)
        driver.quit()
    except Exception as e:
        print(f"❌ Motor 2 Hatası: {e}")
        driver.quit()


def canli_cekilis_takip_et():
    try:
        motor_1_api()
    except Exception as api_hatasi:
        print(f"⚠️ Motor 1 (API) pas geçildi, hibrit moda aktarılıyor...")
        try:
            motor_2_stealth_selenium()
        except Exception as sel_hatasi:
            print(f"❌ Kritik Hata: İki motor da başarısız! {sel_hatasi}")

if __name__ == "__main__":
    canli_cekilis_takip_et()
