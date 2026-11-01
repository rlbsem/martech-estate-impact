"""Stable safe node identifiers; encode every non-alphanumeric label character."""

import hashlib

from estate_impact.topology import data_flows


def label(text):
    return "".join(c if c.isalnum() or c in " -_:./" else f"#{ord(c)};" for c in str(text))


def node(identity):
    return "n" + hashlib.sha256(identity.encode()).hexdigest()[:16]


def topology(facts, title, systems=None, max_edges=100):
    all_edges = data_flows(facts)
    edges = [
        e
        for e in all_edges
        if systems is None or e["source"] in systems and e["destination"] in systems
    ]
    selected = edges[:max_edges]
    included = {end for e in selected for end in (e["source"], e["destination"])}
    if systems is None:
        included |= {f["subject"] for f in facts.values() if f["kind"] == "system"}
    else:
        included |= set(systems)
    lines = [
        f"%% {label(title)}",
        f"%% Data-flow view only. Filtered: {systems is not None}. Edges shown {len(selected)}/{len(all_edges)}. Truncated: {len(edges) > max_edges}.",
        "flowchart LR",
    ]
    for identity in sorted(included):
        fact = facts.get(f"system:{identity}")
        value = fact["value"] if fact else None
        lines.append(f'  {node(identity)}["{label(value["label"] if value else identity)}"]')
        style = (
            "unknown"
            if not value
            else "removed"
            if value["lifecycle"] == "retired"
            else "proposed"
            if fact.get("proposed") or value["lifecycle"] == "proposed"
            else "established"
        )
        lines.append(f"  class {node(identity)} {style}")
    for edge in selected:
        arrow = "-.->" if edge["proposed"] or edge["state"] != "SUPPORTED" else "-->"
        lines.append(
            f'  {node(edge["source"])} {arrow}|"{label(edge["id"])}"| {node(edge["destination"])}'
        )
    lines += [
        "  classDef established fill:#edf7ee,stroke:#246634",
        "  classDef unknown fill:#fff4cc,stroke:#946800",
        "  classDef proposed fill:#e4edff,stroke:#265dad,stroke-dasharray:5 5",
        "  classDef removed fill:#ffe6e6,stroke:#a51d2d",
    ]
    return "\n".join(lines) + "\n"


def impact(result):
    nodes, edges = {}, set()
    for value in result["requirements"].values():
        if value["state"] == value["before"] == "SUPPORTED":
            continue
        for path in value["witness"]["paths"]:
            displayed = [
                item
                for item in path
                if not item["node"].startswith("dependency:")
                or item.get("provider") is None
                or item.get("compatibility", {}).get("state", "SUPPORTED") != "SUPPORTED"
            ]
            for item in displayed:
                nodes[item["node"]] = item["state"]
            edges.update((a["node"], b["node"]) for a, b in zip(displayed, displayed[1:]))
    lines = [
        "%% Requirement witness view, filtered to changed or adverse outcomes. Unchanged supported requirements omitted; see assessment table. See JSON for evidence and truncation limits.",
        "%% Resolved dependency assertion nodes collapsed into edges; exact branches and references remain in JSON.",
        "flowchart TB",
    ]
    for key, state in sorted(nodes.items()):
        title = result["node_labels"].get(
            key, "Unresolved dependency" if key.startswith("dependency:") else key
        )
        lines.append(f'  {node(key)}["{label(title)}: {state}"]:::{state}')
    for start, end in sorted(edges):
        lines.append(f"  {node(start)} --> {node(end)}")
    lines += [
        "  classDef SUPPORTED fill:#edf7ee,stroke:#246634",
        "  classDef UNSUPPORTED fill:#ffe6e6,stroke:#a51d2d",
        "  classDef UNKNOWN fill:#fff4cc,stroke:#946800",
    ]
    return "\n".join(lines) + "\n"
