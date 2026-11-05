# Risk Kaydı (NIST AI RMF): SMS Dolandırıcılık Tespiti

Nov 4, 2026 · @Esra

## Amaç ve kapsam

Bu kayıt, SMS'in spam (reklam veya dolandırıcılık) mi meşru mu olduğunu bulan sistemin 12 bilinen riskini, ölçülmüş kanıtlarını ve önlemlerini NIST AI RMF işlevlerine (YÖNET, HARİTALA, ÖLÇ, İDARE ET) göre listeler.

**Sistem:** Nihai model SVM (harf TF-IDF, `svm_v1`, 935 mesajla eğitildi). Kural motoru yalnızca model "spam" dedikten sonra türü (reklam / dolandırıcılık) söyler. Açıklama, mesajdan kelime çıkarıp skor değişimine bakarak üretilir. Hiçbir LLM karar vermez; Ollama kullanılırsa yalnızca açıklama cümlesi yazar.

**Ölçek:** Olasılık ve etki Düşük / Orta / Yüksek olarak yazıldı. Bu, takımın değerlendirmesidir, ölçülmüş bir risk puanı değildir. Kanıt sütunundaki sayılar rapordaki deneylerden gelir.

## Risk tablosu

En yüksek iki risk, dolandırıcılığın kaçması (R1) ve elimizdeki 10 dolandırıcılık mesajıyla ölçümün güvenilmez olmasıdır (R3).

| # | Risk | NIST işlevi | Olasılık | Etki | Kanıt | Önlem | Durum |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | Dolandırıcılık mesajı kaçar (yeni ya da LLM ile üretilmiş saldırı) | MEASURE | Yüksek | Yüksek | SVM, 60 gemma saldırısının 35'ini yakaladı (%58); XLM-R %66 (52–78) | Saldırgan döngüsü (LLM ile üretilen saldırılar) düzenli tekrarlanır, kaçanlar eğitime eklenir | Açık, ölçüldü |
| R2 | Meşru mesaja "spam" denir (kurum bildirimi, kargo, fatura) | MEASURE | Orta | Orta | Yeni 97 gerçek meşru mesajda 7 yanlış alarm (%7.2); zor sette LOSO ile 6/67 | Gerçek kurumsal mesajlar eğitime katıldı (yanlış alarm 41/67'den 6/67'ye); kararın nedeni arayüzde gösterilir | Kısmen azaldı |
| R3 | Dolandırıcılık için ölçüm güvenilmez: çok az örnek | MEASURE | Yüksek | Yüksek | Zor sette 10 dolandırıcılık mesajı; 9/10 ile 10/10 arası tek mesaj; tr\_train'de 7 | Sonuç "kesin" değil "tutarlı eğilim" diye yazılır; sentetik dolandırıcılık eklendi (5/10'dan 9/10'a) | Açık |
| R4 | Model kolay işaretlere takılır (link, marka, "RET yaz") | MAP | Orta | Yüksek | Havuz deneyinde yanlış alarm 39'dan 2'ye indi ama dolandırıcılık yakalama 9/10'dan 2/10'a düştü; sebep etiketleme kuralıydı | Havuz eğitimden çıkarıldı; sentetik veride link ve marka oranları iki sınıfta dengelendi | Kapatıldı |
| R5 | Kişisel bilgi sızıntısı (telefondan alınan gerçek mesajlar) | GOVERN | Düşük | Yüksek | Telefon dışa aktarımları yalnızca data/raw'da | Mesajlar maskelenir (\[TEL\], \[KOD\], \[KART\], \[LINK\], \[İSİM\]); data/, models/ ve ham havuz git'e girmez, paylaşılmaz | Uygulandı |
| R6 | Etiket belirsizliği (hizmet bildirimi mi reklam mı, dolandırıcılık uyarısı meşru mu) | MAP | Orta | Orta | 8 belirsiz mesaj eğitimden çıkarıldı; kurum uyarıları spam sayıldı | İki kişi bağımsız etiketledi; uyuşmazlıklar uyusmazlik\_cozumleri.csv'den gelir; kural Model Card'a yazılır | Kısmen açık |
| R7 | Başarı sayısı iyimser çıkar | MEASURE | Orta | Orta | 58 mesaja bakılıp eğitime katıldı; gönderici örtüşmesi olabilir; ±0.02 gürültü | tr\_test'e nihai model için bir bakış yapıldı (F1 0.972, yanlış alarm 1/62, kaçan spam 2/54; aday modeller bu sette daha önce de ölçülmüştü); LOSO (gönderici bazlı) ölçüm; önce test sonra eğitim notu raporda | Yönetiliyor |
| R8 | Yeni dolandırıcılık şablonları (veri kayması) | MANAGE | Yüksek | Yüksek | Model sadece eğitimdeki şablonları bilir; kolay veri 0.97, zor veri 0.76 gibi düşüyor | Kayıp izleme (Evidently) ve periyodik yeniden eğitim planlandı | Açık, yapılmadı |
| R9 | Yazım bozma ile kaçırma (ş1fre, d0ğrula) | MEASURE | Orta | Yüksek | Zor sette yalnızca sınav mesajları bozuldu: aksansız 61/64, leet 59/64, harf tekrarı 59/64 spam yakalandı (normal 60/64); dolandırıcılık 10/10, 9/10, 8/10. Meşru mesajlar da bozulunca yanlış alarm 6'dan 18'e (leet) ve 9'a (tekrar) çıktı. Kelime tabanlı SVM yakalamayı aynı korudu (60–62/64) ama yanlış alarm daha yüksekti (normal 11, aksansız 16, leet 15, tekrar 18) | Bozuk yazımı eğitime eklemek denenebilir; harf arasına boşluk, benzer görünümlü harf (Kiril) ve kelime sırası bozma ölçülmedi | Kısmen ölçüldü |
| R10 | Kapsam darlığı: az kişi, az operatör, Türkçe ve İngilizce | MAP | Orta | Orta | Veriler birkaç kişinin telefonundan; zor set 131, 58 mesaj; İngilizce UCI testinde spam yakalama 161/747 (%22), F1 0.344 | Model yalnızca Türkçe için doğrulanmıştır, Model Card'da kullanım sınırları açık yazıldı; İngilizce için ayrı eğitim gerekir | Kabul edildi |
| R11 | Tür ve açıklama yanıltır (kural motoru türü kaçırabilir, açıklama kelime bazlı) | MEASURE | Orta | Düşük | Tür, sadece model "spam" dedikten sonra kurallarla bulunuyor; zor sette (64 spam) dolandırıcılık türü 4/10'dan 9/10'a çıktı, reklam 54/54; kurallar bu mesajlar görülerek genişletildi, sayı iyimser | LLM karar vermez, sadece açıklar; açıklama "modelin kelimeye baktığı skor" olarak sunulur | Kısmen azaldı |
| R12 | Sürüm uyuşmazlığı ile model farklı çalışır | MANAGE | Düşük | Orta | Model scikit-learn 1.6.1 ile kaydedildi, bir bilgisayarda 1.9.1 uyarı verdi | Docker'da scikit-learn==1.6.1 sabitlendi; CI her değişiklikte test ve imaj derlemesi yapar | Kapatıldı |

## NIST AI RMF eşlemesi

Dört işlevde de somut bir şey yaptık; en zayıf olan MANAGE, çünkü izleme ve yeniden eğitim henüz kurulmadı.

| İşlev | Ne yaptık | Henüz yok |
| --- | --- | --- |
| GOVERN (yönet) | Tek tasarım kuralı: LLM karar vermez, sadece açıklar. Veri kuralları: ham veri ve modeller git'e girmez, ham havuz paylaşılmaz. Değişiklikler PR ile girer, Salih merge eder, CI test ve Docker derlemesi yapar. Ölçütler sonuçtan önce yazıldı (model seçim kuralı) | Model Card'ın kendisi |
| MAP (haritala) | Amaç ve sınırlar belli: spam / meşru, türü ayrıca kural motoru söyler. Veri kaynakları, etiket sözlüğü ve iki kişinin bağımsız etiketlemesi belgelendi. Bilinen hata türleri listelendi (kargo, operatör, resmî uyarı, sigorta bildirimi) | Etkilenen kullanıcılar ve yanlış karar maliyeti için kısa not (Model Card'a) |
| MEASURE (ölç) | Kolay veri (0.97) yanında zor gerçek mesaj seti; gönderici bazlı LOSO; spam F1, yanlış alarm ve dolandırıcılık yakalama ayrı raporlandı. LLM saldırgan döngüsü ve 97 yeni meşru mesajla sınav. tr\_test kilitli | tr\_test tek bakış ve Kaggle dış test (ayrıca kelime bozma testi) |
| MANAGE (idare et) | Risk önlemleri tabloda; sürüm sabitleme ve CI uygulandı; sistem karar destek olarak sunulur, mesaj engellemez, nedenini gösterir | Veri kayması izleme (Evidently) ve yeniden eğitim takvimi |

## Kalan riskler ve yapılacaklar

Bu kayıttaki 12 riskten 3'ü kapandı (R4, R5, R12), 9'u açık ya da yönetiliyor. Bu sayım, durum sütunundaki etiketlere göre ve takımın kendi değerlendirmesidir.

- [ ] tr\_test'e nihai SVM ile tek bakış yapıldı: F1 0.972, yanlış alarm 1/62, kaçan spam 2/54
- [ ] Kaggle dış test sonucunu R10 satırına yaz
- [ ] Kelime bozma testi yapıldı (R9): normal 60/64 ve 10/10; leet 59/64 ve 9/10; harf tekrarı 59/64 ve 8/10
- [ ] Model Card: bilinen hata türleri (R2, R6), kullanım sınırları (R10), "karar destek, engelleme değil" notu
- [ ] Kayıp izleme ve yeniden eğitim planı (R8): en az bir cümleyle belirt, yapılmadığını saklıma
- [ ] Kural motoru tür doğruluğu ölçüldü (R11): zor sette dolandırıcılık 9/10, reklam 54/54; tr\_test sonrası tekrar bak
- [ ] Salih'in onayı: R1 ve R3 etki/olasılık değerlendirmesi
