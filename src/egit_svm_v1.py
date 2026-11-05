"""svm_v1'i sıfırdan eğitir.

Çalıştırma (proje kökünden):  python -m src.egit_svm_v1 [çıktı_yolu]

Okuduğu veriler (git'te YOK, yerelde bulunmalı):
  data/processed/tr_train.csv            kolay eğitim verisi (belirsiz == "h")
  data/sentetik/sentetik_*.csv           sentetik v2 (LLM ile üretilmiş)
  data/external/zor_gercek_hepsi.csv     telefonlardan toplanan zor gerçek mesajlar
  data/external/salih_kurumsal_etiketli.csv   Salih'in 58 mesajı (belirsiz == "h")

Varsayılan çıktı models/svm_v1_yeniden.joblib: mevcut svm_v1.joblib'in üstüne yazmaz.
"""
import sys
import glob
from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

from src.temizle import Temizleyici

# 1) Dört veri parçasını oku
train = pd.read_csv("data/processed/tr_train.csv")
train = train[train["belirsiz"] == "h"].reset_index(drop=True)
X = train["mesaj"]
y = (train["ikili"] == "spam")

sent = pd.concat(
    [pd.read_csv(d) for d in sorted(glob.glob("data/sentetik/sentetik_*.csv"))],
    ignore_index=True,
)

zor = pd.read_csv("data/external/zor_gercek_hepsi.csv")
zor = zor[zor["etiket"].notna()].reset_index(drop=True)

salih = pd.read_csv("data/external/salih_kurumsal_etiketli.csv")
salih = salih[salih["belirsiz"] == "h"].drop_duplicates("mesaj").reset_index(drop=True)

# 2) Birleştir. Etiket: meşru değilse True (spam = reklam + dolandırıcılık)
tum_mesaj = pd.concat([X, sent["mesaj"], zor["mesaj"], salih["mesaj"]], ignore_index=True)
y_tum = pd.concat(
    [y, sent["etiket"] != "meşru", zor["etiket"] != "meşru", salih["etiket"] != "meşru"],
    ignore_index=True,
)
tum = pd.DataFrame({"mesaj": tum_mesaj, "spam": y_tum}).drop_duplicates("mesaj")

print("parça sayıları:", len(X), len(sent), len(zor), len(salih), "| toplam:", len(tum_mesaj))
print("tekrarsız eğitim mesajı:", len(tum), "(beklenen: 935)")
if len(tum) != 935:
    print("UYARI: beklenen 935 değil, veri dosyaları svm_v1 eğitildiğindekinden farklı olabilir")

# 3) Model: harf n-gram TF-IDF + LinearSVC
model = Pipeline([
    ("temizle", Temizleyici()),
    ("vek", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2,
                            sublinear_tf=True, lowercase=False)),
    ("model", LinearSVC(class_weight="balanced", random_state=55)),
])
model.fit(tum["mesaj"], tum["spam"])

# 4) Kaydet
cikti = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/svm_v1_yeniden.joblib")
cikti.parent.mkdir(exist_ok=True)
joblib.dump(model, cikti)
print("kaydedildi:", cikti)

# 5) Varsa mevcut svm_v1 ile karşılaştır (aynı modeli üretiyor muyuz?)
eski_yol = Path("models/svm_v1.joblib")
if eski_yol.exists() and eski_yol.resolve() != cikti.resolve():
    s_yeni = model.decision_function(tum["mesaj"])
    s_eski = joblib.load(eski_yol).decision_function(tum["mesaj"])
    print("eski modelle aynı karar oranı:", ((s_yeni > 0) == (s_eski > 0)).mean())
    print("skorlarda en büyük fark:", abs(s_yeni - s_eski).max())
