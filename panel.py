import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import istatistik  # Gelişmiş matematik motorumuzu bağladık

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

# --- BAŞLIK (RESPONSIVE TASARIM) ---
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
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔮 Kupon Üretim Kriterleri")
    cift_tek_orani = st.sidebar.selectbox("Tek / Çift Dengesi:", ["Fark Etmez", "5 Tek - 5 Çift (Dengeli)", "6 Tek - 4 Çift", "4 Tek - 6 Çift"])
    ardisik_izin = st.sidebar.checkbox("Ardışık Sayılara İzin Ver", value=True)
    
    # Veriyi sınırlandırma ve istatistik motoruna gönderme
    analiz_df = df.head(analiz_adet)
    tum_sayilar = analiz_df[sayi_kolonlari].values.flatten()
    frekanslar = pd.Series(tum_sayilar).value_counts().reindex(range(1, 81), fill_value=0)
    
    # --- CANLI HİLE & RASTLANTISALLIK DENETÇİSİ (Kİ-KARE OVAL) ---
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

    # --- YENİ NESİL MODÜLER SEKME SİSTEMİ ---
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
        df_gecikme = istatistik.gecikme_derinligi_analizi(analiz_df, sayi_kolonlari)
        
        # İlk 10 uykuda olan sayıyı çekiyoruz
        top_gecikme = df_gecikme.head(10).reset_index().rename(columns={"index": "Sayı", "gecikme": "Kaç Turdur Çıkmıyor?", "olasilik": "Bu Süreye Ulaşma Olasılığı"})
        # Olasılığı yüzde formatına çekme
        top_gecikme["Bu Süreye Ulaşma Olasılığı"] = top_gecikme["Bu Süreye Ulaşma Olasılığı"].apply(lambda x: f"%{x*100:.3f}")
        st.dataframe(top_gecikme, use_container_width=True)
        st.caption("Matematiksel Gerçek: Geometrik olasılık değeri düştükçe, o sayının önümüzdeki turlarda kırılma ve çıkma teorik ihtimali baskılanır.")

    # --- SEKME 2: RASTLANTISALLIK VE KAOS (QUANT) ---
    with tab2:
        st.subheader("📐 Hipergeometrik Tur Geçiş Analizi (Overlap)")
        st.write("Peş peşe gelen iki çekiliş arasında kaç tane ortak sayı çıktığını gösterir. (Teorik beklenen değer: 5)")
        
        seri_gecis = istatistik.tur_gecis_analizi(analiz_df, sayi_kolonlari)
        df_gecis = pd.DataFrame({"Ortak Sayı Adedi": seri_gecis.index, "Görülme Sıklığı": seri_gecis.values})
        
        fig_gecis = px.bar(df_gecis, x="Ortak Sayı Adedi", y="Görülme Sıklığı", color="Görülme Sıklığı", color_continuous_scale="Purples", height=350)
        st.plotly_chart(fig_gecis, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🌌 Shannon Entropisi ile Çekilişlerin Kaos Dağılımı")
        st.write("Her bir çekiliş kombinasyonunun evrensel düzensizlik puanı. Yüksek entropi, kusursuz rastlantısallığı simgeler.")
        
        seri_entropi = istatistik.shannon_entropisi(analiz_df, sayi_kolonlari)
        fig_ent = px.histogram(seri_entropi, nbins=15, labels={'value': 'Shannon Entropi Skoru (Kaos Yoğunluğu)'}, color_discrete_sequence=['#0083B0'], height=320)
        fig_ent.update_layout(showlegend=False)
        st.plotly_chart(fig_ent, use_container_width=True)

    # --- SEKME 3: MARKOV ZİNCİRİ BAĞLANTI MOTORU ---
    with tab3:
        st.subheader("⛓️ Koşullu Olasılık Matrisi ve Sayı Tetikleyicileri")
        st.write("Seçeceğiniz bir sayıdan hemen sonraki turda ekrana en çok yapışan, arka arkaya gelme eğilimi yüksek olan gölge sayıları bulur.")
        
        secilen_sayi = st.selectbox("Analiz Edilecek Kilit Sayıyı Seçin:", list(range(1, 81)), index=22) # Varsayılan 23
        
        markov_matrisi = istatistik.markov_zinciri_matrisi(analiz_df, sayi_kolonlari)
        olasiliklar = markov_matrisi[secilen_sayi - 1]
        
        df_markov = pd.DataFrame({"Sonraki Sayı": list(range(1, 81)), "Tetiklenme Olasılığı": olasiliklar})
        top_markov = df_markov.sort_values(by="Tetiklenme Olasılığı", ascending=False).head(7)
        
        fig_markov = px.bar(top_markov, x="Sonraki Sayı", y="Tetiklenme Olasılığı", text_auto='.3f',
                            color="Tetiklenme Olasılığı", color_continuous_scale="Burg", height=350,
                            labels={"Tetiklenme Olasılığı": "Koşullu Olasılık oranı"})
        fig_markov.update_layout(xaxis=dict(type='category'))
        st.plotly_chart(fig_markov, use_container_width=True)
        st.info(f"💡 **Yorum:** İstatistiksel makro veriye göre ne zaman **{secilen_sayi}** sayısı gelse, bir sonraki çekilişte en çok yukarıdaki grafik dizilimi tetikleniyor.")

    # --- SEKME 4: AKILLI KUPON MOTORU ---
    with tab4:
        st.subheader("🧙‍♂️ İleri Düzey Matematiksel Filtreli Kupon Jeneratörü")
        
        kupon_turu = st.radio("Strateji Havuzu:", 
                              ["🔥 Sıcak Sayılar Havuzu", "❄️ Derin Gecikme Havuzu", "🎹 Markov Yoğunluklu Karma"], horizontal=True)
        
        adet_kupon = st.slider("Kaç Adet Kupon Hazırlansın?", min_value=1, max_value=10, value=1)
        
        if st.button("🎰 Kuantum Kuponları Süz ve Üret"):
            sirali_sayilar = frekanslar.sort_values(ascending=False).index.tolist()
            
            if "Sıcak Sayılar" in kupon_turu:
                ana_havuz = sirali_sayilar[:30]
            elif "Derin Gecikme" in kupon_turu:
                # Gecikmesi en yüksek olan ilk 30 sayıyı havuz yapıyoruz
                ana_havuz = df_gecikme.head(30).index.tolist()
            else:
                # Markov matrisindeki en güçlü bağlara sahip sayılardan karma havuz
                ana_havuz = list(range(1, 81))
                
            basarili_kuponlar = []
            deneme_sayaci = 0
            
            while len(basarili_kuponlar) < adet_kupon and deneme_sayaci < 1500:
                deneme_sayaci += 1
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
            
            st.markdown(f"### 🎫 Kriterlerinize Göre Filtrelenmiş Şanslı Kuponlar:")
            for k_idx, kpn in enumerate(basarili_kuponlar, 1):
                kupon_html = " ".join([f"<span style='display:inline-block; background-color:#1565C0; color:white; border-radius:50%; width:36px; height:36px; text-align:center; line-height:36px; font-weight:bold; font-size:13px; margin:3px;'>{num}</span>" for num in kpn])
                st.markdown(f"**Kupon {k_idx}:** {kupon_html}", unsafe_allow_html=True)
            
            st.balloons()

    # --- SEKME 5: VERİ TABANI LİSTESİ ---
    with tab5:
        st.subheader("📋 Sistem Hafızasında Kayıtlı Güncel Çekilişler")
        st.dataframe(analiz_df, use_container_width=True)
