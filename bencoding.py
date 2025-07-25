import collections

class BDecoder:
    def __init__(self, data: bytes):
        if not isinstance(data, bytes):
            raise TypeError("Girdi byte formatında olmalı")
        self._data = data
        self._index = 0

    def decode(self):
        char = self._peek()
        if char is None:
            raise EOFError("Veri beklenmedik şekilde sonlandı")
        if char == b'i':
            self._index += 1
            return self._decode_int()
        elif char == b'l':
            self._index += 1
            return self._decode_list()
        elif char == b'd':
            self._index += 1
            return self._decode_dict()
        elif char.isdigit():
            return self._decode_string()
        else:
            raise TypeError(f"Geçersiz tip belirteci: {char} at index {self._index}")

    def _peek(self):
        if self._index + 1 > len(self._data):
            return None
        return self._data[self._index:self._index+1]

    def _read(self, length: int) -> bytes:
        if self._index + length > len(self._data):
            raise IndexError("Okuma sırasında veri sonuna ulaşıldı")
        res = self._data[self._index:self._index+length]
        self._index += length
        return res

    def _read_until(self, char: bytes) -> bytes:
        try:
            occurrence = self._data.index(char, self._index)
            res = self._data[self._index:occurrence]
            self._index = occurrence + 1
            return res
        except ValueError:
            raise TypeError(f"'{char}' karakteri bulunamadı")

    def _decode_int(self):
        return int(self._read_until(b'e'))

    def _decode_list(self):
        res = []
        while self._peek() != b'e':
            res.append(self.decode())
        self._index += 1
        return res

    def _decode_dict(self):
        res = collections.OrderedDict()
        while self._peek() != b'e':
            key = self._decode_string()
            value = self.decode()
            res[key] = value
        self._index += 1
        return res

    def _decode_string(self):
        length = int(self._read_until(b':'))
        return self._read(length)

class BEncoder:
    def __init__(self, data):
        self._data = data

    def encode(self) -> bytes:
        return self._encode_next(self._data)

    def _encode_next(self, data):
        if isinstance(data, int):
            return self._encode_int(data)
        elif isinstance(data, bytes):
            return self._encode_bytes(data)
        elif isinstance(data, str):
            return self._encode_bytes(data.encode('utf-8'))
        elif isinstance(data, list):
            return self._encode_list(data)
        elif isinstance(data, (dict, collections.OrderedDict)):
            return self._encode_dict(data)
        raise TypeError(f"Desteklenmeyen tip: {type(data)}")

    def _encode_int(self, value):
        return b'i' + str(value).encode('utf-8') + b'e'

    def _encode_bytes(self, value):
        return str(len(value)).encode('utf-8') + b':' + value

    def _encode_list(self, data):
        return b'l' + b''.join(self._encode_next(item) for item in data) + b'e'

    def _encode_dict(self, data):
        encoded_items = b''
        for key, value in data.items():
            key_bytes = key if isinstance(key, bytes) else key.encode('utf-8')
            encoded_items += self._encode_bytes(key_bytes)
            encoded_items += self._encode_next(value)
        return b'd' + encoded_items + b'e'
