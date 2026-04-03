import argparse
from pathlib import Path

from compressor import benchmark, lz77, sdeflate
from compressor.models import LZ77Config


def build_parser():
    parser = argparse.ArgumentParser( prog="compressor", description="Compress, decompress, and benchmark LZ77 head-to-head against simplified DEFLATE.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compress_parser = subparsers.add_parser("compress", help="Compress a file.")
    compress_parser.add_argument("algorithm", choices=("lz77", "sdeflate", "deflate"))
    compress_parser.add_argument("input", type=Path, help="Input file path.")
    compress_parser.add_argument("-o", "--output", type=Path, help="Output file path.")
    _add_lz77_arguments(compress_parser)
    compress_parser.set_defaults(handler=_handle_compress)

    decompress_parser = subparsers.add_parser("decompress", help="Decompress a file.")
    decompress_parser.add_argument("algorithm", choices=("lz77", "sdeflate", "deflate"))
    decompress_parser.add_argument("input", type=Path, help="Compressed input file path.")
    decompress_parser.add_argument("-o", "--output", type=Path, help="Output file path.")
    decompress_parser.set_defaults(handler=_handle_decompress)

    benchmark_parser = subparsers.add_parser( "benchmark", help="Benchmark one file or all files in a directory.",)
    benchmark_parser.add_argument("target", type=Path, help="Input file or directory.")
    benchmark_parser.add_argument( "--algorithm", choices=("all", "lz77", "sdeflate", "deflate"), default="all", help="Which algorithm(s) to benchmark.",)
    benchmark_parser.add_argument( "--repeat", type=int, default=3, help="Number of repetitions used for compression and decompression timings.",)
    benchmark_parser.add_argument("--csv", type=Path, help="Optional CSV export path.")
    _add_lz77_arguments(benchmark_parser)
    benchmark_parser.set_defaults(handler=_handle_benchmark)

    return parser

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try: return args.handler(args)
    except Exception as exc: parser.exit(status=1, message=f"error: {exc}\n")

def _handle_compress(args):
    input_path = args.input
    if not input_path.is_file(): raise FileNotFoundError(f"Input file does not exist: {input_path}")
    algorithm = _normalize_algorithm(args.algorithm)
    config = _config_from_args(args)
    data = input_path.read_bytes()

    if algorithm == "lz77":
        compressed = lz77.compress(data, config)
        extension = lz77.DEFAULT_EXTENSION
    else:
        compressed = sdeflate.compress(data, config)
        extension = sdeflate.DEFAULT_EXTENSION

    output_path = args.output or _default_compressed_output(input_path, extension)
    output_path.write_bytes(compressed)

    ratio = "n/a" if not data else f"{len(compressed) / len(data):.3f}"
    print(
        f"Compressed {input_path} -> {output_path} "
        f"({len(data)} bytes -> {len(compressed)} bytes, ratio={ratio})"
    )
    return 0

def _handle_decompress(args):
    input_path = args.input
    if not input_path.is_file(): raise FileNotFoundError(f"Input file does not exist: {input_path}")
    algorithm = _normalize_algorithm(args.algorithm)
    payload = input_path.read_bytes()

    if algorithm == "lz77":
        restored = lz77.decompress(payload)
        extension = lz77.DEFAULT_EXTENSION
    else:
        restored = sdeflate.decompress(payload)
        extension = sdeflate.DEFAULT_EXTENSION

    output_path = args.output or _default_decompressed_output(input_path, extension)
    output_path.write_bytes(restored)

    print(f"Decompressed {input_path} -> {output_path} ({len(restored)} bytes)")
    return 0


def _handle_benchmark(args):
    target = args.target
    config = _config_from_args(args)
    results = benchmark.benchmark_paths( target=target, algorithm=args.algorithm, config=config, repeat=args.repeat)
    print(benchmark.render_table(results))

    if args.csv is not None:
        benchmark.write_csv(results, args.csv)
        print(f"\nCSV written to {args.csv}")

    return 0


def _add_lz77_arguments(parser):
    defaults = LZ77Config()
    parser.add_argument( "--window-size", type=int, default=defaults.window_size, help="Sliding window size in bytes.")
    parser.add_argument( "--lookahead-size", type=int, default=defaults.lookahead_size, help="Maximum match length considered during greedy parsing.")
    parser.add_argument( "--min-match-length", type=int, default=defaults.min_match_length, help="Minimum match length required before emitting a back-reference.")

def _config_from_args(args): return LZ77Config( window_size=args.window_size, lookahead_size=args.lookahead_size, min_match_length=args.min_match_length)

def _normalize_algorithm(name): return "sdeflate" if name == "deflate" else name

def _default_compressed_output(input_path, extension): return input_path.with_name(f"{input_path.name}{extension}")

def _default_decompressed_output(input_path, extension):
    if input_path.name.endswith(extension):
        original_name = input_path.name[: -len(extension)]
        if original_name: return input_path.with_name(original_name)
    return input_path.with_name(f"{input_path.name}.out")
