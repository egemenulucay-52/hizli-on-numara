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
    
    st.sidebar.header("⚙️ Analiz Kapsamı")
    analiz_adet = st.sidebar.slider("Kaç Çekiliş İncelensin?", min_value=5, max_value=max(toplam_cekilis, 10), value=max(toplam_cekilis, 5))
    
    analiz_df = df.head(analiz_adet)
    tum_sayilar = analiz_df[sayi_kolonlari].values.flatten()
    frekanslar = pd.Series(tum_sayilar).value_counts().reindex(range(1, 81), fill_value=0)
    
    # --- 💥 GELİŞMİŞ ÖNBELLEK MOTORU ---
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
    def cached_macd_ve_varyans_analizi(_df):
        df_len = len(_df)
        short_len = min(15, df_len)
        long_len = min(150, df_len)
        
        short_vals = _df.head(short_len)[sayi_kolonlari].values.flatten()
        long_vals = _df.head(long_len)[sayi_kolonlari].values.flatten()
        
        short_freq = pd.Series(short_vals).value_counts().reindex(range(1, 81), fill_value=0) / short_len
        long_freq = pd.Series(long_vals).value_counts().reindex(range(1, 81), fill_value=0) / long_len
        
        macd_scores = short_freq - long_freq
        wake_up_scores, mean_gaps, std_gaps, current_gaps = {}, {}, {}, {}
        
        for num in range(1, 81):
            appears = np.where((_df[sayi_kolonlari] == num).any(axis=1))[0]
            if len(appears) > 1:
                gaps = np.diff(appears)
                mean_g = float(np.mean(gaps))
                std_g = float(np.std(gaps)) if len(gaps) > 1 else 1.0
                curr_g = float(appears[0])
                wake_up = (curr_g - mean_g) / std_g if std_g > 0 else 0.0
            else:
                mean_g, std_g, wake_up = 4.0, 2.0, 0.0
                curr_g = float(appears[0]) if len(appears) > 0 else float(df_len)
                
            wake_up_scores[num] = wake_up
            mean_gaps[num] = mean_g
            std_gaps[num] = std_g
            current_gaps[num] = curr_g
            
        return pd.DataFrame({
            "Sayı": range(1, 81),
            "MACD_Skoru": macd_scores.values,
            "Mevcut_Gecikme": [current_gaps[n] for n in range(1, 81)],
            "Ortalama_Dongu": [mean_gaps[n] for n in range(1, 81)],
            "Standart_Sapma": [std_gaps[n] for n in range(1, 81)],
            "Varyans_Gerilimi": [wake_up_scores[n] for n in range(1, 81)]
        })
    
    # Hesaplama çağrıları
    df_gecikme = cached_gecikme_analizi(analiz_df)
    df_mv = cached_macd_ve_varyans_analizi(df)
    markov_matrisi = cached_markov_zinciri_matrisi(analiz_df)
    
    chi2_stat, p_value = istatistik.ki_kare_testi(analiz_df, sayi_kolonlari)
    if p_value > 0.05:
        st.success(f"🎲 **Rastlantısallık Denetimi:** Sistem %95 güvenilirlikle tamamen adil ve rastgele çalışıyor. (p-değeri: {p_value:.4f})")
    else:
        st.warning(f"⚠️ **Rastlantısallık Sapması:** Sayı dağılımlarında teorik sınırın dışında kümelenmeler saptandı! (p-değeri: {p_value:.4f})")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🔥 En Sıcak Sayı", value=f"Sayı: {frekanslar.idxmax()}", delta=f"{frekanslar.max()} Kez Çıktı")
    with col2:
        st.metric(label="❄️ En Soğuk Sayı", value=f"Sayı: {frekanslar.idxmin()}", delta=f"{frekanslar.min()} Kez Çıktı", delta_color="inverse")
    with col3:
        st.metric(label="🎰 Son Çekiliş No", value=f"No: {df.iloc[0]['CekilisNo']}")

    # --- SIKINTISIZ 7'Lİ SEKME SİSTEMİ ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Frekans & Gecikme", 
        "🧠 Rastlantısallık & Kaos", 
        "📈 Trend & Varyans (Lag-3 Çözümü)", 
        "⛓️ Markov Zinciri", 
        "🔮 Akıllı Kupon Motoru", 
        "📋 Canlı Veri Havuzu",
        "🏆 Strateji Performans & Tahmin"
    ])
    
    # --- TAB 1 ---
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

    # --- TAB 2 ---
    with tab2:
        st.subheader("📈 Veri Kümesinin Merkezi Eğilim ve Ortalamalar Analizi")
        aritmetik_ort = float(np.mean(tum_sayilar))
        geometrik_ort = float(np.exp(np.mean(np.log(tum_sayilar))))
        medyan_deger = float(np.median(tum_sayilar))
        
        c_ort1, c_ort2, c_ort3 = st.columns(3)
        with c_ort1:
            st.metric(label="🧮 Genel Aritmetik Ortalama", value=f"{aritmetik_ort:.2f}", delta=f"{aritmetik_ort - 40.50:+.2f} (Teorik Sapma)")
        with c_ort2:
            st.metric(label="📐 Genel Geometrik Ortalama", value=f"{geometrik_ort:.2f}")
        with c_ort3:
            st.metric(label="⚖️ Olasılık Dengesi (Medyan)", value=f"{medyan_deger:.1f}")
            
        st.markdown("---")
        st.subheader("📐 Hipergeometrik Tur Geçiş Analizi (Overlap)")
        seri_gecis = cached_tur_gecis_analizi(analiz_df)
        df_gecis = pd.DataFrame({"Ortak Sayı Adedi": seri_gecis.index, "Görülme Sıklığı": seri_gecis.values})
        fig_gecis = px.bar(df_gecis, x="Ortak Sayı Adedi", y="Görülme Sıklığı", color="Görülme Sıklığı", color_continuous_scale="Purples", height=350)
        st.plotly_chart(fig_gecis, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🌌 Shannon Entropisi ile Çekilişlerin Kaos Dağılımı")
        seri_entropi = cached_shannon_entropisi(analiz_df)
        fig_ent = px.histogram(seri_entropi, nbins=15, labels={'value': 'Shannon Entropi Skoru (Kaos Yoğunluğu)'}, color_discrete_sequence=['#0083B0'], height=320)
        fig_ent.update_layout(showlegend=False)
        st.plotly_chart(fig_ent, use_container_width=True)

    # --- TAB 3 ---
    with tab3:
        st.subheader("📊 Strateji 2: Loto MACD Trend ve Momentum Analizi")
        st.write("Son 15 çekilişin ivmesi ile son 150 çekilişin makro frekansı kıyaslanır. Skoru pozitif ve yüksek olanlar yükselen trenddedir.")
        
        top_macd = df_mv.sort_values(by="MACD_Skoru", ascending=False).head(15)
        fig_macd = px.bar(top_macd, x="Sayı", y="MACD_Skoru", color="MACD_Skoru", color_continuous_scale="Reds", height=320)
        fig_macd.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_macd, use_container_width=True)
        
        st.markdown("---")
        st.subheader("⚖️ Strateji 3: Varyans Gerilimi ve Esneklik Denge Sınırı")
        st.write("Gerilim puanı yüksek (2.0 ve üzeri) olan sayılar varyans sınırlarını aşırı esnetmişlerdir ve patlamaya hazırdır.")
        
        top_varyans = df_mv.sort_values(by="Varyans_Gerilimi", ascending=False).head(15)
        fig_var = px.bar(top_varyans, x="Sayı", y="Varyans_Gerilimi", color="Varyans_Gerilimi", color_continuous_scale="solar", height=320)
        fig_var.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_var, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 İki Stratejinin Birleşik Veri Matrisi")
        st.dataframe(df_mv.sort_values(by="Varyans_Gerilimi", ascending=False), use_container_width=True)

    # --- TAB 4 ---
    with tab4:
        st.subheader("⛓️ Koşullu Olasılık Matrisi ve Sayı Tetikleyicileri")
        secilen_sayi = st.selectbox("Analiz Edilecek Kilit Sayıyı Seçin:", list(range(1, 81)), index=22)
        olasiliklar = markov_matrisi[secilen_sayi - 1]
        df_markov = pd.DataFrame({"Sonraki Sayı": list(range(1, 81)), "Tetiklenme Olasılığı": olasiliklar})
        top_markov = df_markov.sort_values(by="Tetiklenme Olasılığı", ascending=False).head(7)
        fig_markov = px.bar(top_markov, x="Sonraki Sayı", y="Tetiklenme Olasılığı", text_auto='.3f', color="Tetiklenme Olasılığı", color_continuous_scale="Burg", height=350)
        fig_markov.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_markov, use_container_width=True)

    # --- TAB 5 ---
    with tab5:
        st.subheader("🧙‍♂️ İleri Düzey Bağımsız Filtreli Kupon Jeneratörü")
        adet_kupon = st.slider("Kaç Sıra Kupon Üretilsin?", min_value=1, max_value=5, value=3)
        kupon_ayarlari = []
        
        st.markdown("---")
        for k in range(1, adet_kupon + 1):
            with st.expander(f"⚙️ Kupon Sıra {k} Özel Ayarları", expanded=True):
                col_sayi, col_filtre = st.columns([1, 2])
                with col_sayi:
                    s_adedi = st.slider(f"Kupon {k} Kaç Sayıdan Oluşsun?", min_value=1, max_value=10, value=10, key=f"sayi_{k}")
                with col_filtre:
                    filtreler = st.multiselect(
                        f"Kupon {k} İçin Uygulanacak Süzgeçler (Çoklu Seçim):",
                        [
                            "🔥 Sıcak Sayılar Havuzu (En Çok Çıkan İlk 30 Sayı)",
                            "❄️ Derin Gecikme Havuzu (En Uzun Süredir Çıkmayan İlk 30 Sayı)",
                            "📈 MACD İvme Havuzu (Trendi En Yüksek İlk 30 Sayı) 🚀",
                            "⚖️ Varyans Gerilim Havuzu (Patlamaya En Yakın İlk 30 Sayı) 💥",
                            "⛓️ Markov Yoğunluklu Karma (Son Çekilişin Tetiklediği En Güçlü Sayılar)",
                            "☯️ Dengeli Tek / Çift Filtresi (Sayıları Yarı Yarıya Oranlar)",
                            "📏 Ardışık Sayı Yasağı (Kuponda Yan Yana Sayıları Engeller)",
                            "🌌 Shannon Kaos Standardı (Sayı Dağılımının İdeal Entropide Olmasını Şart Koşar)"
                        ],
                        default=["📈 MACD İvme Havuzu (Trendi En Yüksek İlk 30 Sayı) 🚀"],
                        key=f"filtre_{k}"
                    )
                kupon_ayarlari.append({"sıra": k, "sayi_adedi": s_adedi, "filtreler": filtreler})
        
        st.markdown("---")
        if st.button("🎰 Tüm Kuponları Kendi Kriterleriyle Süz ve Üret"):
            with st.spinner("🔮 Kuantum süzgeçler hesaplanıyor..."):
                st.markdown(f"### 🎫 Süzülmüş Özel Kupon Portföyünüz:")
                
                for ayar in kupon_ayarlari:
                    k_idx = ayar["sıra"]
                    s_adedi = ayar["sayi_adedi"]
                    filtreler = ayar["filtreler"]
                    
                    aday_havuz = list(range(1, 81))
                    havuz_listeleri = []
                    
                    if "🔥 Sıcak Sayılar Havuzu (En Çok Çıkan İlk 30 Sayı)" in filtreler:
                        havuz_listeleri.append(frekanslar.sort_values(ascending=False).index.tolist()[:30])
                    if "❄️ Derin Gecikme Havuzu (En Uzun Süredir Çıkmayan İlk 30 Sayı)" in filtreler:
                        havuz_listeleri.append(df_gecikme.head(30).index.tolist())
                    if "📈 MACD İvme Havuzu (Trendi En Yüksek İlk 30 Sayı) 🚀" in filtreler:
                        havuz_listeleri.append(df_mv.sort_values(by="MACD_Skoru", ascending=False)["Sayı"].tolist()[:30])
                    if "⚖️ Varyans Gerilim Havuzu (Patlamaya En Yakın İlk 30 Sayı) 💥" in filtreler:
                        havuz_listeleri.append(df_mv.sort_values(by="Varyans_Gerilimi", ascending=False)["Sayı"].tolist()[:30])
                    if "⛓️ Markov Yoğunluklu Karma (Son Çekilişin Tetiklediği En Güçlü Sayılar)" in filtreler:
                        son_cekilis_sayilari = df.iloc[0][sayi_kolonlari].values.astype(int)
                        toplam_olasiliklar = np.zeros(80)
                        for num in son_cekilis_sayilari:
                            toplam_olasiliklar += markov_matrisi[num - 1]
                        en_iyi_markov = (np.argsort(toplam_olasiliklar)[::-1] + 1).tolist()[:30]
                        havuz_listeleri.append(en_iyi_markov)
                    
                    if havuz_listeleri:
                        aday_havuz = list(set([num for sublist in havuz_listeleri for num in sublist]))
                        if len(aday_havuz) < s_adedi: aday_havuz = list(range(1, 81))
                    
                    kupon_bulundu = False
                    deneme_sayaci = 0
                    
                    while deneme_sayaci < 1200:
                        deneme_sayaci += 1
                        aday_kupon = sorted(np.random.choice(aday_havuz, s_adedi, replace=False).tolist())
                        
                        if "☯️ Dengeli Tek / Çift Filtresi (Sayıları Yarı Yarıya Oranlar)" in filtreler:
                            tekler = [n for n in aday_kupon if n % 2 != 0]
                            ciftler = [n for n in aday_kupon if n % 2 == 0]
                            if abs(len(tekler) - len(ciftler)) > 2: continue
                        
                        if "📏 Ardışık Sayı Yasağı (Kuponda Yan Yana Sayıları Engeller)" in filtreler:
                            has_ardisik = False
                            for idx in range(len(aday_kupon) - 1):
                                if aday_kupon[idx+1] - aday_kupon[idx] == 1:
                                    has_ardisik = True
                                    break
                            if has_ardisik: continue
                        
                        if "🌌 Shannon Kaos Standardı (Sayı Dağılımının İdeal Entropide Olmasını Şart Koşar)" in filtreler and s_adedi > 3:
                            farklar = np.diff(aday_kupon)
                            toplam_fark = farklar.sum()
                            if toplam_fark > 0:
                                p = farklar / toplam_fark
                                p = p[p > 0]
                                entropi = -np.sum(p * np.log2(p))
                                max_ent = np.log2(len(farklar))
                                if entropi < (max_ent * 0.75): continue
                        
                        kupon_html = " ".join([f"<span style='display:inline-block; background-color:#1565C0; color:white; border-radius:50%; width:36px; height:36px; text-align:center; line-height:36px; font-weight:bold; font-size:13px; margin:3px;'>{num}</span>" for num in aday_kupon])
                        st.markdown(f"**Sıra {k_idx} ({s_adedi} Sayı):** {kupon_html}", unsafe_allow_html=True)
                        kupon_bulundu = True
                        break
                    
                    if not kupon_bulundu:
                        st.error(f"❌ **Sıra {k_idx}:** Uygun kupon üretilemedi.")
                st.balloons()

    # --- TAB 6 ---
    with tab6:
        st.subheader("📋 Sistem Hafızasında Kayıtlı Güncel Çekilişler")
        st.dataframe(analiz_df, use_container_width=True)

    # --- 🧙 TAHMİN MOTORU YARDIMCI FONKSİYONU ---
    def strateji_tahmin_uret(data_slice, strateji_adi):
        mv_slice = cached_macd_ve_varyans_analizi(data_slice)
        freq_slice = pd.Series(data_slice[sayi_kolonlari].values.flatten()).value_counts().reindex(range(1, 81), fill_value=0)
        
        havuz = []
        if strateji_adi == "🔥 Sadece Sıcak":
            havuz = freq_slice.sort_values(ascending=False).index[:30].tolist()
        elif strateji_adi == "❄️ Sadece Soğuk":
            havuz = istatistik.gecikme_derinligi_analizi(data_slice, sayi_kolonlari).index[:30].tolist()
        elif strateji_adi == "🚀 Trend Takipçi (MACD)":
            havuz = mv_slice.sort_values(by="MACD_Skoru", ascending=False)["Sayı"].tolist()[:30]
        elif strateji_adi == "💥 Patlama Adayları (Varyans)":
            havuz = mv_slice.sort_values(by="Varyans_Gerilimi", ascending=False)["Sayı"].tolist()[:30]
        elif strateji_adi == "⛓️ Zincir Reaksiyonu (Markov)":
            son_cekilis = data_slice.iloc[0][sayi_kolonlari].values.astype(int)
            probs = np.zeros(80)
            for n in son_cekilis: probs += markov_matrisi[n-1]
            havuz = (np.argsort(probs)[::-1] + 1).tolist()[:30]
        elif strateji_adi == "💎 Kuantum Hibrit (MACD + Varyans)":
            havuz = list(set(mv_slice.sort_values(by="MACD_Skoru", ascending=False)["Sayı"].tolist()[:20]) | set(mv_slice.sort_values(by="Varyans_Gerilimi", ascending=False)["Sayı"].tolist()[:20]))
        elif strateji_adi == "⚖️ Dengeleyici (Sıcak + Soğuk)":
            havuz = list(set(freq_slice.sort_values(ascending=False).index[:20]) | set(istatistik.gecikme_derinligi_analizi(data_slice, sayi_kolonlari).index[:20]))
        elif strateji_adi == "⚡ Hızlı Tetik (Markov + Sıcak)":
            son_n = data_slice.iloc[0][sayi_kolonlari].values.astype(int)
            probs = np.zeros(80)
            for n in son_n: probs += markov_matrisi[n-1]
            havuz = list(set((np.argsort(probs)[::-1] + 1).tolist()[:20]) | set(freq_slice.sort_values(ascending=False).index[:20]))
        elif strateji_adi == "🌪️ Kaotik Seçim (Varyans + Markov)":
            havuz = list(set(mv_slice.sort_values(by="Varyans_Gerilimi", ascending=False)["Sayı"].tolist()[:20]) | set((np.argsort(np.sum(markov_matrisi, axis=0))[::-1] + 1).tolist()[:20]))
        else:
            havuz = np.random.choice(range(1,81), 40, replace=False).tolist()
            
        return sorted(np.random.choice(havuz, 20, replace=False).tolist())

    # --- TAB 7 (STRATEJİ PERFORMANS SİMÜLATÖRÜ) ---
    with tab7:
        st.subheader("🏆 Strateji Performans Ölçümü (Backtest Mode)")
        st.write("Sistem, son gerçekleşen çekilişi 'gelecek' sayıp, önceki verilerle 10 stratejiyi yarıştırır.")
        
        if len(df) > 10:
            gercek_sonuc = set(df.iloc[0][sayi_kolonlari].values.astype(int))
            simulasyon_verisi = df.iloc[1:]
            
            stratejiler = [
                "🔥 Sadece Sıcak", "❄️ Sadece Soğuk", "🚀 Trend Takipçi (MACD)", 
                "💥 Patlama Adayları (Varyans)", "⛓️ Zincir Reaksiyonu (Markov)", 
                "💎 Kuantum Hibrit (MACD + Varyans)", "⚖️ Dengeleyici (Sıcak + Soğuk)", 
                "⚡ Hızlı Tetik (Markov + Sıcak)", "🌪️ Kaotik Seçim (Varyans + Markov)", "🎰 Saf Olasılık (Random)"
            ]
            
            perf_sonuclari = []
            for s in stratejiler:
                tahmin = set(strateji_tahmin_uret(simulasyon_verisi, s))
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
            st.subheader("🔮 Bir Sonraki Çekiliş İçin Canlı Tahminler (Next Round)")
            st.write("Henüz gerçekleşmemiş çekiliş için 20'lik kuantum tahmin listeleri:")
            
            for s in stratejiler:
                t = strateji_tahmin_uret(df, s)
                t_html = " ".join([f"<span style='display:inline-block; background-color:#2E7D32; color:white; border-radius:4px; padding:2px 6px; margin:2px; font-size:12px;'>{n}</span>" for n in t])
                st.markdown(f"**{s}:**<br>{t_html}", unsafe_allow_html=True)
