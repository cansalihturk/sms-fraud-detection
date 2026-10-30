# SMS Dolandırıcılık Tespiti

## Hedef
Türkçe ve İngilizce SMS'lerde dolandırıcılığı tespit etmek; sistemi
kelime bozma ve prompt injection'a karşı test etmek. İki ek parça:
(1) saldırgan LLM ile dedektörü turlar halinde eğiten kırmızı/mavi takım
döngüsü, (2) şüpheli SMS'i analiz eden Telegram botu. Süre: 2 hafta.
Sınıflar: dolandırıcılık / reklam (spam) / meşru.

## Veri kaynakları
- TR: https://huggingface.co/datasets/akuysal/turkishSMS-ds
- EN: https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset
- Risk testi (eğitim için değil): https://www.kaggle.com/datasets/muhammadahmerkhan/ai-agent-security-and-real-world-incidents-2024-26
- Kendi örneklerimiz: resmî uyarılar, gönüllü mesajlar (maskeli), sentetik (ayrı etiket)
- Lisanslar indirmeden önce kontrol edilir, kaynaklar README'de listelenir.

## Klasör yapısı
```
data/raw/        ham veri (repoya girmez)
data/processed/  maskelenmiş, temiz veri
notebooks/       EDA ve denemeler
src/             maskeleme, özellik çıkarımı, eğitim kodu
models/          kayıtlı modeller
app/             FastAPI ve bot
tests/           pytest testleri
docs/            etiket rehberi, Model Card, risk kaydı
```

## Görev dağılımı
| Alan | Esra | Salih |
|---|---|---|
| Veri | Türkçe toplama, maskeleme, etiketleme | İngilizce ayırma, doğrulama, DVC |
| Modeller | Kural motoru, LR, XGBoost hibrit, BERTurk | NB, SVM, MLP, BiLSTM, XLM-R, transfer deneyi |
| Döngü | Kelime bozma testi | Saldırgan/savunmacı döngüsü |
| Sistem | FastAPI, Docker, CI, Telegram botu | MLflow, SHAP + Ollama, injection testi, Evidently |
| Belgeler | Model Card, risk kaydı, Streamlit paneli | README, mimari şeması |
| Birlikte | Etiket rehberi, gün 7 tablosu, sunum, demo | |

## Kararlar
- LLM karar vermez, sadece açıklama yazar.
- Dengesizlik için önce class weight; SMOTE sadece eğitim kısmında küçük deney.
- Döngünün final testi, hiç görmediği ikinci bir saldırgan ile yapılır.
- Gerçek test seti temiz tutulur; saldırgan ve sentetik mesajlar ona karışmaz.
- Her turda yanlış alarm da ölçülür.
- Telegram botu gelen mesajları kaydetmez.
- Ana deney ikili: spam (reklam + dolandırıcılık) / meşru. Gerçek Türkçe dolandırıcılık çok az (7), 3 sınıflı ölçüm anlamsız olurdu.
- Dolandırıcılık ayrı ek deney: kural motoru + sentetik/çevrilmiş örnekler (sadece train'e), gerçek 7 mesajla test edilir.
- Bölme: grup duyarlı (benzerlik eşiği 0.60), %85 train / %15 test, test kilitli. Model seçimi train içinde 5 katlı grup duyarlı CV ile (`fold` sütunu).

## Çalışma kuralları
- Herkes kendi dalında çalışır (veri-esra, model-salih), main'e doğrudan yazılmaz.
- Her PR'ı diğer kişi inceler ve birleştirir.
- Bir karar değişirse önce bu dosya, sonra kod güncellenir.
- Ham veri, bot token'ı ve parolalar repoya girmez.
- Her Claude oturumu "önce PROJECT.md'yi oku" diye başlar.
- Gün başında 5 dakikalık konuşma: dün, bugün, takıldığım şey.
- Kırmızı çizgiler: Gün 3 veri, Gün 7 karşılaştırma tablosu, Gün 10 döngü grafiği.
