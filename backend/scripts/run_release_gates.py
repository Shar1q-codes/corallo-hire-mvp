import os
import subprocess
import sys


def _run(command: list[str]) -> int:
    print(f"Running: {' '.join(command)}")
    proc = subprocess.run(command, check=False)
    return proc.returncode


def main() -> int:
    validator_path = "backend/tests/validators" if os.path.isdir("backend/tests/validators") else "tests/validators"
    commands: list[list[str]] = [
        [sys.executable, "-m", "pytest", "-q", validator_path, "backend/tests/kill_tests"],
    ]

    if os.getenv("LIVE_TESTS", "").lower() == "true":
        commands.append([sys.executable, "-m", "pytest", "-q", "backend/tests/kill_tests/test_live_run_drift_guard.py"])

    failures = 0
    for command in commands:
        code = _run(command)
        if code != 0:
            failures += 1

    if failures:
        print(f"Release gates failed: {failures} command(s) failed.")
        return 1

    print("Release gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
