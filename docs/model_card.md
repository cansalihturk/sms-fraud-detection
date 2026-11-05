# Model Card: SMS Dolandırıcılık Tespiti (SVM)

Nov 4, 2026 · @Esra

## Model ayrıntıları

Bu model, bir SMS'in **spam** (reklam veya dolandırıcılık) mi **meşru** mu olduğunu söyler; kararını açıklar ve spam ise türünü (reklam / dolandırıcılık) kural motoru belirler.

| Alan | Değer |
| --- | --- |
| Ad ve sürüm | `svm_v1` (nihai model, 4 Kasım 2026) |
| Model türü | Doğrusal SVM (`LinearSVC`, `class_weight="balanced"`) |
| Özellik | Harf TF-IDF (`char_wb`, 2–5 harflik parçalar, `min_df=2`, `sublinear_tf`) |
| Ön işleme | Kişisel bilgiler maskelenir (\[KOD\], \[TEL\], \[KART\], \[LINK\], \[İSİM\]); rakamlar 0'a çevrilir; küçük harfe çevrilir |
| Girdi | Tek bir SMS metni (Türkçe; İngilizce için eğitilmedi ve doğrulanmadı) |
| Çıktı | `spam` veya `meşru`, bir skor (`decision_function`), kelime bazlı açıklama, spam ise tür |
| Tür belirleme | Kural motoru (model "spam" dedikten sonra); modelin kendisi tür öğrenmedi; zor sette (64 spam) doğru tür: dolandırıcılık 9/10, reklam 54/54 |
| Açıklama | Her kelimeyi çıkarıp skorun nasıl değiştiğine bakar (kelime çıkarma yöntemi) |
| Yazılım | scikit-learn 1.6.1, Python 3.12; FastAPI ile servis, Streamlit arayüz, Docker |
| Geliştiriciler | Esra ve Salih (graduation projesi) |
| Tasarım kuralı | LLM hiçbir zaman karar vermez; kullanılırsa yalnızca açıklama cümlesi yazar |

Model seçimi: SVM, XLM-R'a karşı önceden yazılmış kurala göre seçildi. Dolandırıcılık yakalamada fark XLM-R'ın belirsizlik bandının içindeydi, yanlış alarmda SVM daha iyiydi.

## Kullanım amaçları ve kapsam dışı

Model, bir insanın kararını destekleyen bir **karar destek aracıdır**: SMS'e "şüpheli" etiketi koyar ve nedenini gösterir.

**Uygun kullanım**

- Kullanıcıya gelen SMS'i uyarmak (örneğin "spam: dolandırıcılık şüphesi" kartı)
- Eğitim ve demo amaçlı gösterim, SMS spam tespitinin sınırlarını anlamak

**Kapsam dışı (yapılmamalı)**

- Mesajı insan kontrolü olmadan otomatik silmek ya da engellemek
- Hukuki veya disiplin kararı için delil olarak kullanmak
- SMS dışı metinler (e-posta, sosyal medya, uzun yazılar) ve Türkçe dışındaki diller (İngilizce dahil: UCI üzerinde spam yakalama %22)
- Resim, bağlantı içeriği ya da gönderen numarası gibi metin dışı bilgiye dayanan kararlar (model yalnızca metne bakar)

## Eğitim verisi

`svm_v1`, dört kaynaktan toplam 935 mesajla eğitildi (936 mesaj, bir tekrar atıldı). Etiketler iki sınıf: spam (reklam ve dolandırıcılık) ve meşru.

| Kaynak | Mesaj | Açıklama |
| --- | --- | --- |
| tr\_train | 651 | 303 spam, 348 meşru; belirsiz işaretli 8 mesaj çıkarıldı |
| Sentetik v2 | 96 | 40 dolandırıcılık + 56 kurumsal meşru; Salih inceledi ve onayladı |
| Zor gerçek mesajlar | 131 | 67 meşru, 54 reklam, 10 dolandırıcılık; Esra ve Salih'in telefonlarından, gönderici başına en fazla 5 mesaj |
| Salih'in 58 mesajı | 58 | 36 meşru, 22 reklam; önce sınav oldu, sonra eğitime katıldı |

**Eğitimde olmayanlar:** tr\_test (kilitli, yalnızca sonda bir kez açılır), kural ile etiketlenen 1287 mesajlık havuz (modele kısayol öğretti), ham telefon dışa aktarımları.

**Etiketleme:** İki kişi mesajları ayrı ayrı etiketledi, ortak mesajları ikisi de etiketledi. Farkı olanlar konuşularak çözüldü ve kayıt altına alındı (uyusmazlik\_cozumleri.csv). Çok az dolandırıcılık mesajı olduğu için model dolandırıcılığı ayrı sınıf olarak öğrenmedi.

**Gizlilik:** Telefon mesajlarındaki kişisel bilgiler maskelendi. Ham dosyalar ve veri git deposuna girmez, yalnızca iki geliştirici arasında paylaşılır.

## Performans

Kolay veride spam F1 0.97 iken gerçek kurumsal mesajlardan oluşan zor sette aynı model 0.76'ya düştü; nihai eğitim tarifi bunu zor sette 0.923'e çıkardı. Başarı verinin zorluğuna bağlıdır, tek bir sayı modeli anlatmaz.

| Ölçüm | Spam F1 | Yanlış alarm | Yakalanan spam | Dolandırıcılık yakalama |
| --- | --- | --- | --- | --- |
| Kolay veri (tr\_train, 5 katlı çapraz doğrulama) | 0.974 | 11/348 | 298/303 | yok (7 örnek) |
| Zor set, yalnızca tr\_train ile eğitim (131 mesaj) | 0.76 |  |  | 8/10 |
| Zor set, nihai tarif E, gönderici bazlı LOSO (131 mesaj) | 0.923 | 6/67 | 60/64 | 10/10 |
| Yeni sınav: 97 görülmemiş meşru + 60 LLM (gemma) saldırısı |  | 7/97 (%7.2) | 35/60 (%58) |  |
| tr\_test (nihai model için bir bakış; aday modeller bu sette daha önce de ölçülmüştü) | 0.972 | 1/62 | 52/54 | ayrı ölçülmedi |
| Kaggle Türkçe SMS: bağımsız değil (765 mesajın 669'u verimizde), kullanılmadı | yok | yok | yok | yok |

**Notlar**

- Zor sette ±0.02 fark gürültü sayılır. Dolandırıcılıkta yalnızca 10 mesaj var, 9/10 ile 10/10 arası tek mesajdır; bu yüzden sonuç "kesin" değil "tutarlı eğilim"dir.
- Salih'in 58 mesajı önce sınav oldu (yanlış alarm 12/36'dan 7/36'ya indi), sonra eğitime katıldı; bu yüzden E tarifinin sonucu biraz iyimser olabilir.
- XLM-R ile karşılaştırma: zor sette F1 0.940 (E\_v2; SVM 0.923, yanlış alarm 7/67 ve 6/67); kilitli tr\_test'te XLM-R 0.953 (2/62, 3/54), SVM 0.972 (1/62, 2/54); yeni sınavda yanlış alarm %12.4, saldırı yakalama %66 (52–78). Önceden yazılmış kurala göre SVM seçildi.
- Saldırı döngüsünde (LLM ile saldırı üretme, kaçanları eğitime ekleme) daha az kaçan saldırı ile daha fazla yanlış alarm arasında bir denge gözlendi.

**Kelime bozma testi** (zor set, yalnızca sınav mesajları bozuldu): normal 60/64 spam ve 10/10 dolandırıcılık; aksansız 61/64 ve 10/10; leet 59/64 ve 9/10; harf tekrarı 59/64 ve 8/10. Meşru mesajlar da bozulunca yanlış alarm 6/67'den 18/67'ye (leet) ve 9/67'ye (tekrar) çıttı; gerçekte dolandırıcı yalnızca kendi mesajını bozar. Aynı testi kelime tabanlı SVM ile de yaptık: yakalama benzer kaldı (60–62/64 spam, 10/10 dolandırıcılık, yani harf tabanlının bozmaya daha dayanıklı olduğunu yakalamada göremedik), ama yanlış alarm daha fazlaydı: normal 11, aksansız 16, leet 15, tekrar 18 (harf tabanlı: 6, 6, 18, 9). Harf tabanlı modeli, aynı yakalamayla daha az yanlış alarm verdiği için seçtik.

**İngilizce dış test (UCI SMS Spam Collection, 5574 mesaj, 747 spam):** F1 0.344, kesinlik 0.852, duyarlılık 0.216; spam'in 747'sinden 161'ini yakaladı (586 kaçtı), yanlış alarm 28/4827. Model yalnızca Türkçe veriyle eğitildi; İngilizce için kullanılmamalı. Sonuç görüldükten sonra model ya da ayar değiştirilmedi.

## Bilinen hatalar, sınırlamalar ve etik notlar

Model en çok **meşru kurum bildirimlerini** spam sanarak ve **yeni, LLM ile üretilmiş dolandırıcılık mesajlarının** yaklaşık %42'sini (60'ın 25'i) kaçırarak yanılır.

**Yanlış alarm veren meşru mesaj türleri**

- Kargo ve sipariş takibi, kısa bildirimler
- Operatör ve abonelik mesajları, borç ve gecikme bildirimi
- Resmî uyarı (örneğin IMEI), güvenlik uyarısı, KVKK bilgilendirmesi
- Kurumun dolandırıcılık uyarısı: dolandırıcıyı anlattığı için ödül, hediye gibi kelimeler geçer; harf tabanlı model niyeti anlamaz

**Kaçırılan spam**

- Model eğitimde görmediği şablonları kaçırır (aynı şablondan iki reklam aynı katta kaldı)
- Kimlik avcı mesajının ("şifreniz bloke, \[LINK\]") sayısı az olduğu için ilk modelde kaçtı

**Sınırlamalar**

- Dolandırıcılıkta yalnızca 10 gerçek mesaj ölçüldü; model dolandırıcılığı ayrı sınıf olarak öğrenmedi
- Veriler birkaç kişinin telefonundan geliyor; operatör, ülke ve yaş çeşitliliği sınırlı; model yalnızca Türkçe veriyle eğitildi
- Sentetik veri insan yazımı değil; link ve marka oranları elle dengelendi
- Basit yazım bozmaları (aksansız, leet, harf tekrarı) ölçüldü ve yakalama 1–2 mesaj düştü; harf arasına boşluk, benzer görünümlü harf ve kelime sırası bozma ölçülmedi. Kural motoru, kurallar zor setin hataları görülerek genişletildiği için yeni kalıplarda düşebilir
- Yeni dolandırıcılık şablonları çıktıkça başarı düşer, izleme ve yeniden eğitim planı henüz kurulmadı

**Etik ve güvenlik**

- Mesajlar kişisel veri içerebilir; maskeleme kullanıldı, ham veri paylaşılmaz
- Yanlış alarm, önemli bir banka ya da kargo bildirimini kullanıcının gözden kaçırmasına yol açabilir; bu yüzden sistem mesajı engellemez, nedenini gösterir
- LLM karar vermez: aynı mesaja her seferinde aynı cevabı vermediği ve nedenini kanıtlayamadığı için yalnızca açıklama yazabilir
- Ayrıntılı risk tablosu ve NIST AI RMF eşlemesi: Risk Kaydı belgesi
