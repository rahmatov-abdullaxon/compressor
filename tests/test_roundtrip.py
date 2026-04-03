import tempfile
import unittest
from pathlib import Path
from compressor import benchmark, lz77, sdeflate
from compressor.models import LZ77Config


class RoundTripTests(unittest.TestCase):
    def setUp(self):
        self.default_config = LZ77Config()
        self.small_window_config = LZ77Config(window_size=128, lookahead_size=64, min_match_length=3)
        self.samples = { "empty": b"", "single-byte": b"A", "plain-ascii": b"abracadabra abracadabra abracadabra", "repetitive": (b"banana_bandana_" * 256), "mostly-unique": bytes((index * 37) % 251 for index in range(2048)), "unicode-text": ("Hello, world! Привет, мир! こんにちは世界! " * 20).encode("utf-8") }

    def test_lz77_roundtrip(self):
        for name, sample in self.samples.items():
            with self.subTest(sample=name):
                compressed = lz77.compress(sample, self.default_config)
                restored = lz77.decompress(compressed)
                self.assertEqual(restored, sample)

    def test_sdeflate_roundtrip(self):
        for name, sample in self.samples.items():
            with self.subTest(sample=name):
                compressed = sdeflate.compress(sample, self.default_config)
                restored = sdeflate.decompress(compressed)
                self.assertEqual(restored, sample)

    def test_token_stream_roundtrip(self):
        sample = ("Token streams should decode exactly. " * 30).encode("utf-8")
        tokens = lz77.tokenize(sample, self.small_window_config)
        restored = lz77.detokenize(tokens)
        self.assertEqual(restored, sample)

    def test_custom_config_roundtrip(self):
        sample = ("abc123abc123___xyzxyzxyz " * 60).encode("utf-8")
        compressed_lz77 = lz77.compress(sample, self.small_window_config)
        compressed_sdeflate = sdeflate.compress(sample, self.small_window_config)
        self.assertEqual(lz77.decompress(compressed_lz77), sample)
        self.assertEqual(sdeflate.decompress(compressed_sdeflate), sample)

    def test_benchmark_single_binary_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "sample.bin"
            source.write_bytes(bytes(range(256)) * 16)
            results = benchmark.benchmark_paths(source, algorithm="all", repeat=1)
            self.assertEqual(len(results), 2)
            self.assertTrue(all(result.correct for result in results))

if __name__ == "__main__":
    unittest.main()
