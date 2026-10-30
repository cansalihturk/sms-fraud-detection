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
- Canlı tahmin sırası: `maskele` → model. `temizle` pipeline'ın içinde, ayrıca çağrılmaz. Maskelenmemiş mesaj modele verilmez (eğitimde gerçek link/numara hiç görülmedi).
- Kaydedilen modeller `src.temizle`'yi adresiyle taşır; yüklendikleri yerde `src` import edilebilir olmalı (API repo kökünden çalışır).
- Öneri (Esra ile karar verilecek): bot, karar skoru sıfıra yakınsa (|skor| < 0.3) "emin değilim, dikkatli ol" der.

## Deney protokolü (adil karşılaştırma için herkes aynısını uygular)

**Veri**
- Türkçe etiketli veri: 775 mesaj (`sms_degil=e` olan 3 mesaj baştan çıkarıldı).
- Bölme: `python -m src.bol` (grup duyarlı, eşik 0.60, tohum 42). Train %85, test %15.
- Eğitimde `belirsiz=e` olan 8 mesaj çıkarılır (train 651). Test'te tutulur (116).
- Test seti kilitli: model ve ayar seçiminde kullanılmaz, en sonda her model için tek sefer ölçülür.

**Model seçimi**
- Train içinde 5 katlı grup duyarlı CV (`fold` sütunu 0-4). GridSearchCV'de `PredefinedSplit` kullanılır.
- Ana ölçü: spam sınıfı için F1. Yanında kesinlik ve duyarlılık raporlanır.
- Test'te tek hata ~1 puan oynatır (116 mesaj). 2 puandan küçük farklar gürültü sayılır.

**Özellikler**
- Klasik modellerde (NB, SVM, LR, XGBoost) her model iki özellikle denenir ve tabloda "model × özellik" olarak gösterilir:
  - kelime TF-IDF
  - harf parçası TF-IDF (char_wb, 3-5 harf)
- Metin temizliği: `src.temizle.temizle` (Türkçe küçük harf, rakam → 0, maskeler korunur).
- BERTurk / XLM-R için temizlik uygulanmaz, kendi tokenizer'ları kullanılır.

**Dolandırıcılık**
- Ana deney ikili (spam / meşru). Dolandırıcılık ayrı ek deney.

## Çalışma kuralları
- Herkes kendi dalında çalışır (veri-esra, model-salih), main'e doğrudan yazılmaz.
- Her PR'ı diğer kişi inceler ve birleştirir.
- Bir karar değişirse önce bu dosya, sonra kod güncellenir.
- Ham veri, bot token'ı ve parolalar repoya girmez.
- Her Claude oturumu "önce PROJECT.md'yi oku" diye başlar.
- Gün başında 5 dakikalık konuşma: dün, bugün, takıldığım şey.
- Kırmızı çizgiler: Gün 3 veri, Gün 7 karşılaştırma tablosu, Gün 10 döngü grafiği.

## Sonuçlar

### Gün 5: NB ve SVM (Salih)
Spam F1. CV = 5 katlı (`fold`), test = 116 mesaj, tek bakış.

| Model | Özellik | Ayar | CV | Test F1 | Test P | Test R |
|---|---|---|---|---|---|---|
| NB | kelime | alpha 0.003 | 0.931 ± 0.025 | 0.955 | 0.930 | 0.981 |
| SVM | kelime | C 10 | 0.961 ± 0.018 | 0.972 | 0.981 | 0.963 |
| NB | harf 3-5 | alpha 0.1 | 0.952 ± 0.018 | 0.973 | 0.947 | 1.000 |
| SVM | harf 3-5 | C 1 | 0.971 ± 0.014 | 0.981 | 0.981 | 0.981 |

- Seçilen: SVM harf. SVM kelime ve NB harf ile farkı 2 puandan küçük (gürültü); seçim gerekçesi skor değil, yeni kelimelere ve harf oyunlarına dayanıklılık.
- Kenarda kalan ayarlar (NB kelime alpha, SVM kelime C) genişletilmiş ızgarayla kontrol edildi, skor değişmedi.
- Etiket kontrolü önerisi: test id 290, 661, 5869 neredeyse tüm modellerde hata ve kaynak etiketle çelişiyor.
- Sınır: spam sınıfının neredeyse tamamı reklam. Elle yazılmış banka taklidi mesaj (reklam kelimesi yok) skor +0.22 ile kıl payı yakalandı. Dolandırıcılık ek deneyi bu yüzden gerekli.
- Not: protokol okunmadan önce test setine keşif amaçlı bakıldı (protokol dışı ayarlarla); raporlanan sonuçlar protokole uygun koşudan.
