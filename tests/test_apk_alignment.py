#!/usr/bin/env python3
"""Synthetic format fixtures test the APK verifier, not device compatibility."""
import contextlib
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location("alignment", Path(__file__).resolve().parents[1] / "scripts/verify-apk-alignment.py")
alignment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alignment)


def elf(alignments=(16384, 16384), bits=64):
    wide = bits == 64
    ident = b"\x7fELF" + bytes([2 if wide else 1, 1, 1]) + bytes(9)
    size, phsize = (64, 56) if wide else (52, 32)
    header = struct.pack("<" + ("HHIQQQIHHHHHH" if wide else "HHIIIIIHHHHHH"),
                         3, 183 if wide else 40, 1, 0, size, 0, 0, size, phsize, len(alignments), 0, 0, 0)
    loads = b"".join(struct.pack("<" + ("IIQQQQQQ" if wide else "IIIIIIII"),
                                *([1, 4, 0, 0, 0, 0, 0, a] if wide else [1, 0, 0, 0, 0, 0, 4, a]))
                     for a in alignments)
    return ident + header + loads


class AlignmentTest(unittest.TestCase):
    def check(self, payload, *, aligned=True, compressed=False, filename="lib/arm64-v8a/test.so"):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "fixture.apk"
            info = zipfile.ZipInfo(filename)
            info.compress_type = zipfile.ZIP_DEFLATED if compressed else zipfile.ZIP_STORED
            if aligned and not compressed:
                padding = (-(30 + len(filename.encode()) + 4)) % 16384
                info.extra = struct.pack("<HH", 0xffff, padding) + bytes(padding)
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr(info, payload)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return alignment.verify(apk)

    def test_all_loads_aligned(self):
        self.assertTrue(self.check(elf()))

    def test_later_load_misaligned(self):
        self.assertFalse(self.check(elf((16384, 4096))))

    def test_zero_load_alignment(self):
        self.assertFalse(self.check(elf((0,))))

    def test_elf32_later_load_misaligned(self):
        self.assertTrue(self.check(elf(bits=32)))
        self.assertFalse(self.check(elf((16384, 4096), bits=32)))

    def test_zip_alignment_independent_of_elf(self):
        self.assertFalse(self.check(elf(), aligned=False))

    def test_compressed_elf_still_checked(self):
        self.assertTrue(self.check(elf(), aligned=False, compressed=True))
        self.assertFalse(self.check(elf((4096,)), compressed=True))

    def test_elf_detected_outside_so_extension(self):
        self.assertFalse(self.check(elf((4096,)), filename="assets/native"))

    def test_truncated_elf_fails_closed(self):
        self.assertFalse(self.check(b"\x7fELF"))

    def test_missing_elf_fails_closed(self):
        self.assertFalse(self.check(b"text", filename="assets/text"))


if __name__ == "__main__":
    unittest.main()
