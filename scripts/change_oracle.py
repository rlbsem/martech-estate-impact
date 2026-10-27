"""Independent bounded recursive proof, including finite typed interface foundations.

The historical recursive oracle is imported directly, unchanged. This adapter never
calls the production evaluator and never uses its computed node states.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "preserved_oracle", ROOT / "tests/oracle/reference_evaluator.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def reference(facts):
    systems = {
        f["subject"]: f["value"]["lifecycle"] if f["state"] == "SUPPORTED" else None
        for f in facts.values()
        if f["kind"] == "system"
    }
    definitions = {}
    systems["__false"] = "retired"

    def foundation(state):
        return "sys:__false" if state == "F" else "sys:__true" if state == "T" else "sys:__unknown"

    systems["__true"] = "active"
    for f in facts.values():
        if f["kind"] != "integration":
            continue
        value = f["value"]
        states = (
            []
            if value is None
            else [systems.get(value[k]) for k in ["source", "destination", "runtime"]]
        )
        state = (
            "?"
            if not states
            else "F"
            if any(s in {"retired", "proposed"} for s in states)
            else "?"
            if None in states
            else "T"
        )
        systems["__int/" + f["subject"]] = {"T": "active", "F": "retired", "?": None}[state]
    for f in facts.values():
        if f["kind"] != "requirement":
            continue
        children = []
        if f["state"] != "SUPPORTED":
            definitions[f["subject"]] = ("ALL", ["sys:__unknown"])
            continue
        for key in f["value"]["inputs"]:
            edge = facts.get(key)
            if edge is None or edge["state"] != "SUPPORTED":
                children.append("sys:__unknown")
                continue
            v = edge["value"]
            if v["optional"]:
                continue
            provider = (
                v["provider"].replace("int:", "sys:__int/", 1)
                if v["provider"].startswith("int:")
                else v["provider"]
            )
            if not v["qualified"]:
                provider = "sys:__false"
            contract = v.get("contract")
            if contract:
                offered = facts.get("interface:" + v["provider"].split(":", 1)[1])
                state = (
                    "?"
                    if not offered or offered["state"] != "SUPPORTED"
                    else "F"
                    if any(
                        set(contract.get(k, [])) - set(offered["value"].get(k, []))
                        for k in ["events", "fields", "keys"]
                    )
                    else "T"
                )
                helper = "__edge/" + edge["subject"]
                definitions[helper] = ("ALL", [provider, foundation(state)])
                provider = "req:" + helper
            children.append(provider)
        definitions[f["subject"]] = (f["value"]["mode"], children)
    results = module.reference(definitions, systems)
    return {
        f["subject"]: results[f["subject"]] for f in facts.values() if f["kind"] == "requirement"
    }
