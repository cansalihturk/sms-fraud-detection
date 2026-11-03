from fastapi import FastAPI   #API’yi kuran araç ve gelen verinin biçimini tarif eden araç
from pydantic import BaseModel

from src.tahmin import tahmin

app = FastAPI(title="SMS Dolandırıcılık Tespiti")


class Istek(BaseModel):
    mesaj: str


@app.get("/")
def ana_sayfa():
    return {"durum": "çalışıyor"}


@app.post("/tahmin")
def tahmin_et(istek: Istek):
    return tahmin(istek.mesaj)
