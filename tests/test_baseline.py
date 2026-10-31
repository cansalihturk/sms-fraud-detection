import pytest

from src.baseline import MODELLER, OZELLIKLER, izgara, pipeline_kur

X = ["hemen ara kazandiniz [TEL] odul", "kredi icin tikla [LINK]", "bedava odul hemen ara",
     "aksam yemege geliyor musun", "toplanti yarin saat 10 da", "annem seni sordu ara onu"] * 4
Y = [1, 1, 1, 0, 0, 0] * 4


@pytest.mark.parametrize("model", list(MODELLER))
@pytest.mark.parametrize("ozellik", list(OZELLIKLER))
def test_her_kombinasyon_egitilir_ve_ayirir(model, ozellik):
    p = pipeline_kur(model, ozellik).fit(X, Y)
    assert list(p.predict(["hemen ara odul kazandiniz [LINK]", "yarin toplantiya geliyorum"])) == [1, 0]


def test_izgara_pipeline_adimlarina_uyar():
    for m in MODELLER:
        for o in OZELLIKLER:
            p = pipeline_kur(m, o)
            p.set_params(**{k: v[0] for k, v in izgara(m, o).items()})   # hata vermemeli
