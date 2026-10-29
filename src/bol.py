"""Türkçe etiketli veriyi train / test olarak böler (grup duyarlı) ve train'e CV katları ekler.

Çalıştırma (repo kökünden, önce `python -m src.birlestir` çalışmış olmalı):
    python -m src.bol                 # benzerlik eşiği 0.60
    python -m src.bol --esik 0.60     # eşiği değiştirmek için

Girdi : data/processed/tr_etiketli.csv
Çıktı : data/processed/tr_train.csv   (%85, "fold" sütunu 0-4: grup duyarlı 5 katlı CV için)
        data/processed/tr_test.csv    (%15, kilitli, model seçimi için KULLANILMAZ)

Neden "grup duyarlı"?
  SMS veri setlerinde aynı şablondan çok mesaj olur ("Mudo ... % indirim" gibi).
  Rastgele bölersek aynı şablon hem train'de hem test'te olur; model ezberler,
  test puanı olduğundan yüksek çıkar (veri sızıntısı). Burada birbirine çok
  benzeyen mesajlar tek bir GRUP sayılır ve bir grup bütünüyle tek parçaya gider.

Adımlar:
  1. sms_degil == 'e' olan satırlar çıkarılır (eğitim/test verisi değil).
  2. Metin normalleştirilir (küçük harf, rakamlar -> 0, boşluklar tek).
  3. Karakter n-gram TF-IDF kosinüs benzerliği >= esik olan mesajlar aynı grup olur
     (zincirleme: A~B ve B~C ise A, B, C aynı grup).
  4. Gruplar, 3 sınıf (meşru / reklam / dolandırıcılık) oranları korunacak şekilde
     %85 train / %15 test dağıtılır (büyük gruplar önce, her grup en çok eksik kalan parçaya).
  5. Train içinde aynı yöntemle 5 kat (fold) ayrılır; CV'de bir grup iki ayrı katta olmaz.
  6. Sızıntı kontrolü: train-test arası en yüksek benzerlik ve en benzer çiftler yazdırılır.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

GIRDI = Path("data/processed/tr_etiketli.csv")
CIKTI = Path("data/processed")
TOHUM = 42
ESIK = 0.60
ORANLAR = {"train": 0.85, "test": 0.15}
KAT_SAYISI = 5


def normalle(metin):
    m = str(metin).lower()
    m = re.sub(r"\d", "0", m)
    return re.sub(r"\s+", " ", m).strip()


def benzerlik_matrisi(metinler):
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
    x = vec.fit_transform(metinler)
    return (x @ x.T).toarray()


def gruplari_bul(metinler, esik=ESIK):
    """Benzerliği eşikten büyük olan mesajları (zincirleme) aynı gruba koyar."""
    n = len(metinler)
    ata = list(range(n))

    def bul(i):
        while ata[i] != i:
            ata[i] = ata[ata[i]]
            i = ata[i]
        return i

    s = benzerlik_matrisi(metinler)
    for i, j in zip(*np.where(np.triu(s, k=1) >= esik)):
        ata[bul(i)] = bul(j)
    kokler = [bul(i) for i in range(n)]
    sirali = {k: g for g, k in enumerate(dict.fromkeys(kokler))}
    return np.array([sirali[k] for k in kokler]), s


def grup_bol(df, grup, sinif_sutunu="etiket", oranlar=ORANLAR, tohum=TOHUM):
    """Grupları sınıf oranlarını koruyarak parçalara dağıtır; satır başına parça adı döner."""
    rng = np.random.default_rng(tohum)
    siniflar = sorted(df[sinif_sutunu].unique())
    toplam = {c: (df[sinif_sutunu] == c).sum() for c in siniflar}
    hedef = {p: {c: toplam[c] * o for c in siniflar} for p, o in oranlar.items()}
    mevcut = {p: {c: 0 for c in siniflar} for p in oranlar}

    sayim = pd.crosstab(grup, df[sinif_sutunu]).reindex(columns=siniflar, fill_value=0)
    # Büyük gruplar önce; eşit büyüklükte olanlar rastgele sırada (tohumlu)
    sira = sorted(sayim.index, key=lambda g: (-sayim.loc[g].sum(), rng.random()))

    atama = {}
    for g in sira:
        # Grubun sınıflarına en çok ihtiyacı olan parça seçilir:
        # (hedef - şu ana kadar dolan) / sınıf toplamı, grubun sınıf sayılarıyla ağırlıklı
        en_iyi = max(oranlar, key=lambda p: sum(
            sayim.loc[g, c] * (hedef[p][c] - mevcut[p][c]) / max(toplam[c], 1) for c in siniflar))
        atama[g] = en_iyi
        for c in siniflar:
            mevcut[en_iyi][c] += sayim.loc[g, c]
    return pd.Series(grup, index=df.index).map(atama)


def sizinti_raporu(parca, s):
    """Parçalar arası en yüksek benzerlik (0..1). 1'e yakınsa sızıntı var demektir."""
    adlar = sorted(set(parca))
    satirlar = []
    for i, x in enumerate(adlar):
        for y in adlar[i + 1:]:
            ia, ib = np.where(parca.values == x)[0], np.where(parca.values == y)[0]
            satirlar.append((x, y, s[np.ix_(ia, ib)].max()))
    return satirlar


def en_benzer_ciftler(d, parca, s, a="train", b="test", n=5):
    """a ve b parçaları arasındaki en benzer n mesaj çifti: (benzerlik, id_a, id_b)."""
    ia, ib = np.where(parca.values == a)[0], np.where(parca.values == b)[0]
    alt = s[np.ix_(ia, ib)]
    en = np.dstack(np.unravel_index(np.argsort(-alt, axis=None)[:n], alt.shape))[0]
    return [(alt[i, j], ia[i], ib[j]) for i, j in en]


def kat_ata(train, tohum=TOHUM, kat=KAT_SAYISI):
    """Train içinde grup duyarlı, sınıf oranlı kat numarası (0..kat-1)."""
    oranlar = {k: 1 / kat for k in range(kat)}
    return grup_bol(train, train["grup"], oranlar=oranlar, tohum=tohum)


def main(esik=ESIK):
    if not GIRDI.exists():
        sys.exit(f"{GIRDI} yok. Önce: python -m src.birlestir")
    d = pd.read_csv(GIRDI, dtype={"tur": str}, keep_default_na=False)
    toplam = len(d)
    d = d[d["sms_degil"] != "e"].reset_index(drop=True)
    print(f"{toplam} mesaj, 'SMS değil' {toplam - len(d)} tanesi çıkarıldı -> {len(d)}")

    metinler = [normalle(m) for m in d["mesaj"]]
    grup, s = gruplari_bul(metinler, esik)
    d["grup"] = grup
    boy = d.groupby("grup").size()
    print(f"\nBenzerlik eşiği {esik}: {boy.size} grup (en büyük {boy.max()} mesaj, "
          f"tek mesajlık grup {int((boy == 1).sum())})")
    print("En büyük 5 grup (şablon örneği):")
    for g in boy.sort_values(ascending=False).head(5).index:
        ornek = d.loc[d["grup"] == g, "mesaj"].iloc[0][:70].replace("\n", " ")
        print(f"  {boy[g]:>3} mesaj | {ornek}")

    d["parca"] = grup_bol(d, d["grup"])
    train = d[d["parca"] == "train"].copy()
    train["fold"] = kat_ata(train)
    test = d[d["parca"] == "test"]
    train.drop(columns="parca").to_csv(CIKTI / "tr_train.csv", index=False)
    test.drop(columns="parca").to_csv(CIKTI / "tr_test.csv", index=False)

    sira = ["train", "test", "All"]
    print("\nParça x etiket:")
    print(pd.crosstab(d["parca"], d["etiket"], margins=True).reindex(sira, fill_value=0).to_string())
    print("\nParça x ikili (meşru / spam):")
    print(pd.crosstab(d["parca"], d["ikili"], margins=True).reindex(sira, fill_value=0).to_string())
    print(f"\nTrain içi {KAT_SAYISI} kat (etiket sayıları):")
    print(pd.crosstab(train["fold"], train["etiket"], margins=True).to_string())

    print(f"\nSızıntı kontrolü (train-test en yüksek benzerlik, {esik} altında olmalı):")
    for a, b, v in sizinti_raporu(d["parca"], s):
        print(f"  {a} - {b}: {v:.2f}  {'TAMAM' if v < esik else 'SORUN'}")
    print("\nTrain-test arasındaki en benzer 5 çift (gözle bakın, aynı şablon mu?):")
    for v, i, j in en_benzer_ciftler(d, d["parca"], s):
        print(f"  {v:.2f} | train id {d.loc[i, 'id']}: {d.loc[i, 'mesaj'][:60]!r}")
        print(f"       | test  id {d.loc[j, 'id']}: {d.loc[j, 'mesaj'][:60]!r}")
    print(f"\nYazıldı: {CIKTI}/tr_train.csv (fold sütunlu), tr_test.csv")


if __name__ == "__main__":
    esik = float(sys.argv[sys.argv.index("--esik") + 1]) if "--esik" in sys.argv else ESIK
    main(esik)
