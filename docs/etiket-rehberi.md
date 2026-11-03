# Etiket Rehberi

SMS Dolandırıcılık Tespiti (TR + EN) · Sürüm 1 · Esra ve Salih

Bu rehber, her mesaja hangi etiketin verileceğini belirler. İkimiz de aynı kurala göre etiketlemezsek model etiket gürültüsünü öğrenir. Bir kural değişirse en alttaki **Değişiklik günlüğü**'ne tarihle yazılır.

## 1. Üç sınıf

| Etiket | Tanım |
|---|---|
| **dolandırıcılık** | Kullanıcıyı aldatarak para, kişisel bilgi (şifre, kart, TC, doğrulama kodu) ya da zararlı bir eylem (şüpheli linke tıklama, sahte numarayı arama, uygulama kurma) elde etmeye çalışan mesaj. |
| **reklam** | Gerçek bir ürün, hizmet ya da kampanyayı tanıtan toplu mesaj. Kullanıcıyı kandırmaya çalışmaz, sadece satış ya da tanıtım yapar. |
| **meşru** | Kişisel yazışma ya da işlemsel/bilgilendirme mesajı: kullanıcının kendi talep ettiği doğrulama kodu, kargo takibi, randevu hatırlatması, sohbet. |

## 2. Karar ağacı (sırayla sor)

1. **Mesaj aldatıcı bir şekilde para, bilgi ya da zararlı bir eylem istiyor mu?** Örnekler: sahte ödül, sahte borç, "hesabınız bloke", sahte kargo ücreti, kurum taklidi, kullanıcıdan şifre ya da kod isteme. **Evet → dolandırıcılık.**
2. **Gerçek bir ürün, kampanya ya da hizmeti tanıtıyor mu ve kullanıcıdan gizli/aldatıcı bir şey istemiyor mu?** **Evet → reklam.**
3. **Kişisel ya da işlemsel bir mesaj mı (kod, takip, randevu, sohbet)?** **Evet → meşru.**
4. **Hâlâ karar veremiyorsan → "belirsiz" işaretle** ve nota nedenini yaz (bölüm 5).

Mesajın gerçekten banka, kargo ya da devletten gelip gelmediğini doğrulayamayız. Etiketi **mesajın içeriğindeki işaretlere** göre veriyoruz: aciliyet, tehdit, bilgi/ödeme talebi, şüpheli link, kurum taklidi.

## 3. Örnekler

Aşağıdakiler etiketleme örnekleri olarak uydurulmuştur. Telefon, link ve numaralar maskelidir.

### Türkçe

| Mesaj | Etiket | Neden |
|---|---|---|
| Hesabınız güvenlik nedeniyle bloke edildi. Açmak için hemen giriş yapın: [LINK] | dolandırıcılık | Aciliyet, hesap tehdidi, link ile giriş talebi |
| Kargonuz teslim edilemedi. 12,50 TL işlem ücretini ödeyin: [LINK] | dolandırıcılık | Sahte kargo ücreti |
| Tebrikler! 50.000 TL ödül kazandınız. Almak için [TEL] numarasını arayın. | dolandırıcılık | Sahte ödül, arama talebi |
| E-Devlet hesabınız askıya alındı. Doğrulama için TC kimlik no ve şifrenizi girin: [LINK] | dolandırıcılık | Kurum taklidi, şifre talebi |
| Yaz indirimi başladı! Tüm ürünlerde %40'a varan indirim, 31 Ağustos'a kadar mağazalarımızda. Ret için RED yazın. | reklam | Gerçek kampanya, aldatıcı talep yok |
| Akaryakıt alımında 100 TL'ye 10 TL puan kampanyası. Detaylar istasyonlarımızda. | reklam | Kampanya tanıtımı |
| Doğrulama kodunuz: [KOD]. Bu kodu kimseyle paylaşmayın. | meşru | Kullanıcının kendi talep ettiği kod |
| Siparişiniz kargoya verildi. Takip no: [NO]. | meşru | İşlemsel bilgilendirme |
| Yarın 14:00'teki randevunuzu hatırlatırız. | meşru | Randevu hatırlatması |
| Akşam geç kalacağım, yemeği bensiz başlayın. | meşru | Kişisel sohbet |

### İngilizce

| Mesaj | Etiket | Neden |
|---|---|---|
| You have won a £1000 prize! Call [TEL] now to claim. | dolandırıcılık | Sahte ödül, arama talebi |
| Your bank account is locked. Verify now: [LINK] | dolandırıcılık | Hesap tehdidi, link |
| Big weekend sale: 30% off all shoes. Reply STOP to opt out. | reklam | Gerçek kampanya |
| Your code is [KOD]. Do not share it. | meşru | Kullanıcının kendi kodu |
| Can you pick up milk on the way home? | meşru | Kişisel sohbet |

## 4. Zor durumlar

| Durum | Karar | Not |
|---|---|---|
| Banka kampanyası, link var, kullanıcıdan bilgi istemiyor | reklam | |
| "Hesabınız bloke, linke tıklayın" | dolandırıcılık | |
| "Kartınızla 500 TL harcama yapıldı." (eylem yok, sadece bilgi) | meşru | |
| Aynı mesajda "Siz yapmadıysanız şu numarayı arayın" | belirsiz | Numara bilinmiyorsa ve acele ettiriyorsa dolandırıcılığa kayar |
| Kısaltılmış link ile kampanya | reklam | Tek başına yetmez. Aciliyet ve ödül de varsa dolandırıcılık |
| Yasa dışı bahis ya da kaçak site tanıtımı | reklam | Türü "bahis" yaz |
| Gizli ücretli abonelik tuzağı | dolandırıcılık | Ödül/ücret aldatmacası varsa |
| Polis, savcı, kargo görevlisi taklidi | dolandırıcılık | |
| "Merhaba, nasılsın?" tarzı bilinmeyen numaradan mesaj | belirsiz | Tuzağın ilk adımı olabilir |
| Çok kısa ya da bağlamsız mesaj | belirsiz | |
| Veri setinde SMS'e benzemeyen metin (özlü söz, makale cümlesi) | meşru | `sms_degil` işaretle, aşağıya bak |

**SMS olmayan metinler:** Türkçe veri setinde bazı "meşru" satırlar gerçek SMS değil, başka kaynaktan gelmiş olabilir. Bunlara `sms_degil` yaz. Böylece model dolandırıcılığı değil "mesaj tarzı farklı mı" diye öğrenmesin, ve istersek bu satırları dışarıda tutabiliriz.

## 5. Belirsiz kuralı

- "Belirsiz" bir kaçış kapısı değildir. Önce karar ağacını bitir.
- Belirsizse `belirsiz = e` yaz ve **notta nedenini** belirt (örneğin "bilinmeyen numara, link yok, bağlam eksik").
- Belirsiz satırlar her hafta ikimiz birlikte gözden geçirir ve son etiketi birlikte veririz.
- Belirsiz satırları model eğitiminde kullanmayın, ayrı sayın ve raporda kaç tane olduğunu yazın.

## 6. Maskeleme etiketleri

Mesajı tabloya koymadan önce kişisel bilgileri sil:

| Etiket | Neyi değiştirir |
|---|---|
| `[TEL]` | Telefon numarası |
| `[LINK]` | URL, kısaltılmış link |
| `[İSİM]` | Kişi adı |
| `[TC]` | TC kimlik numarası |
| `[IBAN]` | IBAN ve hesap numarası |
| `[KART]` | Kart numarası |
| `[KOD]` | Doğrulama kodu |
| `[EPOSTA]` | E-posta adresi |
| `[ADRES]` | Açık adres |

Tutarları ve kampanya metnini **silme**, onlar ayırt edici işaretlerdir. Link maskelendiği için linkin türünü kaybetmemek istersen nota "kısaltılmış link" ya da "banka benzeri alan adı" yaz.

## 7. Etiketleme tablosu sütunları

| Sütun | Değerler |
|---|---|
| `id` | Sıra numarası |
| `mesaj` | Maskelenmiş metin |
| `dil` | `tr` / `en` |
| `kaynak` | `turkishsms` / `uci` / `resmi` / `gonullu` / `sentetik` |
| `etiket` | `dolandırıcılık` / `reklam` / `meşru` |
| `tur` | `banka` / `kargo` / `ödül` / `devlet` / `kredi` / `bahis` / `diğer` |
| `belirsiz` | `e` / `h` |
| `sms_degil` | `e` / `h` |
| `not` | Serbest not |
| `etiketleyen` | Esra / Salih |
| `ikinci_etiket` | Çapraz kontrolden gelen etiket |
| `son_etiket` | Uyuşmazlık çözüldükten sonraki nihai etiket |

**Sentetik mesajlar** `kaynak = sentetik` olarak işaretlenir ve **asla test setine girmez.**

## 8. Kalite kontrol

1. İlk 50 mesajı ikimiz birbirimizden bağımsız etiketleriz.
2. Uyuşmayan mesajları birlikte açar, nedenini konuşur ve rehberi netleştiririz.
3. Uyum oranını yazarız. Hedef yaklaşık %90. Altındaysa rehberdeki belirsiz kuralları netleştirip 50 mesajı yeniden dene.
4. İstersen daha sağlam bir ölçü olarak Cohen'in kappa değerini de hesapla:

```python
from sklearn.metrics import cohen_kappa_score
kappa = cohen_kappa_score(df["etiket"], df["ikinci_etiket"])
```

5. Rapora kaç mesajın iki kişi tarafından etiketlendiğini, uyum oranını ve kaç mesajın belirsiz kaldığını yaz. Bu, veri yönetişimi bölümünün kanıtı olur.

## 8. Netleştirilen kurallar (26 Ekim 2026, ilk 50 sonrası)

**Ücretli SMS hizmetleri ve yem.** Mesaj bir yem kullanıyorsa (cinsel ya da flört içerik, çekiliş, "kazandınız", arkadaş daveti) ve ücretli numaraya yönlendiriyorsa → **dolandırıcılık**, ücret yazsa bile. Yem yoksa, sade bir hizmet ya da abonelik bildirimiyse → **reklam**.

**Kişisel mesaj.** Arkadaş tonu varsa ("kanka", "abi") marka adı geçse bile → **meşru**.

**Gerçek kampanya.** Tanınan bir marka, şartları belli kampanya, hediye ya da puan içerse bile → **reklam**. "Ödül" kelimesi tek başına dolandırıcılık demek değildir; mesaj aldatıcı bir şey istiyor mu diye bak.

**`belirsiz` tanımı.** Rehber iki sınıf arasında kalıyorsa ve gerçekten emin değilsen `e`. "Biraz tereddüt ettim" `h`'dir. `belirsiz` satırında `etiket` boş bırakılmaz: en iyi tahmin yazılır.

**`tur` sütunu.** Mesajın konusunu gösterir, sınıftan bağımsızdır: ödül/hediye/puan geçiyorsa `ödül`; ayrıca banka, kredi, kargo, devlet, bahis, diğer. İki tür birden uyarsa sektör önce (banka, kredi, kargo, devlet), sonra ödül, sonra bahis, sonra diğer. Meşru satırlarda `tur` boş kalır. `tur` model girdisi olarak kullanılmaz, sadece analiz içindir.

**`belirsiz` ve `sms_degil`** hiç boş bırakılmaz: `h` ya da `e`.

**Elle maskeleme.** Otomatik script isim, adres ve boşluklu telefon numaralarını yakalamaz. Etiketlerken bunları kendin maskele: `[İSİM]`, `[ADRES]`, `[TEL]`. Mesajın geri kalanına dokunma.

**Liste değerleri** küçük harf ve virgülden sonra boşluksuz yazılır.

**Bilgilendirme mesajları.** Bir şey satmaya, abone etmeye ya da kampanyaya çekmeye çalışmayan, sadece bilgi veren, uyaran ya da bildirim yapan mesajlar (operatör/banka bildirimi, OTP şifresi, ekstre, kargo teslimi, servis aktif oldu bildirimi, dolandırıcılık uyarısı) → **meşru**. Bu satırlarda `tur` boş kalır.

**Gerçek marka çekilişi/kampanyası.** Tanınan bir markanın çekiliş ya da ödüllü kampanyası, şüpheli numara ya da kişisel bilgi isteği yoksa → **reklam** (dolandırıcılık değil).

**Etiket metne göre verilir.** Mesajın dışında bir araştırma (numarayı internette arama gibi) yapılmaz, çünkü model sadece metni görür.

**`banka` ve `kredi` farkı.** Asıl konu borç verme (ihtiyaç kredisi, anında kredi) → `kredi`. Bankanın kartı, puanı, havalesi, otomatik ödemesi ya da internet şubesi → `banka`. Kart sadece ek avantajsa (örneğin mağaza indirimi) ya da operatör kampanyasıysa → `diğer`.

**İlk 50 sonucu.** İki kişi bağımsız etiketledi: 3 sınıfta uyum %94, Cohen kappa 0.91, ikili uyum %98. Uyuşmazlıklar ücretli SMS ve kişisel mesaj sınırında çıktı, yukarıdaki kurallar bunlardan türetildi.

## Değişiklik günlüğü

| Tarih | Değişiklik | Kim |
|---|---|---|
| 2026-10-24 | İlk sürüm | |
| 2026-10-26 | Ücretli SMS yemi, kişisel mesaj, gerçek kampanya, belirsiz tanımı, tur ve elle maskeleme kuralları eklendi | Esra, Salih |
| 2026-10-27 | Bilgilendirme, marka çekilişi, metne göre etiketleme ve tur önceliği kuralları eklendi | Esra, Salih |

## Ek kural: Siyasi çağrı ve kurum tanıtımı (zor test sırasında eklendi)

Ürün ya da kampanya satmayan, kimseyi para/bilgi için aldatmayan, ama kişisel ya
da işlemsel de olmayan mesajlar **`belirsiz`** etiketlenir ve eğitimde/ölçümde
kullanılmaz. Örnekler:

- Siyasi/parti çağrısı (miting, aday çağrısı)
- Kurum ya da vakıf tanıtımı (kutlama, yıl dönümü, tanıtım videosu)
- Kamu programı duyurusu (ürün/hizmet satmayan, genel bilgilendirme)

*Durum: öneri. Salih ile onaylandıktan sonra bu not "öneri" olmaktan çıkar.*
