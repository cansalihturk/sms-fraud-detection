"""Mesajı klasik modeller (TF-IDF + LR/SVM/NB/XGBoost) için hazırlayan temizlik.

Kullanım:
    from src.temizle import temizle
    temizle("İNDİRİM!!! 50 TL  [LINK]")   # -> "indirim!!! 00 tl  [LINK]" (boşluklar tek olur)

Yaptıkları (sırayla):
  1. Maskeleri ([LINK], [TEL], [KOD], [İSİM]...) olduğu gibi korur.
  2. Türkçe'ye uygun küçük harf: İ -> i, I -> ı, sonra lower().
  3. Her rakamı 0 yapar (hane sayısı kalır: kısa kod ile telefon numarası farklı görünür).
  4. Art arda boşlukları tek boşluk yapar.
  5. Noktalamayı SİLMEZ (!, %, : spam ipucudur).
  İsteğe bağlı: ascii=True ise ç,ğ,ı,ö,ş,ü -> c,g,i,o,s,u (veride aksansız yazılmış mesaj çok).

BERTurk / XLM-R için bu fonksiyon KULLANILMAZ: onlar mesajı kendi tokenizer'ıyla işler.

Temizleyici sınıfı: aynı fonksiyonu scikit-learn Pipeline'ının ilk adımı olarak kullanmak için.
    Pipeline([("temizle", Temizleyici()), ("vek", TfidfVectorizer(lowercase=False)), ("model", ...)])
"""
import re

from sklearn.base import BaseEstimator, TransformerMixin

# [LINK], [TEL], [İSİM] gibi büyük harfli köşeli parantez etiketleri
MASKE = re.compile(r"(\[[A-ZÇĞİÖŞÜ]{2,}\])")
ASCII = str.maketrans("çğıöşü", "cgiosu")


def turkce_kucuk(metin):
    # Python'un lower() fonksiyonu Türkçe İ ve I harflerini yanlış çevirir
    return metin.replace("İ", "i").replace("I", "ı").lower()


def temizle(metin, ascii=False):
    if not isinstance(metin, str):
        return metin
    parcalar = MASKE.split(metin)      # tek indisler maskeler, çift indisler normal metin
    for i in range(0, len(parcalar), 2):
        p = turkce_kucuk(parcalar[i])
        if ascii:
            p = p.translate(ASCII)
        parcalar[i] = re.sub(r"\d", "0", p)
    return re.sub(r"\s+", " ", "".join(parcalar)).strip()


class Temizleyici(BaseEstimator, TransformerMixin):
    """temizle'yi Pipeline içinde kullanmak için sarmalayıcı (herkes aynı temizliği kullansın)."""

    def __init__(self, ascii=False):
        self.ascii = ascii

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [temizle(m, ascii=self.ascii) for m in X]
