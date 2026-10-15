"""Stable safe node identifiers; encode every non-alphanumeric label character."""

import hashlib

from estate_impact.topology import data_flows

# Groundbreakers colours; semantic states remain explicit in labels.
BRAND_THEME = '%%{init: {"theme":"base","themeVariables":{"background":"#10101D","primaryColor":"#2A2A3D","primaryTextColor":"#F0F0FF","primaryBorderColor":"#7C7CAF","lineColor":"#B8B8FF","textColor":"#F0F0FF","secondaryColor":"#181825","tertiaryColor":"#2E2E45","fontFamily":"IBM Plex Sans, Arial, sans-serif","fontSize":"15px","edgeLabelBackground":"#10101D"}}}%%'


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
        BRAND_THEME,
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
        "  classDef established fill:#2A2A3D,stroke:#7C7CAF,color:#F0F0FF,stroke-width:1.4px",
        "  classDef unknown fill:#2E2E45,stroke:#E3BC7F,color:#F0F0FF,stroke-width:2px",
        "  classDef proposed fill:#2E2E45,stroke:#B8B8FF,color:#F0F0FF,stroke-width:2px,stroke-dasharray:5 5",
        "  classDef removed fill:#2E2E45,stroke:#D98EA3,color:#F0F0FF,stroke-width:2px",
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
        BRAND_THEME,
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
        "  classDef SUPPORTED fill:#2A2A3D,stroke:#81C5B0,color:#F0F0FF,stroke-width:2px",
        "  classDef UNSUPPORTED fill:#2E2E45,stroke:#D98EA3,color:#F0F0FF,stroke-width:2px",
        "  classDef UNKNOWN fill:#2E2E45,stroke:#E3BC7F,color:#F0F0FF,stroke-width:2px",
    ]
    return "\n".join(lines) + "\n"
