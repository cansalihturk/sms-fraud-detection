from fastapi import FastAPI   #API’yi kuran araç ve gelen verinin biçimini tarif eden araç
from pydantic import BaseModel

from src.kurallar import tur_bul
from src.tahmin import acikla, tahmin

app = FastAPI(title="SMS Dolandırıcılık Tespiti")


class Istek(BaseModel):
    mesaj: str


@app.get("/")
def ana_sayfa():
    return {"durum": "çalışıyor"}


@app.post("/tahmin")
def tahmin_et(istek: Istek):
    sonuc = tahmin(istek.mesaj)
    sonuc["aciklama"] = acikla(istek.mesaj)
    sonuc["tur"] = tur_bul(istek.mesaj) if sonuc["etiket"] == "spam" else None
    return sonuc
