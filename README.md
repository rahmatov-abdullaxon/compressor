# rahmatov-compressor

Educational implementations of **LZ77** and a **DEFLATE-inspired** compressor, with a command-line interface for compression, decompression, and benchmarking.

## Important note

This project is **not** a standards-compliant DEFLATE implementation.

The `sdeflate` algorithm in this repository is **DEFLATE-inspired**, meaning it uses:

- LZ77 tokenization
- canonical Huffman coding
- a custom `.sdeflate` file format

It does **not** implement RFC-compliant DEFLATE block structure, headers, checksums, wrappers, or extra-bit encoding. This package is meant for **learning, experimentation, and comparison**, not as a replacement for `zlib`, `gzip`, or other standard compression tools.

## Features

- LZ77 compression and decompression
- DEFLATE-inspired compression and decompression
- byte-oriented processing
- support for compressing and decompressing any file type
- CLI for compression, decompression, and benchmark workflows
- CSV export for benchmark results
- tests for round-trip correctness and CLI smoke checks

## Installation

```bash
pip install rahmatov-compressor
```

## Quick start

Show the CLI help:

```bash
python -m compressor --help
```

Compress a file with LZ77:

```bash
python -m compressor compress lz77 path/to/file.bin
```

Decompress it:

```bash
python -m compressor decompress lz77 path/to/file.bin.lz77
```

Benchmark both algorithms on one file:

```bash
python -m compressor benchmark path/to/file.bin --repeat 3
```

## What this package does

This package operates on **raw file bytes**.

That means it can compress and decompress:

- text files
- binary files
- images
- archives
- executables
- any other file type

Round-trip correctness means reconstructing the original byte sequence exactly.

## Algorithms

### LZ77

The LZ77 compressor scans through the input using:

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

This keeps the design simple while still demonstrating why entropy coding on top of LZ77 often improves compression.

## File formats

### `.lz77`

Custom binary format containing:

- magic: `LZ77`
- version byte
- integer-encoded metadata:
  - `window_size`
  - `lookahead_size`
  - `min_match_length`
  - `original_size`
  - `token_count`
- token stream:
  - literal token: tag `0x00`, followed by 1 byte
  - match token: tag `0x01`, followed by encoded integers `distance` and `length`

### `.sdeflate`

Custom DEFLATE-inspired format containing:

- magic: `SDFL`
- version byte
- integer-encoded metadata:
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

## Command examples

### Compress with LZ77

```bash
python -m compressor compress lz77 path/to/file.bin
python -m compressor compress lz77 path/to/file.bin --window-size 8192 --lookahead-size 258 --min-match-length 3
python -m compressor compress lz77 path/to/file.bin --output path/to/file.bin.lz77
```

### Decompress with LZ77

```bash
python -m compressor decompress lz77 path/to/file.bin.lz77
python -m compressor decompress lz77 path/to/file.bin.lz77 --output restored.bin
```

### Compress with simplified DEFLATE-style

```bash
python -m compressor compress sdeflate path/to/file.bin
python -m compressor compress sdeflate path/to/file.bin --window-size 8192 --lookahead-size 258 --min-match-length 3
python -m compressor compress sdeflate path/to/file.bin --output path/to/file.bin.sdeflate
```

### Decompress with simplified DEFLATE-style

```bash
python -m compressor decompress sdeflate path/to/file.bin.sdeflate
python -m compressor decompress sdeflate path/to/file.bin.sdeflate --output restored.bin
```

### Benchmark one file

```bash
python -m compressor benchmark path/to/file.bin
python -m compressor benchmark path/to/file.bin --repeat 5
```

### Benchmark all `files in a directory

```bash
python -m compressor benchmark path/to/texts
python -m compressor benchmark path/to/texts --csv benchmark_results.csv
```

Directory benchmarking currently scans recursively for files.

## Benchmark output

The benchmark prints a terminal table with:

- file path
- algorithm
- original size
- compressed size
- compression ratio
- compression time
- decompression time
- correctness check

Optional CSV export is supported with `--csv`.

## Project layout

```text
compressor/
  __init__.py
  __main__.py
  benchmark.py
  bits.py
  cli.py
  huffman.py
  integers.py
  lz77.py
  models.py
  sdeflate.py
tests/
  test_cli.py
  test_roundtrip.py
```

## Running from source

From the repository root:

```bash
python -m compressor --help
```

## Tests

Run the verification suite:

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

## Limitations

- `sdeflate` is not RFC-compliant DEFLATE
- the custom output formats are specific to this project
- this is an educational project, not a production compression library

## License

MIT
