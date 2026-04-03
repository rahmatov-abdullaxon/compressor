class Writer:
    def __init__(self):
        self._buffer = bytearray()
        self._current_byte = 0
        self._bits_filled = 0
        self._total_bits = 0

    @property
    def total_bits(self): return self._total_bits

    def write_bit(self, bit):
        if bit not in (0, 1): raise ValueError("Bit values must be 0 or 1.")

        self._current_byte = (self._current_byte << 1) | bit
        self._bits_filled = self._bits_filled + 1
        self._total_bits = self._total_bits + 1

        if self._bits_filled == 8:
            self._buffer.append(self._current_byte)
            self._current_byte = 0
            self._bits_filled = 0

    def write_bits(self, value, bit_count):
        if bit_count < 0: raise ValueError("bit_count must not negative.")
        if bit_count == 0: return
        if value < 0 or value >= (1 << bit_count): raise ValueError("value does not fit within bit_count bits.")
        for shift in range(bit_count - 1, -1, -1): self.write_bit((value >> shift) & 1)

    def bytes(self):
        buffer = bytearray(self._buffer)
        if self._bits_filled: buffer.append(self._current_byte << (8 - self._bits_filled))
        return bytes(buffer)

class Reader:
    def __init__(self, data):
        self._data = data
        self._byte_index = 0
        self._bit_index = 0

    def read_bit(self):
        if self._byte_index >= len(self._data): raise EOFError("Unexpected end of Huffman bitstream.")
        current = self._data[self._byte_index]
        bit = (current >> (7 - self._bit_index)) & 1
        self._bit_index = self._bit_index + 1

        if self._bit_index == 8:
            self._bit_index = 0
            self._byte_index = self._byte_index + 1
        return bit

    def read_bits(self, bit_count):
        if bit_count < 0: raise ValueError("bit_count must not be negative.")
        value = 0
        for _ in range(bit_count): value = (value << 1) | self.read_bit()
        return value
