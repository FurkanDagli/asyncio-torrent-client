import asyncio
import struct
from messages import Message, Bitfield, Interested, Unchoke, Choke, Have, Request, Piece, NotInterested
from piece_manager import PieceManager

class PeerConnection:
    def __init__(self, ip: str, port: int, info_hash: bytes, peer_id: bytes, piece_manager: PieceManager):
        self.ip = ip
        self.port = port
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.piece_manager = piece_manager
        self.reader = None
        self.writer = None
        self.peer_is_choking = True
        self.peer_is_interested = False
        self.am_choking = True
        self.am_interested = False

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=10
            )
            print(f"Peer {self.ip}:{self.port} ile bağlantı kuruldu.")
            handshake_success = await self._perform_handshake()
            if not handshake_success:
                self.disconnect()
                return
            await self._message_loop()
        except Exception as e:
            # print(f"Peer {self.ip}:{self.port} ile bağlantı kurulamadı: {e}")
            self.disconnect()

    async def _perform_handshake(self) -> bool:
        handshake_msg = struct.pack('>B19s8x20s20s', 19, b'BitTorrent protocol', self.info_hash, self.peer_id)
        self.writer.write(handshake_msg)
        await self.writer.drain()
        try:
            response = await asyncio.wait_for(self.reader.readexactly(68), timeout=10)
            response_hash = struct.unpack('>B19s8x20s20s', response)[3]
            if self.info_hash == response_hash:
                print("Handshake başarılı!")
                return True
            else:
                # print("Handshake başarısız. Info hash eşleşmedi.")
                return False
        except Exception:
            # print(f"Handshake sırasında hata.")
            return False

    async def _message_loop(self):
        await self._send_message(Interested())
        self.am_interested = True
        while True:
            try:
                length_prefix = await asyncio.wait_for(self.reader.readexactly(4), timeout=125)
                msg_length = struct.unpack('>I', length_prefix)[0]
                if msg_length == 0:
                    continue
                msg_body = await asyncio.wait_for(self.reader.readexactly(msg_length), timeout=125)
                message_id = msg_body[0]
                payload = msg_body[1:]
                await self._handle_message(message_id, payload)
            except Exception:
                self.disconnect()
                break

    async def _handle_message(self, message_id: int, payload: bytes):
        if message_id == Choke.message_id: self.peer_is_choking = True
        elif message_id == Unchoke.message_id:
            self.peer_is_choking = False
            await self._request_piece()
        elif message_id == Have.message_id:
            pass # TODO
        elif message_id == Bitfield.message_id:
            pass # TODO
        elif message_id == Piece.message_id:
            piece_message = Piece.decode(payload)
            self.piece_manager.block_received(
                piece_message.piece_index, 
                piece_message.block_offset, 
                piece_message.data
            )
            await self._request_piece()

    async def _request_piece(self):
        if self.peer_is_choking:
            return
        block = self.piece_manager.get_next_request()
        if block:
            request_message = Request(
                piece_index=block.piece,
                block_offset=block.offset,
                block_length=block.length
            )
            await self._send_message(request_message)

    async def _send_message(self, message: Message):
        self.writer.write(message.encode())
        await self.writer.drain()

    def disconnect(self):
        if self.writer and not self.writer.is_closing():
            self.writer.close()