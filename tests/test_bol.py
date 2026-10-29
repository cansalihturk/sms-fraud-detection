import pandas as pd

from src.bol import ESIK, grup_bol, gruplari_bul, kat_ata, normalle, sizinti_raporu


def sahte_veri():
    satirlar = []
    for i in range(40):  # tek şablondan 40 reklam
        satirlar.append(("reklam", f"Mudo mağazalarında %{i + 10} indirim! Detay için {1000 + i} numarayı arayın"))
    for i in range(40):  # tek şablondan 40 meşru
        satirlar.append(("meşru", f"Sayın müşterimiz {2000 + i} TL ekstre borcunuz son ödeme tarihi 15 Kasım"))
    farkli = ["Akşam yemeğe geliyor musun", "Kargonuz şubeye ulaştı", "Toplantı yarın saat onda",
              "Hesabınızı doğrulamak için bu linke tıklayın [LINK]", "Annem seni sordu ara onu",
              "Büyük ödül kazandınız hemen arayın", "Bugün hava çok güzel", "Faturanız oluşturuldu",
              "Ders notlarını atar mısın", "Kredi başvurunuz onaylandı hemen tıklayın",
              "Maça gidiyor muyuz", "Paketiniz teslim edildi", "Doğum günün kutlu olsun",
              "Kampanya sonu yarın kaçırmayın", "Randevunuz onaylandı", "Hesap özetiniz hazır",
              "Sınav sonuçları açıklandı", "Yeni sezon ürünleri geldi", "Eve geç gelirim", "Şifreniz 0000 kimseyle paylaşmayın"]
    for i, m in enumerate(farkli):
        satirlar.append(("dolandırıcılık" if i < 3 else ("reklam" if i % 2 else "meşru"), m))
    return pd.DataFrame(satirlar, columns=["etiket", "mesaj"])


def test_normalle_rakamlari_sifirlar():
    assert normalle("  ABC  123  ") == "abc 000"


def test_sablon_mesajlar_ayni_gruba_girer():
    d = sahte_veri()
    grup, _ = gruplari_bul([normalle(m) for m in d["mesaj"]])
    assert len(set(grup[:40])) == 1
    assert len(set(grup[40:80])) == 1
    assert grup[0] != grup[40]


def test_sablon_tek_parcada_ve_sizinti_yok():
    d = sahte_veri()
    grup, s = gruplari_bul([normalle(m) for m in d["mesaj"]])
    parca = grup_bol(d, grup)
    assert parca.iloc[:40].nunique() == 1
    assert parca.iloc[40:80].nunique() == 1
    assert set(parca) <= {"train", "test"}
    assert all(v < ESIK for _, _, v in sizinti_raporu(parca, s))


def test_tohum_ayni_sonucu_verir():
    d = sahte_veri()
    grup, _ = gruplari_bul([normalle(m) for m in d["mesaj"]])
    assert grup_bol(d, grup).equals(grup_bol(d, grup))


def test_cv_katlarinda_sablon_bolunmez():
    d = sahte_veri()
    d["grup"], _ = gruplari_bul([normalle(m) for m in d["mesaj"]])
    kat = kat_ata(d)
    assert set(kat) <= set(range(5))
    for g, alt in d.groupby("grup"):
        assert kat[alt.index].nunique() == 1
