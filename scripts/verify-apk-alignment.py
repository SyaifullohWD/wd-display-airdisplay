#!/usr/bin/env python3
"""Verify every ELF PT_LOAD and ZIP data offset, without third-party modules.

Uncompressed .so entries must start at a 16 KiB boundary; other stored entries
must be 4-byte aligned, matching zipalign -c -P 16 -v 4. Compressed entries do
not require ZIP mmap alignment, but their ELF program headers are still checked.
"""
import argparse
import hashlib
import struct
import sys
import zipfile
from pathlib import Path

PAGE = 16384


def inspect_elf(data):
    """Return (program-header index, offset, vaddr, alignment) for all LOADs."""
    if data[:4] != b"\x7fELF":
        raise ValueError("not ELF")
    if data[5] not in (1, 2) or data[4] not in (1, 2):
        raise ValueError("unsupported ELF encoding/class")
    endian = "<" if data[5] == 1 else ">"
    wide = data[4] == 2
    header = struct.unpack_from(endian + ("HHIQQQIHHHHHH" if wide else "HHIIIIIHHHHHH"), data, 16)
    phoff, phsize, phnum = header[4], header[8], header[9]
    fmt = endian + ("IIQQQQQQ" if wide else "IIIIIIII")
    if phnum == 0xffff or phnum == 0 or phsize < struct.calcsize(fmt):
        raise ValueError("missing/unsupported program header table")
    loads = []
    for i in range(phnum):
        ph = struct.unpack_from(fmt, data, phoff + i * phsize)
        if ph[0] == 1:
            offset, vaddr, align = (ph[2], ph[3], ph[7]) if wide else (ph[1], ph[2], ph[7])
            loads.append((i, offset, vaddr, align))
    if not loads:
        raise ValueError("no PT_LOAD segments")
    return loads


def verify(apk):
    failures, elf_count, load_count, stored_count = [], 0, 0, 0
    print(f"APK {apk} SHA256 {hashlib.sha256(apk.read_bytes()).hexdigest()}")
    with zipfile.ZipFile(apk) as archive, apk.open("rb") as raw:
        names = archive.namelist()
        if len(names) != len(set(names)):
            failures.append("duplicate ZIP entry names")
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            data = archive.read(entry)
            native = entry.filename.endswith(".so")
            if entry.compress_type == zipfile.ZIP_STORED:
                raw.seek(entry.header_offset)
                header = raw.read(30)
                if header[:4] != b"PK\x03\x04":
                    raise ValueError("invalid local ZIP header")
                name_size, extra_size = struct.unpack_from("<HH", header, 26)
                offset = entry.header_offset + 30 + name_size + extra_size
                required = PAGE if native else 4
                ok = offset % required == 0
                stored_count += 1
                print(f"ZIP {entry.filename} offset={offset} required={required} {'PASS' if ok else 'FAIL'}")
                if not ok:
                    failures.append(f"ZIP {entry.filename}: offset {offset} not aligned to {required}")
            if data[:4] == b"\x7fELF" or native:
                elf_count += 1
                try:
                    for i, offset, vaddr, align in inspect_elf(data):
                        load_count += 1
                        ok = align >= PAGE and align & (align - 1) == 0 and (vaddr - offset) % align == 0
                        print(f"ELF {entry.filename} PT_LOAD[{i}] offset={offset} vaddr={vaddr} p_align={align} {'PASS' if ok else 'FAIL'}")
                        if not ok:
                            failures.append(f"ELF {entry.filename} PT_LOAD[{i}]: incompatible alignment {align}")
                except (ValueError, IndexError, struct.error) as error:
                    failures.append(f"ELF {entry.filename}: {error}")
    if not elf_count:
        failures.append("no ELF entries found")
    print(f"SUMMARY ELF={elf_count} PT_LOAD={load_count} stored_ZIP={stored_count} failures={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    return not failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    try:
        sys.exit(0 if verify(args.apk) else 1)
    except (OSError, ValueError, zipfile.BadZipFile, struct.error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
