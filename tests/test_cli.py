import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

class CLITests(unittest.TestCase):
    def test_lz77_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "sample.txt"
            restored = temp_path / "restored.txt"
            source.write_text("CLI smoke test. Пример текста. " * 25, encoding="utf-8")
            subprocess.run( [sys.executable, "-m", "compressor", "compress", "lz77", str(source)], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
            compressed = temp_path / "sample.txt.lz77"
            self.assertTrue(compressed.exists())
            subprocess.run( [ sys.executable, "-m", "compressor", "decompress", "lz77", str(compressed), "--output", str(restored)], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
            self.assertEqual(restored.read_bytes(), source.read_bytes())

    def test_lz77_cli_binary_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "sample.bin"
            restored = temp_path / "restored.bin"
            source.write_bytes(bytes(range(256)) * 8)
            subprocess.run([sys.executable, "-m", "compressor", "compress", "lz77", str(source)], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
            compressed = temp_path / "sample.bin.lz77"
            self.assertTrue(compressed.exists())
            subprocess.run([sys.executable, "-m", "compressor", "decompress", "lz77", str(compressed), "--output", str(restored) ], cwd=REPO_ROOT, capture_output=True, text=True, check=True,)
            self.assertEqual(restored.read_bytes(), source.read_bytes())

    def test_benchmark_cli_csv_export(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "bench.txt"
            csv_output = temp_path / "bench.csv"
            source.write_text("benchmark input " * 200, encoding="utf-8")
            completed = subprocess.run( [ sys.executable, "-m", "compressor", "benchmark", str(source), "--repeat", "1", "--csv", str(csv_output)], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
            self.assertIn("Algorithm", completed.stdout)
            self.assertTrue(csv_output.exists())
            self.assertIn("lz77", csv_output.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
