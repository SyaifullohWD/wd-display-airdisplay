#!/usr/bin/env python3
"""Isolated delivery regressions; no Gradle, compiler, SDK, or device execution."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import tarfile
import hashlib

from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class DeliveryGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pad-delivery-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        (self.root / "tests").mkdir()
        for name in ("test_apk_alignment.py", "test_delivery.py", "test_device_startup.py"):
            (self.root / "tests" / name).write_text("import unittest\n")
        self.trace = self.root / "trace"
        self.env = dict(os.environ, TRACE=str(self.trace), FAIL="")
        self.stub("gradlew", "jvm")
        self.stub("scripts/test-native.sh", "native")
        self.stub("scripts/test-core-protocol.sh", "protocol")
        self.stub("scripts/test-native-audit.sh", "audit")

    def stub(self, name, label):
        p = self.root / name
        p.write_text('#!/bin/sh\necho "' + label + ' $*" >> "$TRACE"\n[ "$FAIL" != "' + label + '" ]\n')
        p.chmod(0o755)

    def gate(self):
        return subprocess.run(["bash", str(self.root / "scripts/host-gate.sh")], env=self.env,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def test_explicit_gate_runs_all_required_suites(self):
        result = self.gate()
        self.assertEqual(result.returncode, 0, result.stdout)
        trace = self.trace.read_text()
        self.assertIn(":app:testDebugUnitTest", trace)
        self.assertIn("native", trace)
        self.assertIn("protocol", trace)
        self.assertIn("test_apk_alignment", result.stdout)

    def test_missing_audit_suite_cannot_silently_pass(self):
        (self.root / "scripts/test-native-audit.sh").unlink()
        self.assertNotEqual(self.gate().returncode, 0)

    def test_native_failure_cannot_be_masked(self):
        self.env["FAIL"] = "native"
        result = self.gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("protocol", self.trace.read_text() if self.trace.exists() else "")


class NativeAuditPipelineTest(unittest.TestCase):
    def test_all_four_audit_harnesses_and_shutdown_modes_are_mandatory(self):
        with tempfile.TemporaryDirectory(prefix="pad-audit-pipeline-") as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            shutil.copyfile(ROOT / "scripts/test-native-audit.sh", root / "scripts/test-native-audit.sh")
            header = root / "openssl/include/openssl/evp.h"
            header.parent.mkdir(parents=True)
            header.write_text("fixture, not used by a real compiler")
            cc = root / "fake-cc"
            cc.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
args=sys.argv[1:]
label=next(pathlib.Path(a).stem for a in args if '/tests/native/' in a and a.endswith('.c'))
with open(os.environ['TRACE'],'a') as f: f.write('compile:'+label+' '+ ' '.join(args)+'\\n')
out=pathlib.Path(args[args.index('-o')+1])
out.write_text('#!/bin/sh\\nprintf "ran:'+label+' %s\\\\n" "$*" >> "$TRACE"\\n')
out.chmod(0o755)
''')
            cc.chmod(0o755)
            trace = root / "trace"
            env = dict(os.environ, CC=str(cc), TRACE=str(trace), OPENSSL_PREFIX=str(root / "openssl"))
            result = subprocess.run(["bash", str(root / "scripts/test-native-audit.sh")], env=env,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(result.returncode, 0, result.stdout)
            calls = trace.read_text()
            for name in ("crypto_stream_test", "request_fragment_test", "httpd_shutdown_test", "active_rekey_test", "protocol_tests"):
                self.assertIn("compile:" + name, calls)
                self.assertIn("ran:" + name, calls)
            for mode in [str(i) for i in range(8)] + ["valid", "deadline", "backpressure"]:
                self.assertIn("ran:httpd_shutdown_test " + mode, calls)
            self.assertIn("-DHTTPD_TEST_PRODUCTION_BUDGET", calls)
            self.assertIn("ran:dns_boundary_test invalid-start", calls)
            self.assertIn("ran:dns_boundary_test ", calls)
            self.assertIn("ran:service_name_utf8_test ", calls)
            http_compile = next(line for line in calls.splitlines() if line.startswith("compile:httpd_shutdown_test"))
            self.assertIn("/utils.c", http_compile)
            self.assertIn("-fsanitize=address,undefined", calls)


class PublicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "scripts/delivery.py"
        if not path.is_file():
            raise AssertionError("transactional delivery implementation missing")
        spec = importlib.util.spec_from_file_location("delivery", path)
        cls.delivery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.delivery)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pad-publication-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in self.delivery.SOURCE_INCLUDES:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            if name in self.delivery.SOURCE_DIRS:
                p.mkdir(exist_ok=True)
                (p / "fixture.txt").write_text("source")
            else:
                p.write_text("source")
        self.apk = self.root / "candidate.apk"
        self.apk.write_bytes(b"test-only-apk")
        self.old = self.root / "deliverables"
        self.old.mkdir()
        (self.old / "old").write_text("previous coherent release")

    def test_failure_leaves_previous_delivery_untouched(self):
        def reject(_):
            raise RuntimeError("signature rejected")
        with self.assertRaisesRegex(RuntimeError, "signature rejected"):
            self.delivery.publish(self.root, self.apk, verify=reject)
        self.assertEqual((self.old / "old").read_text(), "previous coherent release")
        self.assertFalse((self.old / "SHA256SUMS").exists())

    def test_signature_verification_failure_cannot_publish(self):
        calls = []
        def command(argv, root):
            calls.append([str(item) for item in argv])
            if Path(str(argv[0])).name == "apksigner":
                raise subprocess.CalledProcessError(1, argv)
        with mock.patch.object(self.delivery, "run", side_effect=command):
            with self.assertRaises(subprocess.CalledProcessError):
                self.delivery.publish(self.root, self.apk)
        self.assertEqual(len(calls), 3)
        self.assertIn("verify-apk-alignment.py", calls[0][2])
        self.assertEqual(calls[1][1:6], ["-c", "-P", "16", "-v", "4"])
        self.assertEqual(calls[2][1:4], ["verify", "--verbose", "--print-certs"])
        self.assertTrue((self.old / "old").exists())

    def test_changed_source_since_build_refuses_publication(self):
        expected = self.delivery.snapshot(self.root)
        (self.root / "scripts/fixture.txt").write_text("changed after build")
        with self.assertRaisesRegex(RuntimeError, "source changed"):
            self.delivery.publish(self.root, self.apk, verify=lambda _: None, expected_source=expected)
        self.assertTrue((self.old / "old").exists())

    def test_repeated_source_bundle_is_reproducible(self):
        first, second = self.root / "one.tar.gz", self.root / "two.tar.gz"
        self.delivery.bundle(self.root, first)
        os.utime(self.root / "scripts/fixture.txt", (123, 456))
        self.delivery.bundle(self.root, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_coherent_release_and_relative_checksums(self):
        self.delivery.publish(self.root, self.apk, verify=lambda _: None)
        self.assertTrue(self.old.is_symlink())
        lines = (self.old / "SHA256SUMS").read_text().splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            digest, name = line.split("  ")
            self.assertEqual(Path(name).name, name)
            self.assertEqual(hashlib.sha256((self.old / name).read_bytes()).hexdigest(), digest)
        with tarfile.open(self.old / "pocket-airdisplay-source.tar.gz") as archive:
            names = archive.getnames()
        self.assertIn("scripts/fixture.txt", names)
        self.assertIn("tests/fixture.txt", names)
        self.assertIn("app/src/androidTest/fixture.txt", names)
        self.assertTrue(any(p.name.startswith("legacy-") for p in (self.root / ".delivery-releases").iterdir()))

    def test_private_material_refuses_publication(self):
        (self.root / "scripts" / ".env").write_text("TOKEN=private")
        with self.assertRaisesRegex(ValueError, "private|forbidden"):
            self.delivery.publish(self.root, self.apk, verify=lambda _: None)
        self.assertTrue((self.old / "old").is_file())

    def test_symlink_cannot_leak_external_private_file(self):
        secret = self.root / "outside-secret"
        secret.write_text("secret")
        (self.root / "scripts" / "leak.txt").symlink_to(secret)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.delivery.publish(self.root, self.apk, verify=lambda _: None)
        self.assertTrue((self.old / "old").exists())


if __name__ == "__main__":
    unittest.main()
