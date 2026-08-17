import numpy as np
import pandas as pd

def ki_kare_testi(df, sayi_kolonlari):
    """Sayı frekanslarının eşit dağılımdan sapmasını Pearson ki-kare testiyle ölçer."""
    import scipy.stats as stats

    tum_sayilar = df[sayi_kolonlari].values.flatten()
    gözlemlenen, _ = np.histogram(tum_sayilar, bins=range(1, 82))
    
    # Teorik olarak her sayının eşit çıkması beklenir
    toplam_top = len(tum_sayilar)
    beklenen = np.full(80, toplam_top / 80)
    
    chi2_stat, p_value = stats.chisquare(gözlemlenen, f_exp=beklenen)
    return float(chi2_stat), float(p_value)

def gecikme_derinligi_analizi(df, sayi_kolonlari):
    """Sayıların kaç turdur çıkmadığını ve bu gecikmeye ulaşma olasılığını hesaplar."""
    son_cekilisler = df[sayi_kolonlari].values
    gecikmeler = {}
    
    for sayi in range(1, 81):
        gecikme = 0
        for tur in son_cekilisler:
            if sayi in tur:
                break
            gecikme += 1
        # Bir sayı her çekilişte 20/80=0.25 olasılıkla yer alır. En az bu kadar
        # çekiliş boyunca görülmeme olasılığı P(X >= gecikme) = 0.75**gecikme'dir.
        teorik_olasilik = 0.75 ** gecikme
        gecikmeler[sayi] = {"gecikme": gecikme, "olasilik": teorik_olasilik}
        
    return pd.DataFrame(gecikmeler).T.sort_values(by="gecikme", ascending=False)

def markov_zinciri_matrisi(df, sayi_kolonlari):
    """Yeni->eski sıralı veriden eski çekilişten yeni çekilişe geçiş matrisi kurar."""
    son_cekilisler = df[sayi_kolonlari].values
    matris = np.zeros((80, 80))
    
    for idx in range(len(son_cekilisler) - 1):
        # CSV en yeniden en eskiye sıralıdır. Zaman yönünü korumak için
        # idx+1 geçmiş, idx ise onu izleyen çekiliştir.
        mevcut_tur = son_cekilisler[idx + 1]
        sonraki_tur = son_cekilisler[idx]
        
        for a in mevcut_tur:
            for b in sonraki_tur:
                matris[int(a)-1, int(b)-1] += 1
                
    # Satırları normalize ederek olasılığa dönüştürüyoruz
    satir_toplamlari = matris.sum(axis=1, keepdims=True)
    # Sıfıra bölünme hatasını engelle
    satir_toplamlari[satir_toplamlari == 0] = 1
    olasilik_matrisi = matris / satir_toplamlari
    return olasilik_matrisi

def shannon_entropisi(df, sayi_kolonlari):
    """Her çekilişteki sıralı sayı aralıklarının entropisini ölçer."""
    entropiler = []
    
    for tur in df[sayi_kolonlari].values:
        # Sayıların fark dağılımlarını normalize edip olasılığa döküyoruz
        farklar = np.diff(np.sort(tur))
        toplam_fark = farklar.sum()
        if toplam_fark == 0: continue
        
        p = farklar / toplam_fark
        # Shannon Entropisi Formülü
        p = p[p > 0]
        entropi = -np.sum(p * np.log2(p))
        entropiler.append(entropi)
        
    return pd.Series(entropiler)
