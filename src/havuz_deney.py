"""Havuz deneyi: Salih'in SMS havuzu son modeli iyileştiriyor mu? (E ve H, isteğe bağlı SVM)

Çalıştırma (repo kökünden; GPU boş, Ollama kapalı):
    python -m src.havuz_deney
    python -m src.havuz_deney --svm models/svm_e.joblib      # Esra'nın SVM'i gelince

Modeller:
    E : son model tarifi (936 mesaj)
    H : E + Salih'in havuzu (şablon tekrarsız, RET ifadesi kesilmiş), ÖLÇÜM GÖNDERİCİLERİ HARİÇ
    E ve H üçer tohumla (42/43/44) eğitilir → gürültü bandı.

Sınav (iki model de hiç görmedi):
    1. Yanlış alarm: havuzdaki meşruların ölçüm yarısı (dongu_v3 bölmesi), Salih'in 58'i ve zor setle
       ortak göndericiler de çıkarılır → tamamen görülmemiş göndericiler.
    2. Dolandırıcılık: gemma4:e4b final saldırıları (döngü v2 + v3, 60 mesaj). Geri bildirimsiz üretildi,
       hiçbir modele göre şekillenmedi. Tur saldırıları (qwen/aya) KULLANILMAZ: XLM-R'a göre seçildiler.

Ön kayıt (koşudan ÖNCE yazıldı, sonuca göre değişmez):
    H, son model E'nin yerine ancak iki koşul birlikte sağlanırsa geçer (3 tohum):
      - dolandırıcılık: H yakalama ortalaması >= E yakalama ortalaması - 2 puan   (kötü değil)
      - yanlış alarm : H ortalaması E'den en az 2 puan düşük VE bantlar örtüşmüyor (H max < E min)
    KABUL ise H tüm havuzla (ölçüm dahil) bir kez eğitilip models/xlmr_h/ altına kaydedilir.
    SVM bu karara girmez; sadece aynı sınavdaki sonucu raporlanır.

Çıktı: docs/havuz_deney_sonuc.json (sadece sayılar), MLflow deney grubu "havuz_deney".
Havuz bu bilgisayardan çıkmaz.
"""
import argparse
import json
import re
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
import sklearn
import torch
import transformers
from transformers import AutoTokenizer

from src.son_model import AYAR, ESIK, egit, veri_yukle

D = Path("data/external")
TOHUMLAR = [42, 43, 44]
KRITER = {"dol_tolerans": 0.02, "ya_iyilesme": 0.02}       # ön kayıt
GERCEK_ETIKET = {"1", "spam", "reklam", "dolandırıcılık"}

# --- 1. RET kuralı (notebook 07/09 ile aynı): kural etiketli veride kuralın baktığı ifade kesilir ---
NO = r"(?:\d{4}|\[TEL\])"
RET = re.compile(
    r"sms\s*(?:iptal|ipt|ret|almak\s+istemiyor|almamak)|\bRET\b|IZINYOK|IPTALIZIN|\bcks\s*:"
    r"|yaz(?:ıp|ip|ın|in|arak)?\s*" + NO +
    r"|" + NO + r"\s*['’]?\s*(?:e|a|ye|ya)\s+(?:gönder|gonder|ilet)"
    r"|(?:iptal|ret)\w*\s+yaz", re.IGNORECASE)


def ret_kes(metin):
    m = RET.search(metin)
    return metin[:m.start()].rstrip(" .,:;-") if m else metin


def grupla(seri):                                          # gruplama v2
    return seri.str.upper().str.replace(r"[^A-Z0-9ÇĞİÖŞÜ]", "", regex=True)


# --- 2. Veri: havuz bölmesi + sınav setleri ---
def veri_hazirla():
    havuz = pd.read_csv(D / "salih_havuz_sablon.csv", dtype=str, keep_default_na=False)
    havuz["grp"] = grupla(havuz["gonderen"])
    bolme = json.loads((D / "dongu_v3" / "bolme.json").read_text(encoding="utf-8"))
    olcum_grp = set(bolme["olcum"])

    # 2a. E'nin gördüğü göndericiler: Salih'in 58'i + zor set
    sal = pd.read_csv(D / "salih_kurumsal_etiketli.csv", dtype=str, keep_default_na=False)
    zor = pd.read_csv(D / "zor_gercek_hepsi.csv")
    zor = zor[zor["etiket"].notna()]
    goruldu = set(grupla(sal["gonderen"])) | set(grupla(zor["gonderen"].astype(str)))

    # 2b. yanlış alarm sınavı: ölçüm yarısının meşruları, görülen göndericiler hariç
    sinav = havuz[(havuz["etiket"] == "meşru") & havuz["grp"].isin(olcum_grp) & ~havuz["grp"].isin(goruldu)]
    assert not set(sinav["grp"]) & goruldu

    # 2c. H'nin havuz kısmı: ölçüm göndericileri TAMAMEN hariç, RET kesilmiş
    ek = havuz[~havuz["grp"].isin(olcum_grp)].copy()
    ek["mesaj"] = ek["mesaj"].apply(ret_kes)
    ek = ek[ek["mesaj"].str.len() >= 15]
    assert not set(ek["grp"]) & set(sinav["grp"])            # sızıntı kontrolü
    assert ek["mesaj"].str.contains(RET).sum() == 0

    # 2d. dolandırıcılık sınavı: gemma final setleri
    gemma = pd.concat([pd.read_csv(D / "dongu" / "final_saldiri.csv"),
                       pd.read_csv(D / "dongu_v3" / "final_saldiri.csv")])["mesaj"].tolist()
    return havuz, ek, sinav["mesaj"].tolist(), sinav["grp"].nunique(), gemma


# --- 3. Puanlama ---
def puanla(model, tok, mesajlar):
    model.to("cuda").eval()
    p = []
    with torch.no_grad():
        for i in range(0, len(mesajlar), 16):
            kod = tok(mesajlar[i:i + 16], padding=True, truncation=True,
                      max_length=AYAR["max_len"], return_tensors="pt").to("cuda")
            with torch.autocast("cuda", dtype=torch.bfloat16):
                p.append(torch.softmax(model(**kod).logits.float(), dim=-1)[:, 1].cpu().numpy())
    return np.concatenate(p)


def uc_tohum(ad, X, y, tok, mesru, gemma):
    ya, yak = [], []
    for s in TOHUMLAR:
        AYAR["seed"] = s
        model = egit(X, y, tok)
        ya.append(float((puanla(model, tok, mesru) >= ESIK).mean()))
        yak.append(float((puanla(model, tok, gemma) >= ESIK).mean()))
        print(f"  {ad} tohum {s}: yanlış alarm {ya[-1]:.1%}  gemma yakalama {yak[-1]:.1%}")
        del model
        torch.cuda.empty_cache()
    AYAR["seed"] = 42
    return {"yanlis_alarm": ya, "yakalama": yak}


def ozet(liste):
    return {"ort": float(np.mean(liste)), "min": float(min(liste)), "max": float(max(liste))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svm", help="Esra'nın SVM E dosyası (.joblib), isteğe bağlı")
    a = ap.parse_args()

    # --- 4. Veri ---
    X_E, y_E, kaynak = veri_yukle()
    havuz, ek, mesru, n_grp, gemma = veri_hazirla()
    X_H = X_E + ek["mesaj"].tolist()
    y_H = np.concatenate([y_E, (ek["etiket"] != "meşru").astype(int).to_numpy()])
    print(f"E: {len(X_E)} {kaynak}")
    print(f"H: {len(X_H)} = E + havuz {len(ek)} ({ek['etiket'].value_counts().to_dict()}, RET kesilmiş)")
    print(f"Sınav: {len(mesru)} görülmemiş meşru ({n_grp} gönderici) + {len(gemma)} gemma saldırısı")

    # --- 5. E ve H, üçer tohum ---
    tok = AutoTokenizer.from_pretrained(AYAR["model"])
    print("\n=== E ===")
    sE = uc_tohum("E", X_E, y_E, tok, mesru, gemma)
    print("\n=== H ===")
    sH = uc_tohum("H", X_H, y_H, tok, mesru, gemma)

    # --- 6. SVM (isteğe bağlı, deterministik: tek koşu) ---
    svm = None
    if a.svm:
        model = joblib.load(a.svm)
        t = lambda m: np.array([str(v).lower() in GERCEK_ETIKET for v in model.predict(m)], dtype=float)
        svm = {"yanlis_alarm": float(t(mesru).mean()), "yakalama": float(t(gemma).mean())}

    # --- 7. Tablo ---
    print(f"\n{'Model':<6}{'Yanlış alarm (' + str(len(mesru)) + ')':<26}{'Gemma yakalama (' + str(len(gemma)) + ')':<26}")
    for ad, s in [("E", sE), ("H", sH)]:
        y_, k_ = ozet(s["yanlis_alarm"]), ozet(s["yakalama"])
        print(f"{ad:<6}{y_['ort']:.1%} ({y_['min']:.1%}–{y_['max']:.1%}){'':<6}"
              f"{k_['ort']:.1%} ({k_['min']:.1%}–{k_['max']:.1%})")
    if svm:
        print(f"{'SVM':<6}{svm['yanlis_alarm']:.1%}{'':<20}{svm['yakalama']:.1%}")

    # --- 8. Ön kayıtlı karar ---
    yE, yH = ozet(sE["yanlis_alarm"]), ozet(sH["yanlis_alarm"])
    kE, kH = ozet(sE["yakalama"]), ozet(sH["yakalama"])
    dol_ok = kH["ort"] >= kE["ort"] - KRITER["dol_tolerans"]
    ya_ok = (yE["ort"] - yH["ort"] >= KRITER["ya_iyilesme"]) and (yH["max"] < yE["min"])
    kabul = bool(dol_ok and ya_ok)
    print(f"\nKRİTER  dolandırıcılık kötü değil: {'✓' if dol_ok else '✗'}  "
          f"yanlış alarm ≥2 puan iyi ve bant dışı: {'✓' if ya_ok else '✗'}  →  "
          f"{'KABUL: son model H' if kabul else 'RED: son model E kalır'}")

    # --- 9. KABUL ise: H'yi tüm havuzla (ölçüm dahil) bir kez eğit, kaydet ---
    if kabul:
        tum = havuz.copy()
        tum["mesaj"] = tum["mesaj"].apply(ret_kes)
        tum = tum[tum["mesaj"].str.len() >= 15]
        X_son = X_E + tum["mesaj"].tolist()
        y_son = np.concatenate([y_E, (tum["etiket"] != "meşru").astype(int).to_numpy()])
        print(f"\nSon H eğitiliyor: {len(X_son)} mesaj")
        model = egit(X_son, y_son, tok)
        hedef = Path("models/xlmr_h")
        hedef.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(hedef)
        tok.save_pretrained(hedef)
        (hedef / "kunye.json").write_text(json.dumps({
            "tarif": "H: E + Salih havuzu (şablon tekrarsız, RET kesilmiş, tamamı)",
            "kaynaklar": {**kaynak, "salih_havuz": len(tum)}, "egitim_boyu": len(X_son),
            "ayar": AYAR, "esik": ESIK, "etiketler": {"0": "meşru", "1": "spam (reklam + dolandırıcılık)"},
            "secim": "havuz_deney ön kayıtlı kriter KABUL", "not": "Girdi önce src.maskele'den geçmeli.",
            "surumler": {"torch": torch.__version__, "transformers": transformers.__version__,
                         "scikit-learn": sklearn.__version__}}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Kaydedildi:", hedef)

    # --- 10. Kaydet: sadece sayılar ---
    sonuc = {"sinav": {"mesru": len(mesru), "mesru_gonderici": n_grp, "gemma": len(gemma)},
             "E": {"yanlis_alarm": yE, "yakalama": kE, "ham": sE},
             "H": {"yanlis_alarm": yH, "yakalama": kH, "ham": sH, "havuz_ek": len(ek)},
             "SVM": svm, "kriter": KRITER, "kabul": kabul}
    Path("docs").mkdir(exist_ok=True)
    Path("docs/havuz_deney_sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("havuz_deney")
    with mlflow.start_run(run_name="E_vs_H"):
        mlflow.log_params({**AYAR, "tohumlar": "42/43/44", "sinav_mesru": len(mesru),
                           "sinav_gemma": len(gemma), "havuz_ek": len(ek), "kabul": kabul})
        mlflow.log_metrics({"E_yanlis_alarm": yE["ort"], "H_yanlis_alarm": yH["ort"],
                            "E_yakalama": kE["ort"], "H_yakalama": kH["ort"]})
        if svm:
            mlflow.log_metrics({"SVM_yanlis_alarm": svm["yanlis_alarm"], "SVM_yakalama": svm["yakalama"]})
    print("\nBitti: docs/havuz_deney_sonuc.json")


if __name__ == "__main__":
    main()
