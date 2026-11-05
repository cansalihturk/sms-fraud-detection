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
    r"part.?time|evden (çalış|calis)|(günlük|gunluk) (maaş|maas|ücret|ucret)|işe alım|ise alim",
    r"bitcoin|\bBTC\b|kripto|binance",
    r"adres(inizi)? (güncelle|guncelle)|adresi nedeniyle|iade edilmi",
    r"teslim edilemedi|gümrük|gumruk|(teslimat|işlem|islem) (ücret|ucret)|iade edilmek üzere|iade edilecek|geri gonderilecek|geri gönderilecek",
    r"adresinizi bulamad|konum paylaş|konum paylas|adres onay",
    r"kazandınız|kazandiniz|tebrikler",
    r"bilgilerinizi (gir|paylaş|paylas)|hesap bilgilerinizi|formu doldur",
    r"siz yapmadıysanız|siz yapmadiysaniz|yapmadıysanız|yapmadiysaniz",
    r"kredi başvurusu|kredi basvurusu|havale geldi|harcama yapıldı|harcama yapildi|trafik ceza|destek ödemesi|destek odemesi",
    r"son uyarı|son uyari|abonelik iptal|ONAY yaz",
]

def dolandiricilik_isareti_say(mesaj): #sahte mesajların sık kullandığı kalıplar. | işareti “ya da” demek: şifre|sifre şifre ya da sifre yazılmış olabilir (Türkçe harfsiz yazılanları da yakalamak için)
    return sum(1 for desen in DOLANDIRICILIK_ISARETLERI if re.search(desen, mesaj, re.IGNORECASE))

def tur_bul(mesaj):
    reklam = reklam_isareti_say(mesaj)
    sahte = dolandiricilik_isareti_say(mesaj)
    if sahte >= 1 and sahte > reklam:
        return "dolandırıcılık"
    return "reklam"
