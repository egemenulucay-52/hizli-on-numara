import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hızlı On Numara Gelişmiş Analiz Paneli", layout="wide")

# --- BULUT BAĞLANTISI ---
GITHUB_CSV_URL = "https://raw.githubusercontent.com/egemenulucay-52/hizli-on-numara/main/hizli_on_numara.csv"
YEREL_CSV = "hizli_on_numara.csv"

@st.cache_data(ttl=15)
def veriyi_yukle():
    try:
        df_data = pd.read_csv(GITHUB_CSV_URL)
        return df_data, "Canlı Bulut Verisi (GitHub)"
    except Exception as e:
        if os.path.exists(YEREL_CSV):
            df_data = pd.read_csv(YEREL_CSV)
            return df_data, "Yerel Yedek Verisi (Bağlantı Sorunu)"
        else:
            return pd.DataFrame(), "Veri Bulunamadı"

df, veri_kaynagi = veriyi_yukle()

# --- BAŞLIK (MOBİL UYUMLU RESPONSIVE TASARIM) ---
st.markdown("<h1 style='text-align: center; font-size: 26px; font-weight: bold;'>🎯 Hızlı On Numara Profesyonel Analiz</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #888;'>Matematiksel Filtreleme ve Kupon Motoru</p>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.markdown(f"**Veri Kaynağı:** {veri_kaynagi}")

if df.empty:
    st.error("⚠️ Analiz yapılacak çekiliş verisi henüz yüklenemedi. Botun yeni veriler eklemesi bekleniyor...")
else:
    sayi_kolonlari = [f"Sayi_{i}" for i in range(1, 21)]
    toplam_cekilis = len(df)
    
    # Mobilde taşmaması için sidebar metrik düzeni
    st.sidebar.metric(label="📊 Sistemdeki Toplam Çekiliş", value=f"{toplam_cekilis} Tur")
    st.sidebar.markdown("---")
    
    # --- YAN MENÜ: GELİŞMİŞ FİLTRELEME ---
    st.sidebar.header("⚙️ Analiz & Filtre Ayarları")
    analiz_adet = st.sidebar.slider("İstatistiki Kapsam (Son Kaç Çekiliş?)", min_value=1, max_value=max(toplam_cekilis, 10), value=max(toplam_cekilis, 1))
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔮 Kupon Filtre Kriterleri")
    cift_tek_orani = st.sidebar.selectbox("Tek / Çift Dengesi Nasıl Olsun?", ["Fark Etmez", "5 Tek - 5 Çift (Dengeli)", "6 Tek - 4 Çift", "4 Tek - 6 Çift"])
    ardisik_izin = st.sidebar.checkbox("Ardışık Sayılara İzin Ver (Örn: 23, 24)", value=True)
    
    # Veriyi sınırlama
    analiz_df = df.head(analiz_adet)
    tum_sayilar = analiz_df[sayi_kolonlari].values.flatten()
    frekanslar = pd.Series(tum_sayilar).value_counts().reindex(range(1, 81), fill_value=0)
    
    # --- ÜST ÖZET KARTLARI (METRİKLER) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        en_cok_cikan = frekanslar.idxmax()
        st.metric(label="🔥 En Sıcak Şanslı Top", value=f"Sayı: {en_cok_cikan}", delta=f"{frekanslar[en_cok_cikan]} Kez")
    with col2:
        en_az_cikan = frekanslar.idxmin()
        st.metric(label="❄️ En Soğuk Şanslı Top", value=f"Sayı: {en_az_cikan}", delta=f"{frekanslar[en_az_cikan]} Kez", delta_color="inverse")
    with col3:
        son_cekilis_no = df.iloc[0]["CekilisNo"]
        st.metric(label="🎰 Son Çekiliş Numarası", value=f"No: {son_cekilis_no}")

    # --- SEKME SİSTEMİ ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Frekans Analizi", "🔮 Kupon Motoru", "📐 Kolon Dağılımı", "📋 Çekiliş Verileri"])
    
    # --- SEKME 1: FREKANS GRAFİKLERİ (MOBİL AYARLI) ---
    with tab1:
        st.subheader("📊 Tüm Sayıların Görülme Frekansı")
        grafik_df = pd.DataFrame({"Sayı": frekanslar.index, "Çıkma Sayısı": frekanslar.values}).sort_values(by="Sayı")
        fig = px.bar(grafik_df, x="Sayı", y="Çıkma Sayısı", color="Çıkma Sayısı", 
                     color_continuous_scale="Viridis", labels={"Çıkma Sayısı":"Frekans"},
                     height=380) # Mobilde taşmayan ideal yükseklik
        fig.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=5), bargap=0.1) 
        st.plotly_chart(fig, use_container_width=True)

    # --- SEKME 2: DETAYLI KUPON ÜRETİCİ ---
    with tab2:
        st.subheader("🧙‍♂️ Filtreli Kupon Jeneratörü")
        
        kupon_turu = st.radio("Ana İstatistik Algoritması:", 
                              ["🔥 Sıcak Sayılar", "❄️ Soğuk Sayılar", "🎹 Dengeli Karma"], horizontal=True)
        
        adet_kupon = st.slider("Kaç Adet Kupon Üretilsin?", min_value=1, max_value=10, value=1)
        
        if st.button("🎰 Kriterlere Uygun Akıllı Kupon(ları) Üret"):
            sirali_sayilar = frekanslar.sort_values(ascending=False).index.tolist()
            
            if "Sıcak Sayılar" in kupon_turu:
                ana_havuz = sirali_sayilar[:30]
            elif "Soğuk Sayılar" in kupon_turu:
                ana_havuz = sirali_sayilar[-30:]
            else:
                ana_havuz = list(range(1, 81))
                
            basarili_kuponlar = []
            deneme_sayaci = 0
            
            while len(basarili_kuponlar) < adet_kupon and deneme_sayaci < 1000:
                deneme_sayaci += 1
                
                if len(df) < 3:
                    aday_kupon = sorted(np.random.choice(range(1, 81), 10, replace=False).tolist())
                else:
                    aday_kupon = sorted(np.random.choice(ana_havuz, 10, replace=False).tolist())
                
                tekler = [n for n in aday_kupon if n % 2 != 0]
                ciftler = [n for n in aday_kupon if n % 2 == 0]
                
                if cift_tek_orani == "5 Tek - 5 Çift (Dengeli)" and (len(tekler) != 5 or len(ciftler) != 5):
                    continue
                if cift_tek_orani == "6 Tek - 4 Çift" and (len(tekler) != 6 or len(ciftler) != 4):
                    continue
                if cift_tek_orani == "4 Tek - 6 Çift" and (len(tekler) != 4 or len(ciftler) != 6):
                    continue
                    
                if not ardisik_izin:
                    has_ardisik = False
                    for idx in range(len(aday_kupon) - 1):
                        if aday_kupon[idx+1] - aday_kupon[idx] == 1:
                            has_ardisik = True
                            break
                    if has_ardisik:
                        continue
                
                if aday_kupon not in basarili_kuponlar:
                    basarili_kuponlar.append(aday_kupon)
            
            st.markdown(f"### 🎫 Üretilen Şanslı Kuponlar:")
            for k_idx, kpn in enumerate(basarili_kuponlar, 1):
                kupon_html = " ".join([f"<span style='display:inline-block; background-color:#1565C0; color:white; border-radius:50%; width:38px; height:38px; text-align:center; line-height:38px; font-weight:bold; font-size:14px; margin:3px;'>{num}</span>" for num in kpn])
                st.markdown(f"**Kupon {k_idx}:** {kupon_html}", unsafe_allow_html=True)
            
            st.balloons()

    # --- SEKME 3: GEOMETRİK BÖLGE VE MATRİS ANALİZİ (MOBİL AYARLI) ---
    with tab3:
        st.subheader("📐 Sayıların Matrisel Dağılım Yoğunluğu (1-80)")
        
        matris_verisi = np.zeros((8, 10))
        for s in range(1, 81):
            satir = (s - 1) // 10
            sutun = (s - 1) % 10
            matris_verisi[satir, sutun] = frekanslar.get(s, 0)
            
        fig_matris = px.imshow(matris_verisi,
                               labels=dict(x="Kolonlar", y="Satırlar", color="Sıklık"),
                               x=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
                               y=['1-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80'],
                               color_continuous_scale="Purples",
                               height=450, 
                               aspect="equal")
        st.plotly_chart(fig_matris, use_container_width=True)

    # --- SEKME 4: KRONOLOJİK LİSTE ---
    with tab4:
        st.subheader("📋 Kayıtlı Çekiliş Listesi")
        st.dataframe(analiz_df, use_container_width=True)
