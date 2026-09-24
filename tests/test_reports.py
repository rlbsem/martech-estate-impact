import json

from estate_impact.impact import assess, scenario
from estate_impact.reporting import markdown, mermaid
from estate_impact.topology import data_flows, reachable


def test_markdown_and_json_same_assessment(snapshot, proposal):
    result = assess(snapshot, proposal())
    rendered = markdown.assessment(result)
    assert result["id"] in rendered
    assert result["disposition"] in rendered
    for key, req in result["requirements"].items():
        assert f"({key}) | {req['before']} | {req['state']}" in rendered
    assert json.loads(json.dumps(result)) == result


def test_mermaid_exact_node_edge_correspondence(snapshot):
    facts = snapshot["facts"]
    diagram = mermaid.topology(facts, "Estate")
    for flow in data_flows(facts):
        arrow = "-->" if flow["state"] == "SUPPORTED" else "-.->"
        assert (
            f'{mermaid.node(flow["source"])} {arrow}|"{flow["id"]}"| {mermaid.node(flow["destination"])}'
            in diagram
        )
    assert len([line for line in diagram.splitlines() if "-->|" in line or "-.->|" in line]) == len(
        data_flows(facts)
    )
    assert "crm" in reachable(data_flows(facts), "automation")
    assert "automation" in reachable(data_flows(facts), "crm")


def test_filtered_truncated_and_escaped_labels(snapshot):
    facts = snapshot["facts"]
    facts["system:crm"]["value"]["label"] = 'CRM"] --> Evil["injected\n<script>'
    diagram = mermaid.topology(facts, "Test", {"crm", "automation"}, max_edges=1)
    assert 'Evil["' not in diagram and "<script>" not in diagram
    assert "Filtered: True" in diagram and "Truncated: True" in diagram
    assert markdown.escape("x|<script>\n") == "x&#124;&lt;script&gt; "


def test_proposed_and_removed_styles(snapshot, proposal):
    facts, _, _ = scenario(snapshot, proposal("replace-webinar-revised"))
    diagram = mermaid.topology(facts, "Target")
    assert f"class {mermaid.node('webinar')} removed" in diagram
    assert f"class {mermaid.node('new-webinar')} proposed" in diagram
    assert '-.->|"campaign-ids"|' in diagram


def test_impact_view_collapses_only_resolved_dependency_branches(snapshot, proposal):
    result = assess(snapshot, proposal())
    diagram = mermaid.impact(result)
    assert "Send webinar follow-up: UNSUPPORTED" in diagram
    assert "Unresolved dependency: UNKNOWN" in diagram
    assert (
        f"{mermaid.node('req:follow-up')} --> {mermaid.node('req:webinar-identifiers')}" in diagram
    )
    assert "assertion nodes collapsed" in diagram
    assert mermaid.node("req:registration") not in diagram
