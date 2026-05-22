import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

CSV_DOSYASI = "hizli_on_numara.csv"

def canli_cekilis_takip_et():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,800")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    # GitHub siteminde otomatik çalışan en temiz sürücü tanımı
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    print("🚀 GITHUB BULUT BOTU ATEŞLENDİ!")
    
    try:
        driver.get("https://www.millipiyangoonline.com/hizli-on-numara/cekilis-sonuclari")
        time.sleep(10)
        
        mevcut_cekilisler = set()
        if os.path.exists(CSV_DOSYASI):
            try:
                eski_df = pd.read_csv(CSV_DOSYASI)
                if "CekilisNo" in eski_df.columns:
                    mevcut_cekilisler = set(eski_df["CekilisNo"].astype(str).tolist())
            except: pass

        satirlar = driver.find_elements(By.XPATH, "//div[contains(@class, 'accordion-item')] | //div[contains(@class, 'results-content-item')]")
        yeni_eklenen_ler = []
        
        for satir in satirlar:
            try:
                metin = satir.text
                if "Çekiliş no" not in metin: continue
                
                c_no = ""
                for s in metin.split("\n"):
                    if "Çekiliş no" in s:
                        c_no = "".join(filter(str.isdigit, s))
                        break
                
                if not c_no or c_no in mevcut_cekilisler: continue
                    
                toplar = satir.find_elements(By.CLASS_NAME, "numbers-item")
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
                    print(f"✨ Yeni Çekiliş Yakalandı: {c_no}")
            except: continue
        
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
            print(f"💾 CSV Güncellendi. Toplam satır: {len(toplam_df)}")
        else:
            print("💤 Yeni çekiliş yok.")
            
        driver.quit()
    except Exception as e:
        print(f"❌ Hata: {e}")
        driver.quit()

if __name__ == "__main__":
    canli_cekilis_takip_et()
