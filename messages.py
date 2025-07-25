import struct

class Message:
    def encode(self) -> bytes:
        raise NotImplementedError
    @staticmethod
    def decode(data: bytes):
        raise NotImplementedError

class Choke(Message):
    message_id = 0
    def __repr__(self): return "Choke"

class Unchoke(Message):
    message_id = 1
    def __repr__(self): return "Unchoke"

class Interested(Message):
    message_id = 2
    def __repr__(self): return "Interested"

class NotInterested(Message):
    message_id = 3
    def __repr__(self): return "NotInterested"

class Have(Message):
    message_id = 4
    def __init__(self, piece_index: int):
        self.piece_index = piece_index
    def encode(self) -> bytes:
        return struct.pack('>IBI', 5, self.message_id, self.piece_index)
    def __repr__(self): return f"Have(piece_index={self.piece_index})"

class Bitfield(Message):
    message_id = 5
    def __init__(self, bitfield: bytes):
        self.bitfield = bitfield
    def __repr__(self): return "Bitfield"

class Request(Message):
    message_id = 6
    def __init__(self, piece_index, block_offset, block_length):
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length
    def encode(self) -> bytes:
        return struct.pack('>IBIII', 13, self.message_id, self.piece_index, self.block_offset, self.block_length)
    def __repr__(self): return f"Request(piece_index={self.piece_index}, offset={self.block_offset}, length={self.block_length})"

class Piece(Message):
    message_id = 7
    def __init__(self, piece_index, block_offset, data):
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.data = data
    @staticmethod
    def decode(payload: bytes):
        piece_index = struct.unpack('>I', payload[0:4])[0]
        block_offset = struct.unpack('>I', payload[4:8])[0]
        data = payload[8:]
        return Piece(piece_index, block_offset, data)
    def __repr__(self): return f"Piece(piece_index={self.piece_index}, offset={self.block_offset}, length={len(self.data)})"

class Cancel(Message):
    message_id = 8

for msg_class in [Choke, Unchoke, Interested, NotInterested]:
    msg_class.encode = lambda self: struct.pack('>IB', 1, self.message_id)