# Compression algorithm comparisons

This project implements two compression algorithms: 

1. **LZ77**
2. **A simplified DEFLATE-style compressor**

The simplified DEFLATE-style compressor in this repository is **DEFLATE-inspired**, not RFC-compliant DEFLATE. It uses:

- LZ77 tokenization with literals and `(distance, length)` matches
- Canonical Huffman coding over the token stream
- Exact length and distance symbols instead of DEFLATE's block format, extra bits, and RFC headers

The code operates on **raw file bytes**. That means Unicode `.txt` files round-trip correctly as long as the original byte encoding is preserved, which the compressors do.

## Algorithms

### LZ77

The LZ77 compressor scans through the input with:

- a configurable sliding window over previously seen bytes
- a configurable lookahead buffer
- greedy longest-match search

If it finds a match of at least `min_match_length`, it emits a back-reference token:

- `MatchToken(distance, length)`

Otherwise it emits:

- `LiteralToken(byte_value)`

### Simplified DEFLATE-style

This compressor reuses the LZ77 tokenization stage, then Huffman-encodes the token stream:

- literal bytes are encoded as symbols `0..255`
- an end-of-stream marker uses symbol `256`
- match lengths use symbols `257+`
- match distances are encoded with a separate Huffman alphabet

This keeps the design simple while still demonstrating why adding entropy coding on top of LZ77 often improves compression.

## File Formats

### `.lz77`

Simple custom binary format:

- magic: `LZ77`
- version byte
- integers-encoded metadata:
  - `window_size`
  - `lookahead_size`
  - `min_match_length`
  - `original_size`
  - `token_count`
- token stream:
  - literal token: tag `0x00`, followed by 1 byte
  - match token: tag `0x01`, followed by integers `distance` and integers `length`

### `.sdeflate`

Simple custom DEFLATE-inspired format:

- magic: `SDFL`
- version byte
- integers-encoded metadata:
  - `window_size`
  - `lookahead_size`
  - `min_match_length`
  - `original_size`
  - literal/length alphabet size
  - literal/length code lengths
  - distance alphabet size
  - distance code lengths
- Huffman-coded bitstream

This format stores canonical Huffman code lengths so the decoder can rebuild the exact codebooks.

## Project Layout

```text
compressor/
  __init__.py
  __main__.py
  benchmark.py
  bits.py
  cli.py
  huffman.py
  lz77.py
  models.py
  sdeflate.py
  integers.py
tests/
  test_cli.py
  test_roundtrip.py
```

## Running

You can run the project directly from the repository root:

```bash
python -m compressor --help
```

### Compress with LZ77

```bash
python -m compressor compress lz77 path/to/file.txt
python -m compressor compress lz77 path/to/file.txt --window-size 8192 --lookahead-size 258 --min-match-length 3
python -m compressor compress lz77 path/to/file.txt --output path/to/file.txt.lz77
```

### Decompress with LZ77

```bash
python -m compressor decompress lz77 path/to/file.txt.lz77
python -m compressor decompress lz77 path/to/file.txt.lz77 --output restored.txt
```

### Compress with Simplified DEFLATE-style

```bash
python -m compressor compress sdeflate path/to/file.txt
python -m compressor compress sdeflate path/to/file.txt --window-size 8192 --lookahead-size 258 --min-match-length 3
```

### Decompress with Simplified DEFLATE-style

```bash
python -m compressor decompress sdeflate path/to/file.txt.sdeflate
```

### Benchmark One File

```bash
python -m compressor benchmark path/to/file.txt
python -m compressor benchmark path/to/file.txt --repeat 5
```

### Benchmark All `.txt` Files in a Directory

```bash
python -m compressor benchmark path/to/texts
python -m compressor benchmark path/to/texts --csv benchmark_results.csv
```

Directory benchmarking scans recursively for `*.txt` files.

## Benchmark Output

The benchmark prints a readable terminal table with:

- file path
- algorithm
- original size
- compressed size
- compression ratio
- compression time
- decompression time
- correctness check

Optional CSV export is supported with `--csv`.

## Tests

Run the included verification suite:

```bash
python -m unittest discover -s tests -v
```

The tests cover:

- round-trip correctness for both algorithms
- empty input
- highly repetitive input
- mostly unique input
- Unicode text
- CLI smoke tests
