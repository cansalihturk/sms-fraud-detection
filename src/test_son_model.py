"""Son modelin (models/xlmr_e) kilitli tr_test'te TEK BAKIŞI. PROJECT.md: "test en sonda tek sefer".

Çalıştırma (repo kökünden):
    python -m src.test_son_model

Bu script'i bir kez çalıştır, sonucu PROJECT.md'ye yaz. Sonuca bakıp ayar değiştirilmez.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()
MODEL = Path("models/xlmr_e")


def main():
    # --- 1. Model, tokenizer, künye ---
    kunye = json.loads((MODEL / "kunye.json").read_text(encoding="utf-8"))
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL).to("cuda").eval()

    # --- 2. Kilitli test: tr_test (116 mesaj, belirsizler dahil: protokol "test'te tutulur") ---
    test = pd.read_csv("data/processed/tr_test.csv")
    y = (test["ikili"] == "spam").astype(int).to_numpy()

    # --- 3. Tahmin (16'lık gruplar) ---
    p = []
    with torch.no_grad():
        for i in range(0, len(test), 16):
            parca = test["mesaj"].iloc[i:i + 16].tolist()
            kod = tok(parca, padding=True, truncation=True,
                      max_length=kunye["ayar"]["max_len"], return_tensors="pt").to("cuda")
            p.append(torch.softmax(model(**kod).logits.float(), dim=-1)[:, 1].cpu().numpy())
    p = np.concatenate(p)
    t = (p > kunye["esik"]).astype(int)

    # --- 4. Ölçüm: Gün 5-6 tablolarıyla aynı sütunlar ---
    tn, fp, fn, tp = confusion_matrix(y, t).ravel()
    print(f"tr_test: {len(test)} mesaj (spam {y.sum()}, meşru {(y == 0).sum()})")
    print(f"F1 {f1_score(y, t):.3f}  P {precision_score(y, t):.3f}  R {recall_score(y, t):.3f}")
    print(f"Yanlış alarm {fp}/{(y == 0).sum()}   Kaçan spam {fn}/{y.sum()}")

    # --- 5. Hatalar: id ve olasılık (mesajlar maskeli) ---
    hata = test[t != y].assign(olasilik=p[t != y].round(2))
    print("\nHatalar:")
    for _, s in hata.iterrows():
        print(f"  id {s['id']:>5}  gerçek={s['ikili']:<5}  p={s['olasilik']:.2f}  {s['mesaj'][:70]}")

    # --- 6. Eşiğe yakın kararlar (0.30-0.70): bottaki "emin değilim" bandına kaç mesaj düşerdi? ---
    bant = ((p > 0.30) & (p < 0.70)).sum()
    print(f"\n0.30-0.70 arası (emin değilim bandı): {bant}/{len(test)} mesaj")


if __name__ == "__main__":
    main()
