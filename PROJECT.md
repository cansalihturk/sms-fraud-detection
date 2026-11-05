# SMS Dolandırıcılık Tespiti

## Hedef
Türkçe ve İngilizce SMS'lerde dolandırıcılığı tespit etmek; sistemi
kelime bozma ve prompt injection'a karşı test etmek. İki ek parça:
(1) saldırgan LLM ile dedektörü turlar halinde eğiten kırmızı/mavi takım
döngüsü, (2) şüpheli SMS'i analiz eden Telegram botu. Süre: 2 hafta.
Sınıflar: dolandırıcılık / reklam (spam) / meşru.
> **Kapsam notu (5 Kasım):** LLM açıklaması ve prompt injection testi kapsam dışı bırakıldı. Açıklama kelime etkisiyle yapılıyor (`tahmin.acikla`). Kelime bozma testi yapıldı. Bkz. Durum.

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
- LLM karar vermez, sadece açıklama yazar. (Kapsam dışı kaldı: sistemde LLM yok, açıklama kelime etkisiyle.)
- Dengesizlik için önce class weight; SMOTE sadece eğitim kısmında küçük deney.
- Döngünün final testi, hiç görmediği ikinci bir saldırgan ile yapılır.
- Gerçek test seti temiz tutulur; saldırgan ve sentetik mesajlar ona karışmaz.
- Her turda yanlış alarm da ölçülür.
- Döngü saldırganları yerel (Ollama): qwen3.5:9b, aya-expanse:8b; final saldırgan gemma4:e4b, döngüde hiç kullanılmaz. Yanlış alarm, eğitime girmeyen gerçek meşru kurumsal mesajlarda ölçülür; kıyas 3 tohumlu gürültü bandına göre yapılır.
- Sistemde kullanılan model SVM E (`models/svm_v1.joblib`); XLM-R E araştırma modeli (bkz. Gün 9, model seçimi).
- Kaydedilmiş model, kaydedildiği scikit-learn sürümüyle çalıştırılır (svm_v1: 1.6.1); Docker'da sürüm sabitlendi.
- Telegram botu gelen mesajları kaydetmez.
- Ana deney ikili: spam (reklam + dolandırıcılık) / meşru. Gerçek Türkçe dolandırıcılık çok az (7), 3 sınıflı ölçüm anlamsız olurdu.
- Dolandırıcılık ayrı ek deney: kural motoru + sentetik/çevrilmiş örnekler (sadece train'e), gerçek 7 mesajla test edilir.
- Bölme: grup duyarlı (benzerlik eşiği 0.60), %85 train / %15 test, test kilitli. Model seçimi train içinde 5 katlı grup duyarlı CV ile (`fold` sütunu).
- Canlı tahmin sırası: `maskele` → model. `temizle` pipeline'ın içinde, ayrıca çağrılmaz. Maskelenmemiş mesaj modele verilmez (eğitimde gerçek link/numara hiç görülmedi).
- Kaydedilen modeller `src.temizle`'yi adresiyle taşır; yüklendikleri yerde `src` import edilebilir olmalı (API repo kökünden çalışır).
- "Emin değilim" bandı (|skor| < 0.3) sunumdan sonraya bırakıldı: eşik SVM skorunda ölçülmedi, ölçülmeden eklenirse demonun davranışı değişir. Eklenmeden önce eşik train içinde (CV) seçilecek.
- Derin öğrenme: Keras 3, PyTorch altyapısıyla (`KERAS_BACKEND=torch`). TensorFlow Python 3.14'ü desteklemiyor (en son 2.21, Python 3.10-3.13). Keras kodu aynı kalır.
- Deney takibi: MLflow, `sqlite:///mlflow.db` (repo kökü, gitignore'da), deney adı `tr_ikili`. Parametreler elle yazılmaz, modelden (`get_params`) ya da tek bir ayar sözlüğünden okunur.
- GPU: `pip install torch --index-url https://download.pytorch.org/whl/cu130` (Python 3.14, sürücü CUDA 13.0+). PyPI'daki Windows torch paketi sadece CPU'lu. Transformer modelleri için `transformers`.
- XLM-R / BERTurk ayarları (başlangıç): max_len 80 (en uzun mesaj 71 parça), batch 16, lr 2e-5, 4 epoch, warmup %10, weight decay 0.01, bfloat16. Her fold'da taze model.

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
### Gün 6: MLP ve BiLSTM (Salih)
Spam F1. Aynı protokol (5 katlı `fold` CV, test tek bakış).

| Model | Özellik | Parametre sayısı | CV | Test F1 | Test P | Test R |
|---|---|---|---|---|---|---|
| SVM (Gün 5) | harf 3-5 | ~25 bin | 0.971 ± 0.014 | 0.981 | 0.981 | 0.981 |
| MLP (64 nöron, alpha 1e-3) | harf 3-5, min_df=2 | ~800 bin | 0.974 | 0.981 | 0.981 | 0.981 |
| BiLSTM (embed 32, lstm 32) | kelime, min_df=2 | 51 bin | 0.962 ± 0.036 | 0.971 | 1.000 | 0.944 |

- Üç model arasındaki farklar 2 puandan küçük (gürültü). Kombinasyon öğrenen MLP ve sırayı okuyan BiLSTM, doğrusal SVM'i geçemedi. Canlı sistem için SVM kalıyor (aynı başarı, daha küçük ve açıklanabilir).
- Ezber kontrolü: SVM ve MLP'de train F1 1.000, CV ile fark ~3 puan. Ezber var ama genellemeyi bozmuyor.
- BiLSTM fold'lar arasında en kararsız model (fold 2: 0.894). Kelime seviyesinde sözlük küçük (~1070 kelime); gündelik mesajlarda kelimelerin çoğu "bilinmeyen" oluyor. Test'te yanlış alarm yok ama 3 spam kaçırıyor: dolandırıcılık için yanlış yönde hata.
- `analyzer="char"` (kelime sınırını aşan parçalar) `char_wb`'den kötü: 0.965 vs 0.971.
### Gün 7 (devam ediyor): XLM-R (Salih)

| Model | CV | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 |
|---|---|---|---|---|---|---|
| XLM-R base | 0.961 | 0.969 | 0.976 | 0.916 | 0.967 | 0.975 |

- 278M parametreli çok dilli model de SVM / MLP / BiLSTM ile aynı bölgede (0.96-0.97). Bu veri için tavan bu civarda; kalan hatalar modelden çok veriden kaynaklanıyor.
- Tokenizer bilinmeyen kelime üretmiyor ("gelcekmsn" → gel|cek|ms|n), ama harf oyununa açık: "b3dava" → b|3|dava ("dava").
- **CV hata analizi (out-of-fold, test'e bakılmadı):** 25 hatanın ~20'si kurumsal meşru mesaj (fatura hatırlatma, banka bildirimi, PNR, operatör), %98 güvenle spam deniyor. Model "resmi/kurumsal dil = spam" öğrenmiş, çünkü train'deki spam'in neredeyse tamamı kurumsal reklam, meşru'nun çoğu gündelik sohbet.
- Fold 2'nin her modelde zor çıkması bu yüzden: aynı fatura şablonları grup duyarlı bölmeyle o fold'da toplanmış. Bölme işini yapıyor, rastgele bölme bu zayıflığı gizlerdi.
- Kaçan banka taklidi: id 44 ("Finansbank İnternet Şubesi şifreniz blokelenmi...", olasılık 0.43).
- Resmi uyarı mesajları (390, 575) dolandırıcılık kelimeleri içerdiği için spam deniyor.
- Etiketi tartışmalı (kör denetime): 653, 305 (kampanya içeriyor, meşru etiketli).
- **Sonuç:** Asıl zorluk, gerçek kurumsal bildirim ile onu taklit eden dolandırıcılığı ayırmak. Dolandırıcılık ek deneyinde sentetik veriye sadece dolandırıcılık değil, gerçek kurumsal bildirimler de (hard negative) eklenmeli.
#### Zor test: gerçek kurumsal mesajlar (133 mesaj, 59 gönderici grubu)
A = sadece tr_train ile eğitim. B = leave-one-sender-out (tr_train + diğer göndericiler). Gönderici adları büyük harfe çevrildi (NKOLAY / nkolay aynı grup). max_len 160 (33 mesaj 80 parçayı aşıyor; tr_train'de etkisi yok, en uzun 71). Eşik 0.5, bu sete bakılarak ayarlanmadı.
> Not: Bu sayılar etiket düzeltmesinden **önceki** zor setle hesaplandı. Esra 30 ve 63'ü belirsize, Turkcell uygulama tanıtımını (23) reklama çevirdi. Yeni dosyayla tekrar ölçülecek.

| Model | Yanlış alarm | Spam yakalama | Dolandırıcılık | P | R | F1 |
|---|---|---|---|---|---|---|
| SVM A (Esra) | 35/68 | 60/65 | | | | ~0.75 |
| SVM B (Esra) | 11/68 | 60/65 | | | | ~0.88 |
| XLM-R A | 42/68 | 58/65 | 5/11 | 0.58 | 0.89 | 0.70 |
| XLM-R B | 11/68 | 59/65 | 7/11 | 0.84 | 0.91 | 0.87 |

- Model büyüklüğü veri yanlılığını çözmüyor: XLM-R A, SVM A'dan daha fazla yanlış alarm veriyor. Kazanç modelden değil veriden geliyor (42 → 11).
- **Tür değişimi (dikkatli yorum):** XLM-R B iş ilanı ve IBAN'lı bağış dolandırıcılıklarını yakalamaya başladı, ama iki sahte kargo mesajını kaybetti (id 46: 0.79 → 0.07). Bu iki mesaj neredeyse aynı metin, yani pratikte tek örnek. SVM B ise 11/11 yakalıyor ve kargoları kaybetmiyor (Esra). 11 dolandırıcılık mesajıyla kesin sonuç çıkarılamaz.
- Sonuç: Sadece hard negative eklemek yetmez. Kurumsal taklit dolandırıcılık (**hard positive**: sahte kargo, sahte banka, sahte e-Devlet) birlikte eklenmeli.
- Kalan yanlış alarmların çoğu eşiğe yakın (0.54-0.69). İnatçı olanlar kamu bilgilendirmeleri (AFAD, TTNET, Sağlık Bakanlığı) ve uygulama tanıtımı (Turkcell, 0.99).
- Etiket önerileri (düzeltme listesine, birlikte onay): 30 ("0850 250 6702", metinden anlaşılamaz → belirsiz?), 63 (Yurtiçi şubede bekliyor: reklam mı dolandırıcılık mı?), 23 (Turkcell uygulama tanıtımı: meşru mu reklam mı?).
- Tahminler: `data/external/xlmr_zor_tahmin.csv` (repoya girmez).
- **Son model (zor set ölçütü):** XLM-R, eğitim = tr_train + zor set (LOSO, sınav göndericisi hariç) + sentetik v2/v3 + Salih'in 58 kurumsal mesajı (deney E). Ölçüt sonuçtan önce konuldu: havuz eklenmiş F, dolandırıcılıkta 10/10 ve yanlış alarmda ≤6 olsaydı seçilecekti. F 9/10, 5/67 → E seçildi (fark gürültü seviyesinde, basit olan tercih edildi).
- **Sentetik veri:** v2/v3 kullanılır (96 mesaj: 56 kurumsal meşru + 40 kurum taklidi dolandırıcılık). v1 kullanılmaz ([LINK] kısayolu: sahte %93 / meşru %15 linkli, yanlış alarmı 41 → 48 artırdı). Sentetik sadece eğitimde.
- **Salih'in SMS havuzu:** iPhone (Mac chat.db) → 2108 kurumsal SMS → maskeleme (`maskele` + ad, plaka, kart son 4, abone no, B-kodu kuralları; her adım kontrol edildi) → 1490 tekrarsız. **Sadece Salih'in bilgisayarında kalır, paylaşılmaz** (maskeli halinde bile bakiye, tutar gibi kişisel bilgiler var). Son modelde kullanılmıyor, deney olarak raporlanır.
- **Kademeli kural etiketleme (weak supervision):** ret/iptal seçeneği → reklam; yoksa reklam kelimesi → çekimser (kullanılmaz); ikisi de yoksa → meşru. Esra'nın insan etiketli 121 mesajında: meşru 52/54, reklam 40/41, %22 çekimser. Havuzda rastgele 30 kontrol: 28 doğru, 1 sınırda, 1 boş mesaj.
- **Kural etiketli veri eğitime girerken kuralın baktığı özellik kesilir:** havuzda ret/iptal ifadesi mesajdan çıkarılır. Yoksa model kuralı öğrenir (bkz. Sonuçlar, Gün 8).
- **Gönderici kodu (B001, B016...):** Salih'in SMS'lerinde var, Esra'nınkilerde yok. Kaynak sızıntısı olmasın diye silinir.
- Zor set deneyleri MLflow'da ayrı deney grubunda: `tr_zor`.
### Gün 8: Zor set deneyleri, XLM-R (Salih)
Sınav: `zor_gercek_hepsi.csv` v2, 131 insan etiketli gerçek kurumsal mesaj (meşru 67, reklam 54, dolandırıcılık 10), 58 gönderici grubu (büyük harfe çevrilmiş). Eşik 0.5, bu sete bakılarak ayarlanmadı. tr_test'e dokunulmadı. LOSO = leave-one-sender-out: her turda bir gönderici sınav, o göndericinin mesajları (zor set, Salih'in verisi, havuz) eğitimden çıkarılır.

| Deney | Eğitim | Yanlış alarm | Spam yakalama | Dolandırıcılık | P | R | F1 |
|---|---|---|---|---|---|---|---|
| A | tr_train | 41/67 | 59/64 | 5/10 | 0.590 | 0.922 | 0.720 |
| C1 | + sentetik v1 | 48/67 | 63/64 | 9/10 | 0.568 | 0.984 | 0.720 |
| C2 | + sentetik v2/v3 | 39/67 | 63/64 | 9/10 | 0.618 | 0.984 | 0.759 |
| B | + zor set (LOSO) | 6/67 | 58/64 | 5/10 | 0.906 | 0.906 | 0.906 |
| D | + zor set (LOSO) + sentetik v2/v3 | 10/67 | 62/64 | 9/10 | 0.861 | 0.969 | 0.912 |
| **E** | **+ zor set (LOSO) + sentetik v2/v3 + Salih 58** | **6/67** | **63/64** | **10/10** | 0.913 | 0.984 | **0.947** |
| G_tum | sentetik v2/v3 + havuz (1287, tekrarlı) | 2/67 | 50/64 | 2/10 | 0.962 | 0.781 | 0.862 |
| G_sablon | sentetik v2/v3 + havuz (842, şablon tekrarsız) | 2/67 | 52/64 | 2/10 | 0.963 | 0.812 | 0.881 |
| G_40 | sentetik v2/v3 + havuz (738, göndericide ≤40) | 3/67 | 54/64 | 4/10 | 0.947 | 0.844 | 0.893 |
| G_sablon_retsiz | sentetik v2/v3 + havuz (şablon, ret kesildi) | 4/67 | 58/64 | 7/10 | 0.935 | 0.906 | 0.921 |
| G_40_retsiz | sentetik v2/v3 + havuz (≤40, ret kesildi) | 8/67 | 59/64 | 7/10 | 0.881 | 0.922 | 0.901 |
| F | E + havuz (şablon, ret kesildi) | 5/67 | 60/64 | 9/10 | 0.923 | 0.938 | 0.930 |

G deneylerinde zor setle ortak göndericiler havuzdan çıkarıldı; zor setten hiçbir mesaj eğitimde yok.

**Bulgular**
- **Her kaynak farklı bir işe yarıyor:** gerçek kurumsal mesaj yanlış alarmı çözüyor (A→B: 41 → 6), sentetik dolandırıcılığı çözüyor (A→C2: 5 → 9), Salih'in 58 mesajı ikisini dengeliyor (D→E: yanlış alarm 10 → 6, dolandırıcılık 9 → 10).
- **Sentetik veri kalitesi:** aynı LLM, aynı sayıda mesaj; v1'deki [LINK] dengesizliği yanlış alarmı 9 artırdı (C1 vs C2). Sentetik verinin nasıl üretildiği, üretilip üretilmediğinden önemli.
- **Otomatik etiket tuzağı:** kural etiketli havuz yanlış alarmı neredeyse sıfırladı (2/67) ama dolandırıcılığı 9 → 2 düşürdü. Model içeriği değil etiketleme kuralını öğrendi ("ret ifadesi yok → meşru"); dolandırıcılar ret ifadesi koymadığı için hepsine meşru dedi. Havuz büyüdükçe kötüleşti.
- **Düzeltme:** havuzda ret ifadesi kesilince dolandırıcılık 2 → 7, yanlış alarm 2 → 4, F1 0.881 → 0.921. Zor setten hiçbir mesaj görmeden (G_sablon_retsiz), zor setle eğitilen B'yi (0.906) geçti: tek kişinin SMS kutusu + doğrulanmış kural, ölçeklenebilir bir veri kaynağı.
- **Fazla veri:** şablon tekrarı atılmış sınırsız havuz (842) > göndericide ≤40 sınırlı havuz (738). Tekrarlar atıldıktan sonra daha fazla veri daha iyi.
- **Son model E:** F (E + havuz) ile farkı tek yanlış alarm ve tek dolandırıcılık mesajı, F1 farkı 1.7 puan (gürültü). Önceden konulan ölçüte göre E.
- **Sınırlar:** zor sette 10 dolandırıcılık var, tek mesaj 10 puan oynatıyor. Havuz tek kişinin gelen kutusu (bankaları, operatörü). Salih'in 58 mesajının etiketleri Claude önerisi, Salih tek tek kontrol etti.
**Son model (`models/xlmr_e`, `python -m src.son_model`):** E tarifi, verinin tamamı (936 mesaj), tek eğitim. Künye: `models/xlmr_e/kunye.json`.

**Kilitli tr_test, tek bakış (`python -m src.test_son_model`):** F1 0.953, P 0.962, R 0.944. Yanlış alarm 2/62, kaçan spam 3/54.
- Gün 5 SVM harfin (0.981) 2.8 puan gerisinde: gerçek düşüş.
- 5 hatanın 3'ü Gün 5'ten beri tüm modellerin yanıldığı tartışmalı etiketler (290, 661, 5869).
- Gerçek hata 594 (banka dilinde kredi kartı limit teklifi, p=0.05) ve 393 (Turkcell ücretli servis, p=0.40).
- **Ödünleşim:** son model "kurumsal dil = spam" kısayolunu bıraktı. Zor sette (gerçek kurumsal SMS) yanlış alarm 41 → 6 düştü, karşılığında tr_test'te (2013 SMS) banka diliyle yazılmış reklamlar kaçabiliyor. Botun gerçek kullanımı zor sete daha yakın olduğu için bu ödünleşim kabul edildi.
- "Emin değilim" bandı (0.30-0.70): tr_test'te 2/116 mesaj.
- Akıl kontrolü: elle yazılmış kısa, aciliyetsiz sahte kargo mesajı p=0.44 (`bilinen-hatalar.md`, satır 2). Ayar yapılmadı; saldırgan döngüsünde tekrar ölçülecek.
> **Gruplama düzeltmesi (E_v2):** Gönderici grupları ilk koşuda sadece büyük harf + baştaki/sondaki boşluk silinerek oluşturuldu; "NVI RANDEVU" (Salih) ile "NVIRANDEVU" (zor set) ayrı grup kaldı, NVIRANDEVU sınavdayken Salih'in bu göndericiden mesajı eğitimde kaldı. Düzeltilmiş gruplama (harf/rakam dışı her şey silinir, Esra'nın SVM protokolüyle aynı) ile E tekrar koşuldu (`python -m src.zor_deney E_v2`): yanlış alarm 7/67, spam 63/64, dolandırıcılık 10/10, P 0.900, R 0.984, **F1 0.940**. Fark tam olarak bir NVIRANDEVU mesajı (p=0.63). SVM ile karşılaştırmada **E_v2** kullanılır. B/D'de Salih'in verisi yok, etkilenmez; F'nin kararı değişmez (dolandırıcılık 9/10 < 10/10).
### Gün 9: Saldırgan / savunmacı döngüsü, XLM-R (Salih)
Saldırgan yerel LLM (Ollama) dolandırıcılık SMS'i yazar, savunmacı (E tarifiyle XLM-R) puanlar. Yakalanamayanlar ("kaçanlar") eğitime eklenir, savunmacı sıfırdan yeniden eğitilir, saldırgana yakalanan/kaçan örnekler geri bildirilir. 4 tur, turda 30 saldırı. Final: döngüde hiç kullanılmamış başka aileden saldırgan (gemma4:e4b). Eşik 0.5. Yanlış alarm, eğitime hiç girmeyen gerçek meşru kurumsal mesajlarda (Salih'in havuzu) ölçülür. Saldırı mesajları `data/external/dongu*/` (repoya girmez); grafik ve sayılar `docs/`.

**v1 (atıldı):** saldırgan kaçan mesajları neredeyse aynen kopyaladı (sahte düşüş); uydurduğu maskeler ([OPERATÖR], [KURUM]) gerçek veride yok, kısayol oldu; yanlış alarm tek koşuda ölçüldü, gürültü bilinmiyordu.

**v2 (`python -m src.dongu`):** saldırgan qwen3.5:9b. Düzeltmeler: yenilik filtresi (HashingVectorizer char_wb 3-5, benzerlik > 0.7 olan saldırı reddedilir), uydurma maskeler gerçek marka adına çevrilir, D0 üç tohumla (42/43/44) eğitilir → yanlış alarm gürültü bandı. Yanlış alarm seti: 318 havuz meşrusu.

| Tur | Kaçma (qwen) | Yanlış alarm (yeniden eğitim sonrası, tohum 42) |
|---|---|---|
| 0 (D0) | – | %10.4 – %12.9 (3 tohum, bant) |
| 1 | 15/30 = %50 | 43/318 = %13.5 |
| 2 | 6/30 = %20 | 46/318 = %14.5 |
| 3 | 25/30 = %83 | 62/318 = %19.5 |
| 4 | 0/30 = %0 | yeniden eğitim yok |
| Final (gemma4) | D0: %27 – %43 (3 tohum) → son: %7 (2/30, tek tohum) | |

- Görülmemiş saldırgana karşı kaçma gürültünün çok üstünde düştü. Model qwen'in üslubunu değil, dolandırıcılığı öğrendi.
- Bedeli: yanlış alarm bandın dışına çıktı (%19.5). Modele sadece "bu da dolandırıcılık" dendi, hiç "bu benziyor ama meşru" denmedi.
- Saldırgan uyum sağladı: tur 3'te yeni taktik (uydurma kod "x9y7z5w3", belirsiz "teknik/sistem hatası"), %83 kaçtı; model öğrenince tur 4'te %0.
- Gemma'nın son modelde kaçan 2 mesajı: maskelenmemiş kısa numaralı sahte kargo, IBAN'lı yardım isteği (p 0.23).
- Bilinen hata 2 (sahte kargo) tohuma göre oynak: D0'da 0.44 / 0.90 / 0.84. Bu tür mesajda karar sağlam değil.

**v3 (`python -m src.dongu_v3`):** iki değişiklik. (1) Meşru karşı ağırlık: 318 havuz meşrusu gönderici bazlı bölündü, 162 (38 gönderici) eğitime "meşru" olarak girer (D0 dahil), 156 (41 gönderici) sadece yanlış alarm ölçümünde; ortak gönderici yok (kodda kontrol). Hepsini eğitime koyup aynı sette ölçmek sızıntı olurdu. (2) İki saldırgan sırayla: qwen3.5:9b (tek turlar), aya-expanse:8b (çift turlar). Son savunmacı da üç tohum.
Ön kayıtlı kriter (koşudan önce kodda): v3, v2'nin yerine ancak final kaçma ≤ %10 VE yanlış alarm ≤ %13 ise geçer (3 tohum ortalaması).

| Tur | Saldırgan | Kaçma | Yanlış alarm (tohum 42) |
|---|---|---|---|
| 0 (D0) | – | – | %6.4 – %7.7 (3 tohum, bant) |
| 1 | qwen | 19/30 = %63 | 6/156 |
| 2 | aya | 11/30 = %37 | 18/156 |
| 3 | qwen | 4/30 = %13 | 6/156 |
| 4 | aya | 0/30 = %0 | yeniden eğitim yok |

| | D0 (3 tohum) | Son savunmacı (3 tohum) |
|---|---|---|
| Gemma kaçma | %43 – %70 (ort. %53.3) | %13 – %23 (ort. %18.9) |
| Yanlış alarm (156) | %6.4 – %7.7 | %3.8 – %8.3 (ort. %5.6) |

- **Karar: RED** (kaçma %18.9 > %10). Döngü sonucu olarak v2 raporlanır, v3 karşılaştırma olarak.
- Meşru karşı ağırlık yanlış alarm bedelini kaldırdı (son model bandın içinde). Turlarda kaçma düzenli indi (63 → 37 → 13 → 0), v2'deki tur 3 sıçraması yok.
- **Ödünleşim:** v2 daha dayanıklı ama yanlış alarm bant dışı; v3 yanlış alarmda bedelsiz ama daha az dayanıklı. Dayanıklılık ile yanlış alarm arasında ayar düğmesi var, iki ucu da ölçüldü.
- **Kriter hatası:** final gemma seti her koşuda yeniden üretildi. v3'ün seti belirgin şekilde daha zor (D0 kaçma %43–70, v2'de %27–43); mutlak %10 eşiği v2'nin %7'sine bakılarak, farklı bir sınav kâğıdı için konmuştu. Kriter sonuçtan sonra değiştirilmedi (HARKing olurdu).
- **Ders:** final seti bir kez üretilip sabitlenir (`dongu_v3.py` artık `final_mesajlar.csv`'yi kaydedip yeniden kullanıyor) ve eşik göreli konur ("D0'a göre en az X puan düşüş").
- Tek tohumlu tur ölçümleri oynak (v3 tur 2: 18/156, sonra 6/156). Aynı veri ve aynı tohumla bile GPU'da sonuç birkaç mesaj oynayabiliyor. Yorum sadece 3 tohumlu bantlardan yapılır.
- **Sınırlar:** turda 30 saldırı (1 mesaj = 3.3 puan); saldırganlar 8-9B yerel modeller; yanlış alarm tek kişinin gelen kutusunda ölçüldü. Döngü modelleri son model değil; son model E.

### Gün 9: Havuz deneyi, E ve H (`python -m src.havuz_deney`, Salih)
Soru: Salih'in SMS havuzu son modeli iyileştirir mi? F (E + havuz) zor sette eşit çıkmıştı, ama zor setteki 10 dolandırıcılık mesajı (1 mesaj = 10 puan) farkı görecek kadar hassas değil. Bu yüzden havuzun asıl iddia ettiği yerde, gerçek kullanım koşulunda ölçüldü.

- **E:** son model tarifi (936). **H:** E + havuz 679 (reklam 517, meşru 162; şablon tekrarsız, RET kesilmiş), ölçüm göndericileri tamamen hariç (1615). İkisi de üç tohum (42/43/44).
- **Sınav (iki model de hiç görmedi):** (1) yanlış alarm: dongu_v3 bölmesinin ölçüm yarısındaki meşrular; Salih'in 58'i ve zor setle ortak 13 gönderici de çıkarıldı → 97 mesaj, 28 tamamen görülmemiş gönderici (1 mesaj ≈ 1 puan). (2) dolandırıcılık: gemma4:e4b final saldırıları (döngü v2 + v3, 60 mesaj; geri bildirimsiz üretildi, hiçbir modele göre şekillenmedi). Tur saldırıları (qwen/aya) kullanılmadı: XLM-R'ı geçmek için seçildiler, SVM'e haksız avantaj olurdu.
- **Ön kayıt (koşudan önce kodda):** H, E'nin yerine ancak dolandırıcılık yakalamada en fazla 2 puan geride VE yanlış alarmda en az 2 puan iyi ve bantlar örtüşmüyorsa geçer.

| Model | Yanlış alarm (97, 3 tohum) | Gemma yakalama (60, 3 tohum) |
|---|---|---|
| E | %12.4 (9.3 – 14.4) | **%66.1** (51.7 – 78.3) |
| H (E + havuz) | **%7.9** (7.2 – 9.3) | %41.1 (36.7 – 46.7) |

- **Karar: RED**, son model E kalır. Dolandırıcılık 25 puan düştü; yanlış alarm 4.5 puan iyileşti ama bantlar değiyor (H max 9.3 = E min 9.3).
- **Bulgu:** havuzdaki meşrular gerçek banka/operatör bildirimleri. Model "resmi kurum dili → meşru" öğrendi; gemma'nın saldırıları tam bu dili taklit ediyor. Daha çok meşru veri modeli kurumsal taklide karşı saflaştırdı. Gün 8'deki G bulgusuyla (kural etiketli havuz: yanlış alarm ↓, dolandırıcılık 9 → 2) aynı yön; iki ayrı deney, iki ayrı sınav.
- **Ders:** veri miktarı değil, verinin ne öğrettiği önemli. Modelin eksiği meşru örnek değil, kurumsal dili taklit eden dolandırıcılık örneği. Havuz ancak dolandırıcılık verisiyle dengelenirse işe yarar (döngü v3'ün meşru karşı ağırlık + saldırı tasarımı bunu yapıyor).
- **Son modelin gerçek kullanıma yakın sınırları (sunumda söylenir):** hiç görülmemiş gerçek meşru kurumsal SMS'lerin ~%12'sine alarm (tr_test'te %3); görülmemiş bir LLM'in yazdığı dolandırıcılığın ~%66'sını yakalıyor (üçte birini kaçırıyor). Botun "emin değilim" bandı ve LLM açıklaması bu yüzden gerekli.
- **Sınırlar:** yanlış alarm tek kişinin gelen kutusu; dolandırıcılık LLM yazımı (gerçek dolandırıcılık değil); tohumlar arası oynama büyük (E yakalama 52–78).
- SVM E aynı sınava girdi (`--svm models/svm_v1.joblib --sadece-svm`): yanlış alarm 7/97 (%7.2), gemma yakalama 35/60 (%58.3). H kararına girmez; model seçimi aşağıda.

### Gün 9: Model seçimi, SVM E ve XLM-R E (Salih, Esra)
İki model de E verisiyle eğitildi (tr_train + zor set + sentetik v2/v3 + Salih'in 58'i). Seçim kriteri sonuçlardan önce konuldu: (1) dolandırıcılık yakalama, (2) yanlış alarm, (3) F1 farkı 2 puandan küçükse basit olan (SVM).

**Zor set, LOSO (131 mesaj, gruplama v2):**

| Model | Yanlış alarm | Spam yakalama | Dolandırıcılık | F1 |
|---|---|---|---|---|
| XLM-R E_v2 | 7/67 | 63/64 | 10/10 | 0.940 |
| SVM E (Esra) | 6/67 | 60/64 | 10/10 | 0.923 |

Dolandırıcılık berabere, yanlış alarm farkı 1 mesaj, F1 farkı 1.7 puan (< 2) → **SVM**.

- Hatalar tamamen farklı mesajlarda. XLM-R'ın 7 yanlış alarmı: Afad, İçişleri ×2 (dolandırıcılığı anlatan uyarılar, dolandırıcılık kelimeleriyle dolu), BADIWORKS, Turkcell 6968, KUMTEL, NVIRANDEVU. SVM'in 6 yanlış alarmının 3'ü KOLAYGELSIN kargo bildirimi. Ortak tek zayıflık yumuşak dilli eğitim reklamı (kaçan spam). Hataları bu kadar farklı iki modelin birleşimi (ensemble) gelecek iş; zor sette denenirse set ayar için kullanılmış olur.

**Görülmemiş gerçek kullanım sınavı (havuz deneyiyle aynı 97 meşru + 60 gemma saldırısı).** Ön kayıtlı kural (koşudan önce): SVM'in yakalaması E'nin en kötü tohumunun altındaysa XLM-R; yakalama E bandında ya da üstünde ve yanlış alarm E'nin en kötü tohumundan kötü değilse SVM.

| Model | Yanlış alarm (97) | Gemma yakalama (60) |
|---|---|---|
| XLM-R E (3 tohum) | %12.4 (9.3 – 14.4) | %66.1 (51.7 – 78.3) |
| SVM E (`svm_v1.joblib`, tek, deterministik) | **%7.2 (7/97)** | %58.3 (35/60) |

SVM yakalamada E bandının içinde (ortalamaya göre ~8 puan, ~5 mesaj geride; XLM-R'ın kendi tohum oynamasının içinde), yanlış alarmda E'nin en iyi tohumundan da iyi → **SVM**. İki bağımsız sınav aynı yönü gösteriyor.

- **Karar:** sistemde (API, arayüz, bot, Docker) **SVM E** (`models/svm_v1.joblib`, Esra, 935 mesaj) kullanılır. Ek gerekçeler: küçük, CPU'da milisaniyeler, her eğitimde aynı model (XLM-R'da tohuma göre yakalama 52–78 arası oynuyor), açıklanabilir (hangi harf parçasına baktığı görülür).
- **XLM-R E** araştırma modeli olarak raporlanır: zor set serisi (A → E), döngü deneyleri, havuz deneyi.
- **Sürüm uyumu:** `svm_v1.joblib` scikit-learn 1.6.1 ile kaydedildi; 1.9.1'de açılınca `InconsistentVersionWarning` verdi (bu ölçümde çalıştı). Docker'da sürüm sabitlenir ya da model imajdaki sürümle yeniden kaydedilir.
- **Gerçek sınırlar (sunumda söylenir):** SVM, görülmemiş bir LLM'in yazdığı dolandırıcılığın ~%40'ını kaçırıyor; gerçek meşru kurumsal SMS'lerin ~%7'sine alarm veriyor. Bu yüzden bot tek başına modele güvenmez: kural motoru, "emin değilim" bandı ve LLM açıklaması birlikte çalışır.
- **Kilitli tr_test, tek bakış (Esra):** SVM E F1 **0.972**, yanlış alarm 1/62, kaçan spam 2/54 (XLM-R E: 0.953, 2/62, 3/54). Sonuca bakıp ayar değiştirilmedi.

## Durum (5 Kasım, sunum öncesi)
Görev dağılımındaki her iş için: yapıldı mı, nerede. Yapılmayanlar sessizce kalmasın diye yazıldı.

| İş | Durum | Nerede / not |
|---|---|---|
| Türkçe veri, maskeleme, etiketleme | ✅ | `src/maskele.py`, `docs/etiket-rehberi.md`, `docs/zor-test.md` |
| NB, SVM, LR (kelime / harf) | ✅ | `src/baseline.py`, Gün 5 |
| MLP, BiLSTM, XLM-R | ✅ | Gün 6–8, `src/zor_deney.py`, `src/son_model.py` |
| Zor set deneyleri (A → E) | ✅ | Gün 8, `docs/zor-test.md` |
| Saldırgan / savunmacı döngüsü | ✅ | Gün 9, `src/dongu.py`, `src/dongu_v3.py` |
| Model seçimi (SVM) | ✅ | Gün 9, model seçimi |
| Kural motoru (tür) | ✅ | `src/kurallar.py`, `tests/test_kurallar.py` |
| Kelime bozma testi | ✅ | `docs/zor-test.md` 9.3 |
| FastAPI, Streamlit, Telegram botu | ✅ | `src/api.py`, `src/arayuz.py`, `src/telegram_bot.py` |
| Docker, CI | ✅ | `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` |
| MLflow | ✅ | `tr_ikili`, `tr_zor`, `dongu`, `havuz_deney` (yerel, repoda değil) |
| README, mimari şeması | ✅ | `README.md` (şema Mermaid ile README'de) |
| Model Card, Risk Kaydı | ⏳ | Esra'da hazır, `docs/`'a eklenecek |
| Nihai SVM'in eğitim kodu | ⏳ | `svm_v1.joblib` repoda üretilemiyor; eğitim script'i / notebook'u eklenecek |
| XGBoost hibrit, BERTurk | ⚠️ | Notebook'lar var (`xgboost.ipynb`, `berturk-xlm-r.ipynb`), sonuçları bu dosyada yok |
| LLM açıklaması (Ollama) | 🚫 kapsam dışı | Açıklama kelime etkisiyle (`tahmin.acikla`: kelimeyi çıkar, skor ne kadar değişti). Ollama döngüde saldırgan olarak kullanıldı. |
| Prompt injection testi | 🚫 kapsam dışı | Sistemde LLM olmadığı için saldırı yüzeyi yok. LLM açıklaması eklenirse ilk yapılacak test. |
| SHAP | ❌ | Yerine kelime çıkarma açıklaması (aynı fikir: kararı hangi parça değiştiriyor). |
| "Emin değilim" bandı | ⏳ sunumdan sonra | Eşik SVM skorunda ölçülmedi; ölçülmeden demoya eklenmez. |
| DVC, Evidently | ❌ | Süreye sığmadı. Veri sürümü dosya adıyla (v1/v2/v3) ve PROJECT.md'deki notlarla takip edildi. |
| İngilizce | ⚠️ | UCI'da F1 0.344: model yalnızca Türkçe için doğrulandı. |
