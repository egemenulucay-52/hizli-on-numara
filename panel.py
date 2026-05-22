import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import os
import random

st.set_page_config(page_title="Hızlı On Numara Veri Mühendisliği", layout="wide")

st.title("🎯 Hızlı On Numara Veri Mühendisliği & Gelişmiş Analitik")
st.markdown("Standart istatistiklerin ötesinde, olasılık teorisi ve ardışık kombinasyon analizleri.")

CSV_DOSYASI = "gecmis_hizli_on_numara.csv" 
if not os.path.isfile(CSV_DOSYASI):
    CSV_DOSYASI = "hizli_on_numara.csv"

if os.path.isfile(CSV_DOSYASI):
    df = pd.read_csv(CSV_DOSYASI)
    
    # Sol panel
    st.sidebar.header("🎛 Veri Derinliği")
    secenek = st.sidebar.selectbox(
        "Zaman aralığı:",
        ["Son 10 Çekiliş", "Son 50 Çekiliş", "Son 100 Çekiliş", "Tüm Geçmiş Veriler"]
    )
    
    if secenek == "Son 10 Çekiliş":
        analiz_df = df.head(10)
    elif secenek == "Son 50 Çekiliş":
        analiz_df = df.head(50)
    elif secenek == "Son 100 Çekiliş":
        analiz_df = df.head(100)
    else:
        analiz_df = df

    # Sayı havuzlama ve temizleme
    toplam_sayilar = []
    sayi_sutunlari = [f"Sayi_{i}" for i in range(1, 21)]
    satir_sayilari_listesi = []
    
    for index, row in analiz_df.iterrows():
        guncel_satir = []
        for sutun in sayi_sutunlari:
            if sutun in analiz_df.columns and pd.notna(row[sutun]):
                try:
                    val = int(pd.to_numeric(row[sutun]))
                    toplam_sayilar.append(val)
                    guncel_satir.append(val)
                except: pass
        guncel_satir.sort()
        if len(guncel_satir) == 20:
            satir_sayilari_listesi.append(guncel_satir)

    sayi_frekanslari = Counter(toplam_sayilar)
    for i in range(1, 81):
        if i not in sayi_frekanslari: sayi_frekanslari[i] = 0

    grafik_df = pd.DataFrame(sayi_frekanslari.items(), columns=["Sayı", "Çıkma Adedi"]).sort_values(by="Çıkma Adedi", ascending=False)
    
    # --- ÖZGÜN ANALİZ 1: ARDIŞIK SAYI İKİZLERİ ANALİZİ ---
    ardisik_ikililer = []
    for satir in satir_sayilari_listesi:
        for i in range(len(satir) - 1):
            if satir[i+1] - satir[i] == 1:
                ardisik_ikililer.append((satir[i], satir[i+1]))
                
    ikili_frekans = Counter(ardisik_ikililer)
    en_cok_ardisik = pd.DataFrame(
        [(f"{k[0]}-{k[1]}", v) for k, v in ikili_frekans.items()],
        columns=["Ardışık Çift", "Görülme Sıklığı"]
    ).sort_values(by="Görülme Sıklığı", ascending=False).head(10)

    # --- ÖZGÜN ANALİZ 2: SEKTÖR (ÇEYREK MATRİS) ANALİZİ ---
    ceyrek_A = sum(1 for x in toplam_sayilar if 1 <= x <= 20)
    ceyrek_B = sum(1 for x in toplam_sayilar if 21 <= x <= 40)
    ceyrek_C = sum(1 for x in toplam_sayilar if 41 <= x <= 60)
    ceyrek_D = sum(1 for x in toplam_sayilar if 61 <= x <= 80)

    # =========================================================
    # 🎯 GELİŞMİŞ KOLON MÜHENDİSİ (YENİ FİLTRELER EKLENDİ)
    # =========================================================
    st.header("🎯 Çoklu Strateji Tabanlı Kupon Jeneratörü")
    
    with st.form("kupon_formu"):
        kolon_datalari = []
        for sira in range(1, 6):
            st.markdown(f"#### 🏷️ Sıra {sira} Strateji Ayarları")
            c1, c2 = st.columns([1, 2])
            with c1:
                s_adet = st.slider(f"Sayı Adedi:", min_value=3, max_value=10, value=10, key=f"adet_{sira}")
            with c2:
                s_filtreler = st.multiselect(
                    f"Olasılık Filtreleri Kombinasyonu:",
                    [
                        "🔥 Sıcak Sayılar (En Çok Çıkanlar)", 
                        "❄️ Soğuk Sayılar (En Az Çıkanlar)", 
                        "🔗 Ardışık Gelme İhtimali Yüksek Sayılar",
                        "⚖️ Sadece Tek Sayılar", 
                        "⚖️ Sadece Çift Sayılar",
                        "📐 Üst Sektör Yoğunluklu (41-80)"
                    ],
                    default=["🔥 Sıcak Sayılar (En Çok Çıkanlar)"],
                    key=f"filtre_{sira}"
                )
            kolon_datalari.append({"sira": sira, "adet": s_adet, "filtreler": s_filtreler})
            st.markdown("<div style='border-bottom: 1px dashed #444; margin: 10px 0;'></div>", unsafe_allow_html=True)
            
        uret_butonu = st.form_submit_button("🔮 ÖZEL ALGORTİMAYLA KUPONLARI HESAPLA", use_container_width=True)

    if uret_butonu:
        st.subheader("📋 Algoritmik Olarak Üretilen Kupon:")
        
        for kl in kolon_datalari:
            sira_no = kl["sira"]
            hedef_adet = kl["adet"]
            secilen_filtreler = kl["filtreler"]
            
            havuz = list(range(1, 81))
            ağırlıklar = []
            
            for s in havuz:
                frekans = sayi_frekanslari.get(s, 0)
                skor = 1
                
                if "🔥 Sıcak Sayılar (En Çok Çıkanlar)" in secilen_filtreler:
                    skor += frekans
                if "❄️ Soğuk Sayılar (En Az Çıkanlar)" in secilen_filtreler:
                    skor += (max(sayi_frekanslari.values()) - frekans)
                if "🔗 Ardışık Gelme İhtimali Yüksek Sayılar" in secilen_filtreler:
                    # En popüler ardışık çiftlerin içindeki sayıların skorunu yükselt
                    populer_sayilar = []
                    for pair, _ in ikili_frekans.most_common(5):
                        populer_sayilar.extend(pair)
                    if s in populer_sayilar: skor *= 5
                if "⚖️ Sadece Tek Sayılar" in secilen_filtreler:
                    if s % 2 != 0: skor *= 3
                    else: skor = 0
                if "⚖️ Sadece Çift Sayılar" in secilen_filtreler:
                    if s % 2 == 0: skor *= 3
                    else: skor = 0
                if "📐 Üst Sektör Yoğunluklu (41-80)" in secilen_filtreler:
                    if 41 <= s <= 80: skor *= 4
                    else: skor = 0
                    
                ağırlıklar.append(skor)
            
            if sum(ağırlıklar) == 0: ağırlıklar = [1] * 80
                
            üretilen_kolon = []
            while len(üretilen_kolon) < hedef_adet:
                secilen = random.choices(havuz, weights=ağırlıklar, k=1)[0]
                if secilen not in üretilen_kolon:
                    üretilen_kolon.append(secilen)
            üretilen_kolon.sort()
            
            # Kupon Kalite Skoru Hesaplama (Ortalamanın 40.5'e yakınlığı üzerinden)
            kolon_ortalaması = sum(üretilen_kolon) / len(üretilen_kolon)
            kalite_skoru = max(0, 100 - int(abs(kolon_ortalaması - 40.5) * 2.5))
            
            top_html = "".join([f'<span style="background-color:#ffd166; color:black; border-radius:50%; padding:8px 12px; margin-right:8px; font-weight:bold; display:inline-block; min-width:38px; text-align:center;">{x}</span>' for x in üretilen_kolon])
            st.markdown(f"**Sıra {sira_no}:** {top_html} | 📈 *Matematiksel Denge Skoru: %{kalite_skoru}* ", unsafe_allow_html=True)

    st.markdown("---")

    # --- GÖRSEL ŞÖLEN: YENİ NESİL YORUM GRAFİKLERİ ---
    st.header("🔬 İleri Düzey Veri Metrikleri")
    
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        st.subheader("🔗 En Çok Yan Yana Gelen Sayı İkizleri")
        st.markdown("*Geçmiş çekilişlerde birbirini en çok çeken ardışık sayı kombinasyonları.*")
        if not en_cok_ardisik.empty:
            fig_ardisik = px.bar(en_cok_ardisik, x="Ardışık Çift", y="Görülme Sıklığı", color="Görülme Sıklığı", color_continuous_scale="Tealgrn")
            st.plotly_chart(fig_ardisik, use_container_width=True)
        else:
            st.info("Yeterli veri biriktiğinde ardışık analizi burada görünecek.")

    with g_col2:
        st.subheader("📐 Sektör (Çeyrek Matris) Dağılımı")
        st.markdown("*1-80 sayı tablosunun hangi bölgesinden daha çok top seçiliyor?*")
        fig_radar = go.Figure(data=go.Scatterpolar(
          r=[ceyrek_A, ceyrek_B, ceyrek_C, ceyrek_D],
          theta=['A Çeyreği (1-20)', 'B Çeyreği (21-40)', 'C Çeyreği (41-60)', 'D Çeyreği (61-80)'],
          fill='toself',
          line_color='#6f42c1'
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False, height=380)
        st.plotly_chart(fig_radar, use_container_width=True)

else:
    st.error("⚠ Analiz edilecek veri dosyası bulunamadı!")
