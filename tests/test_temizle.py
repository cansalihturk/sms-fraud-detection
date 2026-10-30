import pytest

from src.temizle import temizle


@pytest.mark.parametrize("girdi,beklenen", [
    ("İNDİRİM", "indirim"),                     # büyük İ -> i
    ("IŞIK", "ışık"),                           # büyük I -> ı
    ("Hemen ARA", "hemen ara"),
    ("Kodunuz 482915 geldi", "kodunuz 000000 geldi"),   # rakam -> 0, hane sayısı korunur
    ("50 TL  ve   %40", "00 tl ve %00"),        # boşluklar tek, % korunur
    ("  başta ve sonda  ", "başta ve sonda"),
    ("Hemen ara!!! Kaçırma:", "hemen ara!!! kaçırma:"),  # noktalama silinmez
])
def test_temizle(girdi, beklenen):
    assert temizle(girdi) == beklenen


def test_maskeler_korunur():
    assert temizle("Tıkla: [LINK] Ara: [TEL] Sayın [İSİM]") == "tıkla: [LINK] ara: [TEL] sayın [İSİM]"


def test_maske_icindeki_rakam_yoksa_etkilenmez_ama_disindaki_degisir():
    assert temizle("[TEL] 1234 [KOD]") == "[TEL] 0000 [KOD]"


def test_ascii_secenegi():
    assert temizle("Çiğ KÖFTE şükür", ascii=True) == "cig kofte sukur"
    assert temizle("Çiğ KÖFTE") == "çiğ köfte"          # varsayılan: harfler korunur


def test_string_olmayan_deger_aynen_doner():
    assert temizle(None) is None
