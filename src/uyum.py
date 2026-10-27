"""İki etiketleyicinin uyumunu hesaplar.

Çalıştırma (repo kökünden):
    python -m src.uyum ilk50_esra_etiketli.csv ilk50_salih_etiketli.csv

Gösterir: uyum yüzdesi, Cohen kappa, ikili ve "dolandırıcılık mı" bazlı uyum,
karışıklık tablosu, uyuşmayan satırlar, belirsiz sayıları.
Boşluk ve büyük/küçük harf farkları yok sayılır.
"""
import sys

import pandas as pd
from sklearn.metrics import cohen_kappa_score


def temizle(s):
    return s.astype("string").str.strip().str.lower()


def oku(yol):
    df = pd.read_csv(yol, dtype=str)
    for c in ("etiket", "tur", "belirsiz", "sms_degil"):
        if c in df.columns:
            df[c] = temizle(df[c])
    df["id"] = df["id"].astype(int)
    return df


def yuzde(a, b):
    return 100 * (a == b).mean()


def rapor(a, b, ad):
    print(f"  {ad}: uyum %{yuzde(a, b):.1f}   kappa {cohen_kappa_score(a, b):.2f}")


def main(yol1, yol2):
    e, s = oku(yol1), oku(yol2)
    d = e.merge(s, on="id", suffixes=("_1", "_2"))
    print(f"Ortak mesaj: {len(d)} (1. dosya {len(e)}, 2. dosya {len(s)})")
    if len(d) != len(e) or len(d) != len(s):
        print("UYARI: id'ler tam örtüşmüyor, aynı 50 mesajla mı çalışıyorsunuz?")
    fark = d[d["mesaj_1"] != d["mesaj_2"]]
    if len(fark):
        print(f"UYARI: {len(fark)} mesajın metni iki dosyada farklı (maskeleme/elle düzenleme?): {fark['id'].tolist()}")
    eksik = d[d["etiket_1"].isna() | d["etiket_2"].isna()]
    if len(eksik):
        print(f"UYARI: boş etiketli satırlar: {eksik['id'].tolist()}")
        d = d.drop(eksik.index)

    a, b = d["etiket_1"], d["etiket_2"]
    print("\nUYUM")
    rapor(a, b, "3 sınıf (dolandırıcılık/reklam/meşru)")
    rapor(a.where(a == "meşru", "spam"), b.where(b == "meşru", "spam"), "ikili (spam / meşru)      ")
    rapor(a.where(a == "dolandırıcılık", "diğer"), b.where(b == "dolandırıcılık", "diğer"),
          "dolandırıcılık / diğer        ")

    net = d[(d["belirsiz_1"] == "h") & (d["belirsiz_2"] == "h")]
    if len(net) and len(net) < len(d):
        print(f"\n  İkinizin de net dediği {len(net)} satırda: %{yuzde(net['etiket_1'], net['etiket_2']):.1f}")

    print("\nKARIŞIKLIK TABLOSU (satır: 1. dosya, sütun: 2. dosya)")
    print(pd.crosstab(a, b))

    print("\nBELİRSİZ")
    print(f"  1. dosya: {(d['belirsiz_1'] == 'e').sum()}   2. dosya: {(d['belirsiz_2'] == 'e').sum()}")
    print(f"  SMS değil: 1. dosya {(d['sms_degil_1'] == 'e').sum()}   2. dosya {(d['sms_degil_2'] == 'e').sum()}")

    uyusmayan = d[a != b]
    print(f"\nUYUŞMAYAN {len(uyusmayan)} SATIR")
    for _, r in uyusmayan.iterrows():
        print(f"\n[{r['id']}] {r['etiket_1']} / {r['etiket_2']}"
              f"   (belirsiz: {r['belirsiz_1']}/{r['belirsiz_2']})")
        print(f"   {str(r['mesaj_1'])[:160]}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Kullanım: python -m src.uyum esra.csv salih.csv")
    main(sys.argv[1], sys.argv[2])
