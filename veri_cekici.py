import time
import pandas as pd
import os
import requests
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from veri_modeli import SAYI_KOLONLARI, cekilisleri_sirala, veri_cercevesini_dogrula

CSV_DOSYASI = "hizli_on_numara.csv"
ISTANBUL_SAAT_DILIMI = ZoneInfo("Europe/Istanbul")


def istanbul_zamani():
    return datetime.now(ISTANBUL_SAAT_DILIMI)


def mevcut_cekilisleri_oku():
    mevcut = set()
    if os.path.exists(CSV_DOSYASI):
        try:
            eski_df = pd.read_csv(CSV_DOSYASI)
            if "CekilisNo" in eski_df.columns:
                mevcut = set(eski_df["CekilisNo"].astype(str).tolist())
        except (OSError, ValueError, pd.errors.ParserError) as hata:
            print(f"⚠️ Mevcut CSV okunamadı: {hata}")
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
    toplam_df = toplam_df.drop_duplicates(subset=["CekilisNo"])
    toplam_df = cekilisleri_sirala(toplam_df)
    veri_cercevesini_dogrula(toplam_df)

    hedef_dizin = os.path.dirname(os.path.abspath(CSV_DOSYASI))
    gecici_fd, gecici_yol = tempfile.mkstemp(prefix="hizli_on_numara_", suffix=".csv", dir=hedef_dizin)
    os.close(gecici_fd)
    try:
        toplam_df.to_csv(gecici_yol, index=False, encoding="utf-8")
        os.replace(gecici_yol, CSV_DOSYASI)
    finally:
        if os.path.exists(gecici_yol):
            os.remove(gecici_yol)
    print(f"💾 CSV Başarıyla Güncellendi! Toplam satır sayısı: {len(toplam_df)}")


def motor_1_api():
    print("🎯 MOTOR 1: Sınırlandırılmış API bağlantısı deneniyor...")
    API_URL = "https://www.millipiyangoonline.com/api/v1/games/results/hizli-on-numara?size=30"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.millipiyangoonline.com",
        "Referer": "https://www.millipiyangoonline.com/hizli-on-numara/sonuclar"
    }
    
    response = requests.get(API_URL, headers=headers, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Sunucu durum kodu: {response.status_code}")
        
    data = response.json()
    cekilisler = data.get("data") or data.get("results")
    if isinstance(cekilisler, dict):
        cekilisler = cekilisler.get("content") or cekilisler.get("results")
    if not isinstance(cekilisler, list) or not cekilisler:
        raise ValueError("API geçerli ve boş olmayan bir çekiliş listesi döndürmedi.")
    
    mevcut_cekilisler = mevcut_cekilisleri_oku()
    yeni_eklenen_ler = []
    gecerli_cekilis_sayisi = 0
    
    for c in cekilisler:
        try:
            c_no = str(c.get("drawId") or c.get("id") or c.get("cekilisNo") or "")
            if not c_no:
                continue
            
            toplar = c.get("numbers") or c.get("result") or c.get("kazananSayilar")
            if not toplar or not isinstance(toplar, list): continue
            
            gecici_sayilar = [int(n) for n in toplar if str(n).isdigit() and 1 <= int(n) <= 80]
            if len(gecici_sayilar) == 20 and len(set(gecici_sayilar)) == 20:
                gecerli_cekilis_sayisi += 1
                if c_no in mevcut_cekilisler:
                    continue
                gecici_sayilar.sort()
                satir_verisi = {"Tarih": istanbul_zamani().strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                for i, s in enumerate(gecici_sayilar, start=1):
                    satir_verisi[f"Sayi_{i}"] = s
                yeni_eklenen_ler.append(satir_verisi)
                print(f"✨ API'den Çekiliş Süzüldü: {c_no}")
        except (TypeError, ValueError, AttributeError) as hata:
            print(f"⚠️ API kaydı çözümlenemedi: {hata}")

    if gecerli_cekilis_sayisi == 0:
        raise ValueError("API yanıtında doğrulanabilir 20 sayılı çekiliş bulunamadı.")
        
    veri_tabanina_kaydet(yeni_eklenen_ler)


def motor_2_stealth_selenium():
    print("🚀 MOTOR 2: Çift Dikiş Süpürme Motoru Başlatılıyor...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,1600")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "Europe/Istanbul"})
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    try:
        driver.get("https://www.millipiyangoonline.com/hizli-on-numara/sonuclar")
        time.sleep(12)
        
        # --- 🕒 ARALIK HESAPLAMA (Geçmiş ve Canlı Slot Ayarı) ---
        tr_saati = istanbul_zamani()
        current_hour = tr_saati.hour
        
        # 1. Şu anki canlı slot (Örn: 15:00-16:00)
        curr_slot = f"{current_hour:02d}:00–{(current_hour + 1) % 24:02d}:00"
        # 2. Bir önceki kaçan slot (Örn: 14:00-15:00)
        prev_slot = f"{(current_hour - 1) % 24:02d}:00–{current_hour:02d}:00"
        
        # Sızıntıları önlemek için önce geçmiş saati süpürüp sonra canlı saate geçiyoruz
        hedef_slotlar = [prev_slot, curr_slot]
        yeni_eklenen_ler = []
        mevcut_cekilisler = mevcut_cekilisleri_oku()
        
        for slot_hedef in hedef_slotlar:
            print(f"⏳ [{slot_hedef}] zaman dilimi taranıyor...")
            slot_bulundu = False
            elementler = driver.find_elements(By.XPATH, "//*[contains(text(), '–')]")
            
            for el in elementler:
                try:
                    txt = el.text.strip()
                    if slot_hedef in txt and el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                        time.sleep(1)
                        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));", el)
                        print(f"🎯 Slot Seçildi: {txt}")
                        slot_bulundu = True
                        break
                except Exception as element_hatasi:
                    print(f"⚠️ Saat aralığı öğesi işlenemedi: {element_hatasi}")
                
            if not slot_bulundu:
                print(f"⚠️ [{slot_hedef}] görünür durumda bulunamadı, es geçiliyor.")
                continue
                
            time.sleep(2)
            
            # Filtrele butonuna basma hamlesi
            filtrele_butonlari = driver.find_elements(By.XPATH, "//*[contains(text(), 'FİLTRELE') or contains(text(), 'Filtrele')]")
            for f_btn in filtrele_butonlari:
                try:
                    if f_btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", f_btn)
                        time.sleep(1)
                        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));", f_btn)
                        print("🎯 Filtre uygulandı, veriler çekiliyor...")
                        time.sleep(10)
                        break
                except Exception as buton_hatasi:
                    print(f"⚠️ Filtre düğmesi işlenemedi: {buton_hatasi}")
                
            # Sayfadaki verileri okuma
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)
            
            body_text = driver.find_element(By.TAG_NAME, "body").text
            lines = [line.strip() for line in body_text.split('\n') if line.strip()]
            
            i = 0
            while i < len(lines):
                if "çekiliş no" in lines[i].lower():
                    if i + 1 < len(lines):
                        c_no = lines[i+1]
                        
                        if c_no.isdigit():
                            print(f"🔍 Okunan Çekiliş No: {c_no}")
                            
                            if c_no not in mevcut_cekilisler and not any(d["CekilisNo"] == c_no for d in yeni_eklenen_ler):
                                gecici_sayilar = []
                                j = i + 2
                                
                                if j < len(lines) and ("." in lines[j] or ":" in lines[j] or "-" in lines[j]):
                                    j += 1
                                
                                while j < len(lines) and "detaylar" not in lines[j].lower() and "çekiliş no" not in lines[j].lower():
                                    if lines[j].isdigit():
                                        val = int(lines[j])
                                        if 1 <= val <= 80 and val not in gecici_sayilar:
                                            gecici_sayilar.append(val)
                                    j += 1
                                
                                if len(gecici_sayilar) == 20:
                                    gecici_sayilar.sort()
                                    satir_verisi = {"Tarih": istanbul_zamani().strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                                    for idx, s in enumerate(gecici_sayilar, start=1):
                                        satir_verisi[f"Sayi_{idx}"] = s
                                    yeni_eklenen_ler.append(satir_verisi)
                                    print(f"✨ Havuza Taze Çekiliş Eklendi: {c_no}")
                                
                                i = j - 1
                i += 1
        
        veri_tabanina_kaydet(yeni_eklenen_ler)
    except Exception as e:
        print(f"❌ Motor 2 Hatası: {e}")
        raise
    finally:
        try:
            driver.quit()
        except Exception as kapatma_hatasi:
            print(f"⚠️ Tarayıcı kapatılırken hata oluştu: {kapatma_hatasi}")


def canli_cekilis_takip_et():
    try:
        motor_1_api()
    except Exception as api_hatasi:
        print(f"⚠️ Motor 1 (API) başarısız: {api_hatasi}. Selenium yedeğine geçiliyor...")
        try:
            motor_2_stealth_selenium()
        except Exception as sel_hatasi:
            raise RuntimeError(f"İki veri motoru da başarısız. Selenium hatası: {sel_hatasi}") from sel_hatasi

if __name__ == "__main__":
    canli_cekilis_takip_et()
