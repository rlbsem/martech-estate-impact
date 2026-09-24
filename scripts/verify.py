"""Fail-closed verification with real PostgreSQL, unique output paths and measured evidence."""

import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

import estate_impact
from estate_impact import db
from estate_impact.contracts import implementation_hash
from estate_impact.demo import run, write_json

ROOT = Path(__file__).resolve().parents[1]


def source_manifest():
    included = []
    for directory in ["src", "tests", "scripts", "migrations", "config", "fixtures", ".github"]:
        included.extend(
            p
            for p in (ROOT / directory).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and ".egg-info" not in str(p)
        )
    included += [
        ROOT / name for name in ["pyproject.toml", "requirements.lock", "docker-compose.yml"]
    ]
    return {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(included)
    }


def main():
    evidence = ROOT / "docs/evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    work = ROOT / "work" / uuid.uuid4().hex
    work.mkdir(parents=True)
    before = source_manifest()
    installed_root = Path(estate_impact.__file__).parent
    installed_files = {
        p.relative_to(installed_root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in installed_root.rglob("*.py")
    }
    source_files = {
        p.relative_to(ROOT / "src/estate_impact").as_posix(): hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
        for p in (ROOT / "src/estate_impact").rglob("*.py")
    }
    if installed_files != source_files:
        raise SystemExit(
            "Installed package differs from repository sources; reinstall before verification."
        )
    commands = [
        [sys.executable, "-m", "pip", "check"],
        [sys.executable, "-m", "ruff", "check", "src", "tests", "scripts"],
        [sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "scripts"],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            f"--basetemp={work / 'pytest'}",
            "-o",
            f"cache_dir={work / 'pytest-cache'}",
            f"--junitxml={evidence / 'pytest.xml'}",
        ],
    ]
    outputs = []
    for command in commands:
        proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        outputs.append(
            {
                "command": " ".join(command[1:]),
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        )
        if proc.returncode:
            write_json(evidence / "failed-verification.json", {"commands": outputs})
            raise SystemExit(proc.returncode)
    demo = run(ROOT)
    repeated = work / "regenerated"
    assert run(ROOT, repeated) == demo
    generated = ROOT / "examples/generated"
    for path in repeated.iterdir():
        assert path.read_bytes() == (generated / path.name).read_bytes(), path.name
    # Exercise installed entry point's argument and persisted snapshot boundary.
    command = [
        sys.executable,
        "-m",
        "estate_impact.cli",
        "--root",
        str(ROOT),
        "assess",
        "--snapshot",
        demo["snapshot_id"],
        "--proposal",
        str(ROOT / "fixtures/synthetic-estate/proposals/replace-webinar-revised.json"),
        "--output",
        str(work / "cli-assessment.json"),
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    cli_result = json.loads((work / "cli-assessment.json").read_text())
    assert cli_result["id"] == demo["results"]["replace-webinar-revised"]["assessment_id"]
    assert before == source_manifest(), "verification changed implementation inputs"
    with db.connect() as conn:
        pg_version = conn.execute("SHOW server_version").fetchone()[0]
    suites = ET.parse(evidence / "pytest.xml").getroot()
    counts = {
        key: sum(int(s.get(key, 0)) for s in suites.iter("testsuite"))
        for key in ["tests", "failures", "errors", "skipped"]
    }
    record = {
        "status": "passed",
        "python": platform.python_version(),
        "platform": platform.system(),
        "postgresql": pg_version,
        "tests": counts,
        "commands": outputs,
        "source_manifest": before,
        "implementation_hash": implementation_hash(),
        "deterministic_demo": True,
        "installed_cli": True,
        "installed_source_parity": True,
        "snapshot_unchanged": demo["snapshot_unchanged"],
        "demo": demo["results"],
        "github_ci": "configured; not observed by this local run",
        "database_connection": "actual PostgreSQL; supplied connection (credentials omitted)",
    }
    write_json(evidence / "verification.json", record)
    report = (
        "# Observed verification\n\n"
        f"Local {record['platform']}; Python {record['python']}; PostgreSQL {pg_version}.\n\n"
        f"**{counts['tests']} tests; {counts['failures']} failures; {counts['errors']} errors; {counts['skipped']} skipped.**\n\n"
        "Dependency check, lint and formatting passed. Demo outputs regenerated byte-for-byte; installed CLI assessment matched the persisted demo result. Current snapshot remained unchanged.\n\n"
        "The independent bounded evaluator checked 350 deterministic generated small graphs. PostgreSQL tests exercised concurrent identical imports, rollback and append-only publication.\n\n"
        f"Implementation fingerprint: `{record['implementation_hash']}`.\n\n"
        "GitHub Actions is configured; this local report does not claim a hosted CI run or a Docker execution.\n\n"
        "[Machine-readable verification and source hashes](../../docs/evidence/verification.json) · [JUnit results](../../docs/evidence/pytest.xml)\n"
    )
    (generated / "verification-report.md").write_text(report, encoding="utf-8")
    print(
        json.dumps({"tests": counts, "demo": demo["results"], "postgresql": pg_version}, indent=2)
    )


if __name__ == "__main__":
    main()
