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
    options.add_argument("--window-size=1200,800")
    # Sunucuya taşındığında sorun çıkarmaması için arka plan çalışma ayarları hazırlığı
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    # Tarayıcıyı bir kez başlatıyoruz (Sürekli açılıp kapanarak bilgisayarı yormasın)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    print("🚀 Canlı On Numara Takip Botu Başlatıldı!")
    print("Döngü başladı. Her 5 dakikada bir yeni çekilişler kontrol edilecek...")
    
    try:
        while True:
            print(f"\n⏱️ [{time.strftime('%H:%M:%S')}] Siteden güncel veriler kontrol ediliyor...")
            driver.get("https://www.millipiyangoonline.com/hizli-on-numara/cekilis-sonuclari")
            
            # Sayfanın ve dinamik sayıların yüklenmesi için güvenli bekleme
            time.sleep(10)
            
            # --- MEVCUT CSV'Yİ HAFIZAYA ALMA ---
            mevcut_cekilisler = set()
            if os.path.exists(CSV_DOSYASI):
                try:
                    eski_df = pd.read_csv(CSV_DOSYASI)
                    if "CekilisNo" in eski_df.columns:
                        mevcut_cekilisler = set(eski_df["CekilisNo"].astype(str).tolist())
                except:
                    print("⚠️ Mevcut CSV okunurken hata oluştu, sıfırdan yazılacak.")

            # --- EKRANDAKİ SON ÇEKİLİŞLERİ TARAMA ---
            satirlar = driver.find_elements(By.XPATH, "//div[contains(@class, 'accordion-item')] | //div[contains(@class, 'results-content-item')]")
            
            yeni_eklenen_ler = []
            
            for satir in satirlar:
                try:
                    metin = satir.text
                    if "Çekiliş no" not in metin:
                        continue
                    
                    # Çekiliş numarasını ayıkla
                    c_no = ""
                    for s in metin.split("\n"):
                        if "Çekiliş no" in s:
                            c_no = "".join(filter(str.isdigit, s))
                            break
                    
                    # Eğer bu çekiliş zaten CSV'de varsa hiç uğraşma, pas geç
                    if not c_no or c_no in mevcut_cekilisler:
                        continue
                        
                    # Çekilişin içindeki 20 topu yakala
                    toplar = satir.find_elements(By.CLASS_NAME, "numbers-item")
                    gecici_sayilar = []
                    for top in toplar:
                        top_metni = top.text.strip()
                        if top_metni.isdigit() and 1 <= int(top_metni) <= 80:
                            val = int(top_metni)
                            if val not in gecici_sayilar:
                                gecici_sayilar.append(val)
                    
                    # Eğer 20 top eksiksiz söküldüyse listeye ekle
                    if len(gecici_sayilar) == 20:
                        gecici_sayilar.sort()
                        
                        satir_verisi = {"Tarih": time.strftime('%Y-%m-%d %H:%M:%S'), "CekilisNo": c_no}
                        for i, s in enumerate(gecici_sayilar, start=1):
                            satir_verisi[f"Sayi_{i}"] = s
                            
                        yeni_eklenen_ler.append(satir_verisi)
                        print(f"✨ YENİ ÇEKİLİŞ BULUNDU! No: {c_no} -> {gecici_sayilar[:5]}...")
                except:
                    continue
            
            # --- CSV GÜNCELLEME (EĞER YENİ VERİ VARSA) ---
            if yeni_eklenen_ler:
                yeni_df = pd.DataFrame(yeni_eklenen_ler)
                
                if os.path.exists(CSV_DOSYASI):
                    # Eski veriyle yeniyi birleştir, mükerrer kayıtları engelle ve kronolojik sırala
                    eski_df = pd.read_csv(CSV_DOSYASI)
                    toplam_df = pd.concat([eski_df, yeni_df], ignore_index=True)
                else:
                    toplam_df = new_df
                    
                toplam_df["CekilisNo"] = toplam_df["CekilisNo"].astype(str)
                toplam_df = toplam_df.drop_duplicates(subset=["CekilisNo"])
                toplam_df = toplam_df.sort_values(by="CekilisNo", ascending=False)
                
                # Excel açık kilitlenmesi riskine karşı korumalı kayıt dene
                try:
                    toplam_df.to_csv(CSV_DOSYASI, index=False, encoding='utf-8')
                    print(f"💾 {len(yeni_eklenen_ler)} yeni çekiliş başarıyla CSV dosyasına işlendi. (Toplam Satır: {len(toplam_df)})")
                except PermissionError:
                    print("❌ HATA: CSV dosyası şu an Excel'de açık olduğu için yazılamadı! Lütfen Excel'i kapatın.")
            else:
                print("💤 Yeni bir çekiliş yok, bekleniyor...")

            # 5 dakika (300 saniye) uyku modu
            print("⏳ 5 dakikalık uyku moduna geçiliyor...")
            time.sleep(300)
            
    except KeyboardInterrupt:
        print("\n🛑 Kullanıcı tarafından bot durduruldu.")
        driver.quit()
    except Exception as e:
        print(f"❌ Beklenmedik Sistem Hatası: {e}")
        driver.quit()

if __name__ == "__main__":
    canli_cekilis_takip_et()
