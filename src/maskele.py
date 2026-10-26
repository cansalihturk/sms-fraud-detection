"""SMS metinlerindeki kişisel bilgileri maskeler.

Kullanım:
    python -m src.maskele girdi.csv cikti.csv --kolon mesaj
    python -m src.maskele spam.csv cikti.csv --kolon v2 --kodlama latin-1

Maskelenenler: e-posta, link, IBAN, telefon, kart, TC kimlik, doğrulama kodu.
Maskelenmeyenler: kişi adları ve adresler. Bunları etiketlerken elle [İSİM] ve
[ADRES] ile değiştirin. Tutarlar ve kampanya metni bilerek silinmez.
"""
import argparse
import csv
import re

_TLD = (r"com\.tr|org\.tr|gov\.tr|net\.tr|edu\.tr|com|net|org|tr|xyz|info|co|me|"
        r"ly|gl|top|site|link|click|online|app|club|shop|live|icu|cc")

EPOSTA = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
LINK = re.compile(
    rf"(?:https?://\S+|www\.\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:{_TLD})\b(?:/\S*)?)",
    re.IGNORECASE,
)
IBAN = re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.IGNORECASE)
# +90 5xx xxx xx xx, 05xx xxx xx xx, 5xx xxx xx xx, 444 x xxx kısa numaralar
TEL = re.compile(
    r"(?<!\d)(?:\+?90[\s-]?)?0?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"
    r"|(?<!\d)444[\s-]?\d[\s-]?\d{3}(?!\d)"
)
KART = re.compile(r"(?<!\d)(?:\d{4}[\s-]?){3}\d{1,4}(?!\d)")
TC = re.compile(r"(?<!\d)\d{11}(?!\d)")
KOD = re.compile(
    r"(?i)\b(kod\w*|şifre\w*|sifre\w*|code|pin|otp)(\s*(?:[:=]|\bis\b)?\s*)(\d{4,8})(?!\d)"
)

_SONDA = ".,;:!?)\"'"


def _link_degistir(m: re.Match) -> str:
    s = m.group(0)
    kalan = ""
    while s and s[-1] in _SONDA:
        kalan = s[-1] + kalan
        s = s[:-1]
    return "[LINK]" + kalan


def maskele(metin: str) -> str:
    """Metindeki kişisel bilgileri etiketlerle değiştirir."""
    if not isinstance(metin, str):
        return metin
    t = EPOSTA.sub("[EPOSTA]", metin)
    t = LINK.sub(_link_degistir, t)
    t = IBAN.sub("[IBAN]", t)
    t = TEL.sub("[TEL]", t)
    t = KART.sub("[KART]", t)
    t = TC.sub("[TC]", t)
    t = KOD.sub(lambda m: f"{m.group(1)}{m.group(2)}[KOD]", t)
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description="CSV'deki mesaj sütununu maskeler.")
    ap.add_argument("girdi")
    ap.add_argument("cikti")
    ap.add_argument("--kolon", default="mesaj", help="Maskelenecek sütun adı")
    ap.add_argument("--kodlama", default="utf-8-sig", help="Girdi kodlaması (UCI için latin-1)")
    a = ap.parse_args()
    with open(a.girdi, newline="", encoding=a.kodlama) as f:
        okuyucu = csv.DictReader(f)
        alanlar = list(okuyucu.fieldnames or [])
        if a.kolon not in alanlar:
            raise SystemExit(f"'{a.kolon}' sütunu yok. Sütunlar: {alanlar}")
        satirlar = list(okuyucu)
    hedef = a.kolon + "_maskeli"
    with open(a.cikti, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=alanlar + [hedef])
        yazici.writeheader()
        for s in satirlar:
            s[hedef] = maskele(s[a.kolon])
            yazici.writerow(s)
    print(f"{len(satirlar)} satır maskelendi -> {a.cikti}")
    print("Not: kişi adları ve adresler otomatik maskelenmez, elle kontrol edin.")


if __name__ == "__main__":
    main()
