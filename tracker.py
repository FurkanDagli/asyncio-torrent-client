import asyncio
import hashlib
import random
import secrets
from urllib.parse import urlencode, urlparse
import socket
import struct

import aiohttp
from bencoding import BDecoder, BEncoder

class UDPTrackerProtocol(asyncio.DatagramProtocol):
    def __init__(self, future: asyncio.Future):
        self.future = future
        self.transport = None
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, data, addr):
        if not self.future.done(): self.future.set_result(data)
        self.transport.close()
    def error_received(self, exc):
        if not self.future.done(): self.future.set_exception(exc)
        self.transport.close()
    def connection_lost(self, exc):
        if not self.future.done(): self.future.set_exception(exc or ConnectionError("UDP Bağlantısı koptu"))

class Tracker:
    def __init__(self, torrent_data: dict):
        self.torrent_data = torrent_data
        self.peer_id = self._generate_peer_id()
        self.info_hash = self._generate_info_hash()
        self.total_length = self._calculate_total_length()

    def _generate_peer_id(self) -> bytes:
        return b'-PC0001-' + bytes(''.join(str(random.randint(0, 9)) for _ in range(12)), 'utf-8')

    def _generate_info_hash(self) -> bytes:
        info_bencoded = BEncoder(self.torrent_data[b'info']).encode()
        return hashlib.sha1(info_bencoded).digest()

    def _calculate_total_length(self) -> int:
        info = self.torrent_data[b'info']
        if b'length' in info: return info[b'length']
        elif b'files' in info: return sum(file[b'length'] for file in info[b'files'])
        raise ValueError("Torrent 'info' sözlüğünde 'length' veya 'files' anahtarı bulunamadı.")

    async def get_peers(self) -> list:
        tracker_urls = []
        if b'announce' in self.torrent_data: tracker_urls.append(self.torrent_data[b'announce'].decode('utf-8'))
        if b'announce-list' in self.torrent_data:
            for tier in self.torrent_data[b'announce-list']:
                for url_bytes in tier:
                    url = url_bytes.decode('utf-8')
                    if url not in tracker_urls: tracker_urls.append(url)
        for announce_url in tracker_urls:
            try:
                print(f"Tracker'a bağlanılıyor: {announce_url}")
                if announce_url.startswith('http'): peers = await self._request_peers_from_http_tracker(announce_url)
                elif announce_url.startswith('udp'): peers = await self._request_peers_from_udp_tracker(announce_url)
                else:
                    print(f"Desteklenmeyen tracker protokolü: {announce_url}"); continue
                if peers:
                    print(f"Başarılı! {announce_url} adresinden {len(peers)} peer alındı."); return peers
            except Exception as e: print(f"Tracker {announce_url} ile bağlantı kurulamadı: {e}")
        return []

    async def _request_peers_from_http_tracker(self, announce_url: str) -> list:
        params = {'info_hash': self.info_hash, 'peer_id': self.peer_id, 'port': 6881, 'uploaded': 0, 'downloaded': 0, 'left': self.total_length, 'compact': 1}
        url = announce_url + '?' + urlencode(params)
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200: raise ConnectionError(f"Tracker'dan hata kodu alındı: {response.status}")
                tracker_response_bytes = await response.read()
                tracker_data = BDecoder(tracker_response_bytes).decode()
                peers_raw = tracker_data.get(b'peers', b''); peers = []
                if isinstance(peers_raw, bytes): peers = [(peers_raw[i:i+4], peers_raw[i+4:i+6]) for i in range(0, len(peers_raw), 6)]
                elif isinstance(peers_raw, list):
                    for p in peers_raw:
                        if p.get(b'ip') and p.get(b'port'): peers.append((socket.inet_aton(p[b'ip'].decode('utf-8')), struct.pack('>H', p[b'port'])))
                return peers
    
    async def _request_peers_from_udp_tracker(self, announce_url: str) -> list:
        parsed_url = urlparse(announce_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 6969
        loop = asyncio.get_running_loop()

        protocol_id = 0x41727101980; action = 0; transaction_id = secrets.randbits(32)
        connect_req_packet = struct.pack('>QII', protocol_id, action, transaction_id)
        future = loop.create_future()
        transport, _ = await loop.create_datagram_endpoint(lambda: UDPTrackerProtocol(future), remote_addr=(hostname, port))
        
        connection_id = 0
        try:
            transport.sendto(connect_req_packet)
            response_data = await asyncio.wait_for(future, timeout=10)
            resp_action, resp_tx_id, received_conn_id = struct.unpack('>IIQ', response_data)
            if resp_action != 0 or resp_tx_id != transaction_id: raise ConnectionError("UDP Tracker'dan geçersiz cevap alındı.")
            connection_id = received_conn_id
        finally:
            transport.close()
        
        action = 1; transaction_id = secrets.randbits(32)
        
        announce_req_packet = struct.pack('>QII20s20sQQQIIiH',
            connection_id, action, transaction_id,
            self.info_hash, self.peer_id,
            0, self.total_length, 0,
            0, 0, secrets.randbits(32), -1, 6881
        )

        future = loop.create_future()
        transport, _ = await loop.create_datagram_endpoint(lambda: UDPTrackerProtocol(future), remote_addr=(hostname, port))
        
        try:
            transport.sendto(announce_req_packet)
            response_data = await asyncio.wait_for(future, timeout=10)
            resp_action, resp_tx_id, _, _, _ = struct.unpack('>IIIII', response_data[:20])
            if resp_action != 1 or resp_tx_id != transaction_id:
                raise ConnectionError("UDP Tracker'dan geçersiz announce cevabı alındı.")
            
            peers_raw = response_data[20:]
            peers = [(peers_raw[i:i+4], peers_raw[i+4:i+6]) for i in range(0, len(peers_raw), 6)]
            return peers
        finally:
            transport.close()