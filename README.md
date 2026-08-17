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
                    │              │
                    ▼              ▼
             grup_analizi.py    panel.py
                    │              │
                    ▼              ▼
       grup_raporu.md / CSV   Streamlit Community Cloud
```

- `veri_modeli.py`: CSV şeması, doğrulama ve çekiliş sıralaması.
- `analysis/model.py`: 80/20 teorik olasılık modeli ve beklenen değerler.
- `analysis/descriptive.py`: Frekans, blok ve son basamak betimleyici özetleri.
- `analiz_motoru.py`: Geçiş sürecinde panel ve rapor tarafından paylaşılan eski analizler.
- `istatistik.py`: Ki-kare, gecikme, geçiş matrisi ve sayı aralığı entropisi.
- `veri_cekici.py`: API birincil kaynak, Selenium yedek kaynak.
- `grup_analizi.py`: İkili–dörtlü kombinasyon ve grup raporu üretimi. Beşli ve altılı kombinasyon hesaplanmaz.
- `panel.py`: Yalnız seçilen bölümü hesaplayan hafif Streamlit giriş dosyası.

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
2. Ham CSV değişmediyse rapor hesapları atlanır.
3. Veri değiştiyse grup raporu yeniden üretilir.
4. Yalnız CSV ve rapor dosyaları `main` dalına yazılır.

`.github/workflows/ci.yml`, Python veya bağımlılık dosyaları değiştiğinde testleri çalıştırır.

## Test

```bash
python -m unittest discover -s tests -v
```

Testler; CSV doğrulamasını, API fallback akışını, zaman ayrıştırmasını, Markov yönünü, teorik 80/20 modelini, betimleyici analizleri, tüm Streamlit bölümlerinin açılışını ve kombinasyon kapsamının 2–4 ile sınırlı kalmasını denetler.
