from collections import Counter
from compressor import lz77
from compressor.bits import Reader, Writer
from compressor.huffman import Book
from compressor.models import LZ77Config, LiteralToken
from compressor.integers import decode, encode

MAGIC = b"SDFL"
VERSION = 1
END_OF_STREAM = 256
FIRST_LENGTH_SYMBOL = 257
DEFAULT_EXTENSION = ".sdeflate"


def compress(data, config=None):
    effective_config = config or LZ77Config()
    tokens = lz77.tokenize(data, effective_config)
    literal_length_symbols, distance_symbols, max_length, max_distance = _collect_symbol_stats(tokens, effective_config.min_match_length)
    literal_length_frequencies = Counter(literal_length_symbols)
    distance_frequencies = Counter(distance_symbols)
    literal_length_book = Book.from_frequencies(literal_length_frequencies)
    distance_book = (Book.from_frequencies(distance_frequencies) if distance_symbols else None)
    literal_length_alphabet_size = (FIRST_LENGTH_SYMBOL + (max_length - effective_config.min_match_length + 1) if max_length else END_OF_STREAM + 1)
    distance_alphabet_size = max_distance
    literal_length_code_lengths = _expand_code_lengths(literal_length_book.code_lengths, literal_length_alphabet_size)
    distance_code_lengths = (_expand_code_lengths(distance_book.code_lengths, distance_alphabet_size) if distance_book is not None else [])

    bit_writer = Writer()
    for token in tokens:
        if isinstance(token, LiteralToken): literal_length_book.encode_symbol(bit_writer, token.value); continue
        literal_length_book.encode_symbol(bit_writer, FIRST_LENGTH_SYMBOL + (token.length - effective_config.min_match_length),)
        if distance_book is None: raise ValueError("Distance codebook is missing for a match token.")
        distance_book.encode_symbol(bit_writer, token.distance - 1)

    literal_length_book.encode_symbol(bit_writer, END_OF_STREAM)

    payload = bytearray()
    payload.extend(MAGIC)
    payload.append(VERSION)
    payload.extend(encode(effective_config.window_size))
    payload.extend(encode(effective_config.lookahead_size))
    payload.extend(encode(effective_config.min_match_length))
    payload.extend(encode(len(data)))
    payload.extend(encode(literal_length_alphabet_size))
    for length in literal_length_code_lengths: payload.extend(encode(length))
    payload.extend(encode(distance_alphabet_size))
    for length in distance_code_lengths: payload.extend(encode(length))
    payload.extend(bit_writer.bytes())
    return bytes(payload)

def decompress(payload):
    if len(payload) < len(MAGIC) + 1 or payload[: len(MAGIC)] != MAGIC: raise ValueError("Input is not a valid .sdeflate file.")

    offset = len(MAGIC)
    version = payload[offset]
    offset += 1
    if version != VERSION: raise ValueError(f"Unsupported simplified DEFLATE file version: {version}.")

    window_size, offset = decode(payload, offset)
    lookahead_size, offset = decode(payload, offset)
    min_match_length, offset = decode(payload, offset)
    original_size, offset = decode(payload, offset)
    literal_length_alphabet_size, offset = decode(payload, offset)

    if literal_length_alphabet_size < END_OF_STREAM + 1: raise ValueError("Literal/length alphabet is too small.")
    _ = LZ77Config( window_size=window_size, lookahead_size=lookahead_size, min_match_length=min_match_length,)

    literal_length_code_lengths = []
    for _ in range(literal_length_alphabet_size):
        length, offset = decode(payload, offset)
        literal_length_code_lengths.append(length)

    distance_alphabet_size, offset = decode(payload, offset)
    distance_code_lengths = []
    for _ in range(distance_alphabet_size):
        length, offset = decode(payload, offset)
        distance_code_lengths.append(length)

    literal_length_book = Book.from_code_lengths(literal_length_code_lengths)
    distance_book = (Book.from_code_lengths(distance_code_lengths) if distance_code_lengths else None)

    bit_reader = Reader(payload[offset:])
    output = bytearray()

    while True:
        symbol = literal_length_book.decode_symbol(bit_reader)
        if symbol < 256: output.append(symbol)
        elif symbol == END_OF_STREAM: break
        else:
            if distance_book is None: raise ValueError("Encountered a match symbol without a distance codebook.")
            length = min_match_length + (symbol - FIRST_LENGTH_SYMBOL)
            distance = distance_book.decode_symbol(bit_reader) + 1
            if distance > len(output): raise ValueError("Match distance exceeds the current output size.")
            for _ in range(length): output.append(output[len(output) - distance])

        if len(output) > original_size: raise ValueError("Decoded output exceeds the stored original size.")

    if len(output) != original_size: raise ValueError("Decoded output size does not match the stored original size.")
    return bytes(output)

def _collect_symbol_stats(tokens, min_match_length):
    literal_length_symbols = []
    distance_symbols = []
    max_length = 0
    max_distance = 0

    for token in tokens:
        if isinstance(token, LiteralToken): literal_length_symbols.append(token.value); continue
        literal_length_symbols.append(FIRST_LENGTH_SYMBOL + (token.length - min_match_length))
        distance_symbols.append(token.distance - 1)
        max_length = max(max_length, token.length)
        max_distance = max(max_distance, token.distance)

    literal_length_symbols.append(END_OF_STREAM)
    return literal_length_symbols, distance_symbols, max_length, max_distance

def _expand_code_lengths(code_lengths, alphabet_size):
    expanded = [0] * alphabet_size
    for symbol, length in code_lengths.items():
        if symbol >= alphabet_size: raise ValueError("Symbol exceeds the configured Huffman alphabet size.")
        expanded[symbol] = length
    return expanded
