"""Spam etiketleme dosyalarında SADECE ortak 30 mesajın uyumunu hesaplar.

Çalıştırma (repo kökünden):
    python -m src.ortak_uyum spam_esra_etiketli.csv spam_salih_etiketli.csv
    python -m src.ortak_uyum mesru_esra_etiketli.csv mesru_salih_etiketli.csv mesru

Ortak id listesi: data/etiketleme/spam_ortak_idler.csv
(sondaki "mesru" verilirse mesru_ortak_idler.csv)
(İki dosyada da olmayan mesajlar tek kişiye gitti, karşılaştırılamaz.)
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

from src.uyum import main as uyum_main



def main(yol1, yol2, mod="spam"):
    ortak = set(pd.read_csv(f"data/etiketleme/{mod}_ortak_idler.csv")["id"])
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
    if len(sys.argv) not in (3, 4):
        sys.exit("Kullanım: python -m src.ortak_uyum esra_etiketli.csv salih_etiketli.csv [mesru]")
    main(sys.argv[1], sys.argv[2], "mesru" if len(sys.argv) == 4 else "spam")
