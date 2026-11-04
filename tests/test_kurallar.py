from src.kurallar import tur_bul


def test_kargo_dolandiriciligi():
    mesaj = "Yurtiçi Kargo: Kargonuz adres eksikliği nedeniyle teslim edilemedi. Güncelleyin: [LINK]"
    assert tur_bul(mesaj) == "dolandırıcılık"


def test_banka_dolandiriciligi():
    mesaj = "Akbank: Kartınızdan 4.850 TL harcama yapıldı. Siz yapmadıysanız hemen iptal edin: [LINK]"
    assert tur_bul(mesaj) == "dolandırıcılık"


def test_is_ilani_dolandiriciligi():
    mesaj = "Merhaba, evden part-time çalışmaya davet ediyoruz, günlük maaş 800-3000 TL. WhatsApp: [LINK]"
    assert tur_bul(mesaj) == "dolandırıcılık"


def test_reklam_reklam_kalir():
    mesaj = "Kampanya: %30 indirim sizi bekliyor. SMS almak istemiyorsan RET yaz."
    assert tur_bul(mesaj) == "reklam"
