import itertools
import random

import pytest

from estate_impact.requirements import combine, evaluate
from conftest import fact, graph
from oracle.reference_evaluator import reference


@pytest.mark.parametrize("mode", ["ALL", "ANY"])
def test_complete_three_state_truth_tables(mode):
    for states in itertools.product(["SUPPORTED", "UNSUPPORTED", "UNKNOWN"], repeat=3):
        expected = (
            (
                "UNSUPPORTED"
                if "UNSUPPORTED" in states
                else "UNKNOWN"
                if "UNKNOWN" in states
                else "SUPPORTED"
            )
            if mode == "ALL"
            else (
                "SUPPORTED"
                if "SUPPORTED" in states
                else "UNKNOWN"
                if "UNKNOWN" in states
                else "UNSUPPORTED"
            )
        )
        assert combine(mode, states) == expected
    assert combine(mode, []) == "UNKNOWN"


def test_independent_bounded_oracle():
    rng = random.Random(91024)
    systems = {"on": "active", "off": "retired"}
    names = ["a", "b", "c", "d", "e"]
    providers = ["sys:on", "sys:off", "sys:absent"] + ["req:" + n for n in names]
    for _ in range(350):
        definitions = {
            n: (rng.choice(["ALL", "ANY"]), rng.sample(providers, rng.randrange(4))) for n in names
        }
        production = evaluate(graph(definitions, systems))["requirements"]
        assert {k: v["state"] for k, v in production.items()} == reference(definitions, systems)


def test_unseeded_cycle_unknown_and_seeded_alternative_supported():
    definitions = {"a": ("ALL", ["req:b"]), "b": ("ANY", ["req:a"])}
    assert all(
        r["state"] == "UNKNOWN" for r in evaluate(graph(definitions, {}))["requirements"].values()
    )
    definitions["b"][1].append("sys:seed")
    assert all(
        r["state"] == "SUPPORTED"
        for r in evaluate(graph(definitions, {"seed": "active"}))["requirements"].values()
    )


def test_qualified_alternative_and_optional_dependency():
    facts = graph({"r": ("ANY", ["sys:off", "sys:on"])}, {"off": "retired", "on": "active"})
    alternative = facts["dependency:r:1"]["value"]
    alternative["qualified"] = False
    assert evaluate(facts)["requirements"]["r"]["state"] == "UNSUPPORTED"
    alternative["qualified"] = True
    assert evaluate(facts)["requirements"]["r"]["state"] == "SUPPORTED"
    facts["requirement:r"]["value"]["mode"] = "ALL"
    facts["dependency:r:0"]["value"]["optional"] = True
    assert evaluate(facts)["requirements"]["r"]["state"] == "SUPPORTED"


def test_data_flow_cannot_imply_business_failure():
    facts = graph({"r": ("ALL", ["sys:on"])}, {"off": "retired", "on": "active"})
    facts["integration:x"] = fact(
        "integration", "x", dict(source="off", destination="on", runtime="on")
    )
    result = evaluate(facts)
    assert result["states"]["int:x"] == "UNSUPPORTED"
    assert result["requirements"]["r"]["state"] == "SUPPORTED"


def test_removing_provider_evidence_does_not_improve_support():
    facts = graph({"r": ("ALL", ["sys:on"])}, {"on": "active"})
    assert evaluate(facts)["requirements"]["r"]["state"] == "SUPPORTED"
    del facts["system:on"]
    assert evaluate(facts)["requirements"]["r"]["state"] == "UNKNOWN"
