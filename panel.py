import os

import pandas as pd
import streamlit as st

from analysis.config import AnalysisConfig, MODEL_NAMES
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
BACKTEST_RESULTS = "artifacts/backtest_results.csv"
BACKTEST_SUMMARY = "artifacts/backtest_summary.csv"
BACKTEST_TAIL_SUMMARY = "artifacts/backtest_tail_summary.csv"


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


@st.cache_data(show_spinner=False)
def load_backtest_artifacts(results_path, results_mtime, summary_path, summary_mtime):
    del results_mtime, summary_mtime
    try:
        return pd.read_csv(results_path), pd.read_csv(summary_path)
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_tail_summary(path, modified_time):
    del modified_time
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame()


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
        "Model Karşılaştırma",
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

elif page == "Model Karşılaştırma":
    results_mtime = os.path.getmtime(BACKTEST_RESULTS) if os.path.exists(BACKTEST_RESULTS) else None
    summary_mtime = os.path.getmtime(BACKTEST_SUMMARY) if os.path.exists(BACKTEST_SUMMARY) else None
    tail_mtime = (
        os.path.getmtime(BACKTEST_TAIL_SUMMARY)
        if os.path.exists(BACKTEST_TAIL_SUMMARY)
        else None
    )
    backtest, backtest_summary = load_backtest_artifacts(
        BACKTEST_RESULTS, results_mtime, BACKTEST_SUMMARY, summary_mtime
    )
    tail_summary = load_tail_summary(BACKTEST_TAIL_SUMMARY, tail_mtime)

    st.subheader("Tarihsel walk-forward model karşılaştırması")
    st.caption(
        "Her hedef yalnız önceki verilerle skorlandı. Historical Walk-Forward sonuçları "
        "canlı performans değildir ve altılı kombinasyon hesabı yapılmaz."
    )
    if backtest.empty or backtest_summary.empty or tail_summary.empty:
        st.warning("Önceden hesaplanmış backtest çıktısı bulunamadı.")
        st.stop()

    available_windows = backtest_summary["Window"].drop_duplicates().tolist()
    selected_window = st.sidebar.selectbox(
        "Performans penceresi",
        available_windows,
        index=available_windows.index("Last 250") if "Last 250" in available_windows else 0,
    )
    primary_objective = st.sidebar.selectbox(
        "Birincil hedef",
        [
            "Exact 6/6",
            "NearPerfect 5+/6",
            "Exact 5/5",
            "NearPerfect 4+/5",
            "Exact 4/4",
            "NearPerfect 3+/4",
            "Mean Hit@6",
            "Mean Hit@5",
            "Mean Hit@4",
        ],
    )
    selection_size = int(primary_objective[-1])
    model_options = [*MODEL_NAMES, "Ensemble"]
    selected_models = st.sidebar.multiselect(
        "Karşılaştırılacak modeller",
        model_options,
        default=["M1", "M3", "M4", "Ensemble"],
    )
    if not selected_models:
        st.info("En az bir model seçin.")
        st.stop()

    ranking = backtest_summary[
        (backtest_summary["Window"] == selected_window)
        & (backtest_summary["Model"].isin(selected_models))
    ].copy()
    tail_window = tail_summary[
        (tail_summary["Window"] == selected_window)
        & (tail_summary["Model"].isin(selected_models))
    ].copy()

    overview = ranking[["Model", "Evaluation Count", "Mean Hit@6", "Lift@6"]].copy()
    for size in (4, 5, 6):
        exact = tail_window[
            (tail_window["Objective"] == "Exact")
            & (tail_window["Selection Size"] == size)
        ].set_index("Model")
        near = tail_window[
            (tail_window["Objective"] == "NearPerfect")
            & (tail_window["Selection Size"] == size)
        ].set_index("Model")
        overview[f"Exact {size}/{size} Count"] = overview["Model"].map(exact["Observed Count"])
        overview[f"Exact {size}/{size} Rate"] = overview["Model"].map(exact["Observed Rate"])
        overview[f"Exact {size}/{size} Lift"] = overview["Model"].map(exact["Lift"])
        overview[f"NearPerfect@{size} Rate"] = overview["Model"].map(near["Observed Rate"])
    exact6 = tail_window[
        (tail_window["Objective"] == "Exact")
        & (tail_window["Selection Size"] == 6)
    ].set_index("Model")
    overview["Significance Status"] = overview["Model"].map(exact6["Evidence Status"])

    if primary_objective.startswith("Mean Hit"):
        overview = overview.sort_values(f"Mean Hit@{selection_size}", ascending=False)
    else:
        objective_name = "Exact" if primary_objective.startswith("Exact") else "NearPerfect"
        objective_rows = tail_window[
            (tail_window["Objective"] == objective_name)
            & (tail_window["Selection Size"] == selection_size)
        ][["Model", "Lift CI Low", "Lift"]]
        overview = overview.merge(objective_rows, on="Model", how="left").sort_values(
            ["Lift CI Low", "Lift"], ascending=False
        )

    window_row_count = {
        "All": len(backtest),
        "Last 25": 25,
        "Last 50": 50,
        "Last 100": 100,
        "Last 250": 250,
    }.get(selected_window, len(backtest))
    chart_source = backtest.tail(min(window_row_count, len(backtest))).reset_index(drop=True)
    rolling_period = min(50, len(chart_source))
    rolling = pd.DataFrame({"Evaluation": chart_source.index + 1})
    for model in selected_models:
        rolling[model] = chart_source[f"{model} Hit@{selection_size}"].rolling(
            rolling_period, min_periods=1
        ).mean()
    rolling["Random Benchmark"] = selection_size * 0.25
    if len(rolling) > 2500:
        rolling = rolling.iloc[::((len(rolling) + 2499) // 2500)]

    tabs = st.tabs(
        ["Araştırma Özeti", "Perfect Hit", "Nearly Perfect", "Tail Grafikleri", "Mean Hit ve Detay"]
    )
    with tabs[0]:
        st.subheader("Model seçim dashboardu")
        st.caption(
            "Sıralama seçilen hedefte lift alt güven sınırını önceleyerek tekil şanslı "
            "sonuçların liderliği ele geçirmesini sınırlar."
        )
        numeric = overview.select_dtypes(include="number").columns
        overview[numeric] = overview[numeric].round(6)
        st.dataframe(overview, hide_index=True, width="stretch")
        if not (tail_window["Evidence Status"] == "Statistically supported historical signal").any():
            st.info("Seçilen pencerede istatistiksel olarak desteklenen tarihsel avantaj yok.")

    leaderboard_columns = [
        "Model", "Evaluation Count", "Observed Count", "Expected Count",
        "Observed Rate", "Random Rate", "Lift", "Lift CI Low", "Lift CI High",
        "Exact p-value", "q-value", "Evidence Status",
    ]
    with tabs[1]:
        st.subheader("Perfect Hit Leaderboard")
        for size, tab in zip((4, 5, 6), st.tabs(["4/4", "5/5", "6/6"])):
            with tab:
                table = tail_window[
                    (tail_window["Objective"] == "Exact")
                    & (tail_window["Selection Size"] == size)
                ][leaderboard_columns].sort_values(["Lift CI Low", "Lift"], ascending=False)
                st.dataframe(table.round(6), hide_index=True, width="stretch")

    with tabs[2]:
        st.subheader("Nearly Perfect Leaderboard")
        for size, tab in zip((4, 5, 6), st.tabs(["≥3/4", "≥4/5", "≥5/6"])):
            with tab:
                table = tail_window[
                    (tail_window["Objective"] == "NearPerfect")
                    & (tail_window["Selection Size"] == size)
                ][leaderboard_columns].sort_values(["Lift CI Low", "Lift"], ascending=False)
                st.dataframe(table.round(6), hide_index=True, width="stretch")

    with tabs[3]:
        st.subheader(f"Rolling NearPerfect@{selection_size} Rate")
        tail_chart = pd.DataFrame({"Evaluation": chart_source.index + 1})
        for model in selected_models:
            tail_chart[model] = (
                chart_source[f"{model} Hit@{selection_size}"] >= selection_size - 1
            ).rolling(rolling_period, min_periods=1).mean()
        near_random = tail_window[
            (tail_window["Objective"] == "NearPerfect")
            & (tail_window["Selection Size"] == selection_size)
        ].iloc[0]["Random Rate"]
        tail_chart["Random Benchmark"] = near_random
        if len(tail_chart) > 2500:
            tail_chart = tail_chart.iloc[::((len(tail_chart) + 2499) // 2500)]
        st.line_chart(tail_chart.set_index("Evaluation"), height=330)

        st.subheader(f"Cumulative Exact {selection_size}/{selection_size}")
        cumulative = pd.DataFrame({"Evaluation": chart_source.index + 1})
        for model in selected_models:
            cumulative[model] = (
                chart_source[f"{model} Hit@{selection_size}"] == selection_size
            ).cumsum()
        exact_random = tail_window[
            (tail_window["Objective"] == "Exact")
            & (tail_window["Selection Size"] == selection_size)
        ].iloc[0]["Random Rate"]
        cumulative["Random Expected"] = cumulative["Evaluation"] * exact_random
        if len(cumulative) > 2500:
            cumulative = cumulative.iloc[::((len(cumulative) + 2499) // 2500)]
        st.line_chart(cumulative.set_index("Evaluation"), height=330)

    descriptions = {
        "M1": "Kısa ve uzun dönem görülme oranı farkı.",
        "M2": "Teorik %25 görülme oranından standartlaştırılmış sapma.",
        "M3": "Son çekilişteki sayılarla beklenene göre pair ilişkisi.",
        "M4": "Geçmişten geleceğe koşullu transition sapması.",
        "M5": "Gambler's fallacy kullanmayan yakınlık/recency skoru.",
        "M6": "Onluk blok ve son basamak yoğunluğu skoru.",
        "Ensemble": "Sabit ağırlıklı M1-M6 birleşimi.",
    }
    with tabs[4]:
        st.subheader(f"Rolling Mean Hit@{selection_size}")
        st.line_chart(rolling.set_index("Evaluation"), height=330)
        detail_model = st.selectbox("Model detayı", selected_models)
        st.write(descriptions[detail_model])
        config = AnalysisConfig()
        detail_summary = ranking[ranking["Model"] == detail_model].iloc[0]
        left, right, third = st.columns(3)
        left.metric("Son Top 6", backtest.iloc[-1][f"{detail_model} Top6"])
        right.metric(f"Mean Hit@{selection_size}", f"{detail_summary[f'Mean Hit@{selection_size}']:.3f}")
        third.metric(f"Lift@{selection_size}", f"{detail_summary[f'Lift@{selection_size}']:.3f}")
        st.caption(
            f"Strategy {config.strategy_version} · Config {config.config_version} · "
            f"minimum eğitim {config.minimum_training_size}"
        )
        st.dataframe(
            chart_source[[
                "Target Draw", f"{detail_model} Top6", f"{detail_model} Hit@4",
                f"{detail_model} Hit@5", f"{detail_model} Hit@6",
            ]].tail(10),
            hide_index=True,
            width="stretch",
        )

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
