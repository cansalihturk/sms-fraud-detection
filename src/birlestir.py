"""Etiketlenmiş dosyaları tek bir Türkçe veri setinde birleştirir.

Çalıştırma (repo kökünden):
    python -m src.birlestir

Girdi (data/etiketleme/ içinde ya da repo kökünde aranır):
    ilk50_esra_etiketli.csv, ilk50_salih_etiketli.csv
    spam_esra_etiketli.csv,  spam_salih_etiketli.csv
    mesru_esra_etiketli.csv, mesru_salih_etiketli.csv
    docs/uyusmazlik_cozumleri.csv   (id, son_etiket: iki kişi ayrıştığında konuşup verilen karar)
    data/processed/kaynak_etiketleri.csv

Çıktı: data/processed/tr_etiketli.csv  (git'e girmez)

Kurallar:
  - Aynı mesajı iki kişi etiketlediyse etiketler aynıysa o etiket, değilse
    uyusmazlik_cozumleri.csv'deki karar kullanılır. Kararı olmayan ayrışma
    varsa program durur ve id'leri yazar.
  - Metin farklıysa (biri maskelemiş) daha çok [..] içeren, yani maskeli versiyon alınır.
  - Sadece Türkçe (dil == tr) satırlar alınır.
  - belirsiz / sms_degil: iki kişiden biri 'e' dediyse 'e'.
"""
import sys
from pathlib import Path

import pandas as pd

ETIKETLER = {"dolandırıcılık", "reklam", "meşru"}
TURLER = {"ödül", "banka", "kredi", "kargo", "devlet", "bahis", "diğer"}
DOSYALAR = ["ilk50_esra_etiketli.csv", "ilk50_salih_etiketli.csv",
            "spam_esra_etiketli.csv", "spam_salih_etiketli.csv",
            "mesru_esra_etiketli.csv", "mesru_salih_etiketli.csv"]
ETK = Path("data/etiketleme")
COZUM = Path("docs/uyusmazlik_cozumleri.csv")
KAYNAK = Path("data/processed/kaynak_etiketleri.csv")
CIKTI = Path("data/processed/tr_etiketli.csv")


def bul(ad):
    for yol in (ETK / ad, Path(ad)):
        if yol.exists():
            return yol
    sys.exit(f"Dosya bulunamadı: {ad}")


def oku(yol):
    d = pd.read_csv(yol, dtype=str, keep_default_na=False)
    for c in ("etiket", "tur", "belirsiz", "sms_degil", "etiketleyen"):
        d[c] = d[c].str.strip()
    for c in ("etiket", "tur", "belirsiz", "sms_degil"):
        d[c] = d[c].str.lower()
    d["id"] = d["id"].astype(int)
    return d[d["dil"] == "tr"]


def birlestir():
    tum = pd.concat([oku(bul(d)) for d in DOSYALAR], ignore_index=True)
    cozum = {}
    if COZUM.exists():
        c = pd.read_csv(COZUM, dtype=str)
        cozum = {int(i): e.strip().lower() for i, e in zip(c["id"], c["son_etiket"])}

    satirlar, cozulmemis, metin_farki = [], [], []
    for i, g in tum.groupby("id"):
        mesaj = max(g["mesaj"], key=lambda m: m.count("["))
        if g["mesaj"].nunique() > 1:
            metin_farki.append(i)
        etiketler = set(g["etiket"])
        if len(etiketler) == 1:
            etiket = next(iter(etiketler))
        elif i in cozum:
            etiket = cozum[i]
        else:
            cozulmemis.append((i, sorted(etiketler)))
            continue
        if etiket == "meşru":
            tur = ""
        else:
            turler = [t for t in g.loc[g["etiket"] == etiket, "tur"] if t]
            tur = turler[0] if turler else ""
        satirlar.append({
            "id": i, "mesaj": mesaj, "etiket": etiket,
            "ikili": "meşru" if etiket == "meşru" else "spam",
            "tur": tur,
            "belirsiz": "e" if (g["belirsiz"] == "e").any() else "h",
            "sms_degil": "e" if (g["sms_degil"] == "e").any() else "h",
            "etiketleyen": "+".join(sorted(set(g["etiketleyen"]))),
        })

    if cozulmemis:
        print("KARARI OLMAYAN AYRIŞMALAR (docs/uyusmazlik_cozumleri.csv'ye ekleyin):")
        for i, e in cozulmemis:
            print(f"  id {i}: {e}")
        sys.exit(1)

    d = pd.DataFrame(satirlar)
    d = d.merge(pd.read_csv(KAYNAK), on="id", how="left")
    return d, metin_farki


def dogrula(d):
    sorun = []
    kotu = d[~d["etiket"].isin(ETIKETLER)]
    if len(kotu):
        sorun.append(f"geçersiz etiket: {kotu['id'].tolist()}")
    kotu = d[(d["etiket"] != "meşru") & ~d["tur"].isin(TURLER)]
    if len(kotu):
        sorun.append(f"reklam/dolandırıcılık satırında tur eksik ya da geçersiz: {kotu['id'].tolist()}")
    kotu = d[~d["belirsiz"].isin({"e", "h"}) | ~d["sms_degil"].isin({"e", "h"})]
    if len(kotu):
        sorun.append(f"belirsiz/sms_degil hatalı: {kotu['id'].tolist()}")
    kotu = d[d["id"].duplicated()]
    if len(kotu):
        sorun.append(f"tekrar eden id: {kotu['id'].tolist()}")
    return sorun


def main():
    d, metin_farki = birlestir()
    if metin_farki:
        print(f"Not: {len(metin_farki)} mesajın metni iki dosyada farklıydı, maskeli olan seçildi: {metin_farki}")
    sorun = dogrula(d)
    for s in sorun:
        print("UYARI:", s)
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(CIKTI, index=False)
    print(f"\nYazıldı: {CIKTI}  ({len(d)} mesaj)")
    print("\nEtiket dağılımı:")
    print(d["etiket"].value_counts().to_string())
    print("\nİkili dağılım:")
    print(d["ikili"].value_counts().to_string())
    print(f"\nSMS değil: {(d['sms_degil'] == 'e').sum()}   Belirsiz: {(d['belirsiz'] == 'e').sum()}")
    print("\nVeri setinin kendi etiketi ile bizim etiketimiz:")
    print(pd.crosstab(d["kaynak_etiket"], d["etiket"]).to_string())


if __name__ == "__main__":
    main()
