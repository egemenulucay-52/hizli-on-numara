import os

import pandas as pd
import streamlit as st

from analysis.descriptive import (
    block_summary,
    ending_digit_summary,
    number_frequency_summary,
)
from analiz_motoru import ikili_frekans_farki, kombinasyon_ozeti
from veri_modeli import (
    SAYI_KOLONLARI,
    cekilisleri_sirala,
    veri_cercevesini_dogrula,
    veri_cercevesini_normalize_et,
)


st.set_page_config(
    page_title="Hızlı On Numara İstatistik Laboratuvarı",
    page_icon="📊",
    layout="wide",
)

GITHUB_CSV_URL = (
    "https://raw.githubusercontent.com/egemenulucay-52/"
    "hizli-on-numara/main/hizli_on_numara.csv"
)
LOCAL_CSV = "hizli_on_numara.csv"


def read_and_validate_csv(source):
    data = pd.read_csv(source, dtype={"CekilisNo": str})
    data = veri_cercevesini_normalize_et(data)
    veri_cercevesini_dogrula(data)
    data[SAYI_KOLONLARI] = data[SAYI_KOLONLARI].apply(pd.to_numeric)
    return cekilisleri_sirala(data)


@st.cache_data(ttl=300, show_spinner=False)
def load_data(local_path, local_mtime, remote_url):
    del local_mtime  # Yerel dosya değiştiğinde cache anahtarını yeniler.
    if os.path.exists(local_path):
        try:
            return read_and_validate_csv(local_path), "Repo CSV"
        except (OSError, ValueError, pd.errors.ParserError):
            pass

    try:
        return read_and_validate_csv(remote_url), "GitHub raw yedeği"
    except (OSError, ValueError, pd.errors.ParserError):
        return pd.DataFrame(), "Veri yüklenemedi"


@st.cache_data(ttl=600, show_spinner=False)
def cached_number_summary(data, short_window, long_window):
    return number_frequency_summary(
        data,
        SAYI_KOLONLARI,
        short_window=short_window,
        long_window=long_window,
    )


@st.cache_data(ttl=600, show_spinner=False)
def cached_group_summaries(data, window):
    return (
        block_summary(data, SAYI_KOLONLARI, window),
        ending_digit_summary(data, SAYI_KOLONLARI, window),
    )


@st.cache_data(ttl=600, show_spinner=False)
def cached_pair_summary(data):
    return ikili_frekans_farki(data, SAYI_KOLONLARI)


@st.cache_data(ttl=600, show_spinner=False)
def cached_combination_summary(data):
    return kombinasyon_ozeti(data, SAYI_KOLONLARI)


def first_nonempty(row, columns, default="Bilinmiyor"):
    for column in columns:
        value = row.get(column)
        if pd.notna(value) and str(value).strip():
            return str(value)
    return default


def number_badges(numbers):
    return " ".join(
        f"<span style='display:inline-block;background:#E65100;color:white;"
        f"border-radius:999px;min-width:34px;padding:6px 8px;margin:3px;"
        f"text-align:center;font-weight:600'>{number}</span>"
        for number in sorted(numbers)
    )


local_mtime = os.path.getmtime(LOCAL_CSV) if os.path.exists(LOCAL_CSV) else None
df, data_source = load_data(LOCAL_CSV, local_mtime, GITHUB_CSV_URL)

st.title("Hızlı On Numara İstatistik Laboratuvarı")
st.caption("Betimleyici analiz, rastgele model karşılaştırması ve doğrulanabilir araştırma")
st.info(
    "Kanıtlanmış tahmin avantajı bulunamadı. Gösterilen geçmiş sapmalar, "
    "bir sonraki çekilişin olasılığını değiştirmez."
)

if df.empty:
    st.error("Doğrulanabilir çekiliş verisi yüklenemedi.")
    st.stop()

total_draws = len(df)
latest = df.iloc[0]
latest_timestamp = first_nonempty(latest, ["CekilisTarihi", "ToplanmaTarihi"])

st.sidebar.header("Laboratuvar")
page = st.sidebar.radio(
    "Bölüm",
    [
        "Genel Bakış",
        "Keşifsel Analiz",
        "İkili ve Kombinasyonlar",
        "İstatistiksel Kontrol",
        "Veri",
    ],
)

window_candidates = sorted(
    {min(candidate, total_draws) for candidate in (100, 500, 1000, 5000, total_draws)}
)
default_window = min(1000, total_draws)
analysis_window = st.sidebar.select_slider(
    "Analiz penceresi",
    options=window_candidates,
    value=default_window,
    help="Büyük pencereler yalnız seçilen bölümde hesaplanır.",
)
analysis_df = df.head(analysis_window)

st.sidebar.caption(f"Kaynak: {data_source}")
st.sidebar.caption(f"Toplam kayıt: {total_draws:,}")

if page == "Genel Bakış":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam çekiliş", f"{total_draws:,}")
    col2.metric("Son çekiliş", str(latest["CekilisNo"]))
    col3.metric("Analiz penceresi", f"{analysis_window:,}")
    col4.metric("Kombinasyon kapsamı", "2–4")

    st.subheader("Son çekilişteki sayılar")
    latest_numbers = latest[SAYI_KOLONLARI].to_numpy(dtype=int)
    st.markdown(number_badges(latest_numbers), unsafe_allow_html=True)

    st.subheader("Veri durumu")
    actual_draw_time = first_nonempty(latest, ["CekilisTarihi"])
    status = pd.DataFrame(
        {
            "Alan": ["Kaynak", "Son kayıt zamanı", "Gerçek çekiliş zamanı", "Şema"],
            "Değer": [
                data_source,
                latest_timestamp,
                actual_draw_time,
                "Geçerli: 20 benzersiz sayı",
            ],
        }
    )
    st.dataframe(status, hide_index=True, width="stretch")

    st.subheader("Araştırma aşaması")
    st.write(
        "Teorik 80/20 modeli hazır. Betimleyici analizler nötr gözlenen–beklenen "
        "karşılaştırmalarıyla sunuluyor. Simülasyon ve walk-forward backtest "
        "katmanları doğrulandıktan sonra ayrı bölümler olarak eklenecek."
    )

elif page == "Keşifsel Analiz":
    short_max = min(100, analysis_window)
    short_min = min(5, short_max)
    short_window = st.sidebar.slider(
        "Kısa dönem",
        min_value=short_min,
        max_value=short_max,
        value=min(15, short_max),
    )
    long_options = sorted(
        {min(candidate, analysis_window) for candidate in (50, 150, 500, analysis_window)}
    )
    long_window = st.sidebar.select_slider(
        "Uzun dönem",
        options=long_options,
        value=min(150, analysis_window),
    )

    frequency = cached_number_summary(analysis_df, short_window, long_window)
    blocks, endings = cached_group_summaries(analysis_df, min(150, analysis_window))

    st.subheader("Sayı frekansları")
    st.caption(
        "Frequency Momentum = kısa dönem görülme oranı − uzun dönem görülme oranı. "
        "Pozitif değer yalnızca yakın dönemdeki göreli artışı betimler."
    )
    st.bar_chart(frequency.set_index("Number")[["Long Observed"]], height=320)
    st.dataframe(
        frequency.sort_values("Frequency Momentum", ascending=False),
        hide_index=True,
        width="stretch",
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Onluk bloklar: gözlenen ve beklenen")
        st.bar_chart(
            blocks.set_index("Group")[["Observed per Draw", "Expected per Draw"]]
        )
        st.dataframe(blocks, hide_index=True, width="stretch")
    with right:
        st.subheader("Son basamaklar: gözlenen ve beklenen")
        st.bar_chart(
            endings.set_index("Group")[["Observed per Draw", "Expected per Draw"]]
        )
        st.dataframe(endings, hide_index=True, width="stretch")

elif page == "İkili ve Kombinasyonlar":
    st.caption(
        "Bu bölüm seçilene kadar kombinasyon hesapları çalıştırılmaz. Sonuçlar "
        "yalnız geçmiş tekrarları betimler; tahmin sinyali değildir."
    )
    with st.spinner("İkili ve 2–4 kombinasyon özetleri hesaplanıyor..."):
        pair_table = cached_pair_summary(analysis_df)
        combination_table = cached_combination_summary(analysis_df)

    st.subheader("İkili kısa–uzun dönem frekans farkı")
    st.dataframe(pair_table, hide_index=True, width="stretch")
    st.subheader("2–4 kombinasyon tekrar özeti")
    st.dataframe(combination_table, hide_index=True, width="stretch")

elif page == "İstatistiksel Kontrol":
    import istatistik

    st.subheader("Uzun dönem frekans dağılımı")
    with st.spinner("Ki-kare özeti hesaplanıyor..."):
        chi_square, p_value = istatistik.ki_kare_testi(analysis_df, SAYI_KOLONLARI)
    col1, col2 = st.columns(2)
    col1.metric("Ki-kare istatistiği", f"{chi_square:.3f}")
    col2.metric("Ham p-value", f"{p_value:.6f}")
    st.caption(
        "Bu genel uygunluk kontrolü tek başına adalet veya tahmin gücü kanıtlamaz. "
        "Geri koymadan 20 sayı seçilmesi nedeniyle sonuç daha sonra Monte Carlo "
        "referansıyla birlikte raporlanacaktır."
    )

else:
    st.subheader("Doğrulanmış çekiliş verisi")
    display_count = st.sidebar.select_slider(
        "Gösterilecek kayıt",
        options=sorted({min(value, total_draws) for value in (100, 500, 1000)}),
        value=min(500, total_draws),
    )
    st.dataframe(df.head(display_count), hide_index=True, width="stretch")
