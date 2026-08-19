import os

import pandas as pd
import streamlit as st

from analysis.model_registry import MODEL_DESCRIPTIONS, RESEARCH_MODEL_NAMES
from analysis.prediction_ledger import pending_predictions, read_ledger
from analysis.research_protocol import (
    load_protocol,
    load_protocol_amendment,
    load_split_manifest,
)
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
RESEARCH_RESULTS = "artifacts/research_backtest_results.csv"
RESEARCH_SUMMARY = "artifacts/research_backtest_summary.csv"
RESEARCH_TAIL_SUMMARY = "artifacts/research_tail_summary.csv"
PREDICTION_LEDGER = "artifacts/prediction_ledger.jsonl"


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


@st.cache_data(show_spinner=False)
def load_prediction_events(path, modified_time):
    del modified_time
    try:
        return read_ledger(path), ""
    except (OSError, ValueError) as error:
        return [], str(error)


@st.cache_data(show_spinner=False)
def load_research_protocol(protocol_mtime, amendment_mtime, manifest_mtime):
    del protocol_mtime, amendment_mtime, manifest_mtime
    try:
        protocol = load_protocol()
        amendment = load_protocol_amendment(protocol=protocol)
        return protocol, amendment, load_split_manifest(), ""
    except (OSError, ValueError) as error:
        return {}, {}, pd.DataFrame(), str(error)


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
        "Araştırma Protokolü",
        "Canlı Tahmin",
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
        value=min(10, short_max),
    )
    long_options = sorted(
        {min(candidate, analysis_window) for candidate in (50, 150, 500, analysis_window)}
    )
    long_window = st.sidebar.select_slider(
        "Uzun dönem",
        options=long_options,
        value=min(50, analysis_window),
    )

    frequency = cached_number_summary(analysis_df, short_window, long_window)
    blocks, endings = cached_group_summaries(analysis_df, min(150, analysis_window))

    st.subheader("Sayı frekansları")
    st.caption(
        "Frequency Momentum = kısa dönem görülme oranı − uzun dönem görülme oranı. "
        "Varsayılan pencereler 10/50'dir. Pozitif değer yalnızca yakın dönemdeki "
        "göreli artışı betimler; tahmin avantajı kanıtlamaz."
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

elif page == "Araştırma Protokolü":
    protocol_path = "protocols/research_protocol_v1.json"
    amendment_path = "protocols/research_protocol_v1_amendment_001.json"
    manifest_path = "artifacts/research_split_manifest.csv"
    protocol, amendment, manifest, protocol_error = load_research_protocol(
        os.path.getmtime(protocol_path) if os.path.exists(protocol_path) else None,
        os.path.getmtime(amendment_path) if os.path.exists(amendment_path) else None,
        os.path.getmtime(manifest_path) if os.path.exists(manifest_path) else None,
    )
    st.subheader("Research Protocol v1")
    st.caption(
        "Bu ekran yalnız protokolü ve hedef sayılarını gösterir. Kilitli bölümün "
        "sonuçları hesaplanmaz veya panelden okunmaz."
    )
    if protocol_error:
        st.error(f"Araştırma protokolü doğrulanamadı: {protocol_error}")
        st.stop()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Protokol",
        f"{protocol['protocol_version']} + ek {amendment['amendment_version']}",
    )
    col2.metric("Durum", "Seçim protokolü kilitli")
    col3.metric("Final model", "Henüz kilitlenmedi")
    col4.metric("Kilitli hedef", f"{protocol['splits']['retrospective_locked_candidate']['eligible_target_count']:,}")

    phase_labels = {
        "training_history": "Eğitim geçmişi",
        "historical_development": "Development",
        "historical_validation": "Validation",
        "retrospective_locked_candidate": "Retrospective locked candidate",
        "historical_contaminated": "Bilinen kontamine kuyruk",
        "ineligible_nonconsecutive": "Uygun olmayan / ardışık değil",
    }
    access_labels = {
        "training_history": "Eğitim için açık",
        "historical_development": "Açık",
        "historical_validation": "Tek model seçimi için açık",
        "retrospective_locked_candidate": "KİLİTLİ — değerlendirme yok",
        "historical_contaminated": "Yalnız keşifsel",
        "ineligible_nonconsecutive": "Hedef değil",
    }
    rows = []
    for phase, group in manifest.groupby("Phase", sort=False):
        rows.append(
            {
                "Bölüm": phase_labels[phase],
                "Kayıt": len(group),
                "Uygun hedef": int(group["EligibleTarget"].astype(bool).sum()),
                "İlk çekiliş": group.iloc[0]["DrawID"],
                "Son çekiliş": group.iloc[-1]["DrawID"],
                "Erişim": access_labels[phase],
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.info(
        "Final model kilidinden önce onaylanan ek 001 ile canlı Research 2.1 "
        "frekans pencereleri kısa=10, uzun=50 ve sapma=50 olarak değiştirildi. "
        "Decay=100 ve yapısal pencere=50 değişmedi."
    )
    st.warning(
        "Kilitli tarihsel bölüm, modellerin geçmişin tamamı geliştirme sırasında "
        "görülmüş olduğu için yalnız geriye dönük dayanıklılık denetimi sayılır. "
        "Gerçek doğrulayıcı kanıt final model kilidinden sonraki canlı tahminlerdir."
    )
    st.code(
        f"protocol={protocol['protocol_hash']}\n"
        f"amendment={amendment['amendment_hash']}",
        language=None,
    )

elif page == "Canlı Tahmin":
    ledger_mtime = (
        os.path.getmtime(PREDICTION_LEDGER)
        if os.path.exists(PREDICTION_LEDGER)
        else None
    )
    events, ledger_error = load_prediction_events(PREDICTION_LEDGER, ledger_mtime)
    st.subheader("Canlı tahmin günlüğü")
    st.caption(
        "Bu bölüm yalnız önceden kaydedilmiş, zaman damgalı tahminleri gösterir. "
        "Tarihsel backtest ve canlı sonuçlar kesin olarak ayrı tutulur."
    )
    if ledger_error:
        st.error(f"Tahmin günlüğü doğrulanamadı: {ledger_error}")
        st.stop()
    created = [event for event in events if event.get("event_type") == "prediction_created"]
    evaluated = [
        event for event in events if event.get("event_type") == "prediction_evaluated"
    ]
    if not created:
        st.info("Henüz zaman damgalı canlı tahmin oluşturulmadı.")
        st.stop()

    pending = pending_predictions(events)
    displayed = pending[-1] if pending else created[-1]
    status = "Sonuç bekleniyor" if displayed in pending else "Değerlendirildi"
    phase_labels = {
        "protocol_v1_observational_prelock": "Protokol v1 · gözlemsel ön-kilit",
        "prospective_live_confirmatory": "Protokol v1 · ileriye dönük doğrulama",
    }
    displayed_phase = phase_labels.get(
        displayed.get("evaluation_phase"), "Protokol öncesi canlı kayıt"
    )
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Hedef çekiliş", displayed["target_draw"])
    col2.metric("Eğitim sonu", displayed["train_end_draw"])
    col3.metric("Durum", status)
    col4.metric("Canlı değerlendirme", len(evaluated))
    col5.metric("Araştırma fazı", displayed_phase)
    if displayed.get("research_version") == "2.1.0":
        st.caption("Aktif canlı konfigürasyon: Research 2.1 · kısa=10 · uzun=50 · sapma=50")
    else:
        st.caption(
            "Gösterilen kayıt legacy Research 2.0 olabilir. İlk uygun yeni tahmin "
            "Research 2.1 ve 10/50 pencereleriyle oluşturulacaktır."
        )

    research_results_mtime = (
        os.path.getmtime(RESEARCH_SUMMARY) if os.path.exists(RESEARCH_SUMMARY) else None
    )
    _, research_summary = load_backtest_artifacts(
        RESEARCH_RESULTS,
        os.path.getmtime(RESEARCH_RESULTS) if os.path.exists(RESEARCH_RESULTS) else None,
        RESEARCH_SUMMARY,
        research_results_mtime,
    )
    reference_model = "M4-F"
    if not research_summary.empty:
        historical_all = research_summary[research_summary["Window"] == "All"]
        if not historical_all.empty:
            reference_model = historical_all.sort_values(
                ["Mean Hit@6", "Model"], ascending=[False, True]
            ).iloc[0]["Model"]

    st.info(
        f"Kontamine tarihsel kuyrukta ortalama Hit@6 lideri **{reference_model}** "
        "yalnız keşifsel görüntüleme referansıdır; final model seçimi değildir."
    )
    reference = displayed["models"].get(reference_model)
    if reference:
        st.markdown(f"**{reference_model} · kayıtlı Set@6**")
        st.markdown(number_badges(reference["set_at_6"]), unsafe_allow_html=True)

    with st.expander("Tüm kayıtlı model tahminleri", expanded=True):
        prediction_rows = []
        for model in RESEARCH_MODEL_NAMES:
            selections = displayed["models"].get(model)
            if selections is None:
                continue
            prediction_rows.append(
                {
                    "Model": model,
                    "Set@4": " ".join(map(str, selections["set_at_4"])),
                    "Set@5": " ".join(map(str, selections["set_at_5"])),
                    "Set@6": " ".join(map(str, selections["set_at_6"])),
                    "Yaklaşım": MODEL_DESCRIPTIONS[model],
                }
            )
        st.dataframe(pd.DataFrame(prediction_rows), hide_index=True, width="stretch")

    st.subheader("Canlı değerlendirme geçmişi")
    if not evaluated:
        st.caption(
            "İlk hedef henüz sonuçlanmadı. Bu alan sonuç geldikten sonra canlı "
            "Hit@4/5/6 değerlerini gösterecek."
        )
    else:
        created_by_hash = {
            event.get("event_hash"): event for event in created if event.get("event_hash")
        }
        live_model = st.selectbox(
            "Canlı performansı gösterilecek model",
            list(RESEARCH_MODEL_NAMES),
            index=list(RESEARCH_MODEL_NAMES).index(reference_model),
        )
        live_rows = []
        for event in evaluated:
            result = event["results"].get(live_model)
            if result is None:
                continue
            source_event = created_by_hash.get(event.get("created_event_hash"), {})
            live_rows.append(
                {
                    "Hedef": event["target_draw"],
                    "Faz": phase_labels.get(
                        source_event.get("evaluation_phase"), "Protokol öncesi"
                    ),
                    "Gerçek sayılar": " ".join(map(str, event["actual_numbers"])),
                    "Hit@4": result["hit_at_4"],
                    "Hit@5": result["hit_at_5"],
                    "Hit@6": result["hit_at_6"],
                    "Exact 6/6": result["exact_6"],
                    "NearPerfect ≥5/6": result["nearperfect_6"],
                }
            )
        st.dataframe(pd.DataFrame(live_rows), hide_index=True, width="stretch")

    with st.expander("Günlük bütünlüğü"):
        st.write(
            f"{len(events)} olay · zincir doğrulandı · son olay özeti "
            f"`{events[-1]['event_hash']}`"
        )
        st.caption(
            "Olaylar önceki olayın SHA-256 özetini taşır. Kayıt silme veya geçmiş "
            "tahmini değiştirme zincir doğrulamasını bozar."
        )

elif page == "Model Karşılaştırma":
    results_path = RESEARCH_RESULTS
    summary_path = RESEARCH_SUMMARY
    tail_path = RESEARCH_TAIL_SUMMARY
    results_mtime = os.path.getmtime(results_path) if os.path.exists(results_path) else None
    summary_mtime = os.path.getmtime(summary_path) if os.path.exists(summary_path) else None
    tail_mtime = (
        os.path.getmtime(tail_path)
        if os.path.exists(tail_path)
        else None
    )
    backtest, backtest_summary = load_backtest_artifacts(
        results_path, results_mtime, summary_path, summary_mtime
    )
    tail_summary = load_tail_summary(tail_path, tail_mtime)

    st.subheader("Tarihsel walk-forward model karşılaştırması")
    st.caption(
        "Bu ekran yalnız daha önce görülmüş 1.000 hedeflik kontamine kuyruğu "
        "keşifsel olarak gösterir (48702–49859). Kilitli tarihsel bölüm ve tam tarih "
        "backtesti panelden erişilebilir değildir. Altılı kombinasyon uzayı taranmaz."
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
        "Keşifsel sıralama ölçütü",
        [
            "Mean Hit@6",
            "Mean Hit@5",
            "Mean Hit@4",
            "Exact 6/6",
            "NearPerfect 5+/6",
            "Exact 5/5",
            "NearPerfect 4+/5",
            "Exact 4/4",
            "NearPerfect 3+/4",
        ],
    )
    selection_size = int(primary_objective[-1])
    model_options = list(RESEARCH_MODEL_NAMES)
    default_models = ["M4-F", "M7", "M8", "M9", "M10"]
    selected_models = st.sidebar.multiselect(
        "Karşılaştırılacak modeller",
        model_options,
        default=default_models,
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

    overview = ranking[
        [
            "Model",
            "Evaluation Count",
            "Mean Hit@4",
            "Lift@4",
            "Mean Hit@5",
            "Lift@5",
            "Mean Hit@6",
            "Lift@6",
        ]
    ].copy()
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

    with tabs[4]:
        st.subheader(f"Rolling Mean Hit@{selection_size}")
        st.line_chart(rolling.set_index("Evaluation"), height=330)
        detail_model = st.selectbox("Model detayı", selected_models)
        st.write(MODEL_DESCRIPTIONS[detail_model])
        detail_summary = ranking[ranking["Model"] == detail_model].iloc[0]
        set_column = f"{detail_model} Set@6"
        left, right, third = st.columns(3)
        left.metric("Son Set@6", backtest.iloc[-1][set_column])
        right.metric(f"Mean Hit@{selection_size}", f"{detail_summary[f'Mean Hit@{selection_size}']:.3f}")
        third.metric(f"Lift@{selection_size}", f"{detail_summary[f'Lift@{selection_size}']:.3f}")
        st.caption(
            "Legacy Research 2.0 · 15/150 pencereleri · kontamine son 1.000 "
            "ardışık hedef · yalnız keşifsel. Canlı Research 2.1, 10/50 kullanır."
        )
        st.dataframe(
            chart_source[[
                "Target Draw", set_column, f"{detail_model} Hit@4",
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
