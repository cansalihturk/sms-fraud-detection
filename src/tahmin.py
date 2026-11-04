from pathlib import Path          #dosya yolu aracı ve modeli açacak araç

import joblib
from src.maskele import maskele #telefon numarası, link, isim gibi kişisel bilgileri maskeleyen fonksiyonumuz. Modeli maskelenmiş mesajlarla eğittik, o yüzden yeni mesajı da önce maskelemeliyiz.

MODEL_YOLU = Path(__file__).resolve().parent.parent / "models" / "svm_v0.joblib"  #Böylece kod hangi klasörden çalıştırılırsa çalıştırılsın modeli bulur.

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
