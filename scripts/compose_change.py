"""Finite trusted synthetic seed job. Only the reader credential is shared with the console."""

import json
import os
from pathlib import Path

from estate_change.demo import execute
from estate_change.runtime import Runtime
from estate_change.service import decide

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.environ["ESTATE_DATABASE_URL"] = json.loads(Path("/private/admin.json").read_bytes())["dsn"]
    runtime = Runtime("/shared")
    runtime.dsn = os.environ["ESTATE_DATABASE_URL"]
    execute(ROOT)
    admin = os.environ["ESTATE_DATABASE_URL"]
    reviewer = runtime.identity(
        "group_reviewer", ["atlas", "boreal", "cinder", "parent"], write=False
    )
    os.environ["ESTATE_DATABASE_URL"] = reviewer
    decide(
        "reassignment",
        1,
        "ACCEPT",
        "Synthetic scoped architecture review: unchanged service paths and complete coverage",
    )
    decide(
        "retirement",
        1,
        "REJECT",
        "Critical campaign dependency and seasonal evidence remain unresolved",
    )
    os.environ["ESTATE_DATABASE_URL"] = admin
    runtime.identity("change_console", console=True)
    assert [p.name for p in Path("/shared").iterdir()] == ["change_console.json"]
    print("Synthetic estate published; restricted reader configuration shared.")


if __name__ == "__main__":
    main()
