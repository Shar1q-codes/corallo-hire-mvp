import os
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class GateResult:
    name: str
    code: int


def _run(name: str, command: list[str]) -> GateResult:
    print(f"[gate] {name}: {' '.join(command)}")
    proc = subprocess.run(command, check=False)
    return GateResult(name=name, code=proc.returncode)


def main() -> int:
    results: list[GateResult] = []

    validator_path = "backend/tests/validators" if os.path.isdir("backend/tests/validators") else "tests/validators"
    results.append(
        _run(
            "unit_contract_gates",
            [sys.executable, "-m", "pytest", "-q", validator_path, "backend/tests/kill_tests"],
        )
    )

    if os.getenv("LIVE_DB_LEAKAGE_TESTS", "").lower() == "true":
        results.append(
            _run(
                "live_db_leakage",
                [sys.executable, "-m", "pytest", "-q", "backend/tests/leakage/test_db_rls_leakage_matrix.py"],
            )
        )

    if os.getenv("LIVE_API_TESTS", "").lower() == "true":
        results.append(
            _run(
                "live_api_leakage",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "backend/tests/leakage/test_api_cross_tenant_access.py",
                    "backend/tests/leakage/test_object_id_guessing.py",
                ],
            )
        )

    if os.getenv("LIVE_STORAGE_TESTS", "").lower() == "true":
        results.append(
            _run(
                "live_storage_isolation",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "backend/tests/storage_isolation/test_storage_path_enforcement.py",
                    "backend/tests/storage_isolation/test_signed_url_tenant_isolation.py",
                ],
            )
        )

    failed = [r for r in results if r.code != 0]

    print("\n=== Go/No-Go Report ===")
    for result in results:
        status = "PASS" if result.code == 0 else "FAIL"
        print(f"- {result.name}: {status}")

    if failed:
        print("Go/No-Go: FAIL")
        return 1

    print("Go/No-Go: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
