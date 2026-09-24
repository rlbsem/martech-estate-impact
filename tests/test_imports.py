from copy import deepcopy
import json

import pytest

from estate_impact.importers import prepare
from estate_impact.identity import index_crosswalk
from estate_impact.demo import read
from conftest import ROOT


def setup():
    meta = read(ROOT / "config/sources.json")[0]
    crosswalk = index_crosswalk(read(ROOT / "config/crosswalk.json"))
    text = (ROOT / "fixtures/synthetic-estate/inventory.csv").read_text()
    return text, meta, crosswalk


def test_same_artifact_is_content_addressed():
    args = setup()
    a = prepare(*args)
    b = prepare(*args)
    assert a == b
    assert len(a[1]) == 56


@pytest.mark.parametrize(
    "field,value",
    [("parser", "yaml/v9"), ("source", ""), ("collected_at", "2026-09-24"), ("status", "silent")],
)
def test_invalid_metadata(field, value):
    text, meta, crosswalk = setup()
    meta[field] = value
    with pytest.raises(ValueError):
        prepare(text, meta, crosswalk)


def test_missing_identifier():
    text, meta, crosswalk = setup()
    text = text.replace("crm,Sales", ",Sales", 1)
    with pytest.raises(ValueError, match="external_id"):
        prepare(text, meta, crosswalk)


def test_ambiguous_identity_quarantined_not_fuzzy_merged():
    text, meta, crosswalk = setup()
    text = text.replace("crm,Sales", "campaign-work,Sales", 1)
    _, claims, quarantine = prepare(text, meta, crosswalk)
    assert len(quarantine) == 2
    assert not any(c["subject"] == "crm" for c in claims)


def test_collection_failure_is_retained_without_parsing():
    _, meta, crosswalk = setup()
    meta["status"] = "failed"
    artifact, claims, quarantine = prepare("NOT A VALID CSV", meta, crosswalk)
    assert artifact["status"] == "failed" and not claims and not quarantine


@pytest.mark.parametrize(
    "payload",
    [
        "{",
        '{"format":"orchestration/v99"}',
        json.dumps({"format": "orchestration/v1", "assertions": [{"kind": "untyped"}]}),
    ],
)
def test_bad_json_or_contract_is_rejected(payload):
    meta = deepcopy(read(ROOT / "config/sources.json")[1])
    with pytest.raises(ValueError):
        prepare(payload, meta, {})


@pytest.mark.parametrize("count", ["-1", "not-an-integer"])
def test_bad_execution_count(count):
    meta = next(s for s in read(ROOT / "config/sources.json") if s["source"] == "executions")
    text = f"integration,count,start,end\nx,{count},2026-09-15T00:00:00Z,2026-09-24T00:00:00Z\n"
    with pytest.raises(ValueError):
        prepare(text, meta, {})
