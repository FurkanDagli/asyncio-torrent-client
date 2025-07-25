# Parçacık - Python ile Asenkron BitTorrent İstemcisi

![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Bu proje, bir staj çalışması kapsamında Python'un `asyncio` kütüphanesi kullanılarak sıfırdan geliştirilmiş temel bir BitTorrent istemcisidir. Projenin amacı, BitTorrent protokolünün çalışma prensiplerini, düşük seviye ağ programlamayı ve asenkron mimarileri pratik olarak öğrenmektir.

İstemci, `.torrent` dosyalarını okuyabilir, HTTP ve UDP tracker'lar ile iletişim kurabilir ve birden çok peer'e (eşe) eş zamanlı olarak bağlanarak veri indirme sürecini yönetebilir. Uygulama, ilerlemesini standart komut satırı çıktıları (`print`) aracılığıyla anlık olarak raporlar.

---

## 🚀 Özellikler

- **`.torrent` Dosya Desteği:** Bencoding formatında kodlanmış tek ve çok dosyalı torrent'leri okuyup ayrıştırabilir.
- **Çift Protokollü Tracker Desteği:**
    - **HTTP/HTTPS Tracker'lar:** `aiohttp` kullanılarak asenkron `announce` istekleri gönderir.
    - **UDP Tracker'lar:** `asyncio`'nun datagram soketleri kullanılarak BEP-15 spesifikasyonuna uygun "Connect" ve "Announce" işlemleri yapar.
- **Dayanıklı Tracker Yönetimi:** `announce-list` içindeki tüm tracker'ları dener ve çalışmayanları atlayarak çalışan ilk tracker'dan peer listesini alır.
- **Esnek Peer Listesi Ayrıştırma:** Hem "compact" (binary) hem de "dictionary" formatındaki peer listelerini anlayabilir.
- **Eş Zamanlı Peer Bağlantıları:** `asyncio.create_task` kullanılarak birden çok peer'e aynı anda bağlanmayı dener, bu da çalışan bir peer bulma şansını artırır.
- **Protokol Uyumlu Handshake:** Peer'ler ile standart 68 byte'lık "Handshake" mesajını gönderir ve gelen cevaptaki `info_hash` değerini doğrulayarak doğru "swarm"da olduğundan emin olur.
- **Parça ve Blok Yönetimi:** `PieceManager` sınıfı ile indirilecek dosyayı parçalara ve bloklara ayırır, indirilen blokları takip eder, parça tamamlandığında SHA-1 hash kontrolü ile veri bütünlüğünü doğrular ve dosyayı diske yazar.

---

## 🛠️ Kullanılan Teknolojiler

- **Dil:** Python 3.10+
- **Asenkron Programlama:** `asyncio`
- **HTTP İletişimi:** `aiohttp`
- **Binary Veri İşleme:** `struct`
- **Veri Yapıları ve Diğer:** `collections`, `secrets`, `hashlib`

---

## ⚙️ Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin.

**1. Repository'yi Klonlayın:**
```bash
git clone [https://github.com/KULLANICI_ADIN/parcacik.git](https://github.com/KULLANICI_ADIN/parcacik.git)
cd parcacik
```

**2. Sanal Ortamı Oluşturun ve Aktifleştirin:**
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

**3. Gerekli Kütüphaneleri Yükleyin:**
```bash
pip install -r requirements.txt
```

**4. İstemciyi Çalıştırın:**
   - İndirmek istediğiniz `.torrent` dosyasını proje klasörüne kopyalayın.
   - `main.py` dosyasını açın ve en üstteki `TORRENT_FILE` değişkenini kendi dosyanızın adıyla güncelleyin.
   - Aşağıdaki komut ile istemciyi başlatın:
   ```bash
   python main.py
   ```
   İlerleme durumu, terminal ekranına standart `print` çıktıları olarak yazdırılacaktır.

---

## 🏛️ Projenin Mimarisi

Proje, her biri kendi sorumluluğuna sahip modüler bir yapıda tasarlanmıştır:
- **`main.py`:** Uygulamanın ana giriş noktası. `TorrentClient` nesnesini oluşturur ve başlatır.
- **`client.py`:** Ana istemci sınıfını (`TorrentClient`) içerir. Tüm operasyonları (tracker'a bağlanma, peer'leri yönetme, indirme döngüsü) yönetir.
- **`tracker.py`:** HTTP ve UDP tracker'lar ile olan tüm iletişimi yönetir.
- **`peer.py`:** Tek bir peer ile olan TCP bağlantısını, Handshake'i ve mesajlaşma döngüsünü yönetir.
- **`piece_manager.py`:** Dosyanın parçalara ve bloklara bölünmesi, indirme durumunun takibi, hash doğrulaması ve diske yazma işlemlerinden sorumludur.
- **`messages.py`:** BitTorrent protokolündeki farklı mesaj tiplerini (`Choke`, `Unchoke`, `Interested`, `Request`, `Piece` vb.) temsil eden sınıfları içerir.
- **`bencoding.py`:** `.torrent` dosyalarını okumak ve yazmak için Bencoding formatı ayrıştırıcısını ve kodlayıcısını içerir.

---

## 🎓 Bu Projeden Öğrenilenler

Bu proje, teorik bilgileri pratiğe dökme konusunda son derece öğretici bir deneyim oldu. Başlıca kazanımlar:
- **Asenkron Programlama:** `async/await` yapısını, görev (`task`) yönetimini ve `asyncio`'nun düşük seviye soket ve datagram yeteneklerini kullanarak karmaşık bir G/Ç problemini çözme.
- **Ağ Protokolleri:** HTTP ve UDP gibi temel protokollerin ötesinde, BitTorrent gibi özel ve binary tabanlı bir protokolü spesifikasyonlarını okuyarak sıfırdan implemente etme.
- **Hata Ayıklama (Debugging):** Özellikle ağ ortamından kaynaklanan (`Firewall`, `Timeout` vb.) ve teşhisi zor olan sorunları sistematik bir şekilde analiz etme ve çözme.
- **Yazılım Mimarisi:** Karmaşık bir problemi, yönetilebilir ve modüler parçalara ayırarak temiz ve sürdürülebilir bir kod tabanı oluşturma.

---

## 🔮 Gelecekteki Geliştirmeler

Bu projenin mevcut temeli üzerine eklenebilecek birçok özellik bulunmaktadır:
- [ ] **"Seeding" (Yükleme) Desteği:** İndirme tamamlandıktan sonra dosyayı diğer peer'lere yükleme.
- [ ] **Akıllı Parça Seçimi:** "En Nadir Parça Önce" (Rarest Piece First) gibi stratejiler implemente ederek indirme verimliliğini artırma.
- [ ] **DHT ve Magnet Link Desteği:** Tracker'sız torrent'leri desteklemek için DHT protokolünü ekleme.
- [ ] **Gelişmiş Arayüz:** `rich` gibi kütüphanelerle modern bir komut satırı arayüzü veya `Tkinter`/`PyQt` ile grafiksel bir arayüz ekleme.