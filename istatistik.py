import numpy as np
import pandas as pd
import scipy.stats as stats
import re

def ki_kare_testi(df, sayi_kolonlari):
    """Sistemin rastlantısallığını ölçer (P-Value > 0.05 ise tamamen rastgeledir)"""
    tum_sayilar = df[sayi_kolonlari].values.flatten()
    gözlemlenen, _ = np.histogram(tum_sayilar, bins=range(1, 82))
    
    # Teorik olarak her sayının eşit çıkması beklenir
    toplam_top = len(tum_sayilar)
    beklenen = np.full(80, toplam_top / 80)
    
    chi2_stat, p_value = stats.chisquare(gözlemlenen, f_exp=beklenen)
    return float(chi2_stat), float(p_value)

def gecikme_derinligi_analizi(df, sayi_kolonlari):
    """Sayıların kaç turdur çıkmadığını ve geometrik olasılık sınırını hesaplar"""
    son_cekilisler = df[sayi_kolonlari].values
    gecikmeler = {}
    
    for sayi in range(1, 81):
        gecikme = 0
        for tur in son_cekilisler:
            if sayi in tur:
                break
            gecikme += 1
        # Geometrik Dağılım: Bu gecikmeye ulaşma olasılığı (p=0.25)
        teorik_olasilik = (0.75 ** gecikme) * 0.25
        gecikmeler[sayi] = {"gecikme": gecikme, "olasilik": teorik_olasilik}
        
    return pd.DataFrame(gecikmeler).T.sort_values(by="gecikme", ascending=False)

def tur_gecis_analizi(df, sayi_kolonlari):
    """Peş peşe çekilişler arasındaki ortak sayı adetlerini inceler"""
    son_cekilisler = df[sayi_kolonlari].values
    ortak_adetler = []
    
    for idx in range(len(son_cekilisler) - 1):
        tur_t = set(son_cekilisler[idx])
        tur_t_eksi_1 = set(son_cekilisler[idx+1])
        ortak = len(tur_t.intersection(tur_t_eksi_1))
        ortak_adetler = ortak_adetler + [ortak]
        
    ortak_seri = pd.Series(ortak_adetler)
    return ortak_seri.value_counts().reindex(range(0, 21), fill_value=0)

def markov_zinciri_matrisi(df, sayi_kolonlari):
    """80x80 boyutunda peş peşe sayı tetikleme olasılık matrisini kurar"""
    son_cekilisler = df[sayi_kolonlari].values
    matris = np.zeros((80, 80))
    
    for idx in range(len(son_cekilisler) - 1):
        mevcut_tur = son_cekilisler[idx]
        sonraki_tur = son_cekilisler[idx+1]
        
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
    """Her çekilişin kaos/düzensizlik skorunu ölçer"""
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
