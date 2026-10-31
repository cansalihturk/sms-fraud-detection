"""Klasik modellerin adil karşılaştırması: NB, LR, SVM × kelime / harf TF-IDF.
İkili sınıflandırma (spam / meşru), 5 katlı grup duyarlı CV. PROJECT.md "Deney protokolü".

Çalıştırma (repo kökünden, önce `python -m src.bol` çalışmış olmalı):
    python -m src.baseline              # tabloyu yazar + CV hata analizi (dosyaya)
    python -m src.baseline --kaydet     # ayrıca en iyi modeli models/baseline_best.joblib'e yazar

Girdi : data/processed/tr_train.csv (fold sütunu src.bol tarafından eklendi)
        tr_test.csv'ye BU DOSYA DOKUNMAZ (test kilitli, en sonda tek sefer kullanılır).

Protokol:
  - belirsiz == 'e' olan mesajlar eğitimden çıkarılır.
  - Hepsinde aynı temizlik: src.temizle.Temizleyici (Pipeline'ın ilk adımı).
  - Katlar: train'deki `fold` sütunu (PredefinedSplit), aynı şablon aynı katta.
  - Her (model, özellik) için küçük bir ayar ızgarası aranır; ana ölçü spam F1.
  - Hata analizi TEST'te değil, CV tahminleriyle (cross_val_predict) train üzerinde yapılır.
Pozitif sınıf = spam (reklam + dolandırıcılık).
NOT: CV puanı ayarlar o puana göre seçildiği için biraz iyimsektir; dürüst sayı test'te, en sonda.
"""
import sys
from pathlib import Path

import pandas as pd
from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, PredefinedSplit, cross_val_predict
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.temizle import Temizleyici

GIRDI = Path("data/processed/tr_train.csv")
HATA_YOLU = Path("data/processed/cv_hatalar.csv")
MODEL_YOLU = Path("models/baseline_best.joblib")
KELIME_DESENI = r"\[[A-ZÇĞİÖŞÜ]+\]|\w+|[!%?:]"   # maskeler ve !, %, ?, : ayrı kelime sayılır
OLCUTLER = {"f1": "f1", "kesinlik": "precision", "duyarlılık": "recall", "makro f1": "f1_macro"}

# ad -> (model üreten fonksiyon, ayar ızgarası)
MODELLER = {
    "NB": (lambda: MultinomialNB(), {"model__alpha": [0.1, 0.5, 1.0]}),
    "LR": (lambda: LogisticRegression(max_iter=1000, class_weight="balanced"),
           {"model__C": [0.1, 1, 10]}),
    "SVM": (lambda: LinearSVC(class_weight="balanced", random_state=55),
            {"model__C": [0.1, 1, 10]}),
}
OZELLIKLER = {
    "kelime": (lambda: TfidfVectorizer(analyzer="word", sublinear_tf=True, lowercase=False,
                                       token_pattern=KELIME_DESENI),
               {"vek__ngram_range": [(1, 1), (1, 2)]}),
    "harf": (lambda: TfidfVectorizer(analyzer="char_wb", sublinear_tf=True, lowercase=False, min_df=2),
             {"vek__ngram_range": [(2, 5), (3, 5)]}),
}


def pipeline_kur(model_ad, ozellik_ad):
    model, _ = MODELLER[model_ad]
    vek, _ = OZELLIKLER[ozellik_ad]
    return Pipeline([("temizle", Temizleyici()), ("vek", vek()), ("model", model())])


def izgara(model_ad, ozellik_ad):
    return {"temizle__ascii": [False, True], **OZELLIKLER[ozellik_ad][1], **MODELLER[model_ad][1]}


def ayar_yazisi(p):
    gosterilen = {k.split("__")[1]: v for k, v in p.items()}
    return ", ".join(f"{k}={v}" for k, v in gosterilen.items())


def main(kaydet=False):
    if not GIRDI.exists():
        sys.exit(f"{GIRDI} yok. Önce: python -m src.bol")
    df = pd.read_csv(GIRDI, keep_default_na=False)
    belirsiz = int((df["belirsiz"] == "e").sum())
    df = df[df["belirsiz"] != "e"].reset_index(drop=True)   # protokol: eğitimde belirsiz çıkarılır
    X, y = df["mesaj"], (df["ikili"] == "spam").astype(int)
    kat = PredefinedSplit(df["fold"].to_numpy())
    print(f"{belirsiz} belirsiz mesaj çıkarıldı -> {len(df)} mesaj "
          f"(spam {int(y.sum())}, meşru {int((1 - y).sum())}), {df['fold'].nunique()} kat\n")

    satirlar, modeller = [], {}
    for m in MODELLER:
        for o in OZELLIKLER:
            arama = GridSearchCV(pipeline_kur(m, o), izgara(m, o), scoring=OLCUTLER,
                                 refit="f1", cv=kat, n_jobs=-1)
            arama.fit(X, y)
            i, r = arama.best_index_, arama.cv_results_
            satir = {"model": m, "özellik": o}
            for ad in OLCUTLER:
                satir[ad] = f"{r[f'mean_test_{ad}'][i]:.3f} ± {r[f'std_test_{ad}'][i]:.3f}"
            satir["f1_ort"] = r["mean_test_f1"][i]
            satir["en iyi ayar"] = ayar_yazisi(arama.best_params_)
            satirlar.append(satir)
            modeller[(m, o)] = arama.best_estimator_
            print(f"  {m} + {o} tamam")

    tablo = pd.DataFrame(satirlar).sort_values("f1_ort", ascending=False)
    print("\n5 katlı CV (ortalama ± sapma), spam F1'e göre sıralı:")
    print(tablo.drop(columns="f1_ort").to_string(index=False))

    en = tablo.iloc[0]
    en_model = modeller[(en["model"], en["özellik"])]
    print(f"\nEn iyi: {en['model']} + {en['özellik']}")

    tahmin = cross_val_predict(clone(en_model), X, y, cv=kat)
    hata = df.loc[tahmin != y.to_numpy(), ["id", "mesaj", "ikili"]].copy()
    hata["tahmin"] = ["spam" if t else "meşru" for t in tahmin[tahmin != y.to_numpy()]]
    hata.to_csv(HATA_YOLU, index=False)
    print(f"CV hata analizi: {len(hata)} mesaj yanlış, hepsi {HATA_YOLU} dosyasında (test'e bakılmadı).")
    for _, s in hata.head(10).iterrows():
        print(f"  id {s['id']:>5} gerçek={s['ikili']:<5} tahmin={s['tahmin']:<5} | {s['mesaj'][:70]!r}")

    if kaydet:
        import joblib
        MODEL_YOLU.parent.mkdir(exist_ok=True)
        joblib.dump(en_model, MODEL_YOLU)
        print(f"\nModel yazıldı: {MODEL_YOLU}")


if __name__ == "__main__":
    main(kaydet="--kaydet" in sys.argv)
