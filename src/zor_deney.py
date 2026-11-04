"""Zor set deneyi, XLM-R, leave-one-sender-out (LOSO). PROJECT.md "Gün 8".

Çalıştırma (repo kökünden, GPU boş, Ollama kapalı):
    python -m src.zor_deney E_v2

Deney tarifleri (eğitim = tr_train + aşağıdakiler; sınav = zor set, her turda bir gönderici):
    B_v2 : + zor set (diğer göndericiler)
    D_v2 : + zor set + sentetik v2/v3
    E_v2 : + zor set + sentetik v2/v3 + Salih 58

Gruplama (v2): gönderici adı büyük harf, harf/rakam dışı her şey silinir
    ("NVI RANDEVU" = "NVIRANDEVU" = "nvi-randevu"). Esra'nın SVM protokolüyle aynı.
Sınav göndericisinin mesajları zor setten VE Salih'in dosyasından eğitimde çıkarılır.

Çıktı: MLflow (deney grubu tr_zor, run adı xlmr_zor_<DENEY>) +
       data/external/xlmr_zor_<DENEY>_tahmin.csv (out-of-fold olasılıklar; repoya girmez)
"""
import sys
import time

import mlflow
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import f1_score, precision_score, recall_score
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup
from transformers.utils import logging as hf_logging

hf_logging.set_verbosity_error()

# --- 1. Ayarlar: Gün 8 ile aynı ---
AYAR = {"model": "FacebookAI/xlm-roberta-base", "max_len": 160, "batch": 16,
        "lr": 2e-5, "epoch": 4, "warmup": 0.1, "weight_decay": 0.01, "seed": 42}
D = "data/external/"
TARIFLER = {"B_v2": ["zor"], "D_v2": ["zor", "S2"], "E_v2": ["zor", "S2", "SAL"]}


# --- 2. Veri: her kaynak (metinler, 0/1 etiketler, gönderici grupları) ---
def grupla(seri):
    return seri.str.upper().str.replace(r"[^A-Z0-9ÇĞİÖŞÜ]", "", regex=True).to_numpy()


def hazirla(df, gonderen=True):
    m = df["mesaj"].tolist()
    y = (df["etiket"] != "meşru").astype(int).to_numpy()            # reklam + dolandırıcılık = 1
    g = grupla(df["gonderen"]) if gonderen else np.array([""] * len(df))
    return m, y, g


def veri_yukle():
    tr = pd.read_csv("data/processed/tr_train.csv")
    tr = tr[tr["belirsiz"] != "e"].copy()
    tr["etiket"] = np.where(tr["ikili"] == "spam", "reklam", "meşru")

    zor = pd.read_csv(D + "zor_gercek_hepsi.csv")
    zor = zor[zor["etiket"].notna()].reset_index(drop=True)

    sent = pd.concat([pd.read_csv(D + "sentetik_kurumsal_mesru_v3.csv"),
                      pd.read_csv(D + "sentetik_dolandiricilik_v2.csv")])

    sal = pd.read_csv(D + "salih_kurumsal_etiketli.csv", dtype=str, keep_default_na=False)
    sal = sal[sal["belirsiz"] != "e"]

    kaynak = {"T": hazirla(tr, gonderen=False), "zor": hazirla(zor),
              "S2": hazirla(sent, gonderen=False), "SAL": hazirla(sal)}
    return kaynak, zor


# --- 3. Eğitim seti: kaynakları birleştir, sınav göndericisini her kaynaktan çıkar ---
def egitim_seti(kaynaklar, haric_grup):
    X, y = [], []
    for m, e, g in kaynaklar:
        tut = g != haric_grup
        X += [m[i] for i in np.where(tut)[0]]
        y.append(e[tut])
    return X, np.concatenate(y)


# --- 4. Eğit + tahmin: her çağrıda taze XLM-R (Gün 8 ile aynı döngü) ---
def egit_ve_tahmin(X_e, y_e, X_d, tok):
    torch.manual_seed(AYAR["seed"])
    model = AutoModelForSequenceClassification.from_pretrained(AYAR["model"], num_labels=2).to("cuda")

    def birlestir(parti):
        m, e = zip(*parti)
        kod = tok(list(m), padding=True, truncation=True, max_length=AYAR["max_len"], return_tensors="pt")
        kod["labels"] = torch.tensor(e)
        return kod

    egitim = DataLoader(list(zip(X_e, y_e)), batch_size=AYAR["batch"], shuffle=True, collate_fn=birlestir)
    opt = torch.optim.AdamW(model.parameters(), lr=AYAR["lr"], weight_decay=AYAR["weight_decay"])
    toplam = len(egitim) * AYAR["epoch"]
    plan = get_linear_schedule_with_warmup(opt, int(toplam * AYAR["warmup"]), toplam)

    model.train()
    for _ in range(AYAR["epoch"]):
        for parti in egitim:
            parti = {k: v.to("cuda") for k, v in parti.items()}
            with torch.autocast("cuda", dtype=torch.bfloat16):
                kayip = model(**parti).loss
            kayip.backward(); opt.step(); plan.step(); opt.zero_grad()

    model.eval()
    p = []
    with torch.no_grad():
        for i in range(0, len(X_d), AYAR["batch"]):
            kod = tok(X_d[i:i + AYAR["batch"]], padding=True, truncation=True,
                      max_length=AYAR["max_len"], return_tensors="pt").to("cuda")
            with torch.autocast("cuda", dtype=torch.bfloat16):
                p.append(torch.softmax(model(**kod).logits.float(), dim=-1)[:, 1].cpu().numpy())
    del model, opt
    torch.cuda.empty_cache()
    return np.concatenate(p)


# --- 5. Ölçüm: Esra'nın tablosuyla aynı sütunlar ---
def olc(y, p, etiket):
    t = (p > 0.5).astype(int)
    return {"zor_f1": f1_score(y, t), "zor_p": precision_score(y, t), "zor_r": recall_score(y, t),
            "yanlis_alarm": int(t[y == 0].sum()), "spam_yakalama": int(t[y == 1].sum()),
            "dol_yakalama": int(t[etiket == "dolandırıcılık"].sum())}


def main():
    ad = sys.argv[1] if len(sys.argv) > 1 else "E_v2"
    if ad not in TARIFLER:
        raise SystemExit(f"Bilinmeyen deney: {ad}. Seçenekler: {list(TARIFLER)}")

    # 6a. veri + ortak gönderici kontrolü
    kaynak, zor = veri_yukle()
    Z = kaynak["zor"]
    ortak = sorted(set(kaynak["SAL"][2]) & set(Z[2]))
    print(f"Deney {ad}: tr_train + {' + '.join(TARIFLER[ad])}")
    print(f"Zor set: {len(Z[0])} mesaj, {len(np.unique(Z[2]))} gönderici grubu")
    print(f"Salih'in dosyasıyla ortak göndericiler ({len(ortak)}): {ortak}")

    # 6b. LOSO
    tok = AutoTokenizer.from_pretrained(AYAR["model"])
    kaynaklar = [kaynak["T"]] + [kaynak[k] for k in TARIFLER[ad]]
    gruplar = np.unique(Z[2])
    p = np.zeros(len(Z[0]))
    basla = time.time()
    for i, g in enumerate(gruplar):
        sinav = Z[2] == g
        X_e, y_e = egitim_seti(kaynaklar, haric_grup=g)
        p[sinav] = egit_ve_tahmin(X_e, y_e, [Z[0][j] for j in np.where(sinav)[0]], tok)
        if (i + 1) % 10 == 0 or i + 1 == len(gruplar):
            print(f"  {i + 1}/{len(gruplar)}  {(time.time() - basla) / 60:.1f} dk")

    # 6c. ölç, kaydet
    sonuc = olc(Z[1], p, zor["etiket"].to_numpy())
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("tr_zor")
    with mlflow.start_run(run_name=f"xlmr_zor_{ad}"):
        mlflow.log_params({**AYAR, "deney": ad, "ekler": "+".join(TARIFLER[ad]), "loso": True,
                           "gruplama": "v2: büyük harf, harf/rakam dışı silinir",
                           "sinav": "zor_gercek v2 (131)"})
        mlflow.log_metrics(sonuc)

    zor.assign(grup=Z[2], p=p.round(4), t=(p > 0.5).astype(int)).to_csv(
        D + f"xlmr_zor_{ad}_tahmin.csv", index=False, encoding="utf-8-sig")

    print(f"\n{ad}: yanlış alarm {sonuc['yanlis_alarm']}/{(Z[1] == 0).sum()}, "
          f"spam yakalama {sonuc['spam_yakalama']}/{Z[1].sum()}, "
          f"dolandırıcılık {sonuc['dol_yakalama']}/{(zor['etiket'] == 'dolandırıcılık').sum()}, "
          f"F1 {sonuc['zor_f1']:.3f}, P {sonuc['zor_p']:.3f}, R {sonuc['zor_r']:.3f}")


if __name__ == "__main__":
    main()
