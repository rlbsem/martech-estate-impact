"""Fail closed on stale execution source hashes, altered originals or package drift."""

import json

from change_repository import ROOT, inventory, links, preserve, scan, sha, source_hashes


def main():
    out = ROOT / "docs/evidence/change-assurance/run-01"
    verification = json.loads((out / "verification.json").read_bytes())
    assert verification["status"] == "passed"
    assert verification["source_sha256"] == source_hashes(), "recorded execution source mismatch"
    browser = json.loads((out / "browser/browser.json").read_bytes())
    assert browser["source_sha256"] == source_hashes(), "screenshot source mismatch"
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
