import csv
import time
import statistics
from dataclasses import dataclass
from compressor import lz77, sdeflate
from compressor.models import LZ77Config

@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    file_path: str
    algorithm: str
    original_size: int
    compressed_size: int
    compression_seconds: float
    decompression_seconds: float
    correct: bool

    @property
    def compression_ratio(self):
        if self.original_size == 0: return None
        return self.compressed_size / self.original_size


def collect_text_files(target):
    if not target.exists(): raise FileNotFoundError(f"Target does not exist: {target}")
    if target.is_file():
        if target.suffix.lower() != ".txt": raise ValueError("Benchmark target file must have a .txt extension.")
        return [target]
    files = sorted(path for path in target.rglob("*.txt") if path.is_file())
    if not files: raise ValueError(f"No .txt files found under directory: {target}")
    return files


def benchmark_paths(target, algorithm, config=None, repeat=3):
    if repeat <= 0: raise ValueError("repeat must be positive.")
    effective_config = config or LZ77Config()
    files = collect_text_files(target)
    algorithm_names = _resolve_algorithms(algorithm)
    results = []

    for file_path in files:
        data = file_path.read_bytes()
        for algorithm_name in algorithm_names: results.append( _benchmark_algorithm( algorithm_name=algorithm_name, file_path=file_path, data=data, config=effective_config, repeat=repeat,))

    return results

def render_table(results):
    headers = [ "File", "Algorithm", "Original", "Compressed", "Ratio", "Compress ms", "Decompress ms", "Correct", ]
    rows = [ [ result.file_path, result.algorithm, str(result.original_size), str(result.compressed_size), "n/a" if result.compression_ratio is None else f"{result.compression_ratio:.3f}", f"{result.compression_seconds * 1_000:.3f}", f"{result.decompression_seconds * 1_000:.3f}", "yes" if result.correct else "no", ] for result in results ]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row): widths[index] = max(widths[index], len(cell))

    def format_row(row): return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    lines = [format_row(headers), separator]
    lines.extend(format_row(row) for row in rows)
    return "\n".join(lines)

def write_csv(results, destination):
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow( [ "file_path", "algorithm", "original_size", "compressed_size", "compression_ratio", "compression_seconds", "decompression_seconds", "correct", ])
        for result in results: writer.writerow( [ result.file_path, result.algorithm, result.original_size, result.compressed_size, "" if result.compression_ratio is None else f"{result.compression_ratio:.6f}", f"{result.compression_seconds:.9f}", f"{result.decompression_seconds:.9f}", result.correct, ])

def _benchmark_algorithm(algorithm_name, file_path, data, config, repeat):
    compress_fn, decompress_fn = _get_algorithm_functions(algorithm_name)
    compression_samples = []
    decompression_samples = []
    compressed_payload = b""
    restored = b""

    for _ in range(repeat):
        start = time.perf_counter()
        compressed_payload = compress_fn(data, config)
        compression_samples.append(time.perf_counter() - start)

    for _ in range(repeat):
        start = time.perf_counter()
        restored = decompress_fn(compressed_payload)
        decompression_samples.append(time.perf_counter() - start)

    return BenchmarkResult( file_path=str(file_path), algorithm=algorithm_name, original_size=len(data), compressed_size=len(compressed_payload), compression_seconds=statistics.mean(compression_samples), decompression_seconds=statistics.mean(decompression_samples), correct=restored == data,)

def _resolve_algorithms(algorithm):
    normalized = algorithm.lower()
    if normalized == "all": return ["lz77", "sdeflate"]
    if normalized == "deflate": return ["sdeflate"]
    if normalized in {"lz77", "sdeflate"}: return [normalized]
    raise ValueError(f"Unsupported algorithm selection: {algorithm}")


def _get_algorithm_functions(algorithm_name):
    if algorithm_name == "lz77": return lz77.compress, lz77.decompress
    if algorithm_name == "sdeflate": return sdeflate.compress, sdeflate.decompress
    raise ValueError(f"Unsupported algorithm: {algorithm_name}")
