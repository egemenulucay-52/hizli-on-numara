import time
import pandas as pd
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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
    print("🎯 MOTOR 1: Doğrudan bulut API bağlantısı deneniyor...")
    API_URL = "https://www.millipiyangoonline.com/api/v1/games/results/hizli-on-numara?size=30"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.millipiyangoonline.com",
        "Referer": "https://www.millipiyangoonline.com/hizli-on-numara/sonuclar"
    }
    
    response = requests.get(API_URL, headers=headers, timeout=10)
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
    print("🚀 MOTOR 2: Tarayıcı Tabanlı Doğrudan API Enjeksiyonu Başlatılıyor...")
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
        # Önce sayfaya gidip Cloudflare duvarını tarayıcı kimliğiyle tamamen eritiyoruz
        driver.get("https://www.millipiyangoonline.com/hizli-on-numara/sonuclar")
        print("⏳ Sitenin çerez oturumlarının oturması bekleniyor (15 Saniye)...")
        time.sleep(15)
        
        driver.set_script_timeout(20)
        
        # --- 💥 GİZLİ ENJEKSİYON KOMUTU ---
        # Tarayıcının içinden, hazır oturum kimlikleriyle arka kapı veri damarını vuruyoruz (Son 100 Çekiliş birden)
        script = """
        var callback = arguments[arguments.length - 1];
        fetch("https://www.millipiyangoonline.com/api/v1/games/results/hizli-on-numara?size=100")
            .then(response => response.json())
            .then(data => callback({success: true, json: data}))
            .catch(err => callback({success: false, error: err.toString()}));
        """
        
        print("⚡ Güvenli tarayıcı tüneli üzerinden canlı makro veri talep ediliyor...")
        sonuc = driver.execute_async_script(script)
        
        if not sonuc or not sonuc.get("success"):
            raise Exception(f"Tarayıcı içi veri enjeksiyonu başarısız: {sonuc.get('error') if sonuc else 'Bilinmeyen hata'}")
            
        data = sonuc.get("json")
        cekilisler = []
        if isinstance(data, dict):
            cekilisler = data.get("data") or data.get("results") or data.get("draws") or []
        elif isinstance(data, list):
            cekilisler = data
            
        print(f"🔮 Tarayıcı tünelinden {len(cekilisler)} adet ham çekiliş verisi başarıyla süzüldü!")
        
        mevcut_cekilisler = mevcut_cekilisleri_oku()
        yeni_eklenen_ler = []
        
        for c in cekilisler:
            try:
                c_no = str(c.get("drawId") or c.get("id") or c.get("cekilisNo") or "")
                if not c_no: continue
                
                print(f"🔍 Tünelden Gelen Çekiliş No: {c_no}")
                if c_no in mevcut_cekilisler: continue
                
                toplar = c.get("numbers") or c.get("result") or c.get("kazananSayilar")
                if not toplar or not isinstance(toplar, list): continue
                
                gecici_sayilar = [int(n) for n in toplar if str(n).isdigit() and 1 <= int(n) <= 80]
                if len(gecici_sayilar) == 20:
                    gecici_sayilar.sort()
                    satir_verisi = {"Tarih": time.strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                    for i, s in enumerate(gecici_sayilar, start=1):
                        satir_verisi[f"Sayi_{i}"] = s
                    yeni_eklenen_ler.append(satir_verisi)
                    print(f"✨ Enjeksiyon Moduyla Çekiliş Yakalandı: {c_no}")
            except: continue
            
        veri_tabanina_kaydet(yeni_eklenen_ler)
        driver.quit()
    except Exception as e:
        print(f"❌ Motor 2 Kritik Hatası: {e}")
        driver.quit()


def canli_cekilis_takip_et():
    try:
        motor_1_api()
    except Exception as api_hatasi:
        print(f"⚠️ Motor 1 (Bulut API) pas geçildi, hibrit enjeksiyon modu aktarılıyor...")
        try:
            motor_2_stealth_selenium()
        except Exception as sel_hatasi:
            print(f"❌ Kritik Hata: İki motor da başarısız! {sel_hatasi}")

if __name__ == "__main__":
    canli_cekilis_takip_et()
