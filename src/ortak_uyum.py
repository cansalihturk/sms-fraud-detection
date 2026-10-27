"""Spam etiketleme dosyalarında SADECE ortak 30 mesajın uyumunu hesaplar.

Çalıştırma (repo kökünden):
    python -m src.ortak_uyum spam_esra_etiketli.csv spam_salih_etiketli.csv

Ortak id listesi: data/etiketleme/spam_ortak_idler.csv
(İki dosyada da olmayan mesajlar tek kişiye gitti, karşılaştırılamaz.)
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

from src.uyum import main as uyum_main

ORTAK = Path("data/etiketleme/spam_ortak_idler.csv")


def main(yol1, yol2):
    ortak = set(pd.read_csv(ORTAK)["id"])
    with tempfile.TemporaryDirectory() as tmp:
        yollar = []
        for i, yol in enumerate((yol1, yol2), start=1):
            df = pd.read_csv(yol, dtype=str)
            ayri = df[df["id"].astype(int).isin(ortak)]
            if len(ayri) != len(ortak):
                print(f"UYARI: {yol} dosyasında {len(ayri)} ortak mesaj var, "
                      f"beklenen {len(ortak)}")
            p = Path(tmp) / f"ortak_{i}.csv"
            ayri.to_csv(p, index=False)
            yollar.append(str(p))
        uyum_main(*yollar)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Kullanım: python -m src.ortak_uyum esra_etiketli.csv salih_etiketli.csv")
    main(sys.argv[1], sys.argv[2])
