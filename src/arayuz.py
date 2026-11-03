import requests
import streamlit as st

API_ADRESI = "http://127.0.0.1:8000/tahmin"

ORNEKLER = {
    "(boş)": "",
    "Sahte ödül": "Tebrikler! 50.000 TL ödül kazandınız, hemen tıklayın: bit.ly/abc",
    "Günlük sohbet": "Akşam yemeğe geliyor musun? Ararım seni",
    "Banka doğrulama kodu": "Garanti BBVA doğrulama kodunuz: 482913. Kimseyle paylaşmayın.",
}

st.set_page_config(page_title="SMS Dolandırıcılık Tespiti", page_icon="📱")

st.title("📱 SMS Dolandırıcılık Tespiti")
st.caption("Mesajı yapıştır, sistem spam mı meşru mu söylesin.")

secim = st.selectbox("Örnek mesaj seç (isteğe bağlı):", list(ORNEKLER))
mesaj = st.text_area("SMS metnini yapıştır:", value=ORNEKLER[secim])

if st.button("Kontrol et"):
    cevap = requests.post(API_ADRESI, json={"mesaj": mesaj})
    sonuc = cevap.json()
    if sonuc["etiket"] == "spam":
        st.error(f"⚠️ SPAM (skor: {sonuc['skor']})")
    else:
        st.success(f"✅ Meşru (skor: {sonuc['skor']})")
