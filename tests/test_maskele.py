import pytest
from src.maskele import maskele


@pytest.mark.parametrize("girdi,beklenen", [
    ("Hesabınız bloke oldu: https://banka-giris.xyz/dogrula", "Hesabınız bloke oldu: [LINK]"),
    ("Detay için www.ornek.com.tr adresine bakın.", "Detay için [LINK] adresine bakın."),
    ("bit.ly/abc123 tıklayın!", "[LINK] tıklayın!"),
    ("Bize yazın: destek@sirket.com", "Bize yazın: [EPOSTA]"),
    ("Arayın: 0532 123 45 67", "Arayın: [TEL]"),
    ("Arayın: +90 532 123 45 67", "Arayın: [TEL]"),
    ("Şubelerimiz: 4440202", "Şubelerimiz: [TEL]"),
    ("IBAN: TR33 0006 1005 1978 6457 8413 26", "IBAN: [IBAN]"),
    ("Kart: 4111 1111 1111 1111", "Kart: [KART]"),
    ("TC: 12345678901", "TC: [TC]"),
    ("Doğrulama kodunuz: 482915", "Doğrulama kodunuz: [KOD]"),
    ("Your code is 123456", "Your code is [KOD]"),
])
def test_maskeleme(girdi, beklenen):
    assert maskele(girdi) == beklenen


def test_tutar_ve_kampanya_korunur():
    t = "Akaryakıt alımında 100 TL'ye 10 TL puan, %40 indirim, 12,50 TL işlem ücreti."
    assert maskele(t) == t


def test_normal_cumle_degismez():
    t = "Akşam geç kalacağım, yemeği bensiz başlayın."
    assert maskele(t) == t


def test_string_olmayan_deger_aynen_doner():
    assert maskele(None) is None
