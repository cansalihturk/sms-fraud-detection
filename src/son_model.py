"""Son modeli eğitir ve kaydeder: XLM-R, E tarifi (PROJECT.md "Kararlar" ve "Gün 8").

Çalıştırma (repo kökünden, GPU boş olmalı, Ollama kapalı):
    python -m src.son_model

Eğitim verisi (E tarifi, LOSO yok, hepsi):
    data/processed/tr_train.csv                      651 (belirsiz hariç)
    data/external/zor_gercek_hepsi.csv               131 (etiketli olanların tamamı)
    data/external/sentetik_kurumsal_mesru_v3.csv     56  sentetik meşru
    data/external/sentetik_dolandiricilik_v2.csv     40  sentetik dolandırıcılık
    data/external/salih_kurumsal_etiketli.csv        58  (belirsiz hariç)

Çıktı: models/xlmr_e/  (model + tokenizer + kunye.json). models/ gitignore'da.

NOT: Zor set bu modelin eğitiminde. Bu modeli zor sette ölçmek ezber ölçmek olur.
Raporlanan zor set başarısı LOSO sonucudur (F1 0.947). Bağımsız test: tr_test.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import torch
import transformers
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup
from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()

# --- 1. Ayarlar: zor set deneyleriyle (Gün 8) birebir aynı ---
AYAR = {"model": "FacebookAI/xlm-roberta-base", "max_len": 160, "batch": 16,
        "lr": 2e-5, "epoch": 4, "warmup": 0.1, "weight_decay": 0.01, "seed": 42}
ESIK = 0.5
HEDEF = Path("models/xlmr_e")
D = Path("data/external")


# --- 2. Veri: her kaynak (metinler, 0/1 etiketler). reklam + dolandırıcılık = 1 ---
def hazirla(df):
    return df["mesaj"].tolist(), (df["etiket"] != "meşru").astype(int).to_numpy()


def veri_yukle():
    # 2a. tr_train: belirsizler çıkar, 'ikili' sütunu etikete çevrilir
    tr = pd.read_csv("data/processed/tr_train.csv")
    tr = tr[tr["belirsiz"] != "e"].copy()
    tr["etiket"] = np.where(tr["ikili"] == "spam", "reklam", "meşru")

    # 2b. zor set: etiketli olanların TAMAMI (son modelde LOSO yok)
    zor = pd.read_csv(D / "zor_gercek_hepsi.csv")
    zor = zor[zor["etiket"].notna()]

    # 2c. sentetik v2/v3 (v1 kullanılmaz: [LINK] kısayolu)
    sent = pd.concat([pd.read_csv(D / "sentetik_kurumsal_mesru_v3.csv"),
                      pd.read_csv(D / "sentetik_dolandiricilik_v2.csv")])

    # 2d. Salih'in 58 kurumsal mesajı (belirsizler hariç)
    sal = pd.read_csv(D / "salih_kurumsal_etiketli.csv", dtype=str, keep_default_na=False)
    sal = sal[sal["belirsiz"] != "e"]

    X, y, ozet = [], [], {}
    for ad, df in [("tr_train", tr), ("zor_set", zor), ("sentetik_v2v3", sent), ("salih_58", sal)]:
        m, e = hazirla(df)
        X += m
        y.append(e)
        ozet[ad] = len(m)
    return X, np.concatenate(y), ozet


# --- 3. Eğitim: Gün 8'deki egit_ve_tahmin ile aynı döngü, model silinmiyor ---
def egit(X, y, tok):
    torch.manual_seed(AYAR["seed"])
    model = AutoModelForSequenceClassification.from_pretrained(AYAR["model"], num_labels=2).to("cuda")

    def birlestir(parti):
        m, e = zip(*parti)
        kod = tok(list(m), padding=True, truncation=True, max_length=AYAR["max_len"], return_tensors="pt")
        kod["labels"] = torch.tensor(e)
        return kod

    yukleyici = DataLoader(list(zip(X, y)), batch_size=AYAR["batch"], shuffle=True, collate_fn=birlestir)
    opt = torch.optim.AdamW(model.parameters(), lr=AYAR["lr"], weight_decay=AYAR["weight_decay"])
    toplam = len(yukleyici) * AYAR["epoch"]
    plan = get_linear_schedule_with_warmup(opt, int(toplam * AYAR["warmup"]), toplam)

    model.train()
    for ep in range(AYAR["epoch"]):
        toplam_kayip = 0.0
        for parti in yukleyici:
            parti = {k: v.to("cuda") for k, v in parti.items()}
            with torch.autocast("cuda", dtype=torch.bfloat16):       # yarım hassasiyet
                kayip = model(**parti).loss
            kayip.backward()
            opt.step(); plan.step(); opt.zero_grad()
            toplam_kayip += kayip.item()
        print(f"  epoch {ep + 1}/{AYAR['epoch']}  ortalama kayıp {toplam_kayip / len(yukleyici):.4f}")
    model.eval()
    return model


# --- 4. Akıl kontrolü: üç uydurma mesaj ---
def kontrol(model, tok):
    deneme = ["kanka aksam maca geliyor musun",
              "Yurtiçi Kargo: kargonuz teslim edilemedi, adresinizi güncelleyin [LINK]",
              "Aras Kargo: kargonuz dağıtıma çıkarıldı. Takip: [LINK]"]
    kod = tok(deneme, padding=True, return_tensors="pt").to("cuda")
    with torch.no_grad():
        p = torch.softmax(model(**kod).logits.float(), dim=-1)[:, 1].cpu().numpy()
    print("\nAkıl kontrolü (spam olasılığı):")
    for m, olas in zip(deneme, p):
        print(f"  {olas:.2f}  {m}")


def main():
    if not torch.cuda.is_available():
        raise SystemExit("GPU yok. CUDA'lı torch gerekli (PROJECT.md: Kararlar, GPU).")

    # 5a. veri
    X, y, ozet = veri_yukle()
    print(f"Eğitim: {len(X)} mesaj (spam {y.sum()}, meşru {(y == 0).sum()})  {ozet}")

    # 5b. eğit
    tok = AutoTokenizer.from_pretrained(AYAR["model"])
    model = egit(X, y, tok)

    # 5c. kaydet: model + tokenizer + künye
    HEDEF.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(HEDEF)
    tok.save_pretrained(HEDEF)
    kunye = {
        "tarif": "E: tr_train + zor_gercek v2 (tamamı) + sentetik v2/v3 + salih_kurumsal_etiketli",
        "kaynaklar": ozet, "egitim_boyu": len(X), "ayar": AYAR, "esik": ESIK,
        "etiketler": {"0": "meşru", "1": "spam (reklam + dolandırıcılık)"},
        "zor_set_loso": {"f1": 0.947, "yanlis_alarm": "6/67", "dolandiricilik": "10/10"},
        "not": "Zor set eğitimde; bu modelin bağımsız testi tr_test (tek bakış). "
               "Girdi önce src.maskele'den geçmeli, temizle UYGULANMAZ.",
        "surumler": {"torch": torch.__version__, "transformers": transformers.__version__,
                     "scikit-learn": sklearn.__version__},
    }
    (HEDEF / "kunye.json").write_text(json.dumps(kunye, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5d. kontrol
    kontrol(model, tok)
    print("\nKaydedildi:", HEDEF, sorted(f.name for f in HEDEF.iterdir()))


if __name__ == "__main__":
    main()
