import requests
import streamlit as st

API_ADRESI = "http://127.0.0.1:8000/tahmin"

st.title("SMS Dolandırıcılık Tespiti")

mesaj = st.text_area("SMS metnini yapıştır:")

if st.button("Kontrol et"):
    cevap = requests.post(API_ADRESI, json={"mesaj": mesaj})
    sonuc = cevap.json()
    if sonuc["etiket"] == "spam":
        st.error(f"⚠️ SPAM (skor: {sonuc['skor']})")
    else:
        st.success(f"✅ Meşru (skor: {sonuc['skor']})")
