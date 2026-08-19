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
- `analysis/research_backtest.py`: M1–M10 için kesin hedef listesi kabul eden,
  look-ahead ve kilitli bölüm erişim korumalı araştırma motoru.
- `analysis/research_protocol.py`: Research Protocol v1 hash doğrulaması,
  kronolojik split manifesti ve locked holdout erişim koruması.
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

## Research Protocol v1

Protokol, geçmiş hedefleri kronolojik ve değiştirilemez bir manifestle ayırır:

| Bölüm | Uygun hedef | Kullanım |
| --- | ---: | --- |
| Development | 5.921 | Yöntem geliştirme |
| Validation | 2.960 | Tam bir final model seçme |
| Retrospective locked candidate | 5.922 | Standart araçlara kapalı; sonuç üretilmez |
| Bilinen kontamine kuyruk | 1.000 | Yalnız keşifsel panel ve geçmiş karşılaştırma |

`protocols/research_protocol_v1.json` protokol kararlarını, konfigürasyon
hash'lerini ve birincil ölçüt olan Mean Hit@6'yı sabitler.
`protocols/research_protocol_v1_amendment_001.json`, final model kilidinden önce
onaylanan 10/50 frekans denemesini ana protokol hash'ine bağlar.
`artifacts/research_split_manifest.csv` her çekilişin fazını taşır. Mevcut
modeller geliştirilirken geçmişin tamamı daha önce görüldüğü için kilitli bölüm
yalnız retrospective audit/backcast sayılır; gerçek confirmatory değerlendirme,
final model kilidinden sonraki canlı tahminlerle başlayacaktır.

Aktif canlı Research 2.1 ayarları:

- M1 kısa frekans: son 10 çekiliş.
- M1 uzun frekans: son 50 çekiliş.
- M2 teorik frekans sapması: son 50 çekiliş.
- M6 yapısal pencere: 50 çekiliş; değişmedi.
- M4-B decay yarılanma ömrü: 100 çekiliş; değişmedi.

Repodaki 1.000 hedeflik tarihsel araştırma artefaktları Research 2.0 ve 15/150
ayarlarıyla üretildiğinden legacy/keşifsel olarak etiketlenir. 10/50 değişikliği
bu sonuçların üzerine yazılmaz ve locked holdout üzerinde çalıştırılmaz.

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

M1–M10 araştırma sonuçlarını izinli bir bölüm için yeniden üretmek için:

```bash
python research_backtest_uret.py --split development
python research_backtest_uret.py --split validation
python research_backtest_uret.py --split contaminated
```

Development ve validation çıktıları sırasıyla
`artifacts/protocol_v1/development` ve `artifacts/protocol_v1/validation`
altına yazılır. Kontamine kuyruk mevcut panel artefaktlarını günceller.
`retrospective_locked_candidate` bilinçli olarak komut seçeneklerinde yoktur;
genel backtest motoru da bu hedef kimliklerini reddeder. Yalnız ardışık
`N → N+1` hedefleri değerlendirilir.

Canlı günlüğü yerelde idempotent olarak güncellemek için:

```bash
python tahmin_guncelle.py
```

Komut önce sonucu gelen bekleyen tahmini değerlendirir, ardından yalnız mevcut
son çekilişin bir sonrasına tahmin yazar. Kaçırılmış geçmiş çekilişlere tahmin
eklemez. Günlük `artifacts/prediction_ledger.jsonl` dosyasındadır; her olay bir
önceki olayın özetini taşıdığı için geçmiş kayıt değişiklikleri doğrulanabilir.
Final model kilitlenene kadar yeni kayıtlar
`protocol_v1_observational_prelock` olarak etiketlenir ve confirmatory sayılmaz.
Research 2.0 M10 ağırlıkları Research 2.1 özellikleriyle karıştırılmaz; yeni
konfigürasyon eşleşen bir state oluşana kadar temiz M10 durumuyla başlar.

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
