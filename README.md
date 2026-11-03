# GÜNDEM. – Her gün güncellenen dijital gazete (altyapı)

**Kısa cevap:** Bu paket, internet üzerinde yayımlandıktan sonra her gün yeni RSS haber özetleriyle otomatik güncellenmek üzere tasarlandı. Bir hesapta yayımlama işlemi yapılmadığı için şu anda çevrimiçi ve otomatik çalışan bir servis **değil**.

## Kurulum (GitHub Pages)

1. [GitHub](https://github.com/) üzerinden bir depo oluşturun. Örnek depo adı: `gundem-gazetesi`. Ücretsiz GitHub Pages planından yararlanmak için deponun genel (public) olması gerekebilir; herkese açık depoya özel kişisel bilgiler koymayın.
2. ZIP içindeki **tüm dosya ve klasörleri**, `.github/workflows/yayinla.yml` dahil, deponun `main` dalına yükleyin. GitHub web arayüzü gizli `.github` klasörünü tek seferde yüklemeyi desteklemezse bu dosyayı web arayüzünde **Add file → Create new file** ile aynı yola oluşturarak metnini kopyalayın veya Git ile yükleyin.
3. Depoda **Settings → Pages → Build and deployment → Source: GitHub Actions** seçin.
4. **Actions → GÜNDEM. — Günlük gazeteyi güncelle → Run workflow** ile ilk yayınlamayı başlatın. İş akışı başarılı olunca site adresi Pages bölümünde görünür. Adres genel olarak `https://KULLANICI.github.io/gundem-gazetesi/` olur; `KULLANICI` yer tutucudur.

Her gün saat **07.37 (Türkiye saati)** civarı GitHub Actions yeni bülten oluşturur, `edition.json` dosyasını günceller, ardından siteyi yayımlar. Uygulamanın ↻ düğmesi, o sırada **yayınlanmış olan** son baskıyı yükler; kendi başına RSS kaynaklarını çalıştırmaz.

## Neler çalışır?

- Türkiye, Dünya, Ekonomi, Teknoloji bölümlerinde günlük haber akışı
- Gazete düzeninde manşet, haber okuma, arama, kaydetme, gece modu ve yazı büyütme
- Kaynak ve yayın tarihi gösterimi, her haberi site içinde kısa özet olarak açma
- Önceki baskının otomatik olarak korunması: yeterince güncel haber alınamazsa yayın hatayla durur; mevcut sitedeki son baskı kalır
- RSS derleyici (`update_news.py`) ve günlük otomatik yayın akışı (`.github/workflows/yayinla.yml`)
- Tarayıcıda önceki yüklenen içeriği çevrimdışı okuma (önbellek desteği)

## Sınırlar (önemli)

- RSS, tam makale paylaşmaz. Otomatik sürümde yayımlanan metinler **kısa kaynak özetleridir**. Gerçek gazetecilik araştırması, tam metin yeniden yazımı veya kaynaklar arasında doğrulama yapıldığı iddia edilmez. Kaynağa bağlantı isteğe bağlı sunulur; kısa haberleri okumak için başka sayfaya geçmek gerekmez.
- Günlük güncelleme GitHub, haber yayınevleri ve RSS akışlarının erişilebilirliğine bağlıdır. GitHub zamanlanmış işler bazen gecikebilir veya atlanabilir; belirli saatte yüzde yüz garanti yoktur.
- GitHub genel depolarda 60 gün etkinlik olmaması halinde zamanlanmış işleri devre dışı bırakabilir. Akış her gün yeni baskıyı repoya kaydeder; yine de zaman zaman **Actions** bölümündeki çalışmayı kontrol etmek faydalıdır.
- Kaynakların başlıkları ve RSS önizlemeleri özet olarak gösterilir; telif hakkıyla korunan tam makaleler kopyalanmaz. Kaynakların kullanım koşullarını göz önünde bulundurun.
- İnternete yayımlamak için **kullanıcı tarafından GitHub hesabına yüklenmesi/bağlanması** gerekir. Bu paket kendi başına bir sunucu, alan adı veya bildirim sistemi oluşturmaz.

## İsteğe bağlı yerel deneme

Bilgisayarda:

```bash
python -m http.server 8000
```

Ardından `http://localhost:8000` adresini açabilirsiniz. İlk denemede örnek 3 Kasım 2026 baskısı görünür. Gerçek RSS haberlerini yerel ortamda çekmek için `python update_news.py` komutunu çalıştırın; `edition.json` yazılacaktır. Ağ erişimi yoksa üretim başarısız olur ve arşiv gösterilir.

Ağsız derleyici testi: `python update_news.py --demo` komutu **gerçek haber olmayan**, yalnızca testte kullanılan `edition.demo.json` dosyasını üretir; bunu yayımlamayın.

## Özelleştirme

- RSS adresleri ve kategori seçimi: `update_news.py` içindeki `FEEDS`, `KEYWORDS`
- Tasarım ve uygulama davranışı: `index.html`. Arşiv baskısı kaynak düzenini düzenlemek isterseniz `ornek_baski.json` ve `patch_index.py` kullanılabilir.
- Zaman: `.github/workflows/yayinla.yml` içinde `schedule` bölümü

Kaynaklar: BBC Türkçe, DW Türkçe, Anadolu Ajansı, TRT Haber, Euronews Türkçe, Bloomberg HT, Webtekno ve ShiftDelete.Net RSS akışları. Her akışın erişilebilirliği değişebilir.
