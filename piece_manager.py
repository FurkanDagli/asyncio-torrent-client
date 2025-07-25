import hashlib
import math
from collections import namedtuple

BLOCK_MISSING = 0
BLOCK_PENDING = 1
BLOCK_RETRIEVED = 2
Block = namedtuple('Block', ['piece', 'offset', 'length'])

class Piece:
    def __init__(self, index, blocks, piece_hash):
        self.index = index
        self.blocks = blocks
        self.piece_hash = piece_hash
        self._block_states = [BLOCK_MISSING] * len(blocks)
        self.data = bytearray(sum(b.length for b in blocks))

    def _get_block_index(self, block_offset):
        for i, block in enumerate(self.blocks):
            if block.offset == block_offset:
                return i
        return -1

    def all_blocks_retrieved(self):
        return all(state == BLOCK_RETRIEVED for state in self._block_states)

    def get_next_missing_block(self):
        for i, state in enumerate(self._block_states):
            if state == BLOCK_MISSING:
                self._block_states[i] = BLOCK_PENDING
                return self.blocks[i]
        return None

    def block_received(self, offset, data):
        block_index = self._get_block_index(offset)
        if block_index != -1 and self._block_states[block_index] == BLOCK_PENDING:
            self._block_states[block_index] = BLOCK_RETRIEVED
            self.data[offset:offset + len(data)] = data

    def is_hash_correct(self):
        return hashlib.sha1(self.data).digest() == self.piece_hash

class PieceManager:
    def __init__(self, torrent_data):
        self.torrent_data = torrent_data
        self.pieces = self._initialize_pieces()
        self.output_file = open(self.torrent_data[b'info'][b'name'].decode('utf-8'), "wb")

    def _initialize_pieces(self):
        info = self.torrent_data[b'info']
        piece_length = info[b'piece length']
        piece_hashes = info[b'pieces']
        
        # Tek ve çok dosyalı torrent'ler için toplam boyutu hesapla
        total_length = 0
        if b'length' in info:
            total_length = info[b'length']
        elif b'files' in info:
            total_length = sum(file[b'length'] for file in info[b'files'])
        
        num_pieces = math.ceil(total_length / piece_length)
        pieces = []
        for i in range(num_pieces):
            blocks = []
            current_piece_length = piece_length if i < num_pieces - 1 else total_length % piece_length or piece_length
            block_size = 2**14
            num_blocks = math.ceil(current_piece_length / block_size)
            for j in range(num_blocks):
                current_block_length = block_size if j < num_blocks - 1 else current_piece_length % block_size or block_size
                blocks.append(Block(i, j * block_size, current_block_length))
            start = i * 20
            piece_hash = piece_hashes[start:start + 20]
            pieces.append(Piece(i, blocks, piece_hash))
        return pieces

    def get_next_request(self):
        for piece in self.pieces:
            if not piece.all_blocks_retrieved():
                block = piece.get_next_missing_block()
                if block:
                    return block
        return None

    def block_received(self, piece_index, offset, data):
        piece = self.pieces[piece_index]
        piece.block_received(offset, data)
        print(f"Parça {piece_index}, Blok (offset {offset}) alındı.")
        if piece.all_blocks_retrieved():
            print(f"Parça {piece_index} için tüm bloklar tamamlandı. Hash kontrol ediliyor...")
            if piece.is_hash_correct():
                print(f"Parça {piece_index} hash DOĞRU. Diske yazılıyor...")
                self.write_piece_to_disk(piece)
            else:
                print(f"Parça {piece_index} hash YANLIŞ! Tekrar denenecek.")
                # TODO: Parçanın durumunu sıfırla

    def write_piece_to_disk(self, piece):
        offset = piece.index * self.torrent_data[b'info'][b'piece length']
        self.output_file.seek(offset)
        self.output_file.write(piece.data)

    def is_complete(self):
        return all(p.all_blocks_retrieved() and p.is_hash_correct() for p in self.pieces)
    
    def get_downloaded_percentage(self):
        retrieved_blocks = sum(p._block_states.count(BLOCK_RETRIEVED) for p in self.pieces)
        total_blocks = sum(len(p.blocks) for p in self.pieces)
        return (retrieved_blocks / total_blocks) * 100 if total_blocks > 0 else 0

    def close(self):
        self.output_file.close()