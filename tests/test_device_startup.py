#!/usr/bin/env python3
"""No device access: startup acceptance/parser regressions use recorded fixtures."""
import importlib.util
from pathlib import Path
import unittest
import contextlib
import io
import json
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "org.pocketairdisplay.receiver"


class StartupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "scripts/validate-device-startup.py"
        if not path.is_file():
            raise AssertionError("startup validator implementation missing")
        spec = importlib.util.spec_from_file_location("startup", path)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_invalid_log_bytes_are_escaped_without_hiding_crash_markers(self):
        # Actual subprocess decode, not a mocked decoding result; never calls adb.
        import sys
        from types import SimpleNamespace
        device = self.module.Device(SimpleNamespace(adb=sys.executable, serial="fixture", output=Path(".")))
        device.prefix = [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'bad \\xff Process: org.pocketairdisplay.receiver, PID: 50\\n')"]
        output = device.run()
        self.assertIn(r"\xff", output)
        self.assertIn("Process: org.pocketairdisplay.receiver", output)

    def test_matching_test_apk_identity_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.module.arguments(["--serial", "USB-EXPLICIT", "--apk", "candidate.apk", "--output", "evidence"])

    def test_explicit_target_required(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.module.arguments(["--apk", "candidate.apk", "--output", "evidence"])
        args = self.module.arguments(["--serial", "USB-EXPLICIT", "--apk", "candidate.apk", "--test-apk", "candidate-test.apk", "--output", "evidence"])
        self.assertEqual(self.module.selector(args), ["-s", "USB-EXPLICIT"])
        args = self.module.arguments(["--transport-id", "7", "--apk", "candidate.apk", "--test-apk", "candidate-test.apk", "--output", "evidence"])
        self.assertEqual(self.module.selector(args), ["-t", "7"])

    def test_installed_identity_records_real_bytes_and_rejects_mismatch(self):
        class FixtureDevice:
            payload = b"installed-apk-fixture"
            def run(self, *argv):
                if argv[:3] == ("shell", "pm", "path"):
                    return "package:/data/app/fixture/base.apk\n"
                if argv[0] == "pull":
                    Path(argv[2]).write_bytes(self.payload)
                    return "fixture pull (no adb)"
                raise AssertionError("unexpected command")
        with tempfile.TemporaryDirectory(prefix="pad-device-identity-test-") as directory:
            output = Path(directory)
            apk = output / "candidate.apk"
            apk.write_bytes(FixtureDevice.payload)
            identity = self.module.installed_identity(FixtureDevice(), apk, output)
            self.assertEqual(identity["installed_sha256"], self.module.sha(apk))
            apk.write_bytes(b"different candidate")
            with self.assertRaisesRegex(RuntimeError, "SHA256 differs"):
                self.module.installed_identity(FixtureDevice(), apk, output)
            saved = json.loads((output / "installed-identity.json").read_text())
            self.assertNotEqual(saved["candidate_sha256"], saved["installed_sha256"])

    def test_am_start_ok_without_process_fails(self):
        with self.assertRaisesRegex(RuntimeError, "process"):
            self.module.activity_health("Status: ok", "", "", "", "")

    def test_process_without_native_health_fails(self):
        with self.assertRaisesRegex(RuntimeError, "native"):
            self.module.activity_health("Status: ok", "123", "123", "isForeground=true", "")

    def test_restart_during_observation_fails(self):
        with self.assertRaisesRegex(RuntimeError, "process"):
            self.module.activity_health("Status: ok", "123", "124", "isForeground=true", "Receiver listening on port 7000")

    def test_service_and_native_health_required(self):
        self.module.activity_health("Status: ok", "123", "123", "isForeground=true", "Receiver listening on port 7000")
        with self.assertRaisesRegex(RuntimeError, "foreground"):
            self.module.activity_health("Status: ok", "123", "123", "", "Receiver listening on port 7000")

    def test_unrelated_crash_not_attributed_to_app(self):
        raw = "01-01 12:00:00.000  50 50 E AndroidRuntime: FATAL EXCEPTION: main\n01-01 12:00:00.001 50 50 E AndroidRuntime: Process: other.app, PID: 50\n"
        self.assertEqual(self.module.app_crashes(raw), "")

    def test_app_java_and_native_crash_blocks_retained(self):
        raw = "01-01 12:00:00.000 50 50 E AndroidRuntime: FATAL EXCEPTION: main\n01-01 12:00:00.001 50 50 E AndroidRuntime: Process: " + PACKAGE + ", PID: 50\n01-01 12:00:00.002 50 50 E AndroidRuntime: java.lang.UnsupportedOperationException\n"
        self.assertIn("UnsupportedOperationException", self.module.app_crashes(raw))
        native = "01-01 12:00:01.000 60 60 F DEBUG: *** *** *** ***\n01-01 12:00:01.001 60 60 F DEBUG: Cmdline: " + PACKAGE + "\n01-01 12:00:01.002 60 60 F DEBUG: signal 11 (SIGSEGV)\n"
        self.assertIn("SIGSEGV", self.module.app_crashes(native))

    def test_only_exact_app_process_logs_count_as_health(self):
        system = "1730000000.100  100 101 I ActivityManager: Start proc 123:" + PACKAGE + "/u0a1 for added application\n1730000000.200 100 101 I ActivityManager: Start proc 124:" + PACKAGE + ".other/u0a2 for added application\n"
        pids = self.module.app_pids(system)
        self.assertEqual(pids, {"123"})
        main = "1730000001.001  123 125 I Wormhole: Receiver listening on port 7000\n1730000001.002 124 126 I Wormhole: unrelated native listener\n"
        own = self.module.logs_for_pids(main, pids)
        self.assertIn("Receiver listening", own)
        self.assertNotIn("unrelated", own)

    def test_fresh_evidence_ignores_prior_crashes(self):
        from decimal import Decimal
        logs = "1730000000.001  123 125 E AndroidRuntime: old\n1730000001.002 123 125 E AndroidRuntime: fresh\n"
        self.assertNotIn("old", self.module.fresh(logs, Decimal("1730000001.000")))
        self.assertIn("fresh", self.module.fresh(logs, Decimal("1730000001.000")))

    def test_instrumentation_zero_tests_or_failure_is_not_acceptance(self):
        for output in ("INSTRUMENTATION_CODE: -1", "OK (0 tests)", "FAILURES!!!\nTests run: 1", "INSTRUMENTATION_FAILED: denied"):
            with self.subTest(output=output), self.assertRaises(RuntimeError):
                self.module.instrumentation_health(output)
        self.module.instrumentation_health("OK (1 test)\nINSTRUMENTATION_CODE: -1")


if __name__ == "__main__":
    unittest.main()
