# Zor Test: Gerçek Kurumsal SMS'lerle Ölçüm

## 1. Amaç

İlk modellerimiz `tr_train` üzerindeki 5-fold CV'de spam F1 ≈ 0.97 aldı.
Meşru sınıf çok kolay, çünkü örneklerin büyük kısmı kişisel sohbet; firmaların gönderdiği gerçek ama spam olmayan mesajlar yok.

Gerçek telefon kutularından toplanan kurumsal mesajlarla bir "zor test" kurduk. Sorular:

1. Mevcut model (yalnız `tr_train`) gerçek kurumsal mesajlarda ne kadar iyi?
2. Gerçek kurumsal mesajlar eğitime girince, modelin hiç görmediği göndericilerde
   sonuç düzeliyor mu?

## 2. Veri

Zor test, iki gönüllünün kendi telefon kutusundan dışa aktarılan **kurumsal ve
spam** mesajlardan oluşur. Kişisel yazışmalar hiçbir aşamada dahil edilmedi.

| Kaynak | Etiketli | Meşru | Reklam | Dolandırıcılık |
| **Toplam** | **133** | **68** | **54** | **11** |

**1. kısım:** bir gönüllünün telefon kutusu (84 etiketli mesaj).
**2. kısım:** ikinci gönüllünün iki ayrı dışa aktarması (49 etiketli mesaj).

Bunların dışında **8 mesaj "belirsiz"** olarak işaretlendi (etiketi tartışmalı
ya da rehberde karşılığı olmayan, ör. siyasi çağrı, kurum tanıtımı). Belirsiz
mesajlar ne eğitimde ne ölçümde kullanılır. Dosyada toplam 141 satır var.

Veri kuralları:

- Mesajlar yalnızca Türkçe.
- Her göndericiden **en fazla 5 mesaj** tutuldu. Aksi hâlde tek bir gönderici
  (ör. 98 mesajlık bir reklam numarası) testi ele geçirirdi.
- Aynı göndericiden aynı şablonun (rakamları farklı) tekrarları atıldı.
- `tr_train.csv` ve `tr_test.csv` ile hiçbir mesaj paylaşılmaz.
- Veri **git'e girmez** (`data/external/`, `.gitignore` kapsamında); yalnızca
  proje üyeleri arasında doğrudan paylaşılır.

## 3. Temizlik ve gizlilik

Ham dışa aktarmalar (`data/raw/`) git'e girmez ve paylaşılmaz. Zor teste girmeden
önce her mesaj şu adımlardan geçti:

| Adım | Ne yapıldı | Neden |
|---|---|---|
| Kişisel veri maskeleme | İsim, telefon, IBAN, kart numarası, link `maskele.py` ile `[İSİM]`, `[LINK]` gibi etiketlere çevrildi | Gizlilik |
| Kart son haneleri | "7271 ile biten kart" gibi ifadeler maskelendi | Gizlilik |
| Uzun sayılar | 7+ haneli sayılar (takip no, Mersis, telefon) `0000000` yapıldı | Gizlilik, gürültü |
| Kısa kodlar | 6 haneli doğrulama kodları `000000` yapıldı | Gizlilik |
| `B###` sonekleri | Mesaj sonundaki `B001`, `B002` gibi kodlar silindi | Gönderici kimliğini sızdırır (bkz. aşağıda) |
| Dışa aktarma artıkları | `[Unreadable text]`, `[File: ...]` satırları silindi | Gerçek mesaj değil |

**Gönderici sızıntısı.** Telefon dışa aktarmaları mesajın sonuna gönderici kodu
ekliyor (`B002` vb.). Model bunu görürse mesajın içeriğini değil gönderen kodunu
öğrenir; bu yüzden metinden çıkarıldı. Gönderici adı yalnızca ayrı bir `gonderen`
sütununda tutulur ve **modele girdi olarak verilmez**. Sütun, ölçümde göndericiye
göre bölme (bkz. 5. bölüm) için kullanılır.

**Paylaşım.** Veri dosyaları proje üyeleri arasında doğrudan iletilir, repoya
konmaz. Zor veriyle çalışan notebook'ların çıktıları commit'ten önce temizlenir.

## 4. Etiketleme kuralları

Etiketler `docs/etiket-rehberi.md` karar ağacına göre verildi:

1. Para, bilgi ya da zararlı eylem için **aldatıyorsa** → `dolandırıcılık`
2. Gerçek bir ürün ya da kampanyayı tanıtıyorsa → `reklam`
3. Kişisel ya da işlemsel (kod, kargo, randevu, resmî bildirim) → `meşru`
4. Karar verilemiyorsa → `belirsiz` (eğitimde ve ölçümde kullanılmaz)

Zor teste özgü kararlar:

- **Kaynağı bilinen mesaj.** Mesaj gönüllünün kendi gelen kutusundan, kendi
  siparişi ya da hesabıyla ilgili geldiyse ve gönderici doğrulanabiliyorsa
  `meşru` sayıldı; link ya da "tıklayın" ifadesi içermesi bunu değiştirmez
  (ör. hastane memnuniyet anketi, "onay linki" içeren resmî bildirim).
- **Dolandırıcılığı anlatan resmî uyarılar** (ör. "para isteyenlere inanmayın")
  `meşru`; çünkü gönderen kurum ve amaç bilgilendirme.
- **Siyasi çağrı ve kurum tanıtımı** (ürün/kampanya yok): `belirsiz`.
  *(Öneri; ekibin onayından sonra rehbere eklenecek.)*
- **Bağış çağrıları** (IBAN ile): gerçek mi sahte mi doğrulanamadığı için ilk
  turda `belirsiz`; benzer kalıbın birden fazla göndericide görülmesi üzerine
  `dolandırıcılık` olarak güncellendi.
- Etiketler **gönderici ve şablon düzeyinde** verildi (aynı göndericinin aynı
  türdeki mesajları aynı etiketi alır), istisnalar mesaj düzeyinde işlendi
  (ör. aynı sigorta şirketinden bir kampanya mesajı `reklam`, bir bilgilendirme
  mesajı `belirsiz`).

**Sınırlama:** Tüm zor test etiketlerini tek kişi (Esra) verdi, ikinci bir
etiketleyici yoktur. Kör denetim planlanmaktadır.

## 5. Ölçüm yöntemi

**Metrik.** Ana metrik **spam F1**; `reklam` ve `dolandırıcılık` birlikte "spam"
(1), `meşru` 0 sayılır. Yanında iki sayı daha raporlanır: meşru mesajlara
**yanlış alarm** (meşru olup spam denen / tüm meşru) ve **yakalanan spam**
(spam olup spam denen / tüm spam).

**Model.** Tüm sonuçlar aynı SVM ile alındı: `Temizleyici` → TF-IDF (`char_wb`,
2–5 gram, `min_df=2`, `sublinear_tf`, `lowercase=False`) → `LinearSVC`
(`class_weight="balanced"`, `random_state=55`). Zor test sonuçlarına bakarak
**hiçbir ayar değiştirilmedi**.

**İki eğitim senaryosu.**

| | Eğitimde ne var |
|---|---|
| **Model A** | Yalnızca `tr_train` (651 mesaj) |
| **Model B** | `tr_train` + zor testin diğer göndericileri |

**Model B'nin ölçümü: leave-one-sender-out.** Her turda bir göndericinin
mesajları sınav olarak ayrılır, geri kalan göndericilerin etiketli mesajları
`tr_train`'e eklenip model sıfırdan eğitilir, ayrılan göndericinin mesajları
tahmin edilir. Tüm turların tahminleri toplanıp metrik hesaplanır. Böylece model,
test edilen göndericiyi eğitimde hiç görmez.

Rastgele k-fold yerine göndericiye göre bölme seçildi, çünkü aynı göndericinin
mesajları birbirine çok benzer (ör. aynı kargo firmasının şablonları) ve rastgele
bölme sızıntıya, yani gerçekte olmayan bir başarıya yol açardı.

**Kilitli test.** `tr_test.csv` (116 mesaj) bu çalışmada **hiç kullanılmadı**;
yalnızca projenin sonunda bir kez açılacak. Hocamıza gösterilen birkaç test
örneği olduğu için, bu sette hiçbir karar ya da ayar yapılmayacaktır.

## 6. Sonuçlar

Spam F1 (parantez içinde: meşru mesajlara yanlış alarm):

| Değerlendirme seti | Mesaj | Model A (yalnız `tr_train`) | Model B (+ diğer göndericiler) |
|---|---|---|---|
| **Kolay veri**, `tr_train` 5-fold CV | 651 | **0.97** | n/a |
| **Zor test, 1.kısım** | 84 | 0.65 (28/49) | **0.85** (8/49) |
| **Zor test, 2.kısım** | 49 | 0.90 (7/19) | **0.92** (3/19) |
| **Zor test, birleşik** | 133 | 0.75 (35/68) | **0.88** (11/68) |

Yakalanan spam, birleşik sette her iki modelde de **60/65** (değişmedi).

Okuma:

- Aynı model, kolay sınavda 0.97, gerçek kurumsal mesajlarda 0.75'e düşüyor;
  hocamızın eleştirisi doğrulandı.
- Zor testte yanlış alarm yarıdan fazlası (35/68) meşru kurumsal mesajlardan
  geliyor; model bu mesajları "spam" sanıyor.
- Gerçek kurumsal mesajlar eğitime girince, modelin **hiç görmediği
  göndericilerde** yanlış alarm 35/68 → 11/68'e düştü, spam yakalama aynı kaldı.
- İyileşme 1.kısım'nın setinde büyük (0.65 → 0.85), 2.kısım'in setinde küçük
  (0.90 → 0.92). 2.kısım'in setinin çoğu reklam; reklamı model zaten iyi tanıyor
  ve meşru örnek sayısı az (19).
- Gönüllü kutularındaki işlemsel mesajlar (doğrulama kodu, kargo takip,
  randevu) Model A ile de büyük ölçüde doğru sınıflandı (11 meşrudan 1'i yanlış).

*Not: Zor test için SVM yeniden kurulduğundan, CV'deki ayarlı sürümle küçük
farklar (≈0.02) olabilir.*

## 7. Hangi türlerde yanılıyor

Model A'nın (yalnız `tr_train`) meşru kurumsal mesajlara verdiği yanlış alarmlar
göndericiye göre sayıldığında belirli türlerde toplanıyor (gönderici başına en
çok 5 mesaj tutulduğu için sayılar küçüktür):

| Tür | Yanlış alarm / mesaj |
|---|---|
| Kargo ve sipariş bildirimi | 11 / 19 |
| Operatör ve abonelik bildirimi | 7 / 8 |
| Resmî uyarı (afet, İçişleri) | 4 / 5 |
| Sigorta bildirimi | 2 / 2 |

Doğrulama kodu, randevu hatırlatma ve tek seferlik kargo "teslim edildi"
mesajları gibi işlemsel türlerde Model A zaten büyük ölçüde doğruydu.

**Bağımsız doğrulama.** XLM-R'ın `tr_train` üzerindeki CV hatalarını
inceleyen ekip arkadaşımızın bulguları aynı yönde: 25 hatanın yaklaşık 20'si
kurumsal meşru mesaj (fatura hatırlatma, banka bildirimi, uçuş rezervasyonu)
ve model bunlara %98 güvenle "spam" diyor. Fold 2'nin her modelde zor çıkması,
fatura şablonlarının bu fold'da toplanmasıyla uyumlu.

**Olası neden (hipotez, kanıtlanmadı).** `tr_train`'deki meşru mesajların
yaklaşık %90'ı kişisel sohbet ve yalnızca ~%7'si kurumsal bildirim; bu mesajlar
ayrıca daha eski ve kısmen ASCII/argo üslubunda. Model "resmî ve bildirim dili =
spam" öğrenmiş olabilir.

**Ters yönde risk.** Aynı incelemede banka taklidi bir dolandırıcılık mesajı
("şifre bloke") kaçan bir hata olarak göründü. Modele kurumsal dili kabul
ettirirken bu tür taklit mesajlar meşru sayılabilir; bu yüzden sentetik veri
hem kurumsal meşru (hard negative) hem kurum taklidi dolandırıcılık (hard
positive) örnekleri içermelidir.

**Not:** Bu analiz zor test setleri üzerinde yapıldığından, bu setler tanı
amaçlı kullanıldı; iyileştirmeyi ölçmek için ayrı, hiç görülmemiş mesajlar
gerekir (bkz. 8. bölüm).

## 8. Sınırlamalar ve sıradaki adımlar

**Sınırlamalar**

- **Küçük veri.** 133 etiketli mesaj, yaklaşık 60 gönderici. Sonuçlar yön
  göstericidir, kesin değildir; küçük farklar (±0.02) gürültü sayılmalıdır.
- **Tek etiketleyici.** Zor test etiketlerini tek kişi verdi, ikinci etiketleyici
  yok.
- **Benzer göndericiler.** Leave-one-sender-out'ta ayrılan göndericiye benzeyen
  başka göndericiler eğitimde kalır (ör. iki kargo firması). Tamamen yeni bir
  tür (ör. farklı bir bankanın bildirimi) için iyileşme daha küçük olabilir.
- **Dolandırıcılık az.** Zor testte 11 dolandırıcılık mesajı var; bu türdeki
  sonuçlar güvenilir ölçüm sayılmaz.
- **Tanı amaçlı kullanım.** Zor test setlerine hata analizi için bakıldı. Bu
  yüzden "iyileştik" iddiası için ayrı bir taze set gerekir.
- **Tek model.** Bu bölümdeki sonuçlar yalnızca SVM içindir; BERTurk, XLM-R ve
  diğer modeller zor testte henüz ölçülmedi.

**Sıradaki adımlar**

1. BERTurk ve XLM-R'ı aynı zor testte ölçmek (göndericiye göre gruplu CV).
2. Sentetik veri üretmek: kurumsal meşru (hard negative) ve kurum taklidi
   dolandırıcılık (hard positive); sentetiğin ek faydasını aynı yöntemle ölçmek.
3. Etiket tartışmalarını `uyusmazlik_cozumleri.csv` üzerinden çözmek ve kör
   denetim yapmak.
4. Hiç görülmemiş taze mesajlarla iyileşmeyi doğrulamak.
5. Final modeli tüm gerçek veriyle eğitmek; `tr_test.csv` ile tek seferlik final
   test.
