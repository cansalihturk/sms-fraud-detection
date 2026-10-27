"""Türkçe spam mesajlarını iki kişiye etiketleme için böler.

Çalıştırma (repo kökünden, önce `python -m src.hazirla_veri` çalışmış olmalı):
    python -m src.etiketleme_hazirla

Girdi : data/processed/havuz.csv, data/processed/kaynak_etiketleri.csv
        data/etiketleme/ilk50_esra.csv (ilk 50'deki mesajlar tekrar verilmez)
Çıktı : data/etiketleme/spam_esra.csv, spam_salih.csv

Her dosyada iki parça vardır:
  - ORTAK (30 mesaj): ikisine de gider, ikinci bir uyum ölçümü için
  - PAYLAŞILAN: kalan mesajlar yarı yarıya bölünür (her mesaj tek kişiye gider)
Dosya zaten varsa üzerine yazılmaz (etiketler kaybolmasın). Zorla: --force
"""
import sys
from pathlib import Path

import pandas as pd

TOHUM = 42
ORTAK_SAYI = 30
SUTUNLAR = ["id", "mesaj", "dil", "kaynak", "etiket", "tur", "belirsiz",
            "sms_degil", "not", "etiketleyen", "ikinci_etiket", "son_etiket"]


def main(zorla=False):
    islenmis = Path("data/processed")
    etiketleme = Path("data/etiketleme")
    havuz = pd.read_csv(islenmis / "havuz.csv")
    kaynak = pd.read_csv(islenmis / "kaynak_etiketleri.csv")
    df = havuz.merge(kaynak, on="id")

    spam = df[(df["dil"] == "tr") & (df["kaynak_etiket"] == "spam")]
    ilk50 = pd.read_csv(etiketleme / "ilk50_esra.csv")["id"]
    kalan = spam[~spam["id"].isin(ilk50)].sample(frac=1, random_state=TOHUM)
    print(f"Türkçe spam: {len(spam)}, ilk 50'de olanlar çıkınca: {len(kalan)}")

    ortak = kalan.iloc[:ORTAK_SAYI]
    paylasilan = kalan.iloc[ORTAK_SAYI:]
    yarim = len(paylasilan) // 2 + len(paylasilan) % 2
    parcalar = {"Esra": paylasilan.iloc[:yarim], "Salih": paylasilan.iloc[yarim:]}

    for kisi, kendi in parcalar.items():
        d = pd.concat([ortak, kendi]).sample(frac=1, random_state=TOHUM + len(kisi))
        d = d.reindex(columns=SUTUNLAR)
        d["etiketleyen"] = kisi
        yol = etiketleme / f"spam_{kisi.lower()}.csv"
        if yol.exists() and not zorla:
            print(f"{yol} zaten var, üzerine yazılmadı (zorlamak için --force)")
            continue
        d.to_csv(yol, index=False)
        print(f"{yol}: {len(d)} mesaj ({ORTAK_SAYI} ortak + {len(kendi)} sana özel)")

    ortak[["id"]].to_csv(etiketleme / "spam_ortak_idler.csv", index=False)
    print("Ortak mesajların id listesi: spam_ortak_idler.csv")


if __name__ == "__main__":
    main(zorla="--force" in sys.argv)
