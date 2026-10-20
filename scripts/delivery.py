#!/usr/bin/env python3
"""Fail-closed host build and coherent APK/corresponding-source publication.

Host acceptance is NOT device/AirPlay acceptance. No adb is invoked here.
A single lock covers snapshots, gates, build, and publication. Existing historical
outputs are retained; readers should resolve deliverables once per operation.
"""
import argparse
import fcntl
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid

SOURCE_DIRS = ("app/src/main", "app/src/test", "app/src/androidTest", "scripts", "tests")
SOURCE_INCLUDES = (
    "LICENSE", "README.md", "THIRD_PARTY_NOTICES.md", "build.gradle.kts",
    "settings.gradle.kts", "gradle.properties", "gradlew", "gradlew.bat",
    "gradle/wrapper/gradle-wrapper.jar", "gradle/wrapper/gradle-wrapper.properties",
    "app/build.gradle.kts", *SOURCE_DIRS, "tools/build-deps-provenance.txt",
    "tools/ndk-r27d-provenance.txt", "tools/openssl.tar.gz", "tools/libplist.tar.gz",
)
FORBIDDEN_DIRS = {"references", ".tools", ".gradle", ".kotlin", ".cxx", "evidence",
                  "deliverables", ".git", "__pycache__", "build", "node_modules"}
PRIVATE_SUFFIXES = {".jks", ".keystore", ".p12", ".pfx", ".key", ".pem"}
APK_NAME = "pocket-airdisplay-debug.apk"
SOURCE_NAME = "pocket-airdisplay-source.tar.gz"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def source_files(root):
    result = []
    for include in SOURCE_INCLUDES:
        path = root / include
        if not path.exists():
            raise ValueError("missing source include: " + include)
        candidates = sorted(path.rglob("*")) if path.is_dir() else [path]
        if path.is_symlink():
            raise ValueError("source symlink forbidden: " + include)
        for candidate in candidates:
            relative = candidate.relative_to(root)
            if candidate.is_symlink():
                raise ValueError("source symlink forbidden: " + str(relative))
            if set(relative.parts) & FORBIDDEN_DIRS:
                # Generated caches are not source and are never archived.
                continue
            if not candidate.is_file():
                continue
            name = candidate.name.lower()
            if (name.startswith(".env") or name in {"local.properties", "credentials.json", "id_rsa", "id_ed25519"}
                    or candidate.suffix.lower() in PRIVATE_SUFFIXES):
                raise ValueError("private/forbidden source file: " + str(relative))
            # Scan content without embedding a literal key header in this script.
            data = candidate.read_bytes()
            prefix = b"-----" + b"BEGIN "
            if any(prefix + kind + b"PRIVATE KEY" in data for kind in (b"", b"RSA ", b"EC ", b"OPENSSH ", b"ENCRYPTED ")):
                raise ValueError("private key material in source: " + str(relative))
            result.append(relative)
    return sorted(set(result))


def snapshot(root):
    return {str(p): digest(root / p) for p in source_files(root)}


def bundle(root, target):
    with target.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
        with tarfile.open(fileobj=gz, mode="w|", format=tarfile.PAX_FORMAT) as archive:
            for relative in source_files(root):
                path = root / relative
                info = archive.gettarinfo(str(path), arcname=str(relative))
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ""
                info.mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                info.pax_headers = {}
                with path.open("rb") as stream:
                    archive.addfile(info, stream)


def run(command, root):
    print("+ " + " ".join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=root, check=True)


def verify_apk(root, apk):
    run([sys.executable, "-B", root / "scripts/verify-apk-alignment.py", apk], root)
    sdk = Path(os.environ.get("ANDROID_HOME", root / ".tools/sdk"))
    tools = sdk / "build-tools/36.0.0"
    # SDK tools are required; custom ELF/ZIP checks remain an additional gate.
    run([tools / "zipalign", "-c", "-P", "16", "-v", "4", apk], root)
    run([tools / "apksigner", "verify", "--verbose", "--print-certs", apk], root)


def publish(root, apk, verify=None, expected_source=None):
    """Caller holds delivery lock; verify every staged artifact before switching."""
    verify = verify or (lambda path: verify_apk(root, path))
    releases = root / ".delivery-releases"
    releases.mkdir(exist_ok=True)
    identifier = uuid.uuid4().hex
    stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=releases))
    release = releases / ("release-" + identifier)
    link = root / (".deliverables-" + identifier)
    legacy = None
    output = root / "deliverables"
    try:
        staged_apk = stage / APK_NAME
        shutil.copyfile(apk, staged_apk)
        verify(staged_apk)
        before = snapshot(root)
        if expected_source is not None and before != expected_source:
            raise RuntimeError("source changed during host gate/build; refusing publication")
        bundle(root, stage / SOURCE_NAME)
        if before != snapshot(root):
            raise RuntimeError("source changed during bundling; refusing publication")
        sums = "".join(digest(stage / name) + "  " + name + "\n" for name in (APK_NAME, SOURCE_NAME))
        (stage / "SHA256SUMS").write_text(sums)
        (stage / (APK_NAME + ".sha256")).write_text(sums.splitlines()[0] + "\n")
        (stage / "ACCEPTANCE.txt").write_text(
            "Host gates/alignment/signature only. Device startup, instrumentation and AirPlay interoperability are separate acceptance gates.\n")
        stage.rename(release)
        link.symlink_to(release.relative_to(root), target_is_directory=True)
        if output.exists() and not output.is_symlink():
            # One-time legacy migration: no mixed release is ever visible. There
            # can be a brief missing path; rollback restores it on Python errors.
            legacy = releases / ("legacy-" + identifier)
            output.rename(legacy)
        os.replace(link, output)
        print("Published coherent host-verified release: " + str(release), flush=True)
        print(sums, end="")
    except BaseException:
        if legacy is not None and not output.exists():
            legacy.rename(output)
        raise
    finally:
        if link.is_symlink():
            link.unlink()
        if stage.exists():
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    evidence = root / "evidence/fix-delivery"
    evidence.mkdir(parents=True, exist_ok=True)
    # Fail immediately rather than overlap Gradle/publishing from these entrypoints.
    with (evidence / "delivery.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        expected = snapshot(root)
        run(["bash", root / "scripts/host-gate.sh"], root)
        run([root / "gradlew", ":app:assembleDebug"], root)
        publish(root, root / "app/build/outputs/apk/debug/app-debug.apk", expected_source=expected)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print("DELIVERY FAILED (previous publication retained): " + str(error), file=sys.stderr)
        sys.exit(1)
