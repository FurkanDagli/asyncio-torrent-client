import asyncio
from bencoding import BDecoder
from client import TorrentClient

#Deneme dosyamın adı oyun.torrent şeklindeydi.İndirilecek dosya adına göre güncelle

TORRENT_FILE = 'oyun.torrent' 

async def main():
    try:
        with open(TORRENT_FILE, 'rb') as f:
            meta_info_bytes = f.read()
    except FileNotFoundError:
        print(f"HATA: {TORRENT_FILE} dosyası bulunamadı.")
        return

    torrent_data = BDecoder(meta_info_bytes).decode()
    client = TorrentClient(torrent_data)
    await client.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram kullanıcı tarafından sonlandırıldı.")
