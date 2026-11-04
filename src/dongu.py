"""Saldırgan / savunmacı döngüsü (kırmızı / mavi takım). PROJECT.md: "Gün 10 döngü grafiği".

Çalıştırma (repo kökünden; Ollama açık, notebook kernel'leri kapalı):
    python -m src.dongu                 # 4 tur, turda 30 saldırı
    python -m src.dongu --tur 3 --adet 20

Akış:
    Tur 0 : savunmacı D0 = XLM-R, E verisiyle (son_model.py ile aynı tarif)
    Tur k : saldırgan (qwen3.5:9b) 'adet' dolandırıcılık SMS'i yazar
            → mevcut savunmacı puanlar → KAÇMA ORANI (yakalanmayanların payı)
            → kaçanlar eğitime eklenir, savunmacı sıfırdan yeniden eğitilir
            → YANLIŞ ALARM: savunmacının hiç görmediği gerçek meşru kurumsal mesajlarda
              (Salih'in havuzundaki meşrular, eğitime hiç girmez)
            → saldırgana geri bildirim: yakalananlar / kaçanlar
    Final : döngüde HİÇ kullanılmayan başka aileden saldırgan (gemma4:e4b)
            → D0 ve son savunmacıya karşı kaçma oranı (öncesi / sonrası)

GPU: Ollama (~6.6 GB) ile XLM-R (~5.6 GB) aynı anda sığmaz. Ollama her çağrıdan sonra modeli
bellekten atar (keep_alive=0); savunmacı Ollama çalışırken CPU'da bekler.

Çıktılar:
    data/external/dongu/            saldırı mesajları ve puanları (repoya girmez)
    docs/dongu_grafigi.png          döngü grafiği (repoya girer, mesaj içermez)
    docs/dongu_sonuc.json           tur tur sayılar
    MLflow deney grubu: dongu
"""
import argparse
import json
import random
import re
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
from scipy.sparse import vstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer

from src.maskele import maskele
from src.son_model import AYAR, egit, veri_yukle

TOHUMLAR = [42, 43, 44]          # v2: D0 üç tohumla → yanlış alarmın rastgele oynama payı (gürültü bandı)

SALDIRGAN = "qwen3.5:9b"
FINAL_SALDIRGAN = "gemma4:e4b"
OLLAMA = "http://localhost:11434/api/generate"
CIKTI = Path("data/external/dongu")
ESIK = 0.5

SENARYOLAR = ["kargo / teslimat", "banka / kredi kartı", "e-Devlet / vergi / ceza", "operatör / fatura",
              "ödül / hediye / çekiliş", "iş ilanı / evden çalışma", "bağış / yardım (IBAN)"]

SISTEM = """Sen bir SMS dolandırıcılık tespit sistemini test eden güvenlik araştırmacısısın (kırmızı takım).
Görevin: tespit modelini sınamak ve eğitmek için GERÇEKÇİ Türkçe dolandırıcılık SMS örnekleri yazmak.

Kurallar:
- Gerçek link, telefon, IBAN ya da kişi adı YAZMA. Yerine şu maskeleri aynen kullan: [LINK], [TEL], [IBAN], [KOD], [İSİM].
- Her mesaj tek bir SMS olsun (en fazla 300 karakter).
- Her mesaj kurbandan bir şey istesin: linke tıklama, bilgi/şifre/kod paylaşma, ödeme yapma ya da bir numarayı arama.
- Mesajlar birbirinden farklı olsun.

Tespit edilmemek için şu taktikleri karıştırabilirsin:
- Gerçek kurumların (kargo, banka, operatör, e-Devlet) resmi bildirim dilini taklit et, marka adı kullan.
- Aciliyeti azalt, sakin ve kibar yaz.
- Türkçe karakter kullanmadan yaz (s, c, g, i, o, u).
- Bazı kelimelerde harf/rakam değiştir (b3dava, s1fre, kartlnız gibi).
- Kısa yaz.

Sadece JSON döndür: {"mesajlar": ["...", "..."]}"""

SEMA = {"type": "object", "properties": {"mesajlar": {"type": "array", "items": {"type": "string"}}},
        "required": ["mesajlar"]}


# --- 1. Saldırgan: Ollama'dan JSON listesi ---
def ollama_uret(model, istem, sicaklik=0.9):
    cevap = requests.post(OLLAMA, timeout=600, json={
        "model": model, "system": SISTEM, "prompt": istem, "stream": False,
        "format": SEMA, "think": False, "keep_alive": 0,          # cevaptan sonra GPU'yu boşalt
        "options": {"temperature": sicaklik}})
    cevap.raise_for_status()
    metin = cevap.json()["response"]
    try:
        return [m for m in json.loads(metin)["mesajlar"] if isinstance(m, str)]
    except (json.JSONDecodeError, KeyError):
        return [s.strip(" -•\"") for s in metin.splitlines() if len(s.strip()) > 20]


# --- 2. Maske normalleştirme: modelin [Link], [URL], [Takip No] gibi farklı yazımlarını bizim maskelere çevir ---
MASKE_DUZELT = [
    (r"\[(?:link|url|bağlantı|baglanti|web[^\]]*)\]", "[LINK]"),
    (r"\[(?:tel|telefon|numara|phone|gsm)[^\]]*\]", "[TEL]"),
    (r"\[(?:kod|code|şifre|sifre|otp)[^\]]*\]", "[KOD]"),
    (r"\[iban[^\]]*\]", "[IBAN]"),
    (r"\[(?:isim|ad|ad soyad|müşteri adı|musteri adi)\]", "[İSİM]"),
    (r"\[(?:takip|sipariş|siparis|gönderi|gonderi|kargo|referans|abone)[^\]]*\]", "0000000"),
]
# v2: modelin uydurduğu maskeler ([OPERATÖR], [KURUM], [BANKA]...) gerçek veride yok → kısayol olur.
# Gerçek bir marka adıyla değiştir; tanınmayan diğer [...] etiketleri sil.
MARKA = {
    r"\[(?:operatör|operator|gsm operatörü)[^\]]*\]": ["Turkcell", "Vodafone", "Türk Telekom"],
    r"\[(?:banka|bankanız|bankaniz)[^\]]*\]": ["Garanti BBVA", "Ziraat Bankası", "Akbank", "Yapı Kredi", "İş Bankası"],
    r"\[(?:kurum|şirket|sirket|firma|marka|kargo firması|kargo firmasi)[^\]]*\]": ["Yurtiçi Kargo", "PTT", "Aras Kargo", "Trendyol", "Hepsiburada"],
}
IZINLI = {"[LINK]", "[TEL]", "[IBAN]", "[KOD]", "[İSİM]", "[KART]", "[EPOSTA]", "[TC]"}
TALEP = re.compile(r"\[(?:LINK|TEL|IBAN|KOD)\]|tıkla|tikla|ara(?:y[ıi]n)?\b|öde|ode|şifre|sifre|kart|bilgi|doğrula|dogrula",
                   re.IGNORECASE)


# v2: yenilik filtresi. Önceki saldırılara ya da eğitim verisine çok benzeyen mesaj reddedilir
# (Tur 1'de kaçan mesajın Tur 2'de neredeyse aynısının yazılması "kopya" sayılır).
class Yenilik:
    # HashingVectorizer: sözlük öğrenmez, yeni mesajın bütün harf parçalarını sayar.
    # (TfidfVectorizer referansa fit edilseydi, yeni mesajdaki tanımadığı parçaları yok sayıp benzerliği şişirirdi.)
    # Ölçüm: neredeyse aynı mesaj ~0.9, aynı konu farklı ifade ~0.2-0.6. Eşik 0.7.
    vek = HashingVectorizer(analyzer="char_wb", ngram_range=(3, 5), alternate_sign=False, n_features=2 ** 20)

    def __init__(self, referans, esik=0.7):
        self.esik = esik
        self.M = self.vek.transform(list(referans))

    def yeni_mi(self, m):
        return cosine_similarity(self.vek.transform([m]), self.M).max() < self.esik

    def ekle(self, mesajlar):
        if mesajlar:
            self.M = vstack([self.M, self.vek.transform(mesajlar)])


def temizle_saldiri(mesajlar, yenilik, rnd):
    temiz = []
    for m in mesajlar:
        m = maskele(" ".join(m.split()))                         # gerçek link/numara kalırsa maskele
        for desen, yerine in MASKE_DUZELT:
            m = re.sub(desen, yerine, m, flags=re.IGNORECASE)
        for desen, markalar in MARKA.items():
            m = re.sub(desen, lambda _: rnd.choice(markalar), m, flags=re.IGNORECASE)
        m = re.sub(r"\[[^\]]+\]", lambda x: x.group(0) if x.group(0) in IZINLI else "", m)
        m = " ".join(m.split())
        if len(m) < 20 or len(m) > 400 or not TALEP.search(m):
            continue                                             # çok kısa/uzun ya da talep içermiyor
        if not yenilik.yeni_mi(m):
            continue                                             # kopya (eğitim verisine, önceki saldırılara ya da bu partiye)
        yenilik.ekle([m])                                        # bu partideki sonraki mesajlar buna da bakar
        temiz.append(m)
    return temiz


def saldiri_uret(model, adet, geri_bildirim, yenilik, tohum):
    rnd = random.Random(tohum)
    mesajlar, deneme, reddedilen = [], 0, 0
    while len(mesajlar) < adet and deneme < adet // 5 + 6:       # 10'arlı çağrılar, sınırlı deneme
        deneme += 1
        senaryo = ", ".join(rnd.sample(SENARYOLAR, 3))
        istem = f"Senaryolar: {senaryo}.\n10 farklı dolandırıcılık SMS'i yaz.\n{geri_bildirim}"
        ham = ollama_uret(model, istem)
        yeni = temizle_saldiri(ham, yenilik, rnd)                # kabul edilenler referansa eklendi
        reddedilen += len(ham) - len(yeni)
        mesajlar += yeni
    print(f"  ({deneme} çağrı, {reddedilen} mesaj reddedildi: kopya / talepsiz / uzunluk)")
    return mesajlar[:adet]


def geri_bildirim_yaz(mesajlar, puanlar):
    if not mesajlar:
        return ""
    sira = np.argsort(puanlar)
    kacan = [mesajlar[i] for i in sira if puanlar[i] < ESIK][:5]
    yakalanan = [mesajlar[i] for i in sira[::-1] if puanlar[i] >= ESIK][:5]
    satirlar = ["Önceki turda tespit modeli şu mesajları YAKALADI, bunlara benzeme:"]
    satirlar += [f"- {m}" for m in yakalanan] or ["- (yok)"]
    satirlar += ["Şu mesajlar YAKALANMADI. Bunların FİKRİNİ farklı kelimelerle, farklı kurumlar ve farklı "
                 "senaryolarla yeniden yaz; cümleleri kopyalama (benzer mesajlar otomatik reddedilir):"]
    satirlar += [f"- {m}" for m in kacan] or ["- (yok)"]
    return "\n".join(satirlar)


# --- 3. Savunmacı: puanlama (spam olasılığı) ---
def puanla(model, tok, mesajlar):
    model.to("cuda").eval()
    p = []
    with torch.no_grad():
        for i in range(0, len(mesajlar), 16):
            kod = tok(mesajlar[i:i + 16], padding=True, truncation=True,
                      max_length=AYAR["max_len"], return_tensors="pt").to("cuda")
            with torch.autocast("cuda", dtype=torch.bfloat16):
                p.append(torch.softmax(model(**kod).logits.float(), dim=-1)[:, 1].cpu().numpy())
    model.to("cpu")                                              # GPU'yu Ollama'ya bırak
    torch.cuda.empty_cache()
    return np.concatenate(p) if p else np.array([])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tur", type=int, default=4)
    ap.add_argument("--adet", type=int, default=30)
    a = ap.parse_args()
    CIKTI.mkdir(parents=True, exist_ok=True)

    # --- 4. Veri: E tarifi + yanlış alarm ölçüm seti (havuz meşruları, eğitime hiç girmez) ---
    X_E, y_E, ozet = veri_yukle()
    havuz = pd.read_csv("data/external/salih_havuz_sablon.csv", dtype=str, keep_default_na=False)
    mesru = havuz.loc[havuz["etiket"] == "meşru", "mesaj"].tolist()
    bilinen = ["Degerli musterimiz kartiniz bloke oldu, [LINK] tiklayin",
               "Yurtiçi Kargo: kargonuz teslim edilemedi, adresinizi güncelleyin [LINK]"]
    print(f"E verisi {len(X_E)} {ozet} | yanlış alarm seti: {len(mesru)} gerçek meşru kurumsal mesaj")

    tok = AutoTokenizer.from_pretrained(AYAR["model"])
    yenilik = Yenilik(X_E)                                       # eğitim verisine benzeyen saldırı da kopya sayılır
    kayit = []

    # --- 5. Tur 0: D0, üç tohumla (v2). Döngü 42 tohumlu D0 ile devam eder ---
    print("\n=== Tur 0: savunmacı D0, üç tohum ===")
    D0lar, fa_tohum = {}, []
    for s in TOHUMLAR:
        AYAR["seed"] = s                                         # son_model.egit bu sözlükten okuyor
        D0lar[s] = egit(X_E, y_E, tok).to("cpu")
        torch.cuda.empty_cache()
        fa_tohum.append(float((puanla(D0lar[s], tok, mesru) >= ESIK).mean()))
        print(f"  tohum {s}: yanlış alarm {fa_tohum[-1]:.1%}")
    AYAR["seed"] = 42
    gurultu = {"ort": float(np.mean(fa_tohum)), "min": float(min(fa_tohum)), "max": float(max(fa_tohum))}
    print(f"Yanlış alarm gürültü bandı (aynı veri, farklı tohum): {gurultu['min']:.1%} – {gurultu['max']:.1%}")

    D0 = D0lar[42]
    bh0 = puanla(D0, tok, bilinen)
    kayit.append({"tur": 0, "kacma": None, "yanlis_alarm": fa_tohum[0],
                  "bilinen_1": float(bh0[0]), "bilinen_2": float(bh0[1]), "eklenen": 0})
    print(f"Bilinen hatalar (tohum 42): {bh0.round(2)}")

    D, ek_X, geri = D0, [], ""
    for k in range(1, a.tur + 1):
        print(f"\n=== Tur {k} ===")
        # 5a. saldırı üret (savunmacı CPU'da, GPU Ollama'nın)
        t0 = time.time()
        saldiri = saldiri_uret(SALDIRGAN, a.adet, geri, yenilik, tohum=k)
        print(f"Saldırgan {len(saldiri)} yeni mesaj yazdı ({time.time() - t0:.0f} sn)")

        # 5b. mevcut savunmacıya karşı kaçma oranı
        p = puanla(D, tok, saldiri)
        kacma = float((p < ESIK).mean()) if len(p) else float("nan")
        kacan = [m for m, s in zip(saldiri, p) if s < ESIK]
        pd.DataFrame({"tur": k, "mesaj": saldiri, "p": p.round(4)}).to_csv(
            CIKTI / f"tur{k}_saldiri.csv", index=False, encoding="utf-8-sig")
        print(f"Kaçma oranı: {len(kacan)}/{len(saldiri)} = {kacma:.0%}")
        geri = geri_bildirim_yaz(saldiri, p)

        # 5c. kaçanları eğitime ekle, savunmacıyı sıfırdan yeniden eğit (v2: kaçan yoksa eğitme)
        if kacan:
            ek_X += kacan
            if D is not D0:
                del D
            torch.cuda.empty_cache()
            D = egit(X_E + ek_X, np.concatenate([y_E, np.ones(len(ek_X), dtype=int)]), tok).to("cpu")
            torch.cuda.empty_cache()
        else:
            print("Kaçan yok, savunmacı aynı kalıyor")

        # 5d. yeni savunmacının yanlış alarmı + bilinen hatalar
        fa = puanla(D, tok, mesru)
        bh = puanla(D, tok, bilinen)
        kayit.append({"tur": k, "kacma": kacma, "yanlis_alarm": float((fa >= ESIK).mean()),
                      "bilinen_1": float(bh[0]), "bilinen_2": float(bh[1]), "eklenen": len(ek_X)})
        print(f"Yeni savunmacı: yanlış alarm {(fa >= ESIK).sum()}/{len(mesru)}  bilinen hatalar {bh.round(2)}")

    # --- 6. Final test: döngüde hiç görülmemiş başka aileden saldırgan ---
    print(f"\n=== Final test: {FINAL_SALDIRGAN} ===")
    yenilik_final = Yenilik(X_E)                                 # final saldırgan Qwen'in mesajlarını hiç görmedi
    final = saldiri_uret(FINAL_SALDIRGAN, a.adet, "", yenilik_final, tohum=999)
    kacma_D0 = [float((puanla(D0lar[s], tok, final) < ESIK).mean()) for s in TOHUMLAR]
    p_once, p_sonra = puanla(D0, tok, final), puanla(D, tok, final)
    pd.DataFrame({"mesaj": final, "p_D0": p_once.round(4), "p_son": p_sonra.round(4)}).to_csv(
        CIKTI / "final_saldiri.csv", index=False, encoding="utf-8-sig")
    son = {"final_saldirgan": FINAL_SALDIRGAN, "final_adet": len(final),
           "final_kacma_D0": float(np.mean(kacma_D0)), "final_kacma_D0_min": min(kacma_D0),
           "final_kacma_D0_max": max(kacma_D0), "final_kacma_son": float((p_sonra < ESIK).mean())}
    print(f"Kaçma oranı  D0 (3 tohum): {min(kacma_D0):.0%} – {max(kacma_D0):.0%}   "
          f"son savunmacı: {son['final_kacma_son']:.0%}")

    # --- 7. Kaydet: JSON, grafik, MLflow ---
    Path("docs").mkdir(exist_ok=True)
    Path("docs/dongu_sonuc.json").write_text(json.dumps(
        {"saldirgan": SALDIRGAN, "turlar": kayit, "yanlis_alarm_gurultu": gurultu, **son, "ayar": vars(a)},
        ensure_ascii=False, indent=2), encoding="utf-8")

    df = pd.DataFrame(kayit)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].axhspan(gurultu["min"] * 100, gurultu["max"] * 100, color="orange", alpha=.15,
                  label="Yanlış alarm gürültü bandı (3 tohum)")
    ax[0].plot(df["tur"][1:], df["kacma"][1:] * 100, "o-", label=f"Kaçma oranı ({SALDIRGAN})")
    ax[0].plot(df["tur"], df["yanlis_alarm"] * 100, "s--", color="orange", label="Yanlış alarm (gerçek meşru)")
    ax[0].set(xlabel="Tur", ylabel="%", title="Saldırgan / savunmacı döngüsü", xticks=df["tur"])
    ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    ort, hata = son["final_kacma_D0"] * 100, (son["final_kacma_D0_max"] - son["final_kacma_D0_min"]) * 50
    ax[1].bar(["D0 (döngü öncesi,\n3 tohum)", f"Tur {a.tur} sonrası"], [ort, son["final_kacma_son"] * 100],
              yerr=[hata, 0], capsize=6, color=["#999", "#2a7"])
    ax[1].set(ylabel="Kaçma oranı (%)", title=f"Final test: {FINAL_SALDIRGAN} (hiç görülmemiş aile)")
    ax[1].grid(alpha=.3, axis="y")
    fig.tight_layout()
    fig.savefig("docs/dongu_grafigi.png", dpi=150)

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("dongu")
    with mlflow.start_run(run_name=f"dongu_{SALDIRGAN}"):
        mlflow.log_params({"saldirgan": SALDIRGAN, "final_saldirgan": FINAL_SALDIRGAN,
                           "tur": a.tur, "adet": a.adet, "esik": ESIK, "yanlis_alarm_seti": len(mesru)})
        for r in kayit:
            mlflow.log_metric("yanlis_alarm", r["yanlis_alarm"], step=r["tur"])
            if r["kacma"] is not None:
                mlflow.log_metric("kacma", r["kacma"], step=r["tur"])
        mlflow.log_metrics({k: v for k, v in son.items() if isinstance(v, float)})
        mlflow.log_artifact("docs/dongu_grafigi.png")
    print("\nBitti: docs/dongu_grafigi.png, docs/dongu_sonuc.json, data/external/dongu/")


if __name__ == "__main__":
    main()
