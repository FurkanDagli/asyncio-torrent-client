import asyncio
from piece_manager import PieceManager
from tracker import Tracker
from peer import PeerConnection
import socket
import struct

MAX_PEER_CONNECTIONS = 20 # Aynı anda en fazla kaç peer'e bağlı kalacağımız

class TorrentClient:
    def __init__(self, torrent_data):
        self.tracker = Tracker(torrent_data)
        self.piece_manager = PieceManager(torrent_data)
        self.active_peers = []
        self.tasks = []

    async def start(self):
        """İstemciyi başlatır ve indirme tamamlanana kadar çalıştırır."""
        
        # 1. Peer'leri al
        peers_raw = await self.tracker.get_peers()
        if not peers_raw:
            print("Hiç peer bulunamadı. Program sonlandırılıyor.")
            return

        print(f"--- {len(peers_raw)} Adet Peer Alındı. Bağlantılar kuruluyor... ---")

        # 2. Peer'lere bağlanmak için görevler oluştur
        for ip_bytes, port_bytes in peers_raw:
            peer_ip = socket.inet_ntoa(ip_bytes)
            peer_port = struct.unpack('>H', port_bytes)[0]
            
            if not peer_ip or peer_port == 0: continue

            peer_conn = PeerConnection(
                ip=peer_ip, port=peer_port,
                info_hash=self.tracker.info_hash,
                peer_id=self.tracker.peer_id,
                piece_manager=self.piece_manager
            )
            # Her bir bağlantı denemesini bir görev olarak başlatıyoruz
            self.tasks.append(asyncio.create_task(peer_conn.connect()))
            
            # Aynı anda çok fazla deneme yapmamak için bir sınır koyalım
            if len(self.tasks) >= MAX_PEER_CONNECTIONS:
                break
        
        # 3. İndirme tamamlanana kadar bekle
        while not self.piece_manager.is_complete():
            await asyncio.sleep(5) # Her 5 saniyede bir durumu kontrol et
            print(f"İndirme Durumu: {self.piece_manager.get_downloaded_percentage():.2f}%")
        
        print("İndirme Tamamlandı! Tüm görevler iptal ediliyor.")
        
        # 4. İndirme bitince tüm açık bağlantıları kapat
        for task in self.tasks:
            task.cancel()
        
        self.piece_manager.close()

# PieceManager'a küçük bir ekleme yapalım:
def get_downloaded_percentage(self):
    retrieved_blocks = sum(p._block_states.count(2) for p in self.pieces)
    total_blocks = sum(len(p.blocks) for p in self.pieces)
    return (retrieved_blocks / total_blocks) * 100 if total_blocks > 0 else 0

PieceManager.get_downloaded_percentage = get_downloaded_percentage
