"""LZ77 compression and decompression."""

from collections import defaultdict, deque

from compressor.integers import decode, encode
from compressor.models import LiteralToken, LZ77Archive, LZ77Config, MatchToken

MAGIC = b"LZ77"
VERSION = 1
DEFAULT_EXTENSION = ".lz77"

def find_longest_match(data, position, config, index):
    if position + config.min_match_length > len(data): return None

    key = data[position : position + config.min_match_length]
    candidates = index.get(key)
    if not candidates: return None

    window_start = max(0, position - config.window_size)
    while candidates and candidates[0] < window_start: candidates.popleft()
    if not candidates: return None

    max_length = min(config.lookahead_size, len(data) - position)
    best_length = 0
    best_distance = 0

    for candidate_position in reversed(candidates):
        distance = position - candidate_position
        if distance <= 0: continue

        current_length = config.min_match_length
        while current_length < max_length:
            left = candidate_position + current_length
            right = position + current_length
            if data[left] != data[right]: break
            current_length += 1

        if current_length > best_length or (current_length == best_length and (best_distance == 0 or distance < best_distance)):
            best_length = current_length
            best_distance = distance
            if best_length == max_length: break

    if best_length < config.min_match_length: return None
    return MatchToken(distance=best_distance, length=best_length)

def index_position(index, data, position, config):
    if position + config.min_match_length > len(data): return

    key = data[position : position + config.min_match_length]
    index[key].append(position)
    oldest_valid = position - config.window_size
    while index[key] and index[key][0] < oldest_valid: index[key].popleft()

def tokenize(data, config=None):
    effective_config = config or LZ77Config()
    if not data: return []

    index = defaultdict(deque)
    tokens = []
    position = 0

    while position < len(data):
        match = find_longest_match(data, position, effective_config, index)
        if match is None:
            tokens.append(LiteralToken(data[position]))
            step = 1
        else:
            tokens.append(match)
            step = match.length

        upper_bound = min(position + step, len(data))
        for seen_position in range(position, upper_bound): index_position(index, data, seen_position, effective_config)
        position = position + step

    return tokens

def detokenize(tokens):
    output = bytearray()

    for token in tokens:
        if isinstance(token, LiteralToken): output.append(token.value); continue
        if token.distance > len(output): raise ValueError("Invalid distance")
        for _ in range(token.length): output.append(output[len(output) - token.distance])

    return bytes(output)

def serialize_archive(archive):
    payload = bytearray()
    payload.extend(MAGIC)
    payload.append(VERSION)
    payload.extend(encode(archive.config.window_size))
    payload.extend(encode(archive.config.lookahead_size))
    payload.extend(encode(archive.config.min_match_length))
    payload.extend(encode(archive.original_size))
    payload.extend(encode(len(archive.tokens)))

    for token in archive.tokens:
        if isinstance(token, LiteralToken):
            payload.append(0)
            payload.append(token.value)
        else:
            payload.append(1)
            payload.extend(encode(token.distance))
            payload.extend(encode(token.length))
    return bytes(payload)

def parse_archive(payload):
    if len(payload) < len(MAGIC) + 1 or payload[: len(MAGIC)] != MAGIC: raise ValueError("Input is not a valid .lz77 file.")

    offset = len(MAGIC)
    version = payload[offset]
    offset = offset + 1
    if version != VERSION: raise ValueError(f"Unsupported LZ77 file version: {version}.")

    window_size, offset = decode(payload, offset)
    lookahead_size, offset = decode(payload, offset)
    min_match_length, offset = decode(payload, offset)
    original_size, offset = decode(payload, offset)
    token_count, offset = decode(payload, offset)
    config = LZ77Config(window_size=window_size, lookahead_size=lookahead_size, min_match_length=min_match_length)
    tokens = []
    for _ in range(token_count):
        if offset >= len(payload): raise ValueError("Unexpected end of LZ77 token stream.")

        tag = payload[offset]
        offset = offset + 1
        if tag == 0:
            if offset >= len(payload): raise ValueError("Missing literal byte in LZ77 token stream.")
            tokens.append(LiteralToken(payload[offset]))
            offset = offset + 1
        elif tag == 1:
            distance, offset = decode(payload, offset)
            length, offset = decode(payload, offset)
            tokens.append(MatchToken(distance=distance, length=length))
        else: raise ValueError(f"Unknown LZ77 token tag: {tag}.")

    if offset != len(payload): raise ValueError("Trailing bytes found after the end of the LZ77 stream.")
    return LZ77Archive(config=config, original_size=original_size, tokens=tokens)

def compress(data, config=None):
    effective_config = config or LZ77Config()
    archive = LZ77Archive(config=effective_config, original_size=len(data), tokens=tokenize(data, effective_config))
    return serialize_archive(archive)

def decompress(payload):
    archive = parse_archive(payload)
    restored = detokenize(archive.tokens)
    if len(restored) != archive.original_size: raise ValueError("Decompressed size does not match the stored original size.")
    return restored
