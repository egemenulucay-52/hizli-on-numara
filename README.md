# Hızlı On Numara İstatistik Paneli

Hızlı On Numara sonuçlarını GitHub Actions ile toplayan, doğrulayan ve Streamlit üzerinde betimleyici istatistikler ile deneysel strateji karşılaştırmaları sunan uygulama.

> Paneldeki skorlar kazanma garantisi veya gelecek çekiliş olasılığı değildir. Gecikme, frekans ve birlikte çıkma verileri geçmiş sonuçları betimler.

## Mimari

```text
Milli Piyango API
        │ başarısız/geçersiz cevap
        └──────────────► Selenium yedeği
                         │
                         ▼
                  veri_cekici.py
                         │ şema doğrulama + atomik yazım
                         ▼
                hizli_on_numara.csv
                 │        │          │
                 ▼        ▼          ▼
        grup_analizi.py  tahmin_guncelle.py  panel.py
                 │        │ hash zincirli    │
                 ▼        ▼                  ▼
       grup raporu   canlı tahmin günlüğü  Streamlit Community Cloud
```

- `veri_modeli.py`: CSV şeması, doğrulama ve çekiliş sıralaması.
- `analysis/model.py`: 80/20 teorik olasılık modeli ve beklenen değerler.
- `analysis/descriptive.py`: Frekans, blok ve son basamak betimleyici özetleri.
- `analysis/strategies.py`: M1–M6 deneysel sayı skorları.
- `analysis/ensemble.py`: Robust skor normalizasyonu ve sabit ağırlıklı ensemble.
- `analysis/backtest.py`: Look-ahead korumalı, eski→yeni walk-forward motoru.
- `analysis/benchmark.py`: Exact random Hit@N beklentileri.
- `analysis/tail_metrics.py`: Exact/NearPerfect oranları, güven aralıkları,
  binom/Monte Carlo kontrolleri ve çoklu test düzeltmesi.
- `analysis/research_backtest.py`: M1–M10 için son 1.000 ardışık hedefte
  look-ahead korumalı araştırma turnuvası.
- `analysis/prediction_ledger.py`: Canlı tahminlerin eklemeli ve SHA-256
  zincirli olay günlüğü.
- `analiz_motoru.py`: Geçiş sürecinde panel ve rapor tarafından paylaşılan eski analizler.
- `istatistik.py`: Ki-kare, gecikme, geçiş matrisi ve sayı aralığı entropisi.
- `veri_cekici.py`: API birincil kaynak, Selenium yedek kaynak.
- `grup_analizi.py`: İkili–dörtlü kombinasyon ve grup raporu üretimi. Beşli ve altılı kombinasyon hesaplanmaz.
- `panel.py`: Yalnız seçilen bölümü hesaplayan hafif Streamlit giriş dosyası.

## Araştırma modelleri

- `M4-A`–`M4-F`: Standart, zaman ağırlıklı, Bayesian yumuşatılmış,
  çoklu-lag, yalnız güçlü geçiş ve güvenilirlik ağırlıklı geçiş varyantları.
- `M7`: Set@4/5/6'yı ortak amaç fonksiyonuyla seçen deterministik beam search.
- `M8`: Bayesian koşullu model.
- `M9`: Pair–triple hypergraph set modeli; triple keşiflerinde FDR kontrolü.
- `M10`: Yalnız hedef görüldükten sonra güncellenen L2 düzenlemeli çevrimiçi
  lojistik sıralama.

Araştırma turnuvası 15 dakikalık Streamlit açılışında yeniden hesaplanmaz.
Panel, repoda saklanan sonuç artefaktlarını okur. Exact 4/4, 5/5, 6/6 ile
Nearly Perfect eşikleri rastgele hypergeometric benchmark, güven aralığı ve
q-value ile birlikte raporlanır. Mevcut araştırma sonucunda istatistiksel olarak
desteklenen tarihsel avantaj yoktur; Ensemble v2 yeterli canlı gözlem oluşana
kadar kapalıdır.

## Veri şeması

| Kolon | Anlamı |
| --- | --- |
| `CekilisTarihi` | Kaynaktan alınabilen gerçek çekiliş zamanı. Eski kayıtlarda boş olabilir. |
| `ToplanmaTarihi` | Sonucun bot tarafından CSV'ye alındığı İstanbul zamanı. |
| `CekilisNo` | Çekiliş kimliği. |
| `Sayi_1`–`Sayi_20` | 1–80 aralığında 20 benzersiz sonuç. |

## Yerel çalıştırma

Python 3.12 kullanılır.

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m streamlit run panel.py
```

Veri toplayıcı için ayrıca:

```bash
python -m pip install -r requirements-bot.txt
python veri_cekici.py
```

Tarihsel walk-forward sonuçlarını yeniden üretmek için:

```bash
python backtest_uret.py --last 0 --minimum-training 500
```

Çıktılar `artifacts/backtest_results.csv` ve `artifacts/backtest_summary.csv`
dosyalarına yazılır. Yalnız ardışık `N → N+1` hedefleri değerlendirilir; eksik
çekilişlerin üzerinden geçiş veya geriye dönük canlı tahmin üretilmez.

M1–M10 araştırma turnuvasını yeniden üretmek için:

```bash
python research_backtest_uret.py --last 1000
```

Canlı günlüğü yerelde idempotent olarak güncellemek için:

```bash
python tahmin_guncelle.py
```

Komut önce sonucu gelen bekleyen tahmini değerlendirir, ardından yalnız mevcut
son çekilişin bir sonrasına tahmin yazar. Kaçırılmış geçmiş çekilişlere tahmin
eklemez. Günlük `artifacts/prediction_ledger.jsonl` dosyasındadır; her olay bir
önceki olayın özetini taşıdığı için geçmiş kayıt değişiklikleri doğrulanabilir.

## Streamlit Community Cloud

1. GitHub deposunu Streamlit Community Cloud hesabına bağlayın.
2. Giriş dosyası olarak `panel.py` seçin.
3. Python sürümünü gelişmiş ayarlardan `3.12` seçin.
4. Uygulama bağımlılıkları kökteki `requirements.txt` üzerinden kurulur.
5. Proje ayarları `.streamlit/config.toml` içinden okunur.

Streamlit uygulaması GitHub'daki `main` dalı güncellendiğinde yeniden dağıtılır. Uygulamanın çalışması için Render servisi gerekmez.

## Otomasyon

`.github/workflows/bot.yml` yaklaşık 15 dakikalık aralıklarla çalışır. GitHub zamanlanmış işleri geciktirebilir.

1. Veri çekici çalışır.
2. Ham CSV değişmediyse grup raporu hesapları atlanır.
3. Veri değiştiyse grup raporu yeniden üretilir.
4. Canlı tahmin günlüğü her çalışmada idempotent olarak güncellenir.
5. CSV, grup raporu ve değişmişse tahmin günlüğü `main` dalına yazılır.

`.github/workflows/ci.yml`, Python veya bağımlılık dosyaları değiştiğinde testleri çalıştırır.

## Test

```bash
python -m unittest discover -s tests -v
```

Testler; CSV doğrulamasını, API fallback akışını, zaman ayrıştırmasını, Markov
yönünü, teorik 80/20 modelini, betimleyici analizleri, look-ahead korumasını,
eksik çekiliş geçişlerini, tüm Streamlit bölümlerinin açılışını ve kombinasyon
kapsamının 2–4 ile sınırlı kalmasını; ayrıca M4–M10 modellerinin deterministik
davranışını, temporal fold ayrımını ve canlı günlük hash zincirini denetler.
