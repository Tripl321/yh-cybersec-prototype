#!/usr/bin/env python3
"""Accept only the two verified pre-migration PRO-45 test failures."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FAILURES = {
    "tests/test_pro45_key_generation.py::test_pro45_uses_stm32_rng",
    "tests/test_pro45_key_generation.py::test_pro45_rng_registers_documented",
}


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "--tb=no"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    sys.stdout.write(output)

    failures = set(re.findall(r"^FAILED (\S+)", output, flags=re.MULTILINE))
    has_collection_error = bool(re.search(r"^ERROR ", output, flags=re.MULTILINE))

    if result.returncode == 1 and failures == EXPECTED_FAILURES and not has_collection_error:
        print("Contact-auth test baseline: PASS (two known PRO-45 failures only)")
        return 0

    print("Contact-auth test baseline: FAIL")
    print(f"Expected failures: {sorted(EXPECTED_FAILURES)}")
    print(f"Observed failures: {sorted(failures)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
