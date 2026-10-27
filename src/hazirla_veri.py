"""Ham veriyi okur, maskeler ve etiketleme dosyalarını üretir.

Çalıştırma (repo kökünden):
    python -m src.hazirla_veri

Girdi : data/raw/turkishsms.csv (train), data/raw/uci_sms.csv,
        data/raw/turkishsms_val.csv (validation, varsa; kendi bölmemizi yapacağız)
Çıktı : data/processed/havuz.csv              (tüm maskeli mesajlar, etiketsiz)
        data/processed/kaynak_etiketleri.csv  (id -> veri setinin kendi etiketi)
        data/etiketleme/ilk50_esra.csv, ilk50_salih.csv  (aynı 50 mesaj, etiketsiz)
"""
from pathlib import Path

import pandas as pd

from src.maskele import maskele

SUTUNLAR = ["id", "mesaj", "dil", "kaynak", "etiket", "tur", "belirsiz",
            "sms_degil", "not", "etiketleyen", "ikinci_etiket", "son_etiket"]
TOHUM = 42


def turkce_oku(yol):
    df = pd.read_csv(yol)
    metin = "sms" if "sms" in df.columns else "text"
    # Etiket sütununu değerlerinden bul (spam / legitimate)
    etiket = next(c for c in df.columns
                  if c != metin and set(df[c].astype(str).unique()) <= {"spam", "legitimate"})
    out = pd.DataFrame({"mesaj": df[metin].astype(str).str.strip(),
                        "kaynak_etiket": df[etiket].astype(str)})
    out["dil"], out["kaynak"] = "tr", "turkishsms"
    return out


def ingilizce_oku(yol):
    df = pd.read_csv(yol)
    out = pd.DataFrame({"mesaj": df["sms"].astype(str).str.strip(),
                        "kaynak_etiket": df["label"].map({0: "ham", 1: "spam"})})
    out["dil"], out["kaynak"] = "en", "uci"
    return out


def ilk50_sec(df):
    """25 TR + 25 EN; her dilde 13 spam + 12 diğer. Aynı mesajlar iki kişiye gider."""
    parcalar = []
    for dil in ("tr", "en"):
        # ek (validation) satırlar ilk 50'ye girmez: ilk 50 hep aynı kalsın
        d = df[(df["dil"] == dil) & (~df["ek"])]
        parcalar.append(d[d["kaynak_etiket"] == "spam"].sample(13, random_state=TOHUM))
        parcalar.append(d[d["kaynak_etiket"] != "spam"].sample(12, random_state=TOHUM))
    return pd.concat(parcalar).sample(frac=1, random_state=TOHUM)  # karıştır


def main():
    ham = Path("data/raw")
    tr = turkce_oku(ham / "turkishsms.csv")
    en = ingilizce_oku(ham / "uci_sms.csv")
    parcalar = [tr, en]
    val_yol = ham / "turkishsms_val.csv"
    if val_yol.exists():
        parcalar.append(turkce_oku(val_yol))  # sona eklenir: mevcut id'ler değişmez
    for p in parcalar:
        p["ek"] = False
    if len(parcalar) == 3:
        parcalar[2]["ek"] = True
    df = pd.concat(parcalar, ignore_index=True)

    df["mesaj"] = df["mesaj"].map(maskele)
    onceki = len(df)
    grup = df.groupby(["mesaj", "dil"])["kaynak_etiket"].nunique()
    celisen = grup[grup > 1]
    print(f"Aynı metin, farklı etiket: {len(celisen)}")
    
    df = df.drop_duplicates(subset=["mesaj", "dil"]).reset_index(drop=True)
    print(f"Tekrar eden {onceki - len(df)} mesaj silindi, kalan: {len(df)}")
    df.insert(0, "id", range(1, len(df) + 1))

    islenmis = Path("data/processed")
    islenmis.mkdir(parents=True, exist_ok=True)
    etiketleme = Path("data/etiketleme")
    etiketleme.mkdir(parents=True, exist_ok=True)

    # Veri setinin kendi etiketi ayrı dosyada: etiketleyiciler görmesin (önyargı olmasın)
    df[["id", "kaynak_etiket"]].to_csv(islenmis / "kaynak_etiketleri.csv", index=False)
    df.reindex(columns=SUTUNLAR).to_csv(islenmis / "havuz.csv", index=False)

    ilk = ilk50_sec(df).reindex(columns=SUTUNLAR)
    for kisi in ("Esra", "Salih"):
        k = ilk.copy()
        k["etiketleyen"] = kisi
        k.to_csv(etiketleme / f"ilk50_{kisi.lower()}.csv", index=False)

    print(df.groupby(["dil", "kaynak_etiket"]).size())
    print("Yazıldı: havuz.csv, kaynak_etiketleri.csv, ilk50_esra.csv, ilk50_salih.csv")


if __name__ == "__main__":
    main()
