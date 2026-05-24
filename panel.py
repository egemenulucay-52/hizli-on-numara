import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import istatistik  # Matematik motorumuz bağlı

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Hızlı On Numara Performans Terminali", layout="wide")

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
st.markdown("<h1 style='text-align: center; font-size: 26px; font-weight: bold;'>🎯 Hızlı On Numara Strateji Validasyon Laboratuvarı</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #888;'>Filtre Performans Takibi ve Tahmin Doğrulama Sistemi</p>", unsafe_allow_html=True)
st.markdown("---")

if df.empty:
    st.error("⚠️ Veri henüz yüklenemedi...")
else:
    sayi_kolonlari = [f"Sayi_{i}" for i in range(1, 21)]
    toplam_cekilis = len(df)
    
    # --- 💥 CACHED HESAPLAMALAR ---
    @st.cache_data(ttl=60)
    def get_mv_analysis(_df):
        df_len = len(_df)
        short_len = min(15, df_len)
        long_len = min(150, df_len)
        short_vals = _df.head(short_len)[sayi_kolonlari].values.flatten()
        long_vals = _df.head(long_len)[sayi_kolonlari].values.flatten()
        short_freq = pd.Series(short_vals).value_counts().reindex(range(1, 81), fill_value=0) / short_len
        long_freq = pd.Series(long_vals).value_counts().reindex(range(1, 81), fill_value=0) / long_len
        macd = short_freq - long_freq
        wake_up = {}
        for num in range(1, 81):
            appears = np.where((_df[sayi_kolonlari] == num).any(axis=1))[0]
            if len(appears) > 1:
                gaps = np.diff(appears)
                wake_up[num] = (appears[0] - np.mean(gaps)) / np.std(gaps) if np.std(gaps) > 0 else 0
            else: wake_up[num] = 0
        return pd.DataFrame({"Sayı": range(1, 81), "MACD": macd.values, "Varyans": [wake_up[n] for n in range(1, 81)]})

    # Analizleri hazırla
    df_mv = get_mv_analysis(df)
    markov_matris = istatistik.markov_zinciri_matrisi(df.head(200), sayi_kolonlari)
    gecikme_df = istatistik.gecikme_derinligi_analizi(df.head(200), sayi_kolonlari)
    
    # --- 🧙 Tahmin Motoru Fonksiyonu ---
    def strateji_tahmin_uret(data_slice, strateji_adi):
        mv = get_mv_analysis(data_slice)
        freq = pd.Series(data_slice[sayi_kolonlari].values.flatten()).value_counts().reindex(range(1, 81), fill_value=0)
        
        havuz = []
        if strateji_adi == "🔥 Sadece Sıcak":
            havuz = freq.sort_values(ascending=False).index[:30].tolist()
        elif strateji_adi == "❄️ Sadece Soğuk":
            havuz = istatistik.gecikme_derinligi_analizi(data_slice, sayi_kolonlari).index[:30].tolist()
        elif strateji_adi == "🚀 Trend Takipçi (MACD)":
            havuz = mv.sort_values(by="MACD", ascending=False)["Sayı"].tolist()[:30]
        elif strateji_adi == "💥 Patlama Adayları (Varyans)":
            havuz = mv.sort_values(by="Varyans", ascending=False)["Sayı"].tolist()[:30]
        elif strateji_adi == "⛓️ Zincir Reaksiyonu (Markov)":
            son_cekilis = data_slice.iloc[0][sayi_kolonlari].values.astype(int)
            probs = np.zeros(80)
            for n in son_cekilis: probs += markov_matris[n-1]
            havuz = (np.argsort(probs)[::-1] + 1).tolist()[:30]
        elif strateji_adi == "💎 Kuantum Hibrit (MACD + Varyans)":
            havuz = list(set(mv.sort_values(by="MACD", ascending=False)["Sayı"].tolist()[:20]) | set(mv.sort_values(by="Varyans", ascending=False)["Sayı"].tolist()[:20]))
        elif strateji_adi == "⚖️ Dengeleyici (Sıcak + Soğuk)":
            havuz = list(set(freq.sort_values(ascending=False).index[:20]) | set(istatistik.gecikme_derinligi_analizi(data_slice, sayi_kolonlari).index[:20]))
        elif strateji_adi == "⚡ Hızlı Tetik (Markov + Sıcak)":
            son_n = data_slice.iloc[0][sayi_kolonlari].values.astype(int)
            probs = np.zeros(80)
            for n in son_n: probs += markov_matris[n-1]
            havuz = list(set((np.argsort(probs)[::-1] + 1).tolist()[:20]) | set(freq.sort_values(ascending=False).index[:20]))
        elif strateji_adi == "🌪️ Kaotik Seçim (Varyans + Markov)":
            havuz = list(set(mv.sort_values(by="Varyans", ascending=False)["Sayı"].tolist()[:20]) | set((np.argsort(np.sum(markov_matris, axis=0))[::-1] + 1).tolist()[:20]))
        else: # Varsayılan: Rastgele Dengeli
            havuz = np.random.choice(range(1,81), 40, replace=False).tolist()
            
        return sorted(np.random.choice(havuz, 20, replace=False).tolist())

    # --- ARAYÜZ SEKMELERİ ---
    tabs = st.tabs(["📊 Genel Analiz", "📈 Trend & Varyans", "⛓️ Markov", "🔮 Manuel Kupon", "📋 Veri", "🏆 Strateji Performans & Tahmin"])
    
    with tabs[5]:
        st.subheader("🏆 Strateji Performans Ölçümü (Backtest Mode)")
        st.write("Sistem, son gerçekleşen çekilişi 'gelecek' sayıp, önceki verilerle 10 stratejiyi yarıştırır.")
        
        if len(df) > 10:
            gercek_sonuc = set(df.iloc[0][sayi_kolonlari].values.astype(int))
            simulasyon_verisi = df.iloc[1:] # Son çekilişi hariç tutarak tahmin yap
            
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
                # Sütun adını f-string dostu 'Isabet' olarak değiştirdik
                perf_sonuclari.append({"Strateji": s, "Isabet": hits, "Tahmin": sorted(list(tahmin))})
            
            df_perf = pd.DataFrame(perf_sonuclari).sort_values(by="Isabet", ascending=False)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write(f"🔍 **Son Gerçekleşen ({df.iloc[0]['CekilisNo']}):**")
                st.markdown(" ".join([f"<span style='color:#FFD700; font-weight:bold;'>{n}</span>" for n in sorted(list(gercek_sonuc))]), unsafe_allow_html=True)
                
                fig_perf = px.bar(df_perf, x="Isabet", y="Strateji", orientation='h', color="Isabet", color_continuous_scale="Viridis")
                fig_perf.update_layout(xaxis_title="İsabet (20'de)") # Grafikte düzgün görünmesi için başlığı elgöz kararı düzelttik
                st.plotly_chart(fig_perf, use_container_width=True)
            
            with c2:
                st.write("📊 **Strateji Detayları ve İsabetli Sayılar:**")
                for _, row in df_perf.iterrows():
                    hit_nums = sorted(list(set(row['Tahmin']) & gercek_sonuc))
                    hit_txt = ", ".join(map(str, hit_nums)) if hit_nums else "Yok"
                    # f-string içindeki o tehlikeli ters eğik çizgi (\) tamamen kaldırıldı:
                    st.markdown(f"**{row['Strateji']}:** {row['Isabet']} İsabet → `{hit_txt}`")

            st.markdown("---")
            st.subheader("🔮 Bir Sonraki Çekiliş İçin Canlı Tahminler (Next Round)")
            st.write("Yukarıdaki performanslara göre en güvendiğin stratejiyi seçebilirsin. Henüz gerçekleşmemiş çekiliş için 20'lik listeler:")
            
            canli_tahminler = []
            for s in stratejiler:
                t = strateji_tahmin_uret(df, s)
                t_html = " ".join([f"<span style='display:inline-block; background-color:#2E7D32; color:white; border-radius:4px; padding:2px 6px; margin:2px; font-size:12px;'>{n}</span>" for n in t])
                st.markdown(f"**{s}:**<br>{t_html}", unsafe_allow_html=True)

    # (Diğer sekmelerin kodları buraya gelecek - Eski kodun tab kısımlarını buraya yapıştırabilirsin)
    # Performans için sadece tabs[5]'i yeni ekledim, diğer analizleri koruyoruz.
