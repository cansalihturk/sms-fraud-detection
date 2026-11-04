import os
import requests
import streamlit as st

API_ADRESI = os.environ.get("API_ADRESI", "http://127.0.0.1:8000/tahmin") #“API_ADRESI diye bir ayar verilmişse onu kullan, verilmemişse yanındaki eski adresi kullan.”

ORNEKLER = {
    "(boş)": "",
    "Sahte ödül": "Tebrikler! 50.000 TL ödül kazandınız, hemen tıklayın: bit.ly/abc",
    "Günlük sohbet": "Akşam yemeğe geliyor musun? Ararım seni",
    "Banka doğrulama kodu": "Garanti BBVA doğrulama kodunuz: 482913. Kimseyle paylaşmayın.",
    "Reklam": "Sepette %50 indirim! Kampanya 3 gün sürecek. SMS iptal için RET yaz 3525'e gönder. MERSİS: [KART]",
}

st.set_page_config(page_title="SMS Dolandırıcılık Tespiti", page_icon="📱")

with st.sidebar:
    st.header("Hakkında")
    st.write(
        "Bu sistem bir SMS'in spam (reklam ya da dolandırıcılık) mı, "
        "yoksa meşru mu olduğunu tahmin eder."
    )
    st.subheader("Nasıl çalışır?")
    st.markdown(
        "1. Kişisel bilgiler maskelenir\n"
        "2. Model mesaja bir skor verir\n"
        "3. Karar ve nedeni gösterilir"
    )
    st.subheader("Not")
    st.caption(
        "Kararı model verir. Açıklama sadece nedenini gösterir. "
        "Mesajlar kaydedilmez."
    )

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;800&display=swap');
    </style>
    <div style="padding:24px;border-radius:16px;
                background:linear-gradient(90deg,#F97316,#E11D48);color:white;">
            <h1 style="margin:0;color:white;font-family:'Poppins',sans-serif;
                 font-weight:800;font-size:2rem;">📱 SMS Dolandırıcılık Tespiti</h1>
      <p style="margin:4px 0 0 0;font-family:'Poppins',sans-serif;
                font-weight:600;">Mesajı yapıştır, sistem spam mı meşru mu söylesin.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
secim = st.selectbox("Örnek mesaj seç (isteğe bağlı):", list(ORNEKLER))
mesaj = st.text_area("SMS metnini yapıştır:", value=ORNEKLER[secim])

if st.button("Kontrol et"):
    if not mesaj.strip():
        st.warning("Önce bir mesaj yaz.")
        st.stop()
    try:
        cevap = requests.post(API_ADRESI, json={"mesaj": mesaj}, timeout=10)
        cevap.raise_for_status()
        sonuc = cevap.json()
    except requests.exceptions.RequestException:
        st.error("Servis çalışmıyor. API'yi başlatıp tekrar dene.")
        st.stop()
    if sonuc["etiket"] == "spam":
        if sonuc["tur"] == "dolandırıcılık":
            renk, ikon, yazi = "#DC2626", "🚨", "SPAM: DOLANDIRICILIK ŞÜPHESİ"
        else:
            renk, ikon, yazi = "#F59E0B", "⚠️", "SPAM: REKLAM"
    else:
        renk, ikon, yazi = "#16A34A", "✅", "MEŞRU"
    st.markdown(
        f"""
        <div style="padding:20px;border-radius:16px;margin-top:12px;
                    background:{renk};color:white;">
          <h2 style="margin:0;color:white;">{ikon} {yazi}</h2>
          <p style="margin:4px 0 0 0;">Model skoru: {sonuc['skor']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("Neden bu karar?")
    for s in sonuc["aciklama"]:
        if s["etki"] > 0:
            st.markdown(f"🔴 `{s['kelime']}` → spam'e çekti (+{s['etki']})")
        else:
            st.markdown(f"🟢 `{s['kelime']}` → meşru'ya çekti ({s['etki']})")
