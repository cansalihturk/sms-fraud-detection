"""Saldırgan / savunmacı döngüsü v3. v2 (src/dongu.py) sonuçlarına dokunmaz, ayrı dosyalara yazar.

Çalıştırma (repo kökünden; Ollama açık, notebook kernel'leri kapalı):
    python -m src.dongu_v3

v2'den farkları:
    1. Meşru karşı ağırlık: havuzdaki 318 gerçek meşru mesaj GÖNDERİCİ BAZLI ikiye bölünür.
       Yarısı (~159) eğitime "meşru" olarak girer (D0 dahil), diğer yarısı sadece yanlış alarm ölçümünde.
       Aynı gönderici iki tarafta olamaz → şablon sızıntısı yok.
    2. İki saldırgan sırayla: tek turlar qwen3.5:9b, çift turlar aya-expanse:8b.
       gemma4:e4b yine SADECE finalde (hiç görülmemiş aile).
    3. Son savunmacı da üç tohumla eğitilir → final kaçma ve yanlış alarm için öncesi/sonrası bant.

Ön kayıt (deneyden ÖNCE yazıldı, sonuca göre değişmez):
    v3, v2'nin yerine ancak şu iki koşul birlikte sağlanırsa geçer:
      - final gemma kaçma oranı (son savunmacı, 3 tohum ortalaması) <= %10
      - yanlış alarm (son savunmacı, 3 tohum ortalaması, ölçüm yarısında) <= %13

Çıktılar (v2'ninkilerin üstüne yazmaz):
    data/external/dongu_v3/      saldırılar, puanlar, bölme listesi (repoya girmez)
    docs/dongu_v3_grafigi.png, docs/dongu_v3_sonuc.json
    MLflow deney grubu: dongu (run adı dongu_v3)
"""
import argparse
import json
import random
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import requests
import torch
from transformers import AutoTokenizer

from src.dongu import (ESIK, OLLAMA, SEMA, SENARYOLAR, SISTEM, TOHUMLAR, Yenilik,
                       geri_bildirim_yaz, puanla, temizle_saldiri)
from src.son_model import AYAR, egit, veri_yukle

# --- 0. Ayarlar ---
SALDIRGANLAR = ["qwen3.5:9b", "aya-expanse:8b"]          # tur 1, 3 → qwen; tur 2, 4 → aya
FINAL_SALDIRGAN = "gemma4:e4b"
CIKTI = Path("data/external/dongu_v3")
KRITER = {"final_kacma_max": 0.10, "yanlis_alarm_max": 0.13}   # ön kayıt
BOLME_TOHUM = 0


# --- 1. Saldırgan: v2 ile aynı, tek fark think parametresi ---
def ollama_uret(model, istem, sicaklik=0.9):
    govde = {"model": model, "system": SISTEM, "prompt": istem, "stream": False,
             "format": SEMA, "keep_alive": 0, "options": {"temperature": sicaklik}}
    cevap = requests.post(OLLAMA, timeout=600, json={**govde, "think": False})
    if cevap.status_code == 400:                           # düşünme modu olmayan model (aya) think'i reddederse
        cevap = requests.post(OLLAMA, timeout=600, json=govde)
    cevap.raise_for_status()
    metin = cevap.json()["response"]
    try:
        return [m for m in json.loads(metin)["mesajlar"] if isinstance(m, str)]
    except (json.JSONDecodeError, KeyError):
        return [s.strip(" -•\"") for s in metin.splitlines() if len(s.strip()) > 20]


def saldiri_uret(model, adet, geri_bildirim, yenilik, tohum):
    rnd = random.Random(tohum)
    mesajlar, deneme, reddedilen = [], 0, 0
    while len(mesajlar) < adet and deneme < adet // 5 + 6:
        deneme += 1
        senaryo = ", ".join(rnd.sample(SENARYOLAR, 3))
        istem = f"Senaryolar: {senaryo}.\n10 farklı dolandırıcılık SMS'i yaz.\n{geri_bildirim}"
        ham = ollama_uret(model, istem)
        yeni = temizle_saldiri(ham, yenilik, rnd)
        reddedilen += len(ham) - len(yeni)
        mesajlar += yeni
    print(f"  ({deneme} çağrı, {reddedilen} mesaj reddedildi: kopya / talepsiz / uzunluk)")
    return mesajlar[:adet]


# --- 2. Meşru havuzu gönderici bazlı ikiye böl (group split) ---
def mesru_bol(havuz):
    m = havuz[havuz["etiket"] == "meşru"].copy()
    m["grp"] = m["gonderen"].str.upper().str.replace(r"[^A-Z0-9ÇĞİÖŞÜ]", "", regex=True)
    gruplar = sorted(m["grp"].unique())                   # sabit başlangıç sırası, sonra tohumla karıştır
    np.random.default_rng(BOLME_TOHUM).shuffle(gruplar)
    egitim_grp, n = set(), 0
    for g in gruplar:                                      # karışık sırayla göndericileri eğitime al,
        if n >= len(m) / 2:                                # mesajların yarısına ulaşınca dur
            break
        egitim_grp.add(g)
        n += (m["grp"] == g).sum()
    egitim = m[m["grp"].isin(egitim_grp)]
    olcum = m[~m["grp"].isin(egitim_grp)]
    assert not set(egitim["grp"]) & set(olcum["grp"])      # sızıntı kontrolü: ortak gönderici yok
    return egitim, olcum


# --- 3. Bir veri setiyle üç tohum eğit, her birini ölç ---
def uc_tohum(X, y, tok, olcum):
    modeller, fa = {}, []
    for s in TOHUMLAR:
        AYAR["seed"] = s
        modeller[s] = egit(X, y, tok).to("cpu")
        torch.cuda.empty_cache()
        fa.append(float((puanla(modeller[s], tok, olcum) >= ESIK).mean()))
        print(f"  tohum {s}: yanlış alarm {fa[-1]:.1%}")
    AYAR["seed"] = 42
    return modeller, fa


def bant(liste):
    return {"ort": float(np.mean(liste)), "min": float(min(liste)), "max": float(max(liste))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tur", type=int, default=4)
    ap.add_argument("--adet", type=int, default=30)
    a = ap.parse_args()
    CIKTI.mkdir(parents=True, exist_ok=True)

    # --- 4. Veri: E + meşru eğitim yarısı; ölçüm yarısı hiç eğitime girmez ---
    X_E, y_E, ozet = veri_yukle()
    havuz = pd.read_csv("data/external/salih_havuz_sablon.csv", dtype=str, keep_default_na=False)
    m_egitim, m_olcum = mesru_bol(havuz)
    X0 = X_E + m_egitim["mesaj"].tolist()
    y0 = np.concatenate([y_E, np.zeros(len(m_egitim), dtype=int)])
    olcum = m_olcum["mesaj"].tolist()
    # bölmeyi kaydet: hangi gönderici hangi tarafta (tekrar üretilebilirlik)
    (CIKTI / "bolme.json").write_text(json.dumps(
        {"egitim": sorted(m_egitim["grp"].unique()), "olcum": sorted(m_olcum["grp"].unique())},
        ensure_ascii=False, indent=2), encoding="utf-8")
    bilinen = ["Degerli musterimiz kartiniz bloke oldu, [LINK] tiklayin",
               "Yurtiçi Kargo: kargonuz teslim edilemedi, adresinizi güncelleyin [LINK]"]
    print(f"E {len(X_E)} {ozet} + meşru eğitim {len(m_egitim)} ({m_egitim['grp'].nunique()} gönderici)")
    print(f"Yanlış alarm ölçüm seti: {len(olcum)} mesaj ({m_olcum['grp'].nunique()} gönderici, eğitimle ortak yok)")

    tok = AutoTokenizer.from_pretrained(AYAR["model"])
    yenilik = Yenilik(X0)
    kayit = []

    # --- 5. Tur 0: D0 üç tohum ---
    print("\n=== Tur 0: savunmacı D0 (E + meşru yarı), üç tohum ===")
    D0lar, fa0 = uc_tohum(X0, y0, tok, olcum)
    gurultu = bant(fa0)
    print(f"Yanlış alarm gürültü bandı: {gurultu['min']:.1%} – {gurultu['max']:.1%}")
    D0 = D0lar[42]
    bh0 = puanla(D0, tok, bilinen)
    kayit.append({"tur": 0, "saldirgan": None, "kacma": None, "yanlis_alarm": fa0[0],
                  "bilinen_1": float(bh0[0]), "bilinen_2": float(bh0[1]), "eklenen": 0})

    # --- 6. Döngü: saldırganlar sırayla ---
    D, ek_X, geri = D0, [], ""
    for k in range(1, a.tur + 1):
        saldirgan = SALDIRGANLAR[(k - 1) % len(SALDIRGANLAR)]
        print(f"\n=== Tur {k}: {saldirgan} ===")
        t0 = time.time()
        saldiri = saldiri_uret(saldirgan, a.adet, geri, yenilik, tohum=k)
        print(f"Saldırgan {len(saldiri)} yeni mesaj yazdı ({time.time() - t0:.0f} sn)")

        p = puanla(D, tok, saldiri)
        kacma = float((p < ESIK).mean()) if len(p) else float("nan")
        kacan = [m for m, s in zip(saldiri, p) if s < ESIK]
        pd.DataFrame({"tur": k, "saldirgan": saldirgan, "mesaj": saldiri, "p": p.round(4)}).to_csv(
            CIKTI / f"tur{k}_saldiri.csv", index=False, encoding="utf-8-sig")
        print(f"Kaçma oranı: {len(kacan)}/{len(saldiri)} = {kacma:.0%}")
        geri = geri_bildirim_yaz(saldiri, p)          # geri bildirim bir sonraki (diğer) saldırgana gider

        if kacan:
            ek_X += kacan
            if D is not D0:
                del D
            torch.cuda.empty_cache()
            D = egit(X0 + ek_X, np.concatenate([y0, np.ones(len(ek_X), dtype=int)]), tok).to("cpu")
            torch.cuda.empty_cache()
        else:
            print("Kaçan yok, savunmacı aynı kalıyor")

        fa = puanla(D, tok, olcum)
        bh = puanla(D, tok, bilinen)
        kayit.append({"tur": k, "saldirgan": saldirgan, "kacma": kacma,
                      "yanlis_alarm": float((fa >= ESIK).mean()),
                      "bilinen_1": float(bh[0]), "bilinen_2": float(bh[1]), "eklenen": len(ek_X)})
        print(f"Yeni savunmacı: yanlış alarm {(fa >= ESIK).sum()}/{len(olcum)}  bilinen hatalar {bh.round(2)}")

    # --- 7. Son savunmacı üç tohum (42 zaten var, 43/44 eğitilir) ---
    print("\n=== Son savunmacı, üç tohum ===")
    X_son = X0 + ek_X
    y_son = np.concatenate([y0, np.ones(len(ek_X), dtype=int)])
    del D
    torch.cuda.empty_cache()
    SONlar, fa_son = uc_tohum(X_son, y_son, tok, olcum)
    print(f"Son savunmacı yanlış alarm: {min(fa_son):.1%} – {max(fa_son):.1%}")

    # --- 8. Final: gemma, hem D0 hem son savunmacı üç tohumla ---
    print(f"\n=== Final test: {FINAL_SALDIRGAN} ===")
    final = saldiri_uret(FINAL_SALDIRGAN, a.adet, "", Yenilik(X0), tohum=999)
    p_D0 = {s: puanla(D0lar[s], tok, final) for s in TOHUMLAR}
    p_son = {s: puanla(SONlar[s], tok, final) for s in TOHUMLAR}
    k_D0 = [float((p_D0[s] < ESIK).mean()) for s in TOHUMLAR]
    k_son = [float((p_son[s] < ESIK).mean()) for s in TOHUMLAR]
    pd.DataFrame({"mesaj": final, **{f"p_D0_{s}": p_D0[s].round(4) for s in TOHUMLAR},
                  **{f"p_son_{s}": p_son[s].round(4) for s in TOHUMLAR}}).to_csv(
        CIKTI / "final_saldiri.csv", index=False, encoding="utf-8-sig")
    print(f"Kaçma oranı  D0: {min(k_D0):.0%} – {max(k_D0):.0%}   son: {min(k_son):.0%} – {max(k_son):.0%}")

    # --- 9. Ön kayıtlı karar ---
    kabul = bool(np.mean(k_son) <= KRITER["final_kacma_max"] and np.mean(fa_son) <= KRITER["yanlis_alarm_max"])
    print(f"\nKRİTER: final kaçma ort {np.mean(k_son):.1%} (<= {KRITER['final_kacma_max']:.0%}), "
          f"yanlış alarm ort {np.mean(fa_son):.1%} (<= {KRITER['yanlis_alarm_max']:.0%})  →  "
          f"{'KABUL: v3, v2 yerine geçer' if kabul else 'RED: sunumda v2 kalır'}")

    # --- 10. Kaydet: JSON, grafik, MLflow ---
    son = {"final_saldirgan": FINAL_SALDIRGAN, "final_adet": len(final),
           "final_kacma_D0": bant(k_D0), "final_kacma_son": bant(k_son),
           "yanlis_alarm_D0": gurultu, "yanlis_alarm_son": bant(fa_son), "kriter": KRITER, "kabul": kabul}
    Path("docs").mkdir(exist_ok=True)
    Path("docs/dongu_v3_sonuc.json").write_text(json.dumps(
        {"saldirganlar": SALDIRGANLAR, "mesru_egitim": len(m_egitim), "mesru_olcum": len(olcum),
         "turlar": kayit, **son, "ayar": vars(a)}, ensure_ascii=False, indent=2), encoding="utf-8")

    df = pd.DataFrame(kayit)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    ax[0].axhspan(gurultu["min"] * 100, gurultu["max"] * 100, color="orange", alpha=.15,
                  label="Yanlış alarm bandı D0 (3 tohum)")
    ax[0].plot(df["tur"][1:], df["kacma"][1:] * 100, "-", color="#1f77b4", alpha=.5)
    for ad, isaret in zip(SALDIRGANLAR, ["o", "D"]):              # her saldırgan kendi işaretiyle
        s = df[df["saldirgan"] == ad]
        ax[0].plot(s["tur"], s["kacma"] * 100, isaret, color="#1f77b4", ms=8, label=f"Kaçma ({ad})")
    ax[0].plot(df["tur"], df["yanlis_alarm"] * 100, "s--", color="orange", label="Yanlış alarm (ölçüm yarısı)")
    ax[0].set(xlabel="Tur", ylabel="%", title="Döngü v3: iki saldırgan + meşru karşı ağırlık", xticks=df["tur"])
    ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)

    x = np.arange(2)
    for i, (ad, b_once, b_son, renk) in enumerate([
            ("Kaçma (gemma4)", son["final_kacma_D0"], son["final_kacma_son"], "#2a7"),
            ("Yanlış alarm", son["yanlis_alarm_D0"], son["yanlis_alarm_son"], "orange")]):
        degerler = [b_once["ort"] * 100, b_son["ort"] * 100]
        hatalar = [[(b["ort"] - b["min"]) * 100 for b in (b_once, b_son)],
                   [(b["max"] - b["ort"]) * 100 for b in (b_once, b_son)]]
        ax[1].bar(x + (i - .5) * .38, degerler, .38, yerr=hatalar, capsize=5, color=renk, label=ad)
    ax[1].set_xticks(x, ["D0 (döngü öncesi)", f"Tur {a.tur} sonrası"])
    ax[1].set(ylabel="% (3 tohum ort., çubuk = min–max)", title=f"Final: {FINAL_SALDIRGAN} (hiç görülmemiş)")
    ax[1].legend(fontsize=8); ax[1].grid(alpha=.3, axis="y")
    fig.tight_layout()
    fig.savefig("docs/dongu_v3_grafigi.png", dpi=150)

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("dongu")
    with mlflow.start_run(run_name="dongu_v3"):
        mlflow.log_params({"saldirganlar": "+".join(SALDIRGANLAR), "final_saldirgan": FINAL_SALDIRGAN,
                           "tur": a.tur, "adet": a.adet, "esik": ESIK, "mesru_egitim": len(m_egitim),
                           "mesru_olcum": len(olcum), "kabul": kabul})
        for r in kayit:
            mlflow.log_metric("yanlis_alarm", r["yanlis_alarm"], step=r["tur"])
            if r["kacma"] is not None:
                mlflow.log_metric("kacma", r["kacma"], step=r["tur"])
        mlflow.log_metrics({"final_kacma_D0": son["final_kacma_D0"]["ort"],
                            "final_kacma_son": son["final_kacma_son"]["ort"],
                            "yanlis_alarm_son": son["yanlis_alarm_son"]["ort"]})
        mlflow.log_artifact("docs/dongu_v3_grafigi.png")
    print("\nBitti: docs/dongu_v3_grafigi.png, docs/dongu_v3_sonuc.json, data/external/dongu_v3/")


if __name__ == "__main__":
    main()
