"""Fresh native PostgreSQL, independent oracle, original CLI and actual browser acceptance."""

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from urllib.request import urlopen
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import psycopg

from estate_impact.demo import run as original_demo
from estate_impact.impact import scenario
from estate_impact.requirements import evaluate
from estate_change.demo import execute
from estate_change.runtime import Runtime, free_port
from estate_change.service import decide, view

from browser_change import check as browser_check
from change_oracle import reference
from change_repository import ROOT, inventory, links, preserve, save, scan, sha, source_hashes


def command(args, log):
    with log.open("w", encoding="utf-8") as f:
        r = subprocess.run([sys.executable, *args], cwd=ROOT, stdout=f, stderr=f, timeout=600)
    if r.returncode:
        raise RuntimeError("verification failed; inspect private " + log.name)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--check-package", action="store_true")
    a = p.parse_args()
    work, out = a.workspace.resolve(), a.output.resolve()
    if work.exists() or out.exists():
        raise ValueError("fresh workspace and output required")
    work.mkdir(parents=True)
    out.mkdir(parents=True)
    before = source_hashes()
    started = datetime.now(UTC).isoformat()
    original_count = preserve()
    public_files = scan()
    if a.check_package:
        inventory(check=True)
    for args, name in [
        (["-m", "pip", "check"], "dependencies"),
        (["-m", "ruff", "check", "src", "tests", "change_tests", "scripts"], "lint"),
        (["-m", "ruff", "format", "--check", "src", "tests", "change_tests", "scripts"], "format"),
    ]:
        command(args, work / (name + ".log"))
    suites = {}
    with Runtime(work / "native") as runtime:
        for folder in ["tests", "change_tests"]:
            xml = work / (folder + ".xml")
            command(
                [
                    "-m",
                    "pytest",
                    folder,
                    "-q",
                    "--basetemp",
                    str(work / (folder + "-temp")),
                    "--junitxml",
                    str(xml),
                ],
                work / (folder + ".log"),
            )
            tree = ET.parse(xml).getroot()
            totals = {
                k: sum(int(s.get(k, 0)) for s in tree.iter("testsuite"))
                for k in ["tests", "errors", "failures", "skipped"]
            }
            assert not any(totals[k] for k in ["errors", "failures", "skipped"])
            totals["cases"] = [
                n.attrib["classname"] + "." + n.attrib["name"] for n in tree.iter("testcase")
            ]
            suites[folder] = totals
        original = original_demo(ROOT, out / "original-demo")
        assert original_demo(ROOT, work / "original-repeat") == original
        for file in (out / "original-demo").iterdir():
            assert file.read_bytes() == (work / "original-repeat" / file.name).read_bytes()
        execute(ROOT)
        admin = os.environ["ESTATE_DATABASE_URL"]
        reviewer = runtime.identity("group_reviewer", ["atlas", "boreal", "cinder", "parent"])
        os.environ["ESTATE_DATABASE_URL"] = reviewer
        decide(
            "reassignment",
            1,
            "ACCEPT",
            "Synthetic scoped architecture review: unchanged service dependencies and complete coverage",
        )
        decide(
            "retirement",
            1,
            "REJECT",
            "Campaign dependencies, owner conflict and seasonal evidence remain unresolved",
        )
        os.environ["ESTATE_DATABASE_URL"] = admin
        state = view()
        comparisons = []
        for v in [dict(id="baseline", revision=0, proposal=None), *state["versions"]]:
            facts = (
                scenario(state["snapshot"], v["proposal"])[0]
                if v["proposal"]
                else state["snapshot"]["facts"]
            )
            actual = {k: r["state"] for k, r in evaluate(facts)["requirements"].items()}
            expected = reference(facts)
            assert actual == expected
            comparisons.append(
                dict(proposal=v["id"], revision=v["revision"], actual=actual, independent=expected)
            )
        save(
            out / "oracle-comparison.json",
            dict(
                status="passed",
                comparisons=comparisons,
                requirements_compared=sum(len(c["actual"]) for c in comparisons),
                method="Preserved recursive proof oracle with separate typed-foundation adapter; no production state reuse",
            ),
        )
        # Persisted JSON is the same data the restricted console reads. No DSN or config is exported.
        save(out / "estate-record.json", state)
        reader = runtime.identity("change_console", console=True)
        with psycopg.connect(reader) as c:
            c.execute("SET TRANSACTION READ ONLY")
            pg = c.execute("SHOW server_version").fetchone()[0]
            assert c.execute("SELECT count(*) FROM ca_version").fetchone()[0] == len(
                state["versions"]
            )
            assert not c.execute(
                "SELECT has_table_privilege(current_user,'ca_version','INSERT')"
            ).fetchone()[0]
        port = free_port()
        url = f"http://127.0.0.1:{port}/"
        with (work / "server-private.log").open("w") as log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "estate_change.server",
                    "--config",
                    str(runtime.path / "change_console.json"),
                    "--port",
                    str(port),
                ],
                cwd=ROOT,
                stdout=log,
                stderr=log,
            )
            try:
                for _ in range(100):
                    try:
                        with urlopen(url, timeout=2) as response:
                            assert response.status == 200
                        break
                    except OSError:
                        if server.poll() is not None:
                            raise RuntimeError("read-only console failed to start")
                        time.sleep(0.1)
                else:
                    raise RuntimeError("console startup timeout")
                browser = browser_check(url, out / "browser")
            finally:
                server.terminate()
                server.wait(timeout=20)
    command(
        [
            "-m",
            "pip",
            "wheel",
            "--no-index",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(work / "wheels"),
            ".",
        ],
        work / "wheel.log",
    )
    wheel = next((work / "wheels").glob("*.whl"))
    members = {
        f.relative_to(ROOT / "src").as_posix(): sha(f.read_bytes())
        for f in (ROOT / "src").rglob("*")
        if f.is_file() and f.suffix in {".py", ".sql", ".html", ".css", ".js"}
    }
    with ZipFile(wheel) as archive:
        assert all(sha(archive.read(n)) == h for n, h in members.items())
    save(
        out / "wheel.json",
        dict(status="passed", wheel_sha256=sha(wheel.read_bytes()), members=members),
    )
    assert source_hashes() == before, "source changed during capture"
    assert preserve() == original_count
    record = dict(
        status="awaiting_final_integrity",
        started_at=started,
        completed_at=datetime.now(UTC).isoformat(),
        platform=platform.system(),
        python=platform.python_version(),
        postgresql=pg,
        suites=suites,
        source_sha256=before,
        original_files_unchanged=original_count,
        original_demo_deterministic=True,
        original_snapshot_unchanged=original["snapshot_unchanged"],
        oracle_requirements=sum(len(c["actual"]) for c in comparisons),
        browser_checks=len(browser["checks"]),
        accessibility_states=len(browser["accessibility"]),
        local_links=None,
        public_files_scanned=public_files,
        console_restricted_select_only=True,
        actual_owned_postgresql_stopped=True,
        boundary="Local native PostgreSQL, synthetic evidence, actual Chromium. This record makes no Docker, hosted CI or production deployment claim.",
    )
    save(out / "verification.json", record)
    # The final record is itself a linked artifact. Publish a non-passing intermediate
    # record before checking links, then attest success only after the complete tree exists.
    record["local_links"] = links()
    record["public_files_scanned"] = scan()
    record["status"] = "passed"
    save(out / "verification.json", record)
    print(
        json.dumps(
            {k: v for k, v in record.items() if k not in {"source_sha256", "suites"}}, indent=2
        )
    )


if __name__ == "__main__":
    main()
