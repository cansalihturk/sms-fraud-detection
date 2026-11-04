from pathlib import Path          #dosya yolu aracı ve modeli açacak araç

import joblib
from src.maskele import maskele #telefon numarası, link, isim gibi kişisel bilgileri maskeleyen fonksiyonumuz. Modeli maskelenmiş mesajlarla eğittik, o yüzden yeni mesajı da önce maskelemeliyiz.

MODEL_YOLU = Path(__file__).resolve().parent.parent / "models" / "svm_v1.joblib"  #Böylece kod hangi klasörden çalıştırılırsa çalıştırılsın modeli bulur.

_model = None


def yukle_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_YOLU)    #kutu boşsa modeli diskten açar, doluysa tekrar açmaz. Neden: modeli her mesajda yeniden açmak yavaş, bir kez açıp saklıyoruz.
    return _model

def tahmin(mesaj):
    temiz = maskele(mesaj)   #gelen ham mesajı maskeler
    model = yukle_model()    #modeli getirir
    skor = float(model.decision_function([temiz])[0]) #Eksi ise meşru, artı ise spam tarafı. Ne kadar büyükse o kadar emin demek.[0] listedeki tek sonucu alır, float düz sayıya çevirir.
    etiket = "spam" if skor > 0 else "meşru"          #skor 0'dan büyükse “spam”, değilse “meşru”
    return {"etiket": etiket, "skor": round(skor, 3)}
def acikla(mesaj, en_cok=5):
    temiz = maskele(mesaj)
    model = yukle_model()
    temel = float(model.decision_function([temiz])[0])

    kelimeler = temiz.split()
    sonuclar = []
    for i, kelime in enumerate(kelimeler):
        eksik = " ".join(kelimeler[:i] + kelimeler[i + 1:])
        yeni = float(model.decision_function([eksik])[0])
        etki = temel - yeni
        sonuclar.append({"kelime": kelime, "etki": round(etki, 3)})

    sonuclar.sort(key=lambda s: abs(s["etki"]), reverse=True)
    return sonuclar[:en_cok]
