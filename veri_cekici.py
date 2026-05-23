import time
import pandas as pd
import os
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
    print("🎯 MOTOR 1: Optimize edilmiş API bağlantısı deneniyor...")
    # Sunucunun şişmesini engellemek için ?size=30 parametresini ekledik
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
    cekilisler = data.get("data") or data.get("results") or (data if isinstance(data, list) else [])
    
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
    print("🚀 MOTOR 2: API tıkandı! Anti-Bot Korumalı Özel Selenium Devreye Giriyor...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,1200")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    # Gelişmiş Anti-Detection (GitHub bot izlerini tamamen silen ayarlar)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Sitenin koruma kalkanını (navigator.webdriver) devre dışı bırakma hilesi
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    try:
        driver.get("https://www.millipiyangoonline.com/hizli-on-numara/sonuclar")
        time.sleep(12)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(3)
        
        mevcut_cekilisler = mevcut_cekilisleri_oku()
        satirlar = driver.find_elements(By.XPATH, "//*[contains(@class, 'draw') or contains(@class, 'row') or contains(@class, 'item')]")
        
        yeni_eklenen_ler = []
        islenen_cekilisler = set()
        
        for satir in satirlar:
            try:
                metin = satir.text
                if not metin or "no" not in metin.lower(): continue
                
                c_no = ""
                for s in metin.split("\n"):
                    if "no" in s.lower() or "çekiliş" in s.lower():
                        c_no = "".join(filter(str.isdigit, s))
                        if c_no: break
                        
                if not c_no or c_no in mevcut_cekilisler or c_no in islenen_cekilisler: continue
                
                toplar = satir.find_elements(By.XPATH, ".//*[contains(@class, 'ball') or contains(@class, 'number')]")
                gecici_sayilar = []
                for top in toplar:
                    top_metni = top.text.strip()
                    if top_metni.isdigit() and 1 <= int(top_metni) <= 80:
                        val = int(top_metni)
                        if val not in gecici_sayilar: gecici_sayilar.append(val)
                        
                if len(gecici_sayilar) == 20:
                    gecici_sayilar.sort()
                    satir_verisi = {"Tarih": time.strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                    for i, s in enumerate(gecici_sayilar, start=1):
                        satir_verisi[f"Sayi_{i}"] = s
                    yeni_eklenen_ler.append(satir_verisi)
                    islenen_cekilisler.add(c_no)
                    print(f"✨ Gizli Web Tarayıcıdan Çekiliş Yakalandı: {c_no}")
            except: continue
            
        veri_tabanina_kaydet(yeni_eklenen_ler)
        driver.quit()
    except Exception as e:
        print(f"❌ Motor 2 de başarısız oldu: {e}")
        driver.quit()


def canli_cekilis_takip_et():
    try:
        # Önce hafif ve hızlı olan sınırlandırılmış API yöntemini dene
        motor_1_api()
    except Exception as api_hatasi:
        print(f"⚠️ Motor 1 (API) engellendi veya zaman aşımına uğradı: {api_hatasi}")
        # API çökerse veya Cloudflare'e takılırsa kurşun geçirmez Selenium'u devreye al
        try:
            motor_2_stealth_selenium()
        except Exception as sel_hatasi:
            print(f"❌ Kritik Hata: İki motor da site korumasını geçemedi! {sel_hatasi}")

if __name__ == "__main__":
    canli_cekilis_takip_et()
