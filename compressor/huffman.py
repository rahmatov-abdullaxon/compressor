import heapq
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Huffman:
    bits: int
    length: int

class _Node:
    def __init__(self, symbol=None, left=None, right=None):
        self.symbol = symbol
        self.left = left
        self.right = right

class Book:
    def __init__(self, code_lengths):
        filtered = {symbol: length for symbol, length in code_lengths.items() if length > 0}
        if not filtered: raise ValueError("At least one Huffman symbol is required.")
        self.code_lengths = dict(filtered)
        self.codes = _build_canonical_codes(self.code_lengths)
        self._root = _build_decoder_tree(self.codes)

    @classmethod
    def from_frequencies(cls, frequencies): return cls(build_code_lengths(frequencies))

    @classmethod
    def from_code_lengths(cls, code_lengths): return cls({symbol: length for symbol, length in enumerate(code_lengths) if length > 0})

    def encode_symbol(self, writer, symbol):
        try: code = self.codes[symbol]
        except KeyError as exc: raise ValueError(f"Symbol {symbol} is not present in the Huffman codebook.") from exc
        writer.write_bits(code.bits, code.length)

    def decode_symbol(self, reader):
        node = self._root
        while node.symbol is None:
            bit = reader.read_bit()
            node = node.right if bit else node.left
            if node is None: raise ValueError("Encountered an invalid Huffman code in the bitstream.")
        return node.symbol

def build_code_lengths(frequencies):
    items = [(symbol, frequency) for symbol, frequency in frequencies.items() if frequency > 0]
    if not items: raise ValueError("At least one positive-frequency symbol is required.")
    if len(items) == 1: symbol, _ = items[0]; return {symbol: 1}

    heap = []
    counter = 0
    for symbol, frequency in sorted(items, key=lambda item: item[0]):
        heapq.heappush(heap, (frequency, symbol, counter, _Node(symbol=symbol)))
        counter = counter + 1

    while len(heap) > 1:
        freq_a, min_symbol_a, _, node_a = heapq.heappop(heap)
        freq_b, min_symbol_b, _, node_b = heapq.heappop(heap)
        parent = _Node(left=node_a, right=node_b)
        heapq.heappush(heap,(freq_a + freq_b, min(min_symbol_a, min_symbol_b), counter, parent))
        counter = counter + 1

    _, _, _, root = heap[0]
    lengths = {}
    stack = [(root, 0)]

    while stack:
        node, depth = stack.pop()
        if node.symbol is not None: lengths[node.symbol] = max(depth, 1); continue
        if node.right is not None: stack.append((node.right, depth + 1))
        if node.left is not None: stack.append((node.left, depth + 1))

    return lengths

def _build_canonical_codes(code_lengths):
    canonical = {}
    code = 0
    previous_length = 0

    for symbol, length in sorted(code_lengths.items(), key=lambda item: (item[1], item[0])):
        code <<= length - previous_length
        canonical[symbol] = Huffman(bits=code, length=length)
        code += 1
        previous_length = length

    return canonical


def _build_decoder_tree(codes):
    root = _Node()
    for symbol, code in codes.items():
        node = root
        for shift in range(code.length - 1, -1, -1):
            bit = (code.bits >> shift) & 1
            if bit == 0:
                if node.left is None: node.left = _Node()
                node = node.left
            else:
                if node.right is None: node.right = _Node()
                node = node.right

        if node.symbol is not None: raise ValueError("Duplicate Huffman code detected.")
        node.symbol = symbol

    return root
