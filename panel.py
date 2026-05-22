import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hızlı On Numara Analiz & Kupon Jeneratörü", layout="wide")

# --- VERİ BAĞLANTI AYARLARI (GÜNCEL BULUT BAĞLANTISI) ---
GITHUB_CSV_URL = "https://raw.githubusercontent.com/egemenulucay-52/hizli-on-numara/main/hizli_on_numara.csv"
YEREL_CSV = "hizli_on_numara.csv"

@st.cache_data(ttl=60) # Verileri her 60 saniyede bir arkada otomatik yeniler
def veriyi_yukle():
    try:
        # Önce GitHub Actions botunun güncellediği canlı internet dosyasını oku
        df_data = pd.read_csv(GITHUB_CSV_URL)
        return df_data, "Canlı Bulut Verisi (GitHub)"
    except Exception as e:
        # İnternet linkinde sorun olursa yedek olarak yerel CSV'ye dön
        if os.path.exists(YEREL_CSV):
            df_data = pd.read_csv(YEREL_CSV)
            return df_data, "Yerel Yedek Verisi (Bağlantı Sorunu)"
        else:
            # Eğer iki tarafta da dosya yoksa boş şablon üret (Çökmeyi engeller)
            return pd.DataFrame(), "Veri Bulunamadı"

# Veriyi çekiyoruz
df, veri_kaynagi = veriyi_yukle()

# --- BAŞLIK VE GÜNCELLEME BİLGİSİ ---
st.title("🚀 Hızlı On Numara Canlı Analiz Paneli")
st.sidebar.markdown(f"**Veri Kaynağı:** {veri_kaynagi}")

if df.empty:
    st.error("⚠️ Analiz yapılacak çekiliş verisi henüz yüklenemedi. Lütfen CSV dosyalarının sunucuda mevcut olduğundan emin olun.")
else:
    # Sayı kolonlarını netleştirelim (Sayi_1, Sayi_2 ... Sayi_20)
    sayi_kolonlari = [f"Sayi_{i}" for i in range(1, 21)]
    
    # Toplam çekiliş sayısını gösterelim
    toplam_cekilis = len(df)
    st.sidebar.metric(label="Sistemdeki Toplam Çekiliş", value=f"{toplam_cekilis} Tur")
    
    # --- YAN MENÜ: FİLTRELEME ---
    st.sidebar.header("🎯 Analiz Kapsamı")
    analiz_adet = st.sidebar.slider("Son Kaç Çekiliş İncelensin?", min_value=10, max_value=max(toplam_cekilis, 10), value=min(toplam_cekilis, 100))
    
    # Veriyi kullanıcının seçtiği adet kadar sınırlayalım
    analiz_df = df.head(analiz_adet)
    
    # TÜM SAYILARIN ÇIKMA FREKANSLARINI HESAPLAMA
    tum_sayilar = analiz_df[sayi_kolonlari].values.flatten()
    frekanslar = pd.Series(tum_sayilar).value_counts().reindex(range(1, 81), fill_value=0)
    
    # --- ÜST ÖZET KARTLARI (METRİKLER) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        en_cok_cikan = frekanslar.idxmax()
        st.metric(label="🔥 En Çok Çıkan Sayı", value=f"Sayı: {en_cok_cikan}", delta=f"{frekanslar[en_cok_cikan]} Kez")
    with col2:
        en_az_cikan = frekanslar.idxmin()
        st.metric(label="❄️ En Az Çıkan Sayı", value=f"Sayı: {en_az_cikan}", delta=f"{frekanslar[en_az_cikan]} Kez", delta_color="inverse")
    with col3:
        son_cekilis_no = df.iloc[0]["CekilisNo"]
        st.metric(label="🎰 Son İncelenen Çekiliş", value=f"No: {son_cekilis_no}")

    # --- SEKME SİSTEMİ (TAB) ---
    tab1, tab2, tab3 = st.tabs(["📊 Frekans Grafikleri", "🔮 Akıllı Kupon Üretici", "📋 Son Çekiliş Verileri"])
    
    # --- SEKME 1: GRAFİKLER ---
    with tab1:
        st.subheader(f"Son {analiz_adet} Çekilişte Sayıların Çıkma Sıklığı (1 - 80)")
        
        grafik_df = pd.DataFrame({"Sayı": frekanslar.index, "Çıkma Sayısı": frekanslar.values})
        fig = px.bar(grafik_df, x="Sayı", y="Çıkma Sayısı", labels={"Sayı": "Şanslı Toplar", "Çıkma Sayısı": "Görülme Sıklığı"},
                     color="Çıkma Sayısı", color_continuous_scale="Purples")
        fig.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=2))
        st.plotly_chart(fig, use_container_width=True)

    # --- SEKME 2: AKILLI KUPON ÜRETİCİ ---
    with tab1:
        pass # Boş geçiyoruz, kupon üretimini kendi sekmesine alacağız
        
    with tab2:
        st.subheader("🧙‍♂️ İstatistik Tabanlı Akıllı Kupon Üretici")
        st.write("Sistem, yukarıda seçtiğin çekiliş aralığındaki sayıların karakterlerini inceleyerek sana en ideal kombinasyonları üretir.")
        
        kupon_turu = st.radio("Kupon Stratejisi Seçin:", 
                              ["🔥 Sıcak Sayılar (En Çok Çıkanlar)", 
                               "❄️ Soğuk Sayılar (En Az Çıkan/Yıldızı Parlayacaklar)", 
                               "🎹 Dengeli Karma (Sıcak, Soğuk ve Sürpriz Karışık)"])
