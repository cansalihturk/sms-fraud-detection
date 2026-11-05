# SMS Dolandırıcılık Tespiti: Şu Ana Kadar Her Şey (Gün 1-10)

Nov 1, 2026 · @Esra

## 1. Proje özeti ve tasarım kuralı

Bu proje, bir SMS'in **spam mi (reklam veya dolandırıcılık) yoksa meşru mu** olduğunu bulan, kararını **açıklayabilen ve denetlenebilen** bir sistem kurar. Süre 2 hafta (26 Ekim 2026'da başladı), dil Türkçe ve İngilizce.

**Takım:** Esra (GitHub: `sezginesra-blip`) ve Salih (`cansalihturk`, özel `sms-fraud-detection` deposunun sahibi).

**Tek tasarım kuralı:** LLM (Ollama) sadece **açıklar**, hiçbir zaman **karar vermez**. Kararı kurallar ve makine öğrenmesi modelleri verir. Bunun sebebi, LLM'in aynı mesaja her seferinde aynı cevabı vermemesi ve neden öyle dediğinin kanıtlanamaması. Yapay zekâ yönetişimi (AI governance) katmanı bu kuralın üstüne kurulu.

**Planlanan parçalar** (hepsi bitmedi, durumları 12. bölümde):

- Kural motoru (açıklanabilir, sabit kurallar)
- Klasik modeller: Naive Bayes, Lojistik Regresyon, SVM; XGBoost; MLP; BiLSTM
- Dil modelleri: BERTurk ve XLM-R (Colab GPU'da ince ayar), İngilizceden Türkçeye aktarım (EN→TR transfer)
- Deney ve veri takibi: MLflow, DVC
- Servis: FastAPI, Docker, GitHub Actions (otomatik test)
- Açıklama: SHAP + Ollama; veri kayması izleme: Evidently
- Yönetişim: Model Card ve NIST AI RMF risk tablosu
- Arayüz ve demo: Streamlit, kırmızı takım / mavi takım döngüsü, Telegram botu

## 2. Takvim ve görev dağılımı

6 günü geride bıraktık: veri hazır, deney protokolü yazıldı, ilk karmaşık baseline tablosu çıktı, PR açıldı ve dolandırıcılık için sentetik veri üretildi. Bugün **31 Ekim, Gün 6**.

| Gün | Tarih | Ne yapıldı |
| --- | --- | --- |
| 6 | 31 Ekim | GridSearch ve CV hata analizi (not defterinde); `baseline.py` ile 6 kombinasyonluk tablo; PR açıldı (`temizle-esra` → `mesru-etiketleme`) ve `.gitignore` çakışması çözüldü; iki dış veri seti incelendi; 100 sentetik + 45 uyarlama dolandırıcılık mesajı üretildi |
| 5 | 30 Ekim | Esra kendi not defterinde baseline'ı sıfırdan kurdu: TF-IDF, SVM, elle 5 katlı CV (ortalama 0.968), Pipeline (aynı sonuç) |
| 3-4 | 28-29 Ekim | Grup duyarlı train/test bölme (`bol.py`), ortak temizleme (`temizle.py`), deney protokolü, Salih'le protokol hizalaması, PR zinciri yönetimi |
| 1-2 | 26-27 Ekim | Veri toplama, maskeleme, iki kişinin bağımsız etiketlemesi, uyuşmazlıkların konuşarak çözülmesi (`birlestir.py`, `docs/etiket-rehberi.md`) |

Gün 1-4 satırlarının gün gün eşlemesi yaklaşıktır (depodaki dosyalardan ve konuşmalardan çıkardım); Gün 5 ve 6 kesindir.

**İş bölümü (gördüğüm kadarıyla):**

- **Esra:** grup duyarlı bölme (`bol.py`), ortak temizleme (`temizle.py`), `baseline.py` ve testleri, kendi not defteri, dış veri incelemesi, sentetik dolandırıcılık verisi.
- **Salih:** `main` ve `mesru-etiketleme` dallarının sahibi (PR inceler ve birleştirir), NB/SVM not defterleri (`nb-svm-salih` dalı), `docs/bilinen-hatalar.md`.
- Sinir ağı, BERTurk, FastAPI ve diğer parçaların kimde olduğu `PROJECT.md` içindeki **Görev dağılımı** tablosunda yazıyor. Güncel halini görmediğim için buraya kopyalamıyorum.

## 3. Veri

Etiketli Türkçe veri **778 mesaj**. Esra ve Salih etiketledi (ortak mesajları ikisi de bağımsız), etiket sözlüğü üç sınıftır: `meşru`, `reklam`, `dolandırıcılık`. Ana deneyde reklam ve dolandırıcılık birleşir (`ikili` sütunu: `spam` / `meşru`).

**Ham dosyalar** (`data/raw/`): `turkishsms.csv`, `turkishsms_val.csv`, `uci_sms.csv` (İngilizce UCI SMS Spam Collection, 5574 mesaj). Ham veri ve işlenmiş veri **git'e girmez**.

**Etiketleme süreci:**

1. Mesajlardaki kişisel bilgiler `maskele.py` ile maskelenir: `[EPOSTA]`, `[LINK]`, `[IBAN]`, `[TEL]`, `[KART]`, `[TC]`, `[KOD]`. Kişi adı ve adres elle `[İSİM]` ve `[ADRES]` yapılır.
2. Esra ve Salih mesajları ayrı ayrı etiketler (`ilk50_*`, `spam_*`, `mesru_*` dosyaları); ortak mesajları (`*_ortak_idler.csv`) ikisi de etiketler.
3. `birlestir.py` iki etiketi birleştirir. Etiketler aynıysa o etiket alınır; farklıysa konuşup verilen karar `docs/uyusmazlik_cozumleri.csv` dosyasından gelir.
4. Dolandırıcılık ve reklam mesajlarına bir **tür** yazılır: `ödül`, `banka`, `kredi`, `kargo`, `devlet`, `bahis`, `diğer`.
5. Etiketleyen şu iki işareti de koyabilir: `belirsiz` (karar verilemedi) ve `sms_degil` (SMS gibi durmuyor).

**Kurallar:**

- `sms_degil = e` olan **3 mesaj en baştan çıkarılır** (778 → 775).
- `belirsiz = e` olan mesajlar **train'den çıkarılır** (8 mesaj), **test'te kalır** (test gerçek hayattaki belirsizliği de ölçmeli).
- Etiket olarak veri setlerinin kendi etiketine güvenilmez; `birlestir.py` onları bizim etiketimizle karşılaştırır ve farkı raporlar.

**Sayılar:** train 659 mesaj, test 116 mesaj. Train'den 8 belirsiz çıkınca **651 mesaj** kalır: 303 spam, 348 meşru. Gerçek dolandırıcılık mesajı sadece **7 tane**. Bu yüzden dolandırıcılığı ana deneyde ayrı sınıf yapmıyoruz (10. bölümdeki karar).

**Git'e girmeyenler** (`.gitignore`): `data/raw/`, `data/processed/`, `data/etiketleme/`, `*_etiketli.csv`, `data/external/`, `models/`, `*.joblib`.

## 4. Bölme protokolü (deneyin kuralları)

Veriyi **grup duyarlı** bölüyoruz: birbirine çok benzeyen mesajlar (aynı şablon) hep aynı kutuya gider. Test seti **kilitli**: model seçimi için kullanılmaz, en sonda bir kez açılır. Ana metrik **spam F1**.

**Neden grup duyarlı?** SMS veri setlerinde aynı şablondan çok mesaj olur ("Mudo ... % indirim" gibi). Rastgele bölersek aynı şablon hem train'de hem test'te kalır, model ezberler ve test puanı olması gerekenden yüksek çıkar (veri sızıntısı).

**`bol.py` nasıl çalışır** (`python -m src.bol --esik 0.60`):

1. Her mesaj normalleştirilir (küçük harf, her rakam 0, tek boşluk). Bu yalnızca benzerlik hesabı içindir.
2. Karakter 3-5'li parçalarla TF-IDF çıkarılır, mesajlar arası kosinüs benzerliği hesaplanır.
3. Benzerliği **0.60 ve üstü** olan mesajlar aynı grup olur. Zincirleme geçerlidir: A∼B ve B∼C ise A, B, C aynı gruptur (union-find).
4. Gruplar büyükten küçüğe, üç sınıfın (meşru / reklam / dolandırıcılık) oranı korunacak şekilde %85 train, %15 test parçasına dağıtılır. Tohum 42.
5. Train içinde aynı yöntemle 5 kat (`fold` sütunu, 0-4) ayrılır; bir grup iki farklı kata düşmez.
6. **Sızıntı kontrolü:** train-test arası en yüksek benzerlik eşiğin altında olmalı; en benzer 5 çift gözle bakılır.

**Eşik neden 0.60?** İlk deneme 0.80'di: 692 grup çıktı, en büyüğü 5 mesajdı. Birbirine benzeyen çiftlere tek tek bakınca gerçek şablonların 0.80'in altında kaldığını gördük. 0.60 bu şablon çiftlerini yakaladı; sızıntı raporu da train-test benzerliğinin eşiğin altında kaldığını gösteriyor.

**Sonuç:** train 659, test 116 mesaj; train 5 kata dengeli bölünmüş. `tests/test_bol.py` içinde 5 test var (normalle, şablon aynı grup, şablon tek parçada ve sızıntı yok, tohum sonucu aynı, CV katlarında şablon bölünmez).

**Deney kuralları:**

- **Ana metrik:** spam F1. Yanında precision, recall ve macro F1 raporlanır.
- **Gürültü sınırı:** test 116 mesaj. 2 puandan küçük farklar anlamlı sayılmaz.
- **CV:** `fold` sütunu + scikit-learn `PredefinedSplit`. Tüm model ve özellik denemeleri bunu kullanır.
- **Model × özellik tablosu:** NB, LR, SVM; her biri kelime ve harf TF-IDF ile.
- **Ortak temizlik:** `src.temizle` (BERTurk ve XLM-R kendi tokenizer'ını kullanır, `temizle` kullanılmaz).
- **Tek bir örneği düzeltmek için ayar yapılmaz** (aşırı uyum / overfit).
- **Hata analizi** train üzerinde CV tahminleriyle (`cross_val_predict`) yapılır, test'te değil.
- **Etiket denetimi kural bazlı ve tüm veride** yapılır. Sadece yanlış tahmin edilen test mesajlarının etiketini düzeltmek, sonucu yapay olarak iyileştirir; yapılmaz.
- **GridSearch sonrası CV puanı iyimserdir** (en iyi ayar CV'ye bakılarak seçildi). Dürüst sayı en sonda test setinin tek seferlik sonucudur.

## 5. Temizleme ve maskeleme

Mesaj modele girmeden iki adımdan geçer: **önce `maskele`, sonra `temizle`**. Bu sıra eğitimde de, canlı kullanımda (FastAPI) da aynı olmak zorunda.

**1. `maskele.py`** (kişisel veriyi gizler, etiketlemeden önce de kullanıldı):

- E-posta → `[EPOSTA]`, link → `[LINK]`, IBAN → `[IBAN]`, telefon → `[TEL]` (05xx, +90, 444'lü kısa numaralar, 0 ile başlayan 11 haneli), kart → `[KART]`, TC kimlik → `[TC]`, "kod/şifre/PIN/OTP" kelimesinden sonra gelen 4-8 haneli sayı → `[KOD]`.
- Kişi adı ve adres maskelenmez, etiketlerken elle `[İSİM]` ve `[ADRES]` yapılır.
- Tutarlar ve kampanya metni **bilerek silinmez**: dolandırıcılığın ipucu orada.

**2. `temizle.py`** (klasik modeller: TF-IDF + NB/LR/SVM/XGBoost için), sırayla:

1. `[LINK]`, `[TEL]` gibi maskelere dokunmaz.
2. **Türkçe küçük harf:** `İ` → `i`, `I` → `ı`, sonra `lower()`. Python'un `lower()` fonksiyonu bu iki harfi yanlış çevirir.
3. **Her rakam 0 olur,** hane sayısı kalır: 4 haneli kod ile 11 haneli telefon numarası farklı görünür (`482915` → `000000`).
4. Art arda boşluklar tek boşluk olur.
5. **Noktalama silinmez** (`!`, `%`, `:` spam ipucudur).
6. İsteğe bağlı `ascii=True`: `ç ğ ı ö ş ü` → `c g i o s u`. Veride akşansız yazılmış mesaj çok olduğu için kullanıldı.

`Temizleyici` sınıfı aynı fonksiyonu scikit-learn Pipeline'ının ilk adımı yapar. Böylece herkes **aynı temizliği** kullanır ve not defterlerinde kod kopyalanıp her seferinde farklılaşmaz. BERTurk ve XLM-R için `temizle` **kullanılmaz**, bu modeller mesajı kendi tokenizer'ıyla işler.

**Training-serving skew (eğitimde ve canlıda farklı işlem) tehlikesi:** Eğitimde linkler `[LINK]` oldu. Canlı bir mesaj maskelenmeden gelirse model onu çok farklı görür. Bir denemede `[URL]` ile `[LINK]` yazmanın model skorunu **0.22** değiştirdiğini gördük. Bu yüzden FastAPI'de `maskele → temizle` sırası sabit ve test edilecek.

**Bilinen sınır:** Rakamların hepsini 0 yapmak, harf yerine rakam koyan bozuk yazımı (`b3dava`, `V0DAF0NE`) bozar: `3` de 0 olur ve kelimeden iz kalmaz. Bunu Gün 8'deki "kelime bozma testi" ile ölçeceğiz. Gerekirse `temizle`'ye leet düzeltmesi (`3`→`e`, `1`→`i`, `0`→`o`) eklenir.

**Test:** `tests/test_temizle.py` 12 test içeriyor. Tüm repoda şu an **41 test geçiyor** (`python -m pytest tests -q`).

## 6. Kavramlar adım adım

Klasik modellerin hepsi aynı sırayla çalışır: **mesajı temizle → parçala ve sayıya çevir (TF-IDF) → modele ver.** Aşağıdakiler bu zincirin parçaları.

**N-gram ve TF-IDF iki ayrı şeydir** (karışıyor, ama farklı):

- **N-gram = metni nasıl kesiyoruz.** *Kelime* n-gram'ı mesajı kelimelere böler (`(1,2)` = tek kelimeler ve ardışık kelime çiftleri). *Harf* n-gram'ı (`char_wb`) kelimeleri 2-5 harflik parçalara böler ve kelime sınırını boşlukla doldurur. Harf parçaları `bedava`, `b3dava`, `bedavaa` gibi yazım bozukluklarına kelime n-gram'ından daha dayanıklı olması beklenir (bunu Gün 8'de ölçeriz).
- **TF-IDF = her parçayı ne kadar önemli sayacağız.** Bir parça mesajda ne kadar sık geçiyorsa ağırlığı artar; tüm mesajlarda çok geçiyorsa ("bir", "ve") ağırlığı düşer, nadir ve ayırt edici parçalar yükselir. Sonuç her mesaj için bir sayı satırı (seyrek matris; örneğin 651 mesaj × 2990 kelime ya da 13403 harf parçası).
- TF-IDF seyrek matriste **StandardScaler gerekmez**: değerler zaten 0-1 arası ağırlık.
- "Embedding" (anlam vektörü) yapmıyoruz: klasik modeller anlam bilmez, sadece hangi kelime ya da harf parçalarının geçtiğine bakar. Anlam BERTurk gibi dil modellerinin işi.

**Modeller:**

- **Naive Bayes (NB):** hangi kelimenin hangi sınıfta ne sıklıkta geçtiğini sayar, olasılık hesaplar. Çok hızlı, basit. Ayar: `alpha` (sıfır sayımı yumuşatma).
- **Lojistik Regresyon (LR):** her kelime/harf parçasına bir puan verir, toplam puan spam olasılığına çevrilir. Ayar: `C` (küçük C = daha temkinli model, büyük C = veriye daha sıkı uyum).
- **SVM (LinearSVC):** iki sınıfı ayıran en geniş boşluğa sahip çizgiyi bulur. Ayar: `C`. Metinde çok iyi çalışır.
- `class_weight='balanced'`: az sınıfı (spam) kaçırmanın cezasını artırır.

**Değerlendirme:**

- **Precision (kesinlik):** "spam dediğimin kaçı gerçekten spam" (yanlış alarm azlığı).
- **Recall (duyarlılık):** "gerçek spam'in kaçını yakaladım".
- **F1:** ikisinin dengesi. Ana metriğimiz **spam sınıfının F1'i**. Macro F1 iki sınıfın ortalaması.
- **5 katlı çapraz doğrulama (CV):** train 5 parçaya bölünür, her seferinde 4'üyle eğitilip 1'iyle ölçülür, 5 puanın ortalaması alınır. Katlar `fold` sütunundan gelir (`PredefinedSplit`), grup duyarlı.

**Pipeline ve GridSearch:**

- **Pipeline:** `temizle → TF-IDF → model` tek nesne. Her CV katmanında TF-IDF sadece o katın eğitim kısmından öğrenilir (test kısmından bilgi sızmaz). Aynı nesne FastAPI'de de kullanılır.
- **GridSearchCV:** ayarların (C, n-gram aralığı, ascii) tüm kombinasyonlarını her biri 5 katla dener, en iyi spam F1'e sahip olanı seçer.

**Dil modelleri:**

- **BERTurk / XLM-R (encoder):** mesajı okuyup anlamını bir vektöre çevirir; sınıflandırma için **ince ayar** yapılır. Bunun için GPU gerekir, bu yüzden Colab'da yapılacak.
- **Ollama LLM (decoder):** metin üretir. Biz onu eğitmiyoruz, sadece **prompt ile açıklama yazdırmak** için kullanıyoruz (tasarım kuralı: karar vermez).

## 7. Baseline sonuçları ve hata analizi

Üç model aynı seviyede: SVM+kelime, LR+harf ve SVM+harf'in spam F1'i **0.973-0.974**. Aralarındaki 0.001'lik fark, her birinin standart sapmasının (±0.013-0.015) çok altında.

&#91;embedded content: python -m src.baseline · 5 katlı CV, 651 mesaj, 31 Ekim 2026\]

`baseline.py` scriptinin yazdığı "En iyi: SVM + kelime" satırı gerçek bir kazananı göstermez, sadece sıralamadaki ilk satırı gösterir.

**Tablodan ne çıkar:**

- **Kelime mi harf mi fark etmiyor** (SVM için ikisi de 0.973-0.974). Harf TF-IDF'i yazım bozmaya daha dayanıklı olması beklendiği için tercih edilebilir, ama bunu sadece Gün 8'deki kelime bozma testi kanıtlar.
- **NB biraz geride** (0.955-0.967): duyarlılığı çok yüksek (0.997) ama kesinliği düşük (0.918-0.940), yani çok fazla yanlış alarm veriyor.
- **Tüm modellerde duyarlılık (0.98-0.99) kesinlikten (0.92-0.96) yüksek:** model spam'i neredeyse kaçırmıyor ama meşru mesajlara fazla spam diyor.
- 6 kombinasyonun 5'inde en iyi ayarda `ascii=True` çıktı.

**Not defterindeki doğrulama (Esra):** elle 5 katlı döngü 0.945, 0.976, 0.975, 0.967, 0.975 verdi (ortalama **0.968**). Pipeline ile aynı 5 sayı çıktı. Kat 0 en zor kat. Salih'in CV sonucu 0.971, yani üç ayrı yoldan aynı bölgeye geldik. Salih'in test sonucunu (0.981) karşılaştırmada kullanmıyoruz: o not defterinde test seti birden fazla kez görülmüştü ve bizim kuralımız test'e bir kez bakmak.

**GridSearch (not defteri, SVM + harf):** 12 ayar (`ascii` × n-gram × `C`) denendi, hepsi **0.960-0.974** arasında kaldı (fark gürültü düzeyinde). En iyi: `C=1`, `ascii=True`, n-gram `(2,5)` → 0.974 ±0.008. Hangi ayar daha iyi diye bakınca: `ascii=True` altı eşleşen çiftin altısında da `False`'tan biraz iyi (+0.001 ile +0.008), `C=0.1` en zayıf (model fazla basit kalıyor). 0.974 en iyi ayar CV'ye bakılarak seçildiği için **iyimser**; dürüst sayı test setinin tek seferlik sonucu olacak.

**CV hata analizi** (train'de, test'e bakılmadı; 651 mesajda **16 hata**): 337 meşru doğru, **11 yanlış alarm**, **5 kaçırılan spam**, 298 spam yakalandı. Spam precision 0.964, recall 0.983, F1 0.974.

Hatalar tek tek düzeltilecek şeyler değil, sınıfın zor olduğu yerleri gösteriyor:

1. **Yanlış alarmlar (meşru etiketli, spam denmiş):** çoğu **kurum bilgilendirme mesajı**: Tivibu ve Cepavans bildirimi, fatura, operatör kampanya bildirimi ("kazandığınız 50 dakika yüklenmiştir"). Bir kısmı **kurumun dolandırıcılık uyarısı**: Vakıfbank "dijital sertifika", "hediye kazandığınızı bildirenlere dikkat", "kamu görevlisi olarak tanıtan" mesajları. Bunlar dolandırıcıyı anlatıyor ama içinde ödül, hediye, TL yükle gibi dolandırıcı kelimeleri var; kelime ve harf tabanlı model niyeti anlamaz. Ayrıca `[TEL] buydu` gibi **maskelenince içi boşalan kısa mesajlar**.
2. **Kaçırılan spam:** "Finansbank şifreniz bloke, \[LINK\] tıkla" (klasik kimlik avı; veride gerçek dolandırıcılık mesajı 7 tane olduğu için normal), aynı şablondan iki "Darphin davet" reklamı (ikisi aynı katta, model o şablonu eğitimde görmedi), meşru bildirime benzeyen operatör ve banka reklamları.
3. **Etiket sınırı belirsiz:** "operatör hizmet bildirimi" ve "dolandırıcılık uyarısı" meşru mü reklam mı? Karar verilirse **tüm 778 mesaj** bu kurala göre taranacak, sadece yanlış bulunanlar değil. Bu soru Salih'e gönderildi (12. bölüm).

Bu bulgular Model Card'a girecek: "Kurumun dolandırıcılık uyarı mesajları spam sanılıyor." BERTurk gibi anlam bilen modelle denenecek.

## 8. Dış veri setleri

İki dış veri seti inceledik ve ikisini de **eğitime katmama** kararı aldık: biri bizim verimize çok az benziyor ama kolay bir kısayol öğretir, öbürü büyük ölçüde zaten elimizdeki UCI verisi. Dosyalar `data/external/` içinde, git'e girmiyor.

| Veri | Mesaj | Dil | Etiketler | Karar |
| --- | --- | --- | --- | --- |
| [Turkish SMS Collection (Kaggle)](https://www.kaggle.com/datasets/onurkarasoy/turkish-sms-collection) | 4751 | Türkçe | Spam 2536, Normal 2215 | Sadece **dış test** (spam yakalama oranı) |
| Dataset\_5971 | 5971 | İngilizce | ham 4844, spam 489, smishing 638 | Eğitime katılmaz; 145 yeni smishing mesajı **uyarlama için kaynak** |

### Turkish SMS Collection (Kaggle)

Sayfada "spam veya normal etiketli Türkçe SMS'ler" yazıyor; kaynak ve lisans belirtilmemiş. Dosya `;` ile ayrılı, sütunlar `Message`, `Group`, `GroupText`. Tekrar eden mesaj 11.

**İçerik bizim sınıflarımıza tam uymuyor:**

- **"Normal" = arkadaş sohbeti** ("Canım benim çok üzgünüm"). Bizim meşru sınıfımızda kurumsal mesajlar da var (banka kodu, kargo, fatura) ve bu veride onlar yok.
- **"Spam" = reklam** (Turkcell kampanyası, indirim, "Mersis:", "SMS çıkmak için RET yaz"). Dolandırıcılık yok.
- **Kısayol riski yüksek:** Spam mesajlar uzun ve çoğunlukla akşansız, normaller kısa ve Türkçe harfli. Model "mesaj uzun mu, ç/ğ/ş var mı" diye bakarak yüksek puan alabilir; bu gerçek başarı olmaz.

| Ölçü | Normal | Spam |
| --- | --- | --- |
| Ortalama uzunluk (karakter) | 46 | 176 |
| En kısa mesaj (karakter) | 1 | 59 |
| Linkli mesaj oranı | %0 | %35 |
| Türkçe harf (ç ğ ı ö ş ü) içeren oranı | %72 | %13 |

**Bizim verimizle çakışma** (`temizle(ascii=True)` + harf TF-IDF benzerliği): 778 mesajımızdan 4'ü birebir aynı, 12'si %80 ve üzeri, 34'ü %60 ve üzeri benziyor. Çiftlere baktık: hepsi kısa sohbet cümleleri ("tamam", "görüşürüz", "nerdesin"), aynı şablondan çıkan mesajlar değil. Dış verinin spam tarafında sadece **5 / 2536**, normal tarafında 47 / 2215 mesaj bizimkilere %60+ benziyor.

**Karar:** Eğitime eklenmez (model "resmi ve kurumsal dil = spam" öğrenir, bizim meşru kurumsal mesajlarımızı spam yapar). **Dış test** olarak, eğitimden sonra bir kez: bizim verimizle eğitilen model bu veriden 5 çakışan mesajı çıkarıp kalan **2531 reklam**ın kaçını yakalıyor (recall). Normal taraf çok kolay olduğu için raporda "dış doğruluk" diye gösterilmez. Bu ölçüm **reklam spam'ini yakalamayı** ölçer, dolandırıcılığı değil. Lisans ve kaynak sayfasından kontrol edilip rapora yazılacak.

### Dataset\_5971 (İngilizce)

Sütunlar `LABEL`, `TEXT`, `URL`, `EMAIL`, `PHONE`. Etiket yazımı tutarsız (`Smishing`/`smishing`, `spam`/`Spam`), küçük harfe çevirince üç sınıf: ham, spam, smishing. Tekrar eden 22 mesaj var. Ham mesajlar kısa sohbet (ort. 71 karakter), spam ve smishing uzun (130-150): Türkçe veride gördüğümüz uzunluk kısayolunun aynısı.

**UCI ile çakışma:** bu veri büyük ölçüde UCI SMS Spam Collection'ın kendisi. Elimizdeki UCI dosyasıyla (5574 mesaj) karşılaştırdık:

| Etiket | Toplam | UCI'de birebir aynı | UCI'ye %80+ benzer |
| --- | --- | --- | --- |
| ham | 4844 | 4319 | 4548 (%94) |
| spam | 489 | 345 | 422 (%86) |
| smishing | 638 | 361 | 453 (%71) |

**"Smishing" etiketi UCI spam'inin bir kısmının yeniden etiketlenmiş hali:** 361 smishing mesajı UCI'de birebir var (ödül ve arama numaralı eski İngiliz mesajları). Spam ile smishing arasındaki çizgi de tutarsız: reklam gibi duran bazı mesajlar "smishing" etiketli. Bu yüzden dolandırıcılık etiketi için güvenilir kaynak değil.

**UCI'de olmayan 145 smishing mesajı** (benzerlik 0.60'ın altında) daha güncel: banka ve ATM bloke, hesap doğrulama, çekiliş, vergi iadesi, COVID yardımı ve ceza, miras. `V0DAF0NE`, `W1NNER` gibi harf-rakam bozmaları da var. Ama **145 mesaj 83 farklı şablona iniyor**: aynı şablon sadece telefon numarası değişerek tekrarlanmış ("Paytm KYC" \~20 kez, "V0DAF0NE ödül" 8, "ATM BLOCK" 10). İçinde dolandırıcılık olmayanlar da var (gözlük, villa ve bilgisayar reklamı, yetişkin sohbet daveti, meşru bir FASTag bildirimi).

**Karar:** Eğitime ya da teste katılmaz (UCI ile çakışıyor, aynı mesajlar iki yerde olursa sızıntı olur). 145 mesaj, Türkçe dolandırıcılık örneği üretmek için **kaynak** olarak kullanıldı (9. bölüm). Atfı ve lisansı raporda belirtilecek.

## 9. Sentetik dolandırıcılık verisi

Gerçek dolandırıcılık mesajımız 7 tane olduğu için iki dosya hazırladık: **100 sıfırdan üretilmiş** ve **145 İngilizce smishing mesajından uyarlanmış 45** Türkçe mesaj. İkisi de **sadece eğitimde** kullanılacak; test hiçbir zaman sentetik mesaj görmez.

| Dosya | Mesaj | Kaynak sütunu | Türler | Ton (resmi / acil / cazip / samimi) |
| --- | --- | --- | --- | --- |
| `data/sentetik/dolandiricilik_v1.csv` | 100 | sentetik | banka, ödül, devlet, kargo, diğer (20'şer) | 35 / 31 / 21 / 13 |
| `data/sentetik/ceviri_v1.csv` | 45 | ceviri | banka 15, ödül 13, devlet 10, diğer 7 | 18 / 16 / 10 / 1 |

**Sütunlar:** `mesaj`, `etiket` (dolandırıcılık), `ikili` (spam), `tur`, `ton`, `bozuk` (hayır / akşansız / leet), `kaynak`, `uretici` (claude).

**1. Sentetik (100 mesaj).** Her türe ton ve yazım çeşitliliği verildi: 81 normal, 14 akşansız, 5 leet (`T3BRIKLER`, `H3SABINIZ`). "Diğer" türünde miras ve fon aktarımı, yatırım ve evden iş vaadi, "anne yeni numaram" ve ilan kaporası gibi tanıdık taklidi dolaylar var. Linkler `[LINK]`, telefonlar `[TEL]`, IBAN'lar `[IBAN]` maskesiyle yazıldı (gerçek link ya da numara yok); `maskele.py`'den geçirince hiçbir mesaj değişmedi. Mesajlar birbirine çok benzemiyor: en yüksek iç benzerlik 0.57, `bol.py` eşiği olan 0.60'ın altında.

**2. Uyarlama (45 mesaj).** 145 mesaj 83 şablona indi; aynı şablonun telefon numarası değişmiş kopyalarını tekrar çevirmenin anlamı yoktu. Kural: **bir şablondan en fazla 1-3 uyarlama**. Düz çeviri yerine Türkiye'ye uyarlandı: para birimi TL ve Türkiye'ye uygun ölçek, BVN/UKGOV/HMRC yerine banka ve e-Devlet gibi karşılıklar, İngiliz arama hatları yerine `[TEL]`, "evden çıkma cezası" gibi pandemi mesajları e-Devlet cezasına çevrildi, `V0DAF0NE` ve `F1VE STAR` gibi bozuk yazımlar korundu. Dolandırıcılık olmayan 145'ten gelenler (reklam, yetişkin sohbet, meşru bildirim) alınmadı. 100'lük dosyayla %60 üzeri benzerlik yok.

**Kontrol:** Esra iki dosyadan yaklaşık 30 mesaja baktı ve "gayet iyi" dedi (Türkçe doğallığı, TL tutarları, kurum yapıları). Model Card'a "sentetik veri üreticisi: Claude, \~30 mesaj örneklemle Esra tarafından incelendi" yazılacak.

**Nasıl kullanılacak** (ek deney: dolandırıcılık):

1. Dosyalar **ayrı kalır**, eğitim kodu bunları tek tabloya ekler (`pd.concat`). Böylece etkisi ayrı ölçülür.
2. Üç koşullı karşılaştırma: **(a)** sadece gerçek veri, **(b)** gerçek + sentetik, **(c)** gerçek + sentetik + çeviri. Çeviri bir fark yaratmıyorsa fazladan karmaşıklık eklememiş oluruz.
3. Ölçü: 7 gerçek dolandırıcılık mesajı ve `docs/bilinen-hatalar.md` örnekleri. Test setindeki gerçek mesajlara dokunulmaz.
4. `bozuk` sütunu Gün 8'deki kelime bozma testinde leet ve akşansız mesajları ayrı ölçmek için kullanılacak.

**Sınırlar:**

- Mesajlar benim (Claude'un) yazım tarzımı taşıyor; gerçek dolandırıcılar daha dağınık ve hatalı yazar. Bu yüzden yalnızca eğitimde kullanılıyor ve etkisi ablation ile ölçülecek.
- `bahis` türü hiç yok (sözlükte var, örnek yazılmadı). `kredi` türü ayrı değil, "banka" ve "diğer" içinde. Kargo sadece sentetik dosyada (20 mesaj).
- Üretim bu bilgisayarda Ollama kurulu olmadığı için burada yapıldı; Ollama açıklama katmanı için ayrıca kurulacak.
- Commit için Salih'in onayı bekleniyor (gizli ya da gerçek kişi verisi yok, kendi ürettiğimiz veri; yine de kurallarımız gereği önce sorulacak).

## 10. Kararlar ve nedenleri

Aşağıdaki kararların hepsi konuşularak alındı. Her birinin nedeni yanında, böylece önce sorulduğunda cevap hazır.

| Karar | Neden |
| --- | --- |
| **Ana deney ikili:** spam (reklam + dolandırıcılık) ve meşru. Dolandırıcılık **ayrı ek deney.** | Gerçek dolandırıcılık mesajı sadece 7. Ek deneyde kural motoru ve sentetik/çeviri örnekler kullanılır, 7 gerçek mesaj kontrol olarak ayrı tutulur. |
| **Kademeli fikir:** Kademe 1 spam/meşru, Kademe 2 dolandırıcılık/reklam, Kademe 3 tür (banka, ödül, kargo...). | Her kademe daha az veriyle daha dar bir soru çözer; veri yetmeyen yerde kural motoru devreye girer. |
| **Grup duyarlı bölme**, benzerlik eşiği 0.60. | Aynı şablon hem train'de hem test'te olursa puan şişer (sızıntı). |
| **Test seti kilitli;** model seçimi 5 katlı CV ile (`fold` sütunu, `PredefinedSplit`). | Test'e bakarak ayar yaparsak test artık tarafsız değildir. Test en sonda bir kez açılır. |
| **Ana metrik spam F1**, yanında precision, recall, macro F1. 2 puandan küçük fark gürültüdür. | Test 116 mesaj; tek bir mesaj F1'i yaklaşık 1 puan oynatabilir. Ana derdimiz spam'i yakalamak. |
| **`belirsiz` mesajlar train'den çıkarılır, test'te kalır.** `sms_degil` mesajlar en baştan atılır. | Belirsiz etiket modelçe öğretilmemeli, ama test gerçek hayatın belirsizliğini de ölçmeli. |
| **Ortak `src.temizle`** (BERT ve XLM-R hariç). Canlıda sıra `maskele → temizle`. | Herkes aynı temizliği kullanır; eğitim ve canlı arası fark (skew) skoru bozar. |
| **LLM sadece açıklar, karar vermez.** | Aynı mesaja her seferinde aynı cevabı vermez ve kanıtlanamaz. Karar kural ve modelde. |
| **Tek bir örneği düzeltmek için ayar yapılmaz.** Etiket denetimi kural bazlı ve tüm veride yapılır. | Sadece yanlış tahmin edilenleri düzeltmek sonucu yapay iyileştirir (aşırı uyum). |
| **Dış veriler eğitime katılmaz.** Kaggle Türkçe veri sadece dış test, Dataset\_5971 sadece örnek kaynağı. | Uzunluk ve harf kısayolu, UCI ile çakışma, etiket gürültüsü (8. bölüm). |
| **Sentetik veri sadece eğitimde,** `kaynak` sütunuyla işaretli, etkisi (a)(b)(c) karşılaştırmasıyla ölçülür. | Yazarının üslubunu taşıyor; gerçek veri gibi test edilmez. |
| **Not defteri öğrenme için, kalıcı kod `src/` içinde.** Not defteri commit'ten önce çıktıları temizlenir. | Çıktılar gerçek SMS içeriyor; etiketli veriyi git'e koymama kuralını dolaylı yoldan bozar. |
| **Git:** bir iş = bir dal = bir PR. Veri ve model dosyaları (`*.joblib`) commit edilmez. Esra PR açar, **Salih inceler ve birleştirir.** | Değişiklikler izlenebilir kalır, birbirinin işini ezmeyiz. |

## 11. Git ve GitHub durumu

Açık tek PR var: **`temizle-esra` → `mesru-etiketleme`** (4 commit, 6 dosya), Salih'in incelemesini bekliyor. `main` henüz `mesru-etiketleme`'deki işleri (`birlestir.py`, etiket rehberi) içermiyor; bu yüzden PR'ın hedefi `main` değil, `mesru-etiketleme` (Salih birleştirince GitHub hedefi `main`'e kaydırır).

**Depo:** `github.com/cansalihturk/sms-fraud-detection` (özel).

**Dallar:**

- `main`: ana dal.
- `mesru-etiketleme`: Salih'in etiketleme işi ve `bol.py` ile ilk `temizle.py` buraya birleşti.
- `temizle-esra`: bizim dalımız (yukarıdaki PR).
- `bolme-esra`: ilk bölme dalı; PR #10 kapatıldı (Salih sadece bir kısmını birleştirdi), bu dal artık kullanılmıyor.
- `nb-svm-salih`: Salih'in yeni NB/SVM dalı; tablomuzla karşılaştırılacak.

**`temizle-esra` commit'leri:**

| Commit | İçerik |
| --- | --- |
| `76f2840` | `Temizleyici` sınıfı (Pipeline için), `test_temizle` güncellemesi, not defteri |
| `14fdf97` | `.gitignore`: `data/external/` yok sayılır |
| `40577c0` | `baseline.py` ve `test_baseline.py` |
| birleştirme commit'i | `mesru-etiketleme` ile birleştirme, `.gitignore` çakışması çözüldü |

**Çakışma nasıl çözüldü:** PR sayfası "Can't automatically merge" dedi. Salih `.gitignore`'a `models/` ve `*.joblib` eklemişti, biz `data/external/` eklemiştik; ikimiz de dosyanın sonuna yazdığı için git hangisini tutacağını bilemedi. `git merge origin/mesru-etiketleme` yapıp git'in koyduğu 3 işaret satırını sildik, **ikisini de tuttuk**.

**PR'da değişen 6 dosya:** `.gitignore`, `notebooks/baseline_esra.ipynb`, `src/baseline.py`, `src/temizle.py`, `tests/test_baseline.py`, `tests/test_temizle.py`.

**Elde ama commit edilmeyen:** `data/sentetik/` (iki sentetik CSV; Salih'in onayını bekliyor) ve `data/external/` (git yok sayıyor).

**Dosya yapısı:**

```text
sms-fraud-detection/
  src/        bol.py  temizle.py  baseline.py  maskele.py  birlestir.py
              hazirla_veri.py  etiketleme_hazirla.py  ortak_uyum.py  uyum.py
  tests/      test_bol.py  test_temizle.py  test_baseline.py  test_maskele.py
  notebooks/  01_uci_okuma  02_veri_dogrulama  baseline_esra
  docs/       etiket-rehberi.md  uyusmazlik_cozumleri.csv
  data/       raw/  processed/  etiketleme/  external/  sentetik/   (git'e girmez; sentetik onay bekliyor)
  PROJECT.md  README.md  requirements.txt  requirements-app.txt
```

**Komutlar** (repo kökünden): `python -m pytest tests -q` (şu an 41 test geçiyor), `python -m src.bol --esik 0.60` (bölme), `python -m src.baseline` (6 kombinasyon tablosu, `--kaydet` ile model dosyası `models/baseline_best.joblib`).

**Git kuralları (hatırlatma):** bir iş = bir dal = bir PR. PR hedefi, alttaki iş birleşmişse `main`, birleşmemişse o dal olur. Commit'ten önce `git status --short` ile `data/` ya da `*.joblib` görünmediğini kontrol et. Not defterinin çıktılarını temizle (`grep -c '"output_type"'` 0 çıkmalı).

## 12. Sıradaki adımlar, Salih'e sorular ve riskler

Bu haftanın ana hedefi **üç şey**: (1) Salih'in kararlarıyla etiket ve protokolü kilitlemek, (2) kural motoru ve dolandırıcılık ek deneyini bitirmek, (3) 1 Kasım'daki model karşılaştırma tablosunu çıkarmak.

### Sırada (öncelik sırasıyla)

- [ ] **Salih'in PR incelemesi** ve aşağıdaki soruların cevabı.
- [ ] **`PROJECT.md` güncelle** (`git pull` sonrası): "Deney protokolü" bölümü, kararlar (ikili ana deney, dolandırıcılık ek deney, belirsiz kuralı) ve "canlı mesaj önce maskele, sonra temizle" satırı.
- [ ] **Kural motoru** (Gün 6): kelime grupları (banka, aciliyet, ödül, devlet, kargo), 8-10 kural, her kararın hangi kuraldan geldiği kayıtlı. Test: 7 gerçek dolandırıcılık mesajı ve sentetik/çeviri mesajlarda kaçını yakalar, meşru mesajlarda yanlış alarm verir mi.
- [ ] **Sentetik veri ablation'ı:** (a) sadece gerçek, (b) + sentetik, (c) + sentetik + çeviri.
- [ ] **`nb-svm-salih` ile tablo karşılaştırması:** Salih'in NB/SVM sonuçları ve bizimkiler aynı protokolle aynı tabloya.
- [ ] **XGBoost ve hibrit** (kural + model).
- [ ] **BERTurk ve XLM-R** Colab GPU'da (Gün 6-7). Bu modeller `temizle` kullanmaz.
- [ ] **1 Kasım (Gün 7): model × özellik karşılaştırma tablosu.**
- [ ] **Gün 8: kelime bozma testi** (`b3dava`, aksansız, harf tekrarı). `temizle`'ye leet düzeltmesi eklemeyi dene.
- [ ] **Servis:** FastAPI (sıra `maskele → temizle → model` testli), Docker, GitHub Actions, Telegram botu.
- [ ] **Yönetişim:** Model Card, NIST AI RMF risk tablosu, Evidently ile veri kayması, SHAP + Ollama açıklaması (Ollama kurulumu gerekecek), MLflow ve DVC, Streamlit, kırmızı/mavi takım döngüsü.
- [ ] **En sonda:** test seti **bir kez**, Kaggle dış testi **bir kez** (2531 reklam, spam recall).
- [ ] Sunum ve demo.

### Salih'e sorular ve istekler

1. **Etiket sınırı:** kurumun "dolandırıcılara dikkat" uyarıları ve operatör hizmet bildirimleri (Tivibu, Cepavans, kampanya yüklendi) meşru mü kalsın? Karar verilirse **tüm 778 mesaj** bu kurala göre taranacak, sadece yanlış bulunanlar değil.
2. **Kaggle Türkçe veri** sadece dış test olarak (spam recall) kullanılsın mı?
3. **Sentetik veri** (`data/sentetik/`) commit edilebilir mi?
4. **Ollama:** Salih hangi modeli kullanıyor? Esra'nın bilgisayarında Ollama kurulu değil.
5. **Not defteri → `src/`:** NB/SVM kodunu `src/`'e taşımak, ortak `Temizleyici`'yi kullanmak, küçük bir `C` ızgarası eklemek, ana metriği macro F1 yerine **spam F1** yapmak, `*.joblib` commit etmemek.
6. **`docs/bilinen-hatalar.md`:** CV hata analizinden çıkan kalıpları (kurum uyarısı, içi boşalan `[TEL]` mesajları, "Finansbank şifreniz bloke") ve Salih'in elle yazdığı banka kimlik avı örneği buraya konacak.

### Riskler

- **Dolandırıcılık verisi çok az** (7 gerçek mesaj). Sentetik veri farklı bir dağılım; işe yaradığını ancak ablation gösterir.
- **Test küçük** (116 mesaj): 2 puandan küçük farkları yorumlamayız.
- **Etiket sınırı belirsiz** (kurum bildirimi ve uyarısı ile reklam); karar gelmeden hata analizi tam kapanmaz.
- **Rakamların 0 yapılması** leet yazımı (b3dava) bozabilir; Gün 8'de ölçülecek.
- **Zaman:** kapsam geniş (listenin sonuna kadar gitmek zor olabilir). Öncelik sırası: ana tablo, kural motoru ve hibrit, FastAPI, Model Card; diğerleri zaman kalırsa.

## 13. Küçük sözlük

Belge boyunca geçen terimlerin basit açıklaması.

| Terim | Ne demek |
| --- | --- |
| **Spam** | İstemediğimiz toplu mesaj. Bizde reklam ve dolandırıcılık birlikte. |
| **Smishing** | SMS ile yapılan kimlik avı dolandırıcılığı (banka şifresini ya da kart bilgisini çalmaya çalışmak). |
| **Meşru** | Gerçek kişiden ya da kurumdan gelen normal mesaj (sohbet, banka kodu, kargo bildirimi). |
| **Etiket / ikili / tür** | Etiket: meşru, reklam, dolandırıcılık. İkili: meşru ya da spam. Tür: dolandırıcılığın kategorisi (banka, ödül, kargo...). |
| **Maske** | Kişisel veriyi `[LINK]`, `[TEL]` gibi etiketle gizlemek. |
| **Train / test** | Train: modelin öğrendiği mesajlar. Test: modelin hiç görmediği, sonda notunu veren mesajlar. |
| **Veri sızıntısı (leakage)** | Test'teki bilginin eğitime karışması (örneğin aynı şablon iki tarafta). Puanı yapay yükseltir. |
| **Grup duyarlı bölme** | Birbirine çok benzeyen mesajları hep aynı tarafa koymak. |
| **Fold / CV (çapraz doğrulama)** | Train'i 5 parçaya bölüp sırayla 4'üyle eğitip 1'iyle ölçmek; 5 puanın ortalaması. |
| **N-gram** | Metni nasıl kestiğimiz: kelime kelime ya da 2-5 harflik parçalar. |
| **TF-IDF** | Her parçayı ne kadar önemli sayacağımız: nadir ve ayırt edici parçalar yüksek, sık geçenler düşük ağırlık. |
| **Pipeline** | Temizle, sayıya çevir, model: üç adımı tek nesne yapar; eğitimde ve canlıda aynı sırayı garanti eder. |
| **GridSearch** | Ayar kombinasyonlarını tek tek deneyip en iyisini seçmek. |
| **Precision / recall / F1** | Precision: spam dediklerimin kaçı doğru. Recall: gerçek spam'in kaçını yakaladım. F1: ikisinin dengesi. |
| **Aşırı uyum (overfit)** | Modelin eğitim verisini ezberleyip yeni mesajda başarısız olması. |
| **Ablation** | Bir parçayı ekleyip çıkararak gerçekten işe yarıyor mu diye ölçmek. |
| **Training-serving skew** | Eğitimde ve canlıda mesajın farklı işlenmesi; model şaşırır. |
| **Leet yazım** | Harf yerine rakam koymak (`b3dava`, `V0DAF0NE`). |
| **Kural motoru** | "Mesajda X ve Y varsa şüpheli" gibi sabit kurallar; hangi kuraldan işaretlendiği bellidir. |
| **Hibrit** | Kural motoru ile modelin birlikte karar vermesi. |
| **Encoder / decoder** | Encoder (BERTurk): metni okuyup anlam vektörüne çevirir, sınıflandırmada kullanılır. Decoder (Ollama LLM): metin üretir, biz açıklama için kullanıyoruz. |
| **İnce ayar (fine-tune)** | Hazır bir dil modelini kendi verimizle biraz daha eğitmek. |
| **SHAP** | Bir kararı hangi kelimelerin etkilediğini gösteren yöntem. |
| **Veri kayması (drift)** | Zamanla mesajların yapısı değiştiği için modelin bozulması; Evidently ile izlenir. |
| **Model Card** | Modelin ne işe yaradığını, sınırlarını ve risklerini anlatan belge. |
| **NIST AI RMF** | Yapay zekâ risklerini yönetmek için bir çerçeve; riskleri tablo halinde yazacağız. |
| **Dış test** | Eldeki verinin dışından gelen başka bir veriyle yapılan ek ölçüm. |
| **Sentetik veri** | Yapay zekâyla üretilmiş örnek mesajlar (gerçek kişi mesajı değil). |
| **Branch / PR / merge** | Branch: ayrı çalışma dalı. PR: "bu dalı ana dala katmamı ister misiniz" isteği. Merge: katılması. Çakışma: iki kişi aynı satırı değiştirdiğinde git'in hangisini tutacağını sorması. |

## 14. Gün 7 (1 Kasım): Notebook'ta TF-IDF ve CV'nin içini açtık

Bugün yeni bir model kurmadık; Esra'nın notebook'unda TF-IDF matrisini, harf parçalarını ve CV'nin tek turunu elle açıp her satırın ne yaptığını öğrendik. Amaç, `src` içindeki kodun arkasında ne döndüğünü anlamak.

### 14.1 TF-IDF matrisi M nasıl okunur

`M` bir tablo gibidir: **her satır bir mesaj, her sütun bir kelime**, hücre de o kelimenin o mesajdaki puanıdır. Gerçek `M` 651 satır × 2990 sütun (yaklaşık 1,9 milyon hücre) ve neredeyse hepsi 0 olduğu için Python sıfırları saklamaz, sadece dolu hücreleri tutar (**seyrek matris**). `print(M)` bu yüzden şöyle görünür:

```text
(0, 228)    0.3676
(0, 1255)   0.5369
```

İlk sayı **satır** (mesaj no), ikinci sayı **sütun** (kelime no), sonuncusu **puan**. Mesaj 0'ın 4 dolu hücresi var; yani 4 farklı kelimeden oluşuyor.

Kelime numarasını kelimeye çevirmek için kullanılan parçalar:

| Kod | Ne yapar |
| --- | --- |
| `vek.get_feature_names_out()` | Sütun başlıkları: sütun no → kelime listesi (2990 kelime) |
| `satir = M[0]` | İlk mesajın satırı |
| `satir.nonzero()` | İki liste verir: `[0]` dolu hücrelerin **satır** no'ları (tek satır aldığımız için hep 0), `[1]` **sütun** no'ları |
| `kelimeler[satir.nonzero()[1]]` | Dolu sütunların kelimeleri |
| `satir.data.round(3)` | Dolu hücrelerin puanları, 3 basamak |
| `zip(kelimeler, puanlar)` | Kelime ile puanını eşler |
| `sorted(..., key=lambda t: -t[1])` | Puana göre büyükten küçüğe sıralar |

Yüksek puan = kelime o mesajı ayırt ediyor (az mesajda geçiyor); düşük puan = her yerde geçen yaygın kelime. Her satır L2 normalize olduğu için puanların karelerinin toplamı yaklaşık 1'dir.

### 14.2 Kelime yerine harf parçası (char\_wb)

`TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), lowercase=False, min_df=2)` mesajı kelime kelime alır, her kelimenin içinden 2-5 harflik parçalar çıkarır. `bedava` kelimesinden örneğin `  b `, `be`, `eda`, `dava`, ` ava  ` gibi parçalar çıkar. `min_df=2` yalnızca tek mesajda geçen parçaları atar; `lowercase=False` çünkü küçük harfe çevirmeyi `temizle` zaten yaptı.

|  | analyzer=word | analyzer=char\_wb |
| --- | --- | --- |
| Ek alan kelimelere dayanıklılık (kazandınız / kazandın) | hayır, ayrı kelimeler | evet, ortak parçalar eşleşir |
| Yazım bozmaya dayanıklılık (bedavaaa) | hayır | kısmen |
| Okunabilirlik | yüksek | düşük |
| Sütun sayısı | az (\~3 bin) | çok fazla |
| Bizim veride CV skoru | \~0.97 | \~0.97 |

İkisini de denedik; fark 2 puandan küçük olduğu için gürültü sayıldı. char\_wb'nin üstünlüğü bu veride **kanıtlanmış değil, beklenen bir avantaj**. Karar Gün 8'deki kelime bozma testine kalıyor.

### 14.3 CV'nin tek turu elle: fold 0

Notebook'taki hücre, 5 katlı CV'nin yalnızca birinci turunu elle yapıyor. Amaç `cross_val_score`'un içinde ne döndüğünü görmek ve sınıflara göre tam raporu okumak.

1. `egit = train["fold"] != 0` ve `dene = train["fold"] == 0`: her mesaj için True/False işaretleri. `X` ve `y` değişmez, `X[egit]` onların süzülmüş halidir (Excel'de filtre gibi). Eğitim: fold 1-4 (\~520 mesaj), sınav: fold 0 (\~130 mesaj).
2. `temizle` her mesaja uygulanır: `X_egit`, `X_dene`.
3. `A = vek.fit_transform(X_egit)` kelime/parça listesini **yalnızca eğitimden öğrenir**; `B = vek.transform(X_dene)` öğrenmeden, eğitimdeki listeyi kullanır. Sınav mesajlarından bir şey öğrenmemek, sızıntıyı önler.
4. `model.fit(A, y[egit])` modele mesajları ve doğru cevapları verir. `model.predict(B)` yalnızca mesajları alır, **y almaz**; kendi tahminini üretir.
5. `classification_report(y[dene], tahmin)` gerçek etiketlerle tahminleri karşılaştırır ve precision, recall, F1 tablosu yazar. Ana metriğimiz spam satırındaki F1.

`class_weight="balanced"` az olan sınıfa daha fazla ağırlık verir; `random_state=55` tekrar çalıştırmada aynı sonucu garanti eder (55 ya da 42, fark etmez).

### 14.4 X ve y, eğit/dene ve klasik isimler

`X` modele verdiğimiz girdi (mesajlar), `y` modelin bulmaya çalıştığı cevap (1 spam, 0 meşru). `y = f(x)` yazımından gelen genel adlandırmadır. Eğitimde ikisi birlikte verilir (`fit`), tahminde yalnızca X (`predict`), değerlendirmede y ile tahmin karşılaştırılır.

| Klasik isim | Bizdeki karşılığı |
| --- | --- |
| `X_train` | `X_egit` (fold ≠ 0) |
| `X_test` | `X_dene` (fold = 0) |
| `y_train` | `y[egit]` |
| `y_test` | `y[dene]` |

**Dikkat:** buradaki "dene" gerçek test seti değil, train'in içinden ayırdığımız geçici sınav kısmıdır. Gerçek test (`tr_test.csv`, 116 mesaj) hiç açılmadı ve en sonda bir kez açılacak. Bu yüzden kodda "test" değil "dene" adını kullandık.

### 14.5 Pipeline + PredefinedSplit: aynı işin otomatik hali

```python
p = Pipeline([("temizle", Temizleyici()), ("vek", TfidfVectorizer(...)), ("model", LinearSVC(...))])
kat = PredefinedSplit(train["fold"])
skor = cross_val_score(p, X, y, cv=kat, scoring="f1")
```

`PredefinedSplit` sklearn'e "bölmeyi sen yapma, `fold` sütununda hazır" demenin yoludur. Her fold sırayla sınav olur, kalanlar eğitim. Sklearn'ün kendi rastgele bölmesi benzer mesajları ayırıp sızıntı yaratırdı, `bol.py`'ninki yaratmaz.

|  | Elle (fold 0) | `cross_val_score` + `PredefinedSplit` |
| --- | --- | --- |
| Bölme | `egit` / `dene` işaretleri | `PredefinedSplit` kurar |
| TF-IDF | `fit_transform` / `transform` elle | Pipeline içinde, her turda yalnızca o turun eğitiminden |
| Model | `fit` / `predict` elle | otomatik |
| Kapsam | yalnızca fold 0, tam rapor | 5 fold, 5 skor |

Kim ne yaptı? `bol.py` fold numarasını **verdi** (bir kez, kalıcı); notebook hücresi ve `cross_val_score` o numarayı **kullanır**. Elle yazmak öğrenmek içindir, gerçek deneylerde `cross_val_score` / GridSearch kullanılır. Bölmek şarttır: modeli gördüğü mesajlarla sınarsan skor \~1.00 çıkar ve hiçbir şey kanıtlamaz.

## 15. Gün 8-9 (2-3 Kasım): Zor test ve SVM ile ilk ölçüm

Kolay veride SVM'in spam F1 değeri 0.97 idi. Gerçek kurumsal mesajlardan oluşan zor sette aynı model 0.76'ya düştü, yani başarı verinin zorluğuna bağlıydı.

**Zor set.** Esra ve Salih'in telefonlarından gerçek mesajlar: 131 etiketli mesaj (67 meşru, 54 reklam, 10 dolandırıcılık), belirsiz mesajlar dışarıda. Her gönderici için en fazla 5 mesaj tutuldu, aynı şablonun tekrarı atıldı, gönderici adları büyük harfe ve boşluksuza çevrildi (NKOLAY / nkolay sızıntısı böyle kapandı).

**Ölçüm.** Ana ölçüt spam F1 (spam = reklam + dolandırıcılık), yanında yanlış alarm (meşru mesaja "spam" demek) ve dolandırıcılık yakalama sayısı. Gerçek mesajlar eğitime girdiğinde şablon sızıntısı olmasın diye gönderici bazlı "birini dışarıda bırak" (LOSO) kullandık. Test dosyası `tr_test.csv` kilitli, sadece en sonda bir kez açılacak.

| Deney | Eğitim | Spam F1 | Dolandırıcılık yakalama |
| --- | --- | --- | --- |
| A | tr\_train | 0.76 | 8/10 |
| B | A + gerçek mesajlar (LOSO) | 0.87 | 9/10 |
| C | A + sentetik | 0.81 | 9/10 |
| D | A + gerçek + sentetik (LOSO) | 0.89 | 10/10 |

(SVM, ±0.02 gürültü payı sayılır.) Hatalar dört türde toplanıyor: kargo ve sipariş bildirimi, operatör ve abonelik mesajı, resmî uyarı, sigorta bildirimi. tr\_train'deki meşru mesajların yaklaşık %90'ı günlük sohbet olduğu için model bu türleri hiç görmemişti; bu bir varsayım ve henüz kanıtlanmadı.

## 16. Gün 9-10 (3-4 Kasım): Sentetik v2, 58 mesaj ve A'dan E'ye sonuç

Gerçek kurumsal mesaj yanlış alarmını 40'tan 6'ya indirdi, sentetik dolandırıcılık mesajları yakalamayı 5/10'dan 9/10'a çıkardı; ikisi birlikte en iyi sonucu verdi (Salih'in LOSO deneyi, 131 zor mesaj, 67 meşru, 64 spam, 10 dolandırıcılık).

**Sentetik v2.** Salih ilk sentetik veriyi inceledi: zor setle sızıntı yok (en yüksek benzerlik 0.43), tekrar yok. Üç düzeltme istedi ve uygulandı:

| Sorun | Önce | Sonra |
| --- | --- | --- |
| `[LINK]` dengesi, sahte mesajlarda link | 37/40 | 28/40 |
| `[LINK]`, meşru sentetiklerde link | 7/48 | 26/56 (gerçekte yaklaşık %51) |
| Marka adı, sahte mesajlarda | 1/40 | 26/40 |
| Maske biçimi | 0000000, 000000 | `[TEL]`, `[KOD]` (sipariş ve takip no 0000000 kalıyor) |

Model "link varsa sahte" kısayolunu öğrenmesin diye link ve marka iki sınıfta benzer oranlara getirildi. Bunlara ek olarak 8 banka kaynaklı meşru mesaj eklendi (sahtelerde banka markası çoktu, meşrularda hiç yoktu). Salih'in tespiti: düzeltilmiş sentetik veri işe yarıyor.

**Salih'in 58 mesajı.** Salih kurumsal kutusundan 60 mesaj etiketledi. Aynı mesajın iki kopyası (OEDAS, belirsiz işareti) çıkarılınca 58 mesaj kaldı (36 meşru, 22 reklam). Bu mesajlar eğitimde yoktu, o yüzden taıze bir sınav oldu:

| Model | Eğitim | Spam F1 | Yanlış alarm | Yakalanan spam |
| --- | --- | --- | --- | --- |
| SVM A | sadece tr\_train | 0.79 | 12/36 | 22/22 |
| SVM v0 | tr\_train + sentetik v1 + zor gerçek | 0.86 | 7/36 | 22/22 |

v0'ın 7 yanlış alarmı: borç ve gecikme bildirimi (2), resmî uyarı (IMEI), güvenlik uyarısı (Vodafone Pay), KVKK bilgilendirmesi, kısa kargo ve sipariş takibi (2). Bu mesajlara baktığımız için artık "hiç görmemiş test" sayılmaz; karar olarak eğitime katıldılar ve rapora "önce test, sonra eğitim" diye yazıldı.

**A'dan E'ye (Salih'in LOSO deneyi, 131 zor mesaj).**

| Deney | Eğitim | Yanlış alarm | Spam yakalama | Dolandırıcılık | F1 |
| --- | --- | --- | --- | --- | --- |
| A | tr\_train | 41/67 | 59/64 | 5/10 | 0.720 |
| C2 | + sentetik v2/v3 | 39/67 | 63/64 | 9/10 | 0.759 |
| B | + gerçek (LOSO) | 6/67 | 58/64 | 5/10 | 0.906 |
| D | + gerçek + sentetik | 10/67 | 62/64 | 9/10 | 0.912 |
| E | + gerçek + sentetik + 58 mesaj | 6/67 | 63/64 | 10/10 | 0.947 |

Gerçek mesaj yanlış alarmı bitiriyor, sentetik dolandırıcılığı yakalatıyor, ikisi birlikte en iyisi. Dolandırıcılıkta yalnızca 10 mesaj var, 9/10 ile 10/10 arası tek mesajdır; bu yüzden "kesin" değil "tutarlı eğilim" deriz. E'deki 58 mesajın göndericileri sınav göndericileriyle örtüşüyorsa E biraz iyimser olabilir (Salih'e sorulacak).

## 17. Havuz deneyi: kural ile etiketlenen veri modele kısayol öğretti

Salih'in telefonundan toplanan 1287 mesajlık havuz yanlış alarmı 39'dan 2'ye indirdi ama dolandırıcılık yakalamayı 9/10'dan 2/10'a düşürdü; neden etiketleme kuralıydı ve "RET yaz" ifadesi silinince sorun büyük ölçüde geçti.

**Havuz nasıl etiketlendi.** Elle değil, bir kuralla: mesajda "SMS RET / İPTAL yazıp 3525'e gönder" gibi bir satır varsa reklam, yoksa meşru. Havuzda bu kural yüzde 100 geçerliydi, çünkü etiketi onunla koyduk.

| Deney | Eğitim | Yanlış alarm | Spam yakalama | Dolandırıcılık |
| --- | --- | --- | --- | --- |
| C2 | tr\_train + sentetik | 39/67 | 63/64 | 9/10 |
| B | + Esra'nın gerçek verisi | 6/67 | 58/64 | 5/10 |
| G\_tum | + havuz (1287) | 2/67 | 50/64 | 2/10 |
| G\_sablon | + havuz (842, şablon tekrarı atılmış) | 2/67 | 52/64 | 2/10 |
| G\_40 | + havuz (738, sınırlı) | 3/67 | 54/64 | 4/10 |

**Neden?** Model mesajın içeriğine değil etiketleme kuralına baktı: "RET yazısı yok, o halde meşru." Dolandırıcılık mesajlarında RET satırı olmadığı için hepsini meşru saydı. Bu, daha önce sentetikte gördüğümüz `[LINK]` kısayoluyla aynı türden bir hata (zayıf denetimle etiketleme tuzağı).

**Düzeltme.** RET ifadesi eğitim verisinden silinince dolandırıcılık yakalama 2/10'dan 7/10'a çıktı, yanlış alarm 2/67'den yalnızca 4/67'ye çıktı. Bu şekilde (G\_sablon\_retsiz) Esra'nın verisi olmadan F1 0.921 elde edildi; B (0.906) ve D (0.912) ile aynı düzeyde, ±0.02 gürültü payı içinde. Yani tek kişinin SMS kutusu ve doğrulanmış bir kural, elle toplanan veri kadar işe yaradı: ölçeklenebilir veri toplama yöntemi. Şablon tekrarı atılmış sınırsız havuz (842), sınırlı havuzdan (738) daha iyiydi.

**Son deney F.** E (Esra'nın verisi + sentetik + 58 mesaj) ile havuzun birleşimi:

|  | Yanlış alarm | Spam yakalama | Dolandırıcılık | F1 |
| --- | --- | --- | --- | --- |
| E | 6/67 | 63/64 | 10/10 | 0.947 |
| F (E + havuz) | 5/67 | 60/64 | 9/10 | 0.930 |

Ölçüt sonuçtan önce konmuştu: "dolandırıcılıkta 10/10 ve yanlış alarm 6 veya daha az". E bunu karşılıyor. F yanlış alarmda 1 iyi, dolandırıcılıkta 1 kötü; F1 farkı 1.7 puan, protokolde 2 puanın altında, yani gürültü. Ayırt edilemeyince daha basit olan seçilir: **son modelin veri tarifi E.** Havuz son modele girmiyor ama deneyi rapora girer. Havuz Salih'in bilgisayarında kalıyor ve kimseyle paylaşılmıyor, yalnızca sonuçlar paylaşılıyor.

## 18. Arayüz demosu (4 Kasım)

Mesajı yapıştırınca spam mı meşru mu, hangi türde ve neden olduğunu gösteren çalışan bir demo hazır: Streamlit sayfası FastAPI'ye mesaj gönderir, API maskeler, SVM skor verir, kural motoru türü ve açıklama nedenini ekler.

| Parça | Dosya | Ne yapıyor |
| --- | --- | --- |
| Tahmin | `src/tahmin.py` | `models/svm_v1.joblib` modelini açar, mesajı maskeler, skor ve etiket üretir (skor 0'dan büyükse spam) |
| Açıklama | `src/tahmin.py` | Her kelimeyi tek tek çıkarır, skorun ne kadar değiştiğine bakar; artı değer kelimenin mesajı spam'e çektiği anlamına gelir |
| Tür | `src/kurallar.py` | Model "spam" derse türü işaret kalıplarıyla bulur. Reklam: RET yaz, SMS iptal, MERİS, indirim ve kampanya. Dolandırıcılık: şifre, kart bilgisi, IBAN, kimlik, doğrulama, kapatılacak veya bloke, hemen tıkla, icra, haciz, ceza. En az 1 dolandırıcılık işareti ve reklam işaretlerinden fazlası gerekir, aksi halde reklam |
| API | `src/api.py` | `POST /tahmin` etiket, skor, `aciklama` ve `tur` döndürür |
| Sayfa | `src/arayuz.py` | Kırmızı (dolandırıcılık şüphesi), turuncu (reklam), yeşil (meşru) kart; "Neden bu karar?" bölümü; örnek mesajlar; boş mesaj ve API kapalı uyarıları |

**İlk bulgu.** İlk modelle (v0) "Tebrikler! 50.000 TL ödül kazandınız, hemen tıklayın" mesajında en büyük spam etkisi `[LINK]` (+0.52), sonra "hemen" (+0.253) ve "tıklayın" (+0.189) çıktı; "50.000" ise meşru yönünde (-0.126). Açıklama, modelin link kısayolunu kullandığını gözle görmemizi sağladı ve Salih'in sentetik veri düzeltmesini destekledi.

**Notlar.**

- Karar yalnızca modelin; kural motoru sadece tür etiketi verir, açıklama sadece nedenini gösterir. LLM (Ollama) cümlesi sonraya bırakıldı.
- Kural motorunun kalıpları basit bir ilk sürüm. Bir veri setinde ölçülmedi, yalnızca örnek mesajlarla denendi.
- `svm_v1`: 935 mesajla eğitildi (tr\_train 651, sentetik v2 96, zor gerçek 131, Salih'in 58'i; 1 tekrar atıldı), yani E veri tarifi.
- Model not defterinde scikit-learn 1.6.1 ile kaydedildi, API ortamında 1.9.1 var; yükleme sırasında sürüm uyarısı çıkıyor. Son model aynı sürümle eğitilip kaydedilecek.
- Sentetik ve zor veri dosyaları ile model dosyaları git'e girmiyor; arayüz kodu `esra/arayuz-demo` dalında, Salih'in onayında.

## 19. Kararlar ve dürüstlük notları (Gün 8-10)

Ölçütleri sonuçtan önce koyuyoruz, yeni veriyi önce ölçüp sonra eğitime kattık ve sınırlarımızı raporda açık yazıyoruz.

| Karar | Neden |
| --- | --- |
| `tr_test.csv` kilitli, sonda bir kez açılır, üzerinde ayar yapılmaz | Hoca bazı test örneklerini gördü, test sonucunu kendimize uydurmamalıyız |
| Ham telefon dışa aktarımları yalnızca `data/raw/`, `data/`, `models/` ve `*.joblib` git'e girmez, ham havuz kimseyle paylaşılmaz | Kişisel bilgi (ör. hesap bakiyesi) içerebilir; yalnızca sonuçlar ve maskeli örnekler paylaşılır |
| Eğitim dışı gönderici bazlı ölçüm (LOSO) | Rastgele k-fold, aynı şablonun hem eğitimde hem testte olmasına yol açar |
| Belirsiz mesajlar eğitim ve testten çıkarılır; yeni kural: siyasi çağrı ve kurum tanıtımı belirsiz (Salih'in onayı bekliyor) | Etiketi tartışmalı mesaj ölçümü bozar |
| Salih'in 58 mesajı önce sınav, sonra eğitim; raporda öyle yazılır | Hatalarına baktık, artık taıze test sayılmaz. Nihai ölçüm `tr_test.csv` ve Kaggle dış testi |
| Son modelin veri tarifi E (havuz yok) | Ölçüt önceden konmuştu: dolandırıcılık 10/10 ve yanlış alarm en fazla 6; F ayırt edilemedi, basit olan seçildi |
| Sentetik veri Salih onayından sonra kullanılır; link, marka ve maske oranları iki sınıfta dengeli | Model kısayol (link var, marka var) öğrenmesin |
| Kural ile etiketlenen veriden etiketleme ipucu silinir | Havuz deneyinde RET kuralı modele kısayol öğretti |

**Sınırlamalar.**

- Dolandırıcılıkta yalnızca 10 gerçek mesaj var; 9/10 ile 10/10 arası tek mesajdır.
- Zor set ve 58 mesaj küçük; ±0.02 fark gürültü sayılır.
- 58 mesajın göndericileri zor setin göndericileriyle örtüşebilir, E bu yüzden biraz iyimser olabilir.
- Veriler az sayıda kişinin telefonundan geliyor; ülke ve operatör çeşitliliği sınırlı.
- Kural motoru (reklam ya da dolandırıcılık türü) ölçülmedi.
- E deneyleri Salih'in modeli ile yapıldı; SVM için aynı LOSO (E) deneyi henüz koşulmadı.

## 20. Sıradaki adımlar: çarşamba, perşembe, cuma

Veri çarşamba gece yarısı donuyor; perşembe son eğitim ve tek seferlik test, cuma sunum.

| Gün | İş | Kim |
| --- | --- | --- |
| Çarşamba | Kural motoru ve arayüz değişikliklerini commit'le, PR'ı Salih'e bildir | Esra |
| Çarşamba | Rapor ve `docs/zor-test.md` tablolarını güncel sayılarla güncelle | Esra |
| Çarşamba | SVM için E deneyi (LOSO), aynı protokol | Esra |
| Çarşamba | Yeni veri gelirse etiketle, temizle (tekrar, belirsiz, gönderici başına en fazla 5), gece yarısı dondur | Salih ve Esra |
| Perşembe | Son eğitim (E tarifi, aynı scikit-learn sürümü), model dosyasını arayüze tak | Salih ve Esra |
| Perşembe | `tr_test.csv` tek seferlik ölçüm, Kaggle dış testi, model seçimi (SVM ya da XLM-R) | Salih ve Esra |
| Perşembe | Maske tutarlılığı (`[KOD]`, `[TEL]` ile 000000, 0000000), Model Card ve NIST AI RMF, Docker ve CI | Salih ve Esra |
| Perşembe | Slaytlar ve prova | Esra |
| Cuma | Sunum: problem ve veri, modeller tablosu, hoca eleştirisi ve zor test hikayesi, sistem, canlı demo, sınırlamalar | Esra ve Salih |

## 21. Gün 10 akşamı (4 Kasım): nihai model SVM, Docker ve CI, kural motoru, kelime bozma

Nihai model SVM oldu; aynı akşam Docker ve CI kuruldu, kural motorunun tür doğruluğu ölçülüp 4/10'dan 9/10'a çıkarıldı ve kelime bozma testi yapıldı.

### 21.1 Nihai model kararı: SVM

Salih SVM'i bizim `tahmin()` yolumuzla aynı sınava soktu (97 görülmemiş gerçek meşru + 60 gemma saldırısı).

| Model | Yanlış alarm | Saldırı yakalama | Zor set F1 |
| --- | --- | --- | --- |
| SVM (E tarifi) | 7/97 (%7.2) | 35/60 (%58) | 0.923 (6/67, 60/64, 10/10) |
| XLM-R E (3 tohum) | %12.4 | %66 (52–78) | 0.940 (E\_v2, düzeltilmiş gruplama; 7/67, 63/64, 10/10) |

Önceden yazdığımız kural: dolandırıcılıkta fark XLM-R'ın bandının içindeyse yanlış alarm az olan kazanır. SVM'in %58'i XLM-R bandının (52–78) içinde, yanlış alarmı da daha iyi; zor sette de SVM öndeydi. Karar kapandı: **SVM**.

### 21.2 Docker ve CI

- `Dockerfile`, `requirements-docker.txt`, `docker-compose.yml` (api + arayüz, `models/` dışarıdan bağlanır), `.dockerignore`
- GitHub Actions (`ci.yml`): her push ve PR'da pytest ve `docker build`; PR #22 ile `main`'e girdi
- Model scikit-learn 1.6.1 ile kaydedildi, `.venv`'de 1.9.1 uyarı verdi: Docker'da `scikit-learn==1.6.1` sabitlendi
- Docker yerelde denenmedi (kurulu değil), derlemeyi CI doğruladı
- Arayüzün API adresi `API_ADRESI` ortam değişkeninden okunuyor

### 21.3 Kural motoru tür doğruluğu

Model "spam" dedikten sonra türü kural motoru belirliyor. Zor sette 64 spam mesajında ölçüldü: dolandırıcılığın 6/10'u "reklam" çıktı (sebep: iş ilanı, kripto ve kargo adresi gibi kalıpların kurallarda olmamasıydı).

|  | Dolandırıcılık mesajını bulma (zor, 10) | Reklam doğru (zor, 54) | Sentetik dolandırıcılık (40) |
| --- | --- | --- | --- |
| Önce | 4/10 | 54/54 | 24/40 |
| Kurallar genişletildi (zor set hataları) | 9/10 | 54/54 | 24/40 |
| Kurallar genişletildi (sentetik hataları) | 9/10 | 54/54 | 39/40 |

**Dikkat:** Kurallar bu mesajlara bakılarak genişletildi, sayılar iyimser. Yeni kalıplarda düşebilir. `tests/test_kurallar.py` ile 4 örnek koruma altına alındı.

### 21.4 Kelime bozma testi ve harf–kelime karşılaştırması

Zor sette yalnızca sınav mesajları bozuldu (aksansız, leet, harf tekrarı); model gönderici dışı bırakılarak (LOSO) eğitildi.

| Bozma | Harf: yakalanan spam / dolandırıcılık / yanlış alarm | Kelime: yakalanan spam / dolandırıcılık / yanlış alarm |
| --- | --- | --- |
| Normal | 60 / 10 / 6 | 60 / 10 / 11 |
| Aksansız | 61 / 10 / 6 | 62 / 10 / 16 |
| Leet | 59 / 9 / 18 | 60 / 10 / 15 |
| Harf tekrarı | 59 / 8 / 9 | 62 / 10 / 18 |

Bulgu: yakalamada fark yok (iki model de bozuk mesajı yakaladı), yanlış alarmda harf tabanlı 4 durumun 3'ünde daha az. Bu yüzden "harf bozmaya daha dayanıklı" iddiasını yakalamada doğrulayamadık; "aynı yakalamayla daha az yanlış alarm" diyoruz. Meşru mesajlar da bozulduğu için yanlış alarm arttı (gerçekte dolandırıcı yalnızca kendi mesajını bozar). Test edilmeyenler: harf arasına boşluk, benzer görünümlü harf, kelime sırası.

### 21.5 Yönetişim belgeleri

Risk Kaydı (NIST AI RMF, 12 risk) ve Model Card: [Risk Kaydı](risk_kaydi.md), [Model Card](model_card.md). tr_test ve dış test sonuçları bu belgelere işlendi.

### 21.6 Yapılmayanlar

Evidently ile veri kayması izleme, Ollama açıklaması, Telegram botu, boşluklu ve benzer görünümlü harfli bozma testi, kural motoru için bağımsız bir tür test seti.

## 22. Gün 11 sabahı (5 Kasım): kilitli tr\_test ve dış testler

Nihai `svm_v1` kilitli tr\_test'te F1 0.972 verdi; Kaggle dosyaları bağımsız değil, İngilizce UCI testinde ise model başarısız.

| Test | Mesaj | F1 | Yanlış alarm | Kaçan spam |
| --- | --- | --- | --- | --- |
| tr\_test (kilitli, tek bakış) | 116 (54 spam, 62 meşru) | 0.972 | 1/62 | 2/54 |
| UCI SMS Spam (İngilizce) | 5574 (747 spam) | 0.344 | 28/4827 | 586/747 |

**tr\_test:** Aynı sette XLM-R E (Salih, bir bakış): F1 0.953, yanlış alarm 2/62, kaçan spam 3/54. Not: tr\_test projede ilk kez açılmıyor, Salih'in Gün 5-6 tablolarında aday modeller de bu sette ölçülmüştü; bu yüzden "dokunulmamış" değil, "ayar yapılmadan model başına bir bakış" diyoruz. SVM'in 3 hatasından ikisinin (id 661, 5869) etiketi tartışmalıydı (`uyusmazlik_cozumleri.csv`); test etiketleri değiştirilmedi, sonuç olduğu gibi raporlandı. tr\_test, kolay veri dağılımına yakın olduğu için 0.97 seviyesi beklenen bir değerdir; zor gerçek mesajlarda başarı 0.92'dir. Eklenecek bağlam: hoca bu testten bazı örnekleri görmüştü.

**Kaggle:** `turkishsms.csv` (765 mesaj) ve `turkishsms_val.csv` (85 mesaj) bizim verimizin kaynağı çıktı (669 ve 75 mesaj verimizde birebir var), bu yüzden bağımsız dış test olarak kullanılmadı.

**İngilizce (UCI):** Model yalnızca Türkçe veriyle eğitildi, İngilizce spam'in %22'sini yakaladı (161/747). Model Card'daki "Türkçe veya İngilizce" ifadesi bu yüzden "yalnızca Türkçe" olarak düzeltildi. Proje hedefindeki İngilizce desteği (EN→TR aktarım) yapılmadı.
