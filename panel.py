import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import istatistik  # Matematik motorumuz bağlı

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hızlı On Numara Kuantum Analiz Terminali", layout="wide")

# --- BULUT BAĞLANTISI ---
GITHUB_CSV_URL = "https://raw.githubusercontent.com/egemenulucay-52/hizli-on-numara/main/hizli_on_numara.csv"
YEREL_CSV = "hizli_on_numara.csv"

@st.cache_data(ttl=10)
def veriyi_yukle():
    try:
        df_data = pd.read_csv(GITHUB_CSV_URL)
        return df_data, "Canlı Bulut Verisi (GitHub)"
    except:
        if os.path.exists(YEREL_CSV):
            df_data = pd.read_csv(YEREL_CSV)
            return df_data, "Yerel Yedek Verisi (Bağlantı Sorunu)"
        else:
            return pd.DataFrame(), "Veri Bulunamadı"

df, veri_kaynagi = veriyi_yukle()

# --- BAŞLIK ---
st.markdown("<h1 style='text-align: center; font-size: 26px; font-weight: bold;'>🎯 Hızlı On Numara Gelişmiş Analiz Terminali</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #888;'>Makro Ölçekli Kantitatif ve Rastlantısallık Laboratuvarı</p>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.markdown(f"**Veri Kaynağı:** {veri_kaynagi}")

if df.empty:
    st.error("⚠️ Analiz yapılacak çekiliş verisi henüz yüklenemedi. Botun yeni veriler eklemesi bekleniyor...")
else:
    sayi_kolonlari = [f"Sayi_{i}" for i in range(1, 21)]
    toplam_cekilis = len(df)
    
    st.sidebar.metric(label="📊 Sistemdeki Toplam Çekiliş", value=f"{toplam_cekilis} Tur")
    st.sidebar.markdown("---")
    
    # --- YAN MENÜ: GELİŞMİŞ FİLTRELEME ---
    st.sidebar.header("⚙️ Analiz Kapsamı")
    analiz_adet = st.sidebar.slider("Kaç Çekiliş İncelensin?", min_value=5, max_value=max(toplam_cekilis, 10), value=max(toplam_cekilis, 5))
    
    # Veriyi sınırlandırma ve istatistik motoruna gönderme
    analiz_df = df.head(analiz_adet)
    tum_sayilar = analiz_df[sayi_kolonlari].values.flatten()
    frekanslar = pd.Series(tum_sayilar).value_counts().reindex(range(1, 81), fill_value=0)
    df_gecikme = istatistik.gecikme_derinligi_analizi(analiz_df, sayi_kolonlari)
    
    # --- CANLI HİLE & RASTLANTISALLIK DENETÇİSİ ---
    chi2_stat, p_value = istatistik.ki_kare_testi(analiz_df, sayi_kolonlari)
    if p_value > 0.05:
        st.success(f"🎲 **Rastlantısallık Denetimi:** Sistem %95 güvenilirlikle tamamen adil ve rastgele çalışıyor. (p-değeri: {p_value:.4f})")
    else:
        st.warning(f"⚠️ **Rastlantısallık Sapması:** Sayı dağılımlarında teorik sınırın dışında kümelenmeler saptandı! (p-değeri: {p_value:.4f})")

    # --- ÜST ÖZET KARTLARI ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🔥 En Sıcak Sayı", value=f"Sayı: {frekanslar.idxmax()}", delta=f"{frekanslar.max()} Kez Çıktı")
    with col2:
        st.metric(label="❄️ En Soğuk Sayı", value=f"Sayı: {frekanslar.idxmin()}", delta=f"{frekanslar.min()} Kez Çıktı", delta_color="inverse")
    with col3:
        st.metric(label="🎰 Son Çekiliş No", value=f"No: {df.iloc[0]['CekilisNo']}")

    # --- SEKME SİSTEMİ ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Frekans & Gecikme Analizi", 
        "🧠 Rastlantısallık & Kaos (Quant)", 
        "⛓️ Markov Zinciri Bağlantıları", 
        "🔮 Akıllı Kupon Motoru", 
        "📋 Canlı Veri Havuzu"
    ])
    
    # --- SEKME 1: FREKANS VE GECİKME DERİNLİĞİ ---
    with tab1:
        st.subheader("📊 Sayıların Görülme Sıklıkları")
        grafik_df = pd.DataFrame({"Sayı": frekanslar.index, "Çıkma Sayısı": frekanslar.values}).sort_values(by="Sayı")
        fig = px.bar(grafik_df, x="Sayı", y="Çıkma Sayısı", color="Çıkma Sayısı", color_continuous_scale="Viridis", height=350)
        fig.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=5), bargap=0.1)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.subheader("⏳ Geometrik Dağılımlı Gecikme Derinliği (En Uzun Süredir Çıkmayanlar)")
        top_gecikme = df_gecikme.head(10).reset_index().rename(columns={"index": "Sayı", "gecikme": "Kaç Turdur Çıkmıyor?", "olasilik": "Bu Süreye Ulaşma Olasılığı"})
        top_gecikme["Bu Süreye Ulaşma Olasılığı"] = top_gecikme["Bu Süreye Ulaşma Olasılığı"].apply(lambda x: f"%{x*100:.3f}")
        st.dataframe(top_gecikme, use_container_width=True)

    # --- SEKME 2: RASTLANTISALLIK VE KAOS (QUANT) ---
    with tab2:
        st.subheader("📐 Hipergeometrik Tur Geçiş Analizi (Overlap)")
        seri_gecis = istatistik.tur_gecis_analizi(analiz_df, sayi_kolonlari)
        df_gecis = pd.DataFrame({"Ortak Sayı Adedi": seri_gecis.index, "Görülme Sıklığı": seri_gecis.values})
        fig_gecis = px.bar(df_gecis, x="Ortak Sayı Adedi", y="Görülme Sıklığı", color="Görülme Sıklığı", color_continuous_scale="Purples", height=350)
        st.plotly_chart(fig_gecis, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🌌 Shannon Entropisi ile Çekilişlerin Kaos Dağılımı")
        seri_entropi = istatistik.shannon_entropisi(analiz_df, sayi_kolonlari)
        fig_ent = px.histogram(seri_entropi, nbins=15, labels={'value': 'Shannon Entropi Skoru (Kaos Yoğunluğu)'}, color_discrete_sequence=['#0083B0'], height=320)
        fig_ent.update_layout(showlegend=False)
        st.plotly_chart(fig_ent, use_container_width=True)

    # --- SEKME 3: MARKOV ZİNCİRİ BAĞLANTI MOTORU ---
    with tab3:
        st.subheader("⛓️ Koşullu Olasılık Matrisi ve Sayı Tetikleyicileri")
        secilen_sayi = st.selectbox("Analiz Edilecek Kilit Sayıyı Seçin:", list(range(1, 81)), index=22)
        markov_matrisi = istatistik.markov_zinciri_matrisi(analiz_df, sayi_kolonlari)
        olasiliklar = markov_matrisi[secilen_sayi - 1]
        df_markov = pd.DataFrame({"Sonraki Sayı": list(range(1, 81)), "Tetiklenme Olasılığı": olasiliklar})
        top_markov = df_markov.sort_values(by="Tetiklenme Olasılığı", ascending=False).head(7)
        fig_markov = px.bar(top_markov, x="Sonraki Sayı", y="Tetiklenme Olasılığı", text_auto='.3f', color="Tetiklenme Olasılığı", color_continuous_scale="Burg", height=350)
        fig_markov.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_markov, use_container_width=True)

    # --- SEKME 4: YENİ NESİL ÇOKLU SEÇİMLİ AKILLI KUPON MOTORU ---
    with tab4:
        st.subheader("🧙‍♂️ İleri Düzey Çoklu Matematiksel Filtreli Kupon Jeneratörü")
        
        col_satir, col_sayi = st.columns(2)
        with col_satir:
            adet_kupon = st.slider("Kaç Sıra Kupon Üretilsin?", min_value=1, max_value=5, value=5, help="Maksimum 5 sıra kupon üretebilirsiniz.")
        with col_sayi:
            sayi_adedi = st.slider("Her Kupon İçin Kaç Sayı Seçilsin?", min_value=1, max_value=10, value=10, help="Her kupon satırında çıkacak top adedi (1-10 arası).")
            
        st.markdown("#### 🧠 Uygulanacak Strateji ve Filtre Havuzu")
        secilen_filtreler = st.multiselect(
            "Kuponları süzmek için kullanmak istediğiniz tüm kriterleri seçin (Çoklu Seçim):",
            [
                "🔥 Sıcak Sayılar Havuzu (En Çok Çıkan İlk 30 Sayı)",
                "❄️ Derin Gecikme Havuzu (En Uzun Süredir Çıkmayan İlk 30 Sayı)",
                "⛓️ Markov Yoğunluklu Karma (Son Çekilişin Tetiklediği En Güçlü Sayılar)",
                "☯️ Dengeli Tek / Çift Filtresi (Sayıları Yarı Yarıya Oranlar)",
                "📏 Ardışık Sayı Yasağı (Kuponda Yan Yana Sayıları Engeller)",
                "🌌 Shannon Kaos Standardı (Sayı Dağılımının İdeal Entropide Olmasını Şart Koşar)"
            ],
            default=["🔥 Sıcak Sayılar Havuzu (En Çok Çıkan İlk 30 Sayı)", "☯️ Dengeli Tek / Çift Filtresi (Sayıları Yarı Yarıya Oranlar)"]
        )
        
        if st.button("🎰 Seçili Tüm Filtreleri Uygula ve Kuponları Üret"):
            # Başlangıçta tüm sayılar havuzda
            aday_havuz = list(range(1, 81))
            havuz_listeleri = []
            
            # 1. Sıcak Sayılar Havuz Filtresi
            if "🔥 Sıcak Sayılar Havuzu (En Çok Çıkan İlk 30 Sayı)" in secilen_filtreler:
                havuz_listeleri.append(frekanslar.sort_values(ascending=False).index.tolist()[:30])
                
            # 2. Derin Gecikme Havuz Filtresi
            if "❄️ Derin Gecikme Havuzu (En Uzun Süredir Çıkmayan İlk 30 Sayı)" in secilen_filtreler:
                havuz_listeleri.append(df_gecikme.head(30).index.tolist())
                
            # 3. Markov Tetikleme Filtresi
            if "⛓️ Markov Yoğunluklu Karma (Son Çekilişin Tetiklediği En Güçlü Sayılar)" in secilen_filtreler:
                son_cekilis_sayilari = df.iloc[0][sayi_kolonlari].values.astype(int)
                m_matris = istatistik.markov_zinciri_matrisi(analiz_df, sayi_kolonlari)
                toplam_olasiliklar = np.zeros(80)
                for num in son_cekilis_sayilari:
                    toplam_olasiliklar += m_matris[num - 1]
                en_iyi_markov = (np.argsort(toplam_olasiliklar)[::-1] + 1).tolist()[:30]
                havuz_listeleri.append(en_iyi_markov)
            
            # Havuz filtreleri seçildiyse ortak havuzu birleştiriyoruz
            if havuz_listeleri:
                aday_havuz = list(set([num for sublist in havuz_listeleri for num in sublist]))
                if len(aday_havuz) < sayi_adedi:
                    st.warning("⚠️ Seçilen havuz kısıtlamaları nedeniyle yeterli sayı kalmadı, havuz genel kapsama (1-80) genişletildi.")
                    aday_havuz = list(range(1, 81))
            
            basarili_kuponlar = []
            deneme_sayaci = 0
            
            # Süzgeç döngüsü (Rejection Sampling)
            while len(basarili_kuponlar) < adet_kupon and deneme_sayaci < 3000:
                deneme_sayaci += 1
                aday_kupon = sorted(np.random.choice(aday_havuz, sayi_adedi, replace=False).tolist())
                
                # 4. Tek/Çift Dengesi
