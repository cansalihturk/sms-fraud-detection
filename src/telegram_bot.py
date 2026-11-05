import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM = f"https://api.telegram.org/bot{TOKEN}"
API = os.environ.get("API_ADRESI", "http://127.0.0.1:8000/tahmin")

son_id = 0
print("Bot çalışıyor. Durdurmak için Ctrl+C.")

while True:
    istek = requests.get(
        f"{TELEGRAM}/getUpdates",
        params={"offset": son_id + 1, "timeout": 30},
        timeout=40,
    )
    for guncelleme in istek.json()["result"]:
        son_id = guncelleme["update_id"]
        gelen = guncelleme.get("message", {})
        metin = gelen.get("text")
        sohbet_id = gelen.get("chat", {}).get("id")
        if not metin:
            continue
        if metin == "/start":
            requests.post(
                f"{TELEGRAM}/sendMessage",
                json={"chat_id": sohbet_id, "text": "Merhaba! Bana bir SMS yaz, spam mi diye bakayım."},
                timeout=10,
            )
            continue

        tahmin = requests.post(API, json={"mesaj": metin}, timeout=10).json()

        if tahmin["etiket"] == "spam":
            cevap = f"⚠️ SPAM ({tahmin['tur']})"
        else:
            cevap = "✅ Temiz görünüyor"

        etkili = [a for a in tahmin["aciklama"] if a["etki"] > 0][:3]
        if etkili:
            kelimeler = ", ".join(a["kelime"].strip(",.!?:;") for a in etkili)
            cevap += f"\nKararı etkileyen kelimeler: {kelimeler}"

        requests.post(
            f"{TELEGRAM}/sendMessage",
            json={"chat_id": sohbet_id, "text": cevap},
            timeout=10,
        )
