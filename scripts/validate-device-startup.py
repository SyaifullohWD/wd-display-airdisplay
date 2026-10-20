#!/usr/bin/env python3
"""Explicit-target startup check. Never installs, clears logs/data, or changes settings.

Requires the exact application APK and an already-installed matching androidTest
APK. Service-first instrumentation starts the non-exported service legitimately;
its temporary shell identity is limited to that test and is not a device setting.
Not a LAN, hardware-decoder, desktop, or sustained-session acceptance test.
"""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

# Install identity (gradle applicationId).
PACKAGE = "org.wddisplay.receiver"
# Code package (gradle namespace): activity and instrumentation class names live here,
# which is deliberately different from the application id.
CLASS_PREFIX = "org.pocketairdisplay.receiver"
RUNNER = PACKAGE + ".test/androidx.test.runner.AndroidJUnitRunner"
SERVICE_TEST = CLASS_PREFIX + ".ServiceStartupTest#serviceFirstStartsWithApplicationContextAndStopsCleanly"


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--serial")
    target.add_argument("--transport-id", type=int)
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--test-apk", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="new evidence directory; must not exist")
    parser.add_argument("--adb", default=os.environ.get("ADB", "adb"))
    return parser.parse_args(argv)


def selector(args):
    return ["-s", args.serial] if args.serial else ["-t", str(args.transport_id)]


def activity_health(launch, first_pid, final_pid, service, logs):
    if "Status: ok" not in launch:
        raise RuntimeError("cold Activity launch failed")
    if not first_pid.strip().isdigit() or first_pid.strip() != final_pid.strip():
        raise RuntimeError("app process absent/restarted during startup observation")
    if "isForeground=true" not in service:
        raise RuntimeError("receiver foreground service absent")
    if "Receiver listening on port 7000" not in logs:
        raise RuntimeError("no fresh app native listening health evidence")


def instrumentation_health(output):
    if (not re.search(r"\bOK \(1 test\)", output)
            or "INSTRUMENTATION_CODE: -1" not in output
            or any(marker in output for marker in ("FAILURES", "INSTRUMENTATION_FAILED", "shortMsg=", "Process crashed"))):
        raise RuntimeError("service-first instrumentation failed, skipped, or ran a non-singleton test selection")


def app_crashes(raw):
    """Retain only crash writer groups identifying this package (Java/native)."""
    groups = {}
    for line in raw.splitlines():
        match = re.search(r"\s(\d+)\s+(\d+)\s+[VDIWEF]\s+([^:]+):", line)
        if match:
            key = (match[1], match[3].strip())
            groups.setdefault(key, []).append(line)
    selected = []
    package = re.compile(r"\b(?:Process:|Cmdline:|>>>)[ \t]*" + re.escape(PACKAGE) + r"(?=[:,\s]|$)")
    for lines in groups.values():
        if any(package.search(line) for line in lines):
            selected.extend(lines)
    return "\n".join(selected) + ("\n" if selected else "")


def fresh(raw, since):
    result = []
    for line in raw.splitlines():
        match = re.match(r"\s*(\d+\.\d+)\s", line)
        if match and Decimal(match[1]) >= since:
            result.append(line)
    return "\n".join(result) + ("\n" if result else "")


def app_pids(system_logs):
    return set(re.findall(r"\bStart proc (\d+):" + re.escape(PACKAGE) + r"/", system_logs))


def logs_for_pids(raw, pids):
    lines = []
    for line in raw.splitlines():
        match = re.match(r"\s*\d+\.\d+\s+(\d+)\s", line)
        if match and match[1] in pids:
            lines.append(line)
    return "\n".join(lines) + ("\n" if lines else "")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Device:
    def __init__(self, args):
        self.prefix = [args.adb, *selector(args)]
        self.output = args.output
        self.commands = []

    def run(self, *command, check=True):
        argv = [*self.prefix, *map(str, command)]
        self.commands.append(argv)
        # logcat can contain malformed sender/OEM bytes. Escape, never drop them;
        # ASCII timestamps/PIDs/crash markers remain available for strict checks.
        result = subprocess.run(argv, text=True, encoding="utf-8", errors="backslashreplace",
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        if check and result.returncode:
            raise RuntimeError("adb command failed: " + " ".join(command) + "\n" + result.stdout)
        return result.stdout

    def stamp(self):
        value = self.run("shell", "date", "+%s.%N").strip()
        try:
            result = Decimal(value)
            if not result.is_finite():
                raise InvalidOperation
            return result
        except InvalidOperation:
            raise RuntimeError("device date did not provide epoch nanoseconds; cannot prove fresh logs")

    def logs(self, buffer, since):
        # Never -c: inspect in memory, persist only fresh app-owned evidence.
        return fresh(self.run("logcat", "-b", buffer, "-d", "-v", "threadtime", "-v", "epoch"), since)

    def crashes(self, phase, since):
        app = app_crashes(self.logs("crash", since))
        (self.output / (phase + "-crash-app-only.log")).write_text(app)
        if app:
            raise RuntimeError("fresh app crash in " + phase)


def installed_identity(device, apk, output, package=PACKAGE, stem="installed"):
    paths = device.run("shell", "pm", "path", package)
    (output / (stem + "-paths.txt")).write_text(paths)
    entries = [line[len("package:"):].strip() for line in paths.splitlines() if line.startswith("package:")]
    if len(entries) != 1 or not entries[0].endswith("/base.apk"):
        raise RuntimeError("requires one installed base APK, not missing/split package")
    with tempfile.TemporaryDirectory(prefix="pad-installed-sha-") as directory:
        installed = Path(directory) / "base.apk"
        device.run("pull", entries[0], str(installed))
        identity = {"candidate_sha256": sha(apk), "installed_sha256": sha(installed), "installed_path": entries[0]}
    (output / (stem + "-identity.json")).write_text(json.dumps(identity, indent=2) + "\n")
    if identity["candidate_sha256"] != identity["installed_sha256"]:
        raise RuntimeError("installed SHA256 differs from candidate APK; refusing launch")
    return identity


def validate(args):
    if not args.apk.is_file() or not args.test_apk.is_file():
        raise ValueError("candidate application/test APK is missing")
    args.output.mkdir(parents=True, exist_ok=False)
    device = Device(args)
    report = {"target": selector(args), "accepted": False, "scope": "startup only, not AirPlay/device feature acceptance"}
    try:
        if device.run("get-state").strip() != "device":
            raise RuntimeError("selected target not ready")
        report.update(installed_identity(device, args.apk, args.output))
        report["instrumentation_identity"] = installed_identity(
            device, args.test_apk, args.output, package=PACKAGE + ".test", stem="installed-test")
        (args.output / "package-before.txt").write_text(device.run("shell", "dumpsys", "package", PACKAGE))
        device.run("shell", "am", "force-stop", PACKAGE)
        start = device.stamp()
        try:
            launch = device.run("shell", "am", "start", "-W", "-n", PACKAGE + "/" + CLASS_PREFIX + ".MainActivity")
            (args.output / "activity-launch.txt").write_text(launch)
            time.sleep(3)
            first = device.run("shell", "pidof", PACKAGE, check=False).strip()
            time.sleep(5)
            final = device.run("shell", "pidof", PACKAGE, check=False).strip()
            service = device.run("shell", "dumpsys", "activity", "services", PACKAGE + "/" + CLASS_PREFIX + ".WormholeService")
            (args.output / "activity-service.txt").write_text(service)
            logs = device.logs("main", start)
            # Only this exact process's main logs, never unrelated app messages.
            own = "\n".join(line for line in logs.splitlines() if re.match(r"\s*\d+\.\d+\s+" + re.escape(final or "-1") + r"\s", line))
            (args.output / "activity-health-app-only.log").write_text(own + "\n")
            report["activity_pids"] = [first, final]
            activity_health(launch, first, final, service, own)
        finally:
            device.crashes("activity", start)
        report["activity_cold_start"] = "PASS"

        device.run("shell", "am", "force-stop", PACKAGE)
        start = device.stamp()
        try:
            output = device.run("shell", "am", "instrument", "-w", "-r", "-e", "class", SERVICE_TEST, RUNNER)
            (args.output / "service-first-instrumentation.txt").write_text(output)
            instrumentation_health(output)
            # Observe post-test teardown as well, not just am-instrument's exit.
            time.sleep(3)
            # This test deliberately stops the service after checking both states.
            system = device.logs("system", start)
            pids = app_pids(system)
            (args.output / "service-first-processes.txt").write_text(
                "\n".join(line for line in system.splitlines()
                          if re.search(r"\bStart proc \d+:" + re.escape(PACKAGE) + r"/", line)) + "\n")
            if not pids:
                raise RuntimeError("cannot attribute service-first native logs to fresh app process")
            own = logs_for_pids(device.logs("main", start), pids)
            (args.output / "service-first-health-app-only.log").write_text(own + "\n")
            if "Receiver listening on port 7000" not in own:
                raise RuntimeError("service-first test lacks fresh native listener health")
        finally:
            device.crashes("service-first", start)
        report["service_first"] = "PASS"
        report["accepted"] = True
    except BaseException as error:
        report["error"] = str(error)
        raise
    finally:
        (args.output / "commands.json").write_text(json.dumps(device.commands, indent=2) + "\n")
        (args.output / "RESULT.json").write_text(json.dumps(report, indent=2) + "\n")
    print("STARTUP PASS (exact installed SHA recorded; not end-to-end AirPlay acceptance)")


if __name__ == "__main__":
    try:
        validate(arguments())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("STARTUP FAILED: " + str(error), file=sys.stderr)
        sys.exit(1)
