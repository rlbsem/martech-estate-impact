"""Run a fresh synthetic estate locally. No existing database or external estate is changed."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from estate_change.demo import execute
from estate_change.runtime import Runtime
from estate_change.service import decide

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--test", action="store_true")
    p.add_argument("--port", type=int, default=8594)
    a = p.parse_args()
    with Runtime(a.workspace) as runtime:
        if a.test:
            for suite in ["tests", "change_tests"]:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        suite,
                        "-q",
                        "--tb=short",
                        "--basetemp",
                        str(runtime.path / (suite + "-temp")),
                    ],
                    cwd=ROOT,
                    check=True,
                )
            return
        execute(ROOT)
        reviewer = runtime.identity("group_reviewer", ["atlas", "boreal", "cinder", "parent"])
        admin = os.environ["ESTATE_DATABASE_URL"]
        os.environ["ESTATE_DATABASE_URL"] = reviewer
        decide(
            "reassignment",
            1,
            "ACCEPT",
            "Synthetic scoped review: unchanged service path and complete coverage",
        )
        decide(
            "retirement", 1, "REJECT", "Campaign dependency and seasonal evidence remain unresolved"
        )
        os.environ["ESTATE_DATABASE_URL"] = admin
        runtime.identity("change_console", console=True)
        print(
            json.dumps(
                {"console": f"http://127.0.0.1:{a.port}/", "synthetic": True, "read_only": True}
            ),
            flush=True,
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "estate_change.server",
                "--config",
                str(runtime.path / "change_console.json"),
                "--port",
                str(a.port),
            ],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
