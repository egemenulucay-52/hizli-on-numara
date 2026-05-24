import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import istatistik  # Matematik motorumuz bağlı

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hızlı On Numara Çok Boyutlu Kuantum Terminali", layout="wide")

# --- BULUT BAĞLANTISI ---
GITHUB_CSV_URL = "https://raw.githubusercontent.com/egemenulucay-52/hizli-on-numara/main/hizli_on_numara.csv"
YEREL_CSV = "hizli_on_numara.csv"

@st.cache_data(ttl=30)
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
st.markdown("<h1 style='text-align: center; font-size: 26px; font-weight: bold;'>🎯 Hızlı On Numara Çok Boyutlu Kuantum Terminali</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #888;'>Kombinasyonel Veri Madenciliği ve Non-Linear Tahmin Laboratuvarı</p>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.markdown(f"**Veri Kaynağı:** {veri_kaynagi}")

if df.empty:
    st.error("⚠️ Analiz yapılacak çekiliş verisi henüz yüklenemedi. Botun yeni veriler eklemesi bekleniyor...")
else:
    sayi_kolonlari = [f"Sayi_{i}" for i in range(1, 21)]
    toplam_cekilis = len(df)
    
    st.sidebar.metric(label="📊 Sistemdeki Toplam Çekiliş", value=f"{toplam_cekilis} Tur")
    st.sidebar.markdown("---")
    
    st.sidebar.header("⚙️ Analiz Kapsamı")
    analiz_adet = st.sidebar.slider("Kaç Çekiliş İncelensin?", min_value=5, max_value=max(toplam_cekilis, 10), value=max(toplam_cekilis, 5))
    
    analiz_df = df.head(analiz_adet)
    tum_sayilar = analiz_df[sayi_kolonlari].values.flatten()
    frekanslar = pd.Series(tum_sayilar).value_counts().reindex(range(1, 81), fill_value=0)
    
    # --- 💥 YENİ NESİL GELİŞMİŞ ÖNBELLEK MOTORU (HIZLANDIRILMIŞ NUMPY MATRİSLERİ) ---
    @st.cache_data(ttl=60)
    def cached_gecikme_analizi(_df_slice):
        return istatistik.gecikme_derinligi_analizi(_df_slice, sayi_kolonlari)

    @st.cache_data(ttl=60)
    def cached_tur_gecis_analizi(_df_slice):
        return istatistik.tur_gecis_analizi(_df_slice, sayi_kolonlari)

    @st.cache_data(ttl=60)
    def cached_shannon_entropisi(_df_slice):
        return istatistik.shannon_entropisi(_df_slice, sayi_kolonlari)

    @st.cache_data(ttl=60)
    def cached_markov_zinciri_matrisi(_df_slice):
        return istatistik.markov_zinciri_matrisi(_df_slice, sayi_kolonlari)

    @st.cache_data(ttl=60)
    def cached_kuantum_makro_motoru(_df):
        df_len = len(_df)
        # 1. MACD Trend İvmesi
        short_len = min(15, df_len)
        long_len = min(150, df_len)
        short_freq = pd.Series(_df.head(short_len)[sayi_kolonlari].values.flatten()).value_counts().reindex(range(1, 81), fill_value=0) / short_len
        long_freq = pd.Series(_df.head(long_len)[sayi_kolonlari].values.flatten()).value_counts().reindex(range(1, 81), fill_value=0) / long_len
        macd_scores = short_freq - long_freq
        
        # 2. Birlikte Çıkma İlişki Ağları (Co-occurrence)
        matrix_co = np.zeros((80, 80))
        for _, row in _df.head(100)[sayi_kolonlari].iterrows():
            nums = row.values.astype(int) - 1
            for i in nums:
                for j in nums:
                    if i != j: matrix_co[i, j] += 1
        son_cekilis_nums = _df.iloc[0][sayi_kolonlari].values.astype(int)
        co_scores = np.zeros(80)
        for n in son_cekilis_nums:
            co_scores += matrix_co[:, n-1]
            
        # 3. Poisson Boşluk Anomalisi
        poisson_scores = []
        for num in range(1, 81):
            appears = np.where((_df[sayi_kolonlari] == num).any(axis=1))[0]
            if len(appears) > 0:
                curr_gap = float(appears[0])
                lam = len(appears) / df_len
                p_score = 1.0 - np.exp(-lam * curr_gap)
            else: p_score = 0.0
            poisson_scores.append(p_score)
            
        # 4. Bölge Yoğunluk Kilit Modeli (Zonal)
        last_10_matrix = _df.head(10)[sayi_kolonlari].values.flatten()
        zone_counts = pd.Series((last_10_matrix - 1) // 10).value_counts().reindex(range(8), fill_value=0)
        zonal_scores = []
        for num in range(1, 81):
            zone = (num - 1) // 10
            zonal_scores.append(float(25 - zone_counts[zone]))
            
        return pd.DataFrame({
            "Sayı": range(1, 81),
            "MACD_Skoru": macd_scores.values,
            "Iliski_Agi_Skoru": co_scores,
            "Poisson_Anomalisi": poisson_scores,
            "Bolge_Yogunluk_Eksigi": zonal_scores
        })
    
    # Yeni motoru çalıştır ve matrisleri al
    df_kuant = cached_kuantum_makro_motoru(df)
    markov_matrisi = cached_markov_zinciri_matrisi(analiz_df)
    df_gecikme = cached_gecikme_analizi(analiz_df)
    
    chi2_stat, p_value = istatistik.ki_kare_testi(analiz_df, sayi_kolonlari)
    if p_value > 0.05:
        st.success(f"🎲 **Rastlantısallık Denetimi:** Sistem %95 güvenilirlikle adil çalışıyor. (p-değeri: {p_value:.4f})")
    else:
        st.warning(f"⚠️ **Rastlantısallık Sapması:** Kümelenmeler saptandı! (p-değeri: {p_value:.4f})")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🔥 En Sıcak Sayı", value=f"Sayı: {frekanslar.idxmax()}", delta=f"{frekanslar.max()} Kez")
    with col2:
        st.metric(label="❄️ En Soğuk Sayı", value=f"Sayı: {frekanslar.idxmin()}", delta=f"{frekanslar.min()} Kez", delta_color="inverse")
    with col3:
        st.metric(label="🎰 Son Çekiliş No", value=f"No: {df.iloc[0]['CekilisNo']}")

    # --- YENİLENMİŞ 7'Lİ SEKME SİSTEMİ ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Frekans & Gecikme", 
        "🧠 Rastlantısallık & Kaos", 
        "📈 Çok Boyutlu Kuant Laboratuvarı", 
        "⛓️ Markov Zinciri", 
        "🔮 Akıllı Kupon & Kesişim Motoru", 
        "📋 Canlı Veri Havuzu",
        "🏆 Strateji Performans & Tahmin"
    ])
    
    with tab1:
        st.subheader("📊 Sayıların Görülme Sıklıkları")
        grafik_df = pd.DataFrame({"Sayı": frekanslar.index, "Çıkma Sayısı": frekanslar.values}).sort_values(by="Sayı")
        fig = px.bar(grafik_df, x="Sayı", y="Çıkma Sayısı", color="Çıkma Sayısı", color_continuous_scale="Viridis", height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.subheader("⏳ Gecikme Derinliği")
        top_gecikme = df_gecikme.head(10).reset_index().rename(columns={"index": "Sayı", "gecikme": "Kaç Turdur Çıkmıyor?", "olasilik": "Olasılık"})
        top_gecikme["Olasılık"] = top_gecikme["Olasılık"].apply(lambda x: f"%{x*100:.3f}")
        st.dataframe(top_gecikme, use_container_width=True)

    with tab2:
        st.subheader("📈 Merkezi Eğilim Analizleri")
        aritmetik_ort = float(np.mean(tum_sayilar))
        geometrik_ort = float(np.exp(np.mean(np.log(tum_sayilar))))
        medyan_deger = float(np.median(tum_sayilar))
        
        c_ort1, c_ort2, c_ort3 = st.columns(3)
        with c_ort1: st.metric(label="🧮 Aritmetik Ortalama", value=f"{aritmetik_ort:.2f}")
        with c_ort2: st.metric(label="📐 Geometrik Ortalama", value=f"{geometrik_ort:.2f}")
        with c_ort3: st.metric(label="⚖️ Medyan Olasılık", value=f"{medyan_deger:.1f}")
        
        st.markdown("---")
        st.subheader("🌌 Shannon Entropisi (Kaos Dağılımı)")
        seri_entropi = cached_shannon_entropisi(analiz_df)
        fig_ent = px.histogram(seri_entropi, nbins=15, labels={'value': 'Shannon Entropi Skoru'}, color_discrete_sequence=['#0083B0'], height=300)
        st.plotly_chart(fig_ent, use_container_width=True)

    # --- TAB 3: BAŞTAN AŞAĞI YENİLENEN KUANT LABORATUVARI ---
    with tab3:
        st.subheader("🕸️ 1. Birlikte Çıkma İlişki Ağları (Co-occurrence Network)")
        st.write("Son çekilişteki sayıların geçmişte en çok hangi partnerlerle beraber çıktığını kombinasyonel olarak hesaplar.")
        top_co = df_kuant.sort_values(by="Iliski_Agi_Skoru", ascending=False).head(15)
        fig_co = px.bar(top_co, x="Sayı", y="Iliski_Agi_Skoru", color="Iliski_Agi_Skoru", color_continuous_scale="Purples", height=280)
        fig_co.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_co, use_container_width=True)
        
        st.markdown("---")
        st.subheader("⏳ 2. Poisson Boşluk Anomalisi Sınırı")
        st.write("Sayıların çıkış hızlarına göre mevcut gecikmelerinin oluşturduğu non-linear anomali gerilimi. 1.0'a yaklaşanlar patlamak zorundadır.")
        top_poi = df_kuant.sort_values(by="Poisson_Anomalisi", ascending=False).head(15)
        fig_poi = px.bar(top_poi, x="Sayı", y="Poisson_Anomalisi", color="Poisson_Anomalisi", color_continuous_scale="solar", height=280)
        fig_poi.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_poi, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🧱 3. Bölge Yoğunluk Eksik Matrisi (Zonal Deficit)")
        st.write("1-80 tahtasındaki 8 ana bloktan son 10 çekilişte teorik ortalamanın altında kalarak kuraklık yaşayan bölgeler.")
        top_zon = df_kuant.sort_values(by="Bolge_Yogunluk_Eksigi", ascending=False).head(15)
        fig_zon = px.bar(top_zon, x="Sayı", y="Bolge_Yogunluk_Eksigi", color="Bolge_Yogunluk_Eksigi", color_continuous_scale="Teal", height=280)
        fig_zon.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_zon, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 Yeni Nesil Kuant Matris Tablosu")
        st.dataframe(df_kuant.sort_values(by="Poisson_Anomalisi", ascending=False), use_container_width=True)

    with tab4:
        st.subheader("⛓️ Markov Zinciri Koşullu Olasılık")
        secilen_sayi = st.selectbox("Analiz Edilecek Kilit Sayıyı Seçin:", list(range(1, 81)), index=22)
        olasiliklar = markov_matrisi[secilen_sayi - 1]
        df_markov = pd.DataFrame({"Sonraki Sayı": list(range(1, 81)), "Tetiklenme Olasılığı": olasiliklar})
        top_markov = df_markov.sort_values(by="Tetiklenme Olasılığı", ascending=False).head(7)
        fig_markov = px.bar(top_markov, x="Sonraki Sayı", y="Tetiklenme Olasılığı", text_auto='.3f', color="Tetiklenme Olasılığı", color_continuous_scale="Burg", height=350)
        fig_markov.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_markov, use_container_width=True)

    # --- TAB 5: YENİ NESİL KESİŞİM VE KUPON MOTORU ---
    with tab5:
        st.markdown("### 🧬 Strateji Havuz Kesişim Laboratuvarı (Ortak Sayı Bulucu)")
        st.write("Yeni eklenen çok boyutlu havuzların birbiriyle çakışan ortak sayılarını filtre koymadan ham liste olarak dökmenizi sağlar.")
        
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            havuz1_secim = st.selectbox("1. Strateji Havuzu Seçin:", ["🔥 Sıcak Sayılar (İlk 30)", "❄️ Derin Gecikme (İlk 30)", "📈 MACD İvme Havuzu (İlk 30)", "🕸️ İlişki Ağları Ortakları (İlk 30)", "⏳ Poisson Anomalisi Liderleri (İlk 30)", "🧱 Bölge Yoğunluk Eksikleri (İlk 30)"], index=2)
        with col_h2:
            havuz2_secim = st.selectbox("2. Strateji Havuzu Seçin:", ["🔥 Sıcak Sayılar (İlk 30)", "❄️ Derin Gecikme (İlk 30)", "📈 MACD İvme Havuzu (İlk 30)", "🕸️ İlişki Ağları Ortakları (İlk 30)", "⏳ Poisson Anomalisi Liderleri (İlk 30)", "🧱 Bölge Yoğunluk Eksikleri (İlk 30)"], index=4)
            
        def get_static_pool_v2(secim, _freq, _df_gecikme, _df_k, _markov_matrisi, _df, _sayi_kolonlari):
            if "Sıcak" in secim: return _freq.sort_values(ascending=False).index.tolist()[:30]
            elif "Gecikme" in secim: return _df_gecikme.head(30).index.tolist()
            elif "MACD" in secim: return _df_k.sort_values(by="MACD_Skoru", ascending=False)["Sayı"].tolist()[:30]
            elif "İlişki" in secim: return _df_k.sort_values(by="Iliski_Agi_Skoru", ascending=False)["Sayı"].tolist()[:30]
            elif "Poisson" in secim: return _df_k.sort_values(by="Poisson_Anomalisi", ascending=False)["Sayı"].tolist()[:30]
            elif "Bölge" in secim: return _df_k.sort_values(by="Bolge_Yogunluk_Eksigi", ascending=False)["Sayı"].tolist()[:30]
            return []

        h1_list = get_static_pool_v2(havuz1_secim, frekanslar, df_gecikme, df_kuant, markov_matrisi, df, sayi_kolonlari)
        h2_list = get_static_pool_v2(havuz2_secim, frekanslar, df_gecikme, df_kuant, markov_matrisi, df, sayi_kolonlari)
        ortak_sayilar = sorted(list(set(h1_list) & set(h2_list)))
        
        if ortak_sayilar:
            ortak_html = " ".join([f"<span style='display:inline-block; background-color:#E65100; color:white; border-radius:50%; width:36px; height:36px; text-align:center; line-height:36px; font-weight:bold; font-size:14px; margin:3px;'>{num}</span>" for num in ortak_sayilar])
            st.markdown(f"🎯 **Çakışan Ortak Sayılar Havuzu ({len(ortak_sayilar)} Adet):**<br>{ortak_html}", unsafe_allow_html=True)
        else: st.info("Bu kombinasyonda çakışan ortak sayı saptanamadı.")
            
        st.markdown("---")
        st.markdown("### 🧙‍♂️ Otomatik Filtreli Kupon Jeneratörü")
        adet_kupon = st.slider("Kaç Sıra Kupon Üretilsin?", min_value=1, max_value=5, value=3)
        kupon_ayarlari = []
        
        for k in range(1, adet_kupon + 1):
            with st.expander(f"⚙️ Kupon Sıra {k} Özel Ayarları", expanded=False):
                col_sayi, col_filtre = st.columns([1, 2])
                with col_sayi:
                    s_adedi = st.slider(f"Kupon {k} Kaç Sayıdan Oluşsun?", min_value=1, max_value=10, value=10, key=f"sayi_{k}")
                with col_filtre:
                    filtreler = st.multiselect(
                        f"Kupon {k} İçin Uygulanacak Süzgeçler:",
                        ["🔥 Sıcak Sayılar", "❄️ Derin Gecikme", "📈 MACD İvme Havuzu 🚀", "🕸️ İlişki Ağları Havuzu 🕸️", "⏳ Poisson Anomalisi Havuzu ⌛", "🧱 Bölge Yoğunluk Süzgeci 🧱", "☯️ Dengeli Tek / Çift", "📏 Ardışık Sayı Yasağı", "🌌 Shannon Kaos Standardı"],
                        default=["📈 MACD İvme Havuzu 🚀", "⏳ Poisson Anomalisi Havuzu ⌛"],
                        key=f"filtre_{k}"
                    )
                kupon_ayarlari.append({"sıra": k, "sayi_adedi": s_adedi, "filtreler": filtreler})
        
        if st.button("🎰 Kuponları Süz ve Üret"):
            with st.spinner("🔮 Kuantum süzgeçler işleniyor..."):
                for ayar in kupon_ayarlari:
                    k_idx = ayar["sıra"]
                    s_adedi = ayar["sayi_adedi"]
                    filtreler = ayar["filtreler"]
                    
                    aday_havuz = list(range(1, 81))
                    havuz_listeleri = []
                    
                    if "🔥 Sıcak Sayılar" in filtreler: havuz_listeleri.append(frekanslar.sort_values(ascending=False).index.tolist()[:30])
                    if "❄️ Derin Gecikme" in filtreler: havuz_listeleri.append(df_gecikme.head(30).index.tolist())
                    if "📈 MACD İvme Havuzu 🚀" in filtreler: havuz_listeleri.append(df_kuant.sort_values(by="MACD_Skoru", ascending=False)["Sayı"].tolist()[:30])
                    if "🕸️ İlişki Ağları Havuzu 🕸️" in filtreler: havuz_listeleri.append(df_kuant.sort_values(by="Iliski_Agi_Skoru", ascending=False)["Sayı"].tolist()[:30])
                    if "⏳ Poisson Anomalisi Havuzu ⌛" in filtreler: havuz_listeleri.append(df_kuant.sort_values(by="Poisson_Anomalisi", ascending=False)["Sayı"].tolist()[:30])
                    if "🧱 Bölge Yoğunluk Süzgeci 🧱" in filtreler: havuz_listeleri.append(df_kuant.sort_values(by="Bolge_Yogunluk_Eksigi", ascending=False)["Sayı"].tolist()[:30])
                    
                    if havuz_listeleri:
                        aday_havuz = list(set([num for sublist in havuz_listeleri for num in sublist]))
                        if len(aday_havuz) < s_adedi: aday_havuz = list(range(1, 81))
                    
                    kupon_bulundu, deneme = False, 0
                    while deneme < 1000:
                        deneme += 1
                        aday_kupon = sorted(np.random.choice(aday_havuz, s_adedi, replace=False).tolist())
                        if "☯️ Dengeli Tek / Çift" in filtreler:
                            if abs(len([n for n in aday_kupon if n%2!=0]) - len([n for n in aday_kupon if n%2==0])) > 2: continue
                        if "📏 Ardışık Sayı Yasağı" in filtreler:
                            if any(aday_kupon[i+1] - aday_kupon[i] == 1 for i in range(len(aday_kupon)-1)): continue
                        if "🌌 Shannon Kaos Standardı" in filtreler and s_adedi > 3:
                            farklar = np.diff(aday_kupon)
                            if farklar.sum() > 0:
                                p = farklar / farklar.sum()
                                p = p[p > 0]
                                if -np.sum(p * np.log2(p)) < (np.log2(len(farklar)) * 0.75): continue
                        
                        kupon_html = " ".join([f"<span style='display:inline-block; background-color:#1565C0; color:white; border-radius:50%; width:36px; height:36px; text-align:center; line-height:36px; font-weight:bold; font-size:13px; margin:3px;'>{num}</span>" for num in aday_kupon])
                        st.markdown(f"**Sıra {k_idx} ({s_adedi} Sayı):** {kupon_html}", unsafe_allow_html=True)
                        kupon_bulundu = True
                        break
                    if not kupon_bulundu: st.error(f"❌ Sıra {k_idx} için uygun kombinasyon süzülemedi.")
                st.balloons()

    with tab6:
        st.subheader("📋 Güncel Çekiliş Veritabanı")
        st.dataframe(analiz_df, use_container_width=True)

    # --- TAHMİN YARDIMCI MOTORU ---
    def strateji_tahmin_uret_v2(data_slice, strateji_adi):
        k_slice = cached_kuantum_makro_motoru(data_slice)
        freq_slice = pd.Series(data_slice[sayi_kolonlari].values.flatten()).value_counts().reindex(range(1, 81), fill_value=0)
        
        havuz = []
        if strateji_adi == "🔥 Sadece Sıcak": havuz = freq_slice.sort_values(ascending=False).index[:30].tolist()
        elif strateji_adi == "❄️ Sadece Soğuk": havuz = istatistik.gecikme_derinligi_analizi(data_slice, sayi_kolonlari).index[:30].tolist()
        elif strateji_adi == "🚀 Trend Takipçi (MACD)": havuz = k_slice.sort_values(by="MACD_Skoru", ascending=False)["Sayı"].tolist()[:30]
        elif strateji_adi == "🕸️ İlişki Ağları (Co-occurrence)": havuz = k_slice.sort_values(by="Iliski_Agi_Skoru", ascending=False)["Sayı"].tolist()[:30]
        elif strateji_adi == "⏳ Poisson Boşluk Anomalisi": havuz = k_slice.sort_values(by="Poisson_Anomalisi", ascending=False)["Sayı"].tolist()[:30]
        elif strateji_adi == "🧱 Bölge Yoğunluk Süzgeci": havuz = k_slice.sort_values(by="Bolge_Yogunluk_Eksigi", ascending=False)["Sayı"].tolist()[:30]
        elif strateji_adi == "💎 Çok Boyutlu Kuant (MACD + Poisson)":
            havuz = list(set(k_slice.sort_values(by="MACD_Skoru", ascending=False)["Sayı"].tolist()[:20]) | set(k_slice.sort_values(by="Poisson_Anomalisi", ascending=False)["Sayı"].tolist()[:20]))
        elif strateji_adi == "⚖️ Dengeleyici (Sıcak + Soğuk)":
            havuz = list(set(freq_slice.sort_values(ascending=False).index[:20]) | set(istatistik.gecikme_derinligi_analizi(data_slice, sayi_kolonlari).index[:20]))
        elif strateji_adi == "⚡ Hızlı Tetik (Markov + İlişki)":
            son_n = data_slice.iloc[0][sayi_kolonlari].values.astype(int)
            probs = np.zeros(80)
            for n in son_n: probs += markov_matrisi[n-1]
            havuz = list(set((np.argsort(probs)[::-1] + 1).tolist()[:20]) | set(k_slice.sort_values(by="Iliski_Agi_Skoru", ascending=False)["Sayı"].tolist()[:20]))
        else: havuz = np.random.choice(range(1,81), 40, replace=False).tolist()
        
        return sorted(np.random.choice(havuz, 20, replace=False).tolist())

    # --- TAB 7: YENİ NESİL BACKTEST VE OTONOM LOG MATRİSİ ---
    with tab7:
        st.subheader("🏆 Strateji Performans Ölçümü (Backtest Mode)")
        st.write("Sistem, son gerçekleşen çekilişi 'gelecek' sayıp, 10 yeni nesil kuant stratejisini yarıştırır.")
        
        stratejiler_v2 = [
            "🔥 Sadece Sıcak", "❄️ Sadece Soğuk", "🚀 Trend Takipçi (MACD)", 
            "🕸️ İlişki Ağları (Co-occurrence)", "⏳ Poisson Boşluk Anomalisi", "🧱 Bölge Yoğunluk Süzgeci",
            "💎 Çok Boyutlu Kuant (MACD + Poisson)", "⚖️ Dengeleyici (Sıcak + Soğuk)", 
            "⚡ Hızlı Tetik (Markov + İlişki)", "🎰 Saf Olasılık (Random)"
        ]

        if len(df) > 10:
            gercek_sonuc = set(df.iloc[0][sayi_kolonlari].values.astype(int))
            simulasyon_verisi = df.iloc[1:]
            
            perf_sonuclari = []
            for s in stratejiler_v2:
                tahmin = set(strateji_tahmin_uret_v2(simulasyon_verisi, s))
                hits = len(tahmin & gercek_sonuc)
                perf_sonuclari.append({"Strateji": s, "Isabet": hits, "Tahmin": sorted(list(tahmin))})
            
            df_perf = pd.DataFrame(perf_sonuclari).sort_values(by="Isabet", ascending=False)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write(f"🔍 **Son Gerçekleşen ({df.iloc[0]['CekilisNo']}):**")
                st.markdown(" ".join([f"<span style='color:#FFD700; font-weight:bold;'>{n}</span>" for n in sorted(list(gercek_sonuc))]), unsafe_allow_html=True)
                
                fig_perf = px.bar(df_perf, x="Isabet", y="Strateji", orientation='h', color="Isabet", color_continuous_scale="Viridis")
                fig_perf.update_layout(xaxis_title="İsabet (20'de)")
                st.plotly_chart(fig_perf, use_container_width=True)
            
            with c2:
                st.write("📊 **Strateji Detayları ve İsabetli Sayılar:**")
                for _, row in df_perf.iterrows():
                    hit_nums = sorted(list(set(row['Tahmin']) & gercek_sonuc))
                    hit_txt = ", ".join(map(str, hit_nums)) if hit_nums else "Yok"
                    st.markdown(f"**{row['Strateji']}:** {row['Isabet']} İsabet → `{hit_txt}`")

            st.markdown("---")
            st.subheader("📜 Yeni Nesil Otonom Tahmin Log Günlüğü (Rolling Backtest)")
            log_derinligi = st.slider("Log İstatistik Derinliği (Çekiliş Sayısı)", min_value=3, max_value=12, value=6)
            
            @st.cache_data(ttl=60)
            def cached_tarihsel_log_v2(_df, _stratejiler):
                log_verisi = []
                for i in range(log_derinligi, 0, -1):
                    if i < len(_df):
                        target_row = _df.iloc[i-1]
                        target_nums = set(target_row[sayi_kolonlari].values.astype(int))
                        tarihsel_slice = _df.iloc[i:]
                        for s in _stratejiler:
                            t_nums = set(strateji_tahmin_uret_v2(tarihsel_slice, s))
                            log_verisi.append({"Çekiliş No": str(target_row['CekilisNo']), "Strateji": s, "İsabet": len(t_nums & target_nums)})
                return pd.DataFrame(log_verisi)
                
            df_log_hist = cached_tarihsel_log_v2(df, stratejiler_v2)
            
            if not df_log_hist.empty:
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.write("📈 **Yeni Nesil Ortalama Başarı Puanları:**")
                    df_ozet = df_log_hist.groupby("Strateji")["İsabet"].mean().reset_index().sort_values(by="İsabet", ascending=False)
                    df_ozet.columns = ["Strateji", "Tarihsel Log Başarı Ortalaması"]
                    st.dataframe(df_ozet, use_container_width=True)
                with col_g2:
                    fig_trend = px.line(df_log_hist, x="Çekiliş No", y="İsabet", color="Strateji", title="Yeni Nesil Başarı Trend Çizelgesi")
                    st.plotly_chart(fig_trend, use_container_width=True)
                
                df_pivot = df_log_hist.pivot(index="Çekiliş No", columns="Strateji", values="İsabet").sort_index(ascending=False)
                st.dataframe(df_pivot, use_container_width=True)

            st.markdown("---")
            gelecek_no = int(df.iloc[0]['CekilisNo']) + 1
            st.subheader(f"🔮 Bir Sonraki Çekiliş İçin Canlı Kuantum Tahminler (🎯 Hedef Çekiliş No: {gelecek_no})")
            st.write(f"Sistem, **{gelecek_no}** numaralı gelecek tur için 10 yeni nesil kuantum portföyünü üretti:")
            
            for s in stratejiler_v2:
                t = strateji_tahmin_uret_v2(df, s)
                t_html = " ".join([f"<span style='display:inline-block; background-color:#2E7D32; color:white; border-radius:4px; padding:2px 6px; margin:2px; font-size:12px;'>{n}</span>" for n in t])
                st.markdown(f"**{s} Tahmini:**<br>{t_html}", unsafe_allow_html=True)
