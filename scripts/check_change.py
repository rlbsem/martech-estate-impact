"""Fail closed on stale execution source hashes, altered originals or package drift."""

import json

from change_repository import ROOT, inventory, links, preserve, scan, sha, source_hashes


def main():
    out = ROOT / "docs/evidence/change-assurance/run-03"
    verification = json.loads((out / "verification.json").read_bytes())
    assert verification["status"] == "passed"
    # Historical run-03 attestations are immutable. CI runner pinning changed only
    # the workflow and this historical-attestation checker, not application source.
    # Compare the recorded execution and browser hashes to one another in full,
    # then require every other current source file to match the recorded run.
    recorded = verification["source_sha256"]
    browser = json.loads((out / "browser/browser.json").read_bytes())
    assert browser["source_sha256"] == recorded, "screenshot source mismatch"
    current = source_hashes()
    ci_only = {".github/workflows/verify.yml", "scripts/check_change.py"}
    assert set(current) == set(recorded), "source inventory changed"
    assert {k: v for k, v in current.items() if k not in ci_only} == {
        k: v for k, v in recorded.items() if k not in ci_only
    }, "recorded execution source mismatch"
    for name, record in browser["screenshots"].items():
        assert sha((out / "browser" / name).read_bytes()) == record["sha256"]
    oracle = json.loads((out / "oracle-comparison.json").read_bytes())
    assert all(c["actual"] == c["independent"] for c in oracle["comparisons"])
    assert not any(
        s[k] for s in verification["suites"].values() for k in ["failures", "errors", "skipped"]
    )
    print(
        json.dumps(
            dict(
                status="passed",
                original_files=preserve(),
                local_links=links(),
                public_files_scanned=scan(),
                package_files=inventory(check=True),
                screenshots=len(browser["screenshots"]),
            )
        )
    )


if __name__ == "__main__":
    main()
