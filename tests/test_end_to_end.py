import json
from pathlib import Path

from estate_impact.demo import run
from conftest import ROOT


def test_real_postgres_demo_deterministic(database, tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    summary = run(ROOT, first)
    repeated = run(ROOT, second)
    assert summary == repeated
    assert summary["snapshot_unchanged"]
    assert summary["counts"]["systems"] == 24
    assert summary["counts"]["integrations"] == 40
    assert (
        summary["results"]["replace-webinar-revised"]["disposition"]
        == "NO_IDENTIFIED_BLOCKERS_WITHIN_REVIEWED_SCOPE"
    )
    for file in first.iterdir():
        assert file.read_bytes() == (second / file.name).read_bytes()
    result = json.loads((first / "retire-work-manager-assessment.json").read_text())
    assert result["sequence"]["cycle_members"] == ["approve-cutover", "remove-legacy"]
    assert len(list(Path(first).glob("*.mmd"))) == 4
