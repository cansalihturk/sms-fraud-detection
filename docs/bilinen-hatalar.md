# Bilinen hatalar (zor örnekler)

Elle yazılmış ya da gözlenmiş, modelin zorlandığı örnekler.

Kurallar:
- Eğitime ve test'e konmaz, ayrı liste olarak durur.
- Ayarlar bu örneklere göre değiştirilmez.
- Yeni bir model ya da deney sonrası (dolandırıcılık ek deneyi, saldırgan döngüsü) tekrar ölçülür: öncesi / sonrası.

| # | Mesaj (maskeli) | Gerçek | Model | Skor | Neden yanılmış olabilir |
|---|---|---|---|---|---|
| 1 | Degerli musterimiz kartiniz bloke oldu, [LINK] tiklayin | dolandırıcılık | SVM harf (Gün 5): spam, kıl payı | +0.221 (karar skoru) | Train'deki spam neredeyse tamamen reklam. Reklam kelimesi yok; "müşterimiz", "oldu" meşruya itiyor. Gerçek dolandırıcılık 6 örnek. Maske [URL] yazılınca model kararsız kalıp meşru dedi; doğru maske [LINK] |
| 2 | Yurtiçi Kargo: kargonuz teslim edilemedi, adresinizi güncelleyin [LINK] | dolandırıcılık | XLM-R E (Gün 8, son model): meşru | 0.44 (spam olasılığı) | Kısa ve aciliyetsiz ("24 saat", "son uyarı" yok); gerçek kargo bildirimine çok benziyor. Son model "kurumsal dil = spam" kısayolunu bıraktığı için bu tür mesajlarda sınırda kalıyor |
