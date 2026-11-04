import re

REKLAM_ISARETLERI = [
    r"\bRET\b",
    r"SMS (almak istemiyorsan|iptal)",
    r"mersis",
    r"indirim|kampanya",
]


def reklam_isareti_say(mesaj):
    return sum(1 for desen in REKLAM_ISARETLERI if re.search(desen, mesaj, re.IGNORECASE))

DOLANDIRICILIK_ISARETLERI = [
    r"şifre|sifre",
    r"kart (bilgi|numara)",
    r"IBAN",
    r"kimlik",
    r"doğrula|dogrula",
    r"kapatıl|bloke|askıya|askiya",
    r"hemen (tıkla|tikla|ödeme|odeme|giriş|giris)",
    r"icra|haciz|ceza",
]

def dolandiricilik_isareti_say(mesaj): #sahte mesajların sık kullandığı kalıplar. | işareti “ya da” demek: şifre|sifre şifre ya da sifre yazılmış olabilir (Türkçe harfsiz yazılanları da yakalamak için)
    return sum(1 for desen in DOLANDIRICILIK_ISARETLERI if re.search(desen, mesaj, re.IGNORECASE))

def tur_bul(mesaj):
    reklam = reklam_isareti_say(mesaj)
    sahte = dolandiricilik_isareti_say(mesaj)
    if sahte >= 1 and sahte > reklam:
        return "dolandırıcılık"
    return "reklam"
