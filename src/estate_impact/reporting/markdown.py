import html


def escape(value):
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("`", "&#96;")


def assessment(result):
    lines = [
        f"# {escape(result['proposal']['title'])}",
        "",
        "**Synthetic enterprise evidence and modeled results.**",
        "",
        f"Result: **{result['disposition']}**",
        "",
        result["claim_boundary"],
        "",
        f"Snapshot: `{result['snapshot_id']}`  ",
        f"Assessment: `{result['id']}`",
        "",
        "## Requirement consequences",
        "",
        "| Requirement | Before | Proposed | Interpretation |",
        "|---|---|---|---|",
    ]
    for key, value in result["requirements"].items():
        interpretation = (
            "established blocker"
            if value["state"] == "UNSUPPORTED"
            else "unresolved / conditional"
            if value["state"] == "UNKNOWN"
            else "supported in declared model"
        )
        lines.append(
            f"| {escape(value['label'])} ({escape(key)}) | {value['before']} | {value['state']} | {interpretation} |"
        )
    lines += [
        "",
        "## Witness branches",
        "",
        "Dependency paths run from the business requirement toward its provider. Evidence IDs resolve in [evidence-index.json](evidence-index.json). Proposal references are proposed future assertions, not observed source evidence.",
        "",
    ]
    for key, value in result["requirements"].items():
        lines += [f"### {escape(key)}", ""]
        for path in value["witness"]["paths"]:
            lines.append(
                "- " + " → ".join(f"{escape(step['node'])} [{step['state']}]" for step in path)
            )
            refs = sorted({e for step in path for e in step.get("evidence", [])})
            lines.append("  Evidence: " + ", ".join(f"`{e}`" for e in refs))
            for step in path:
                if "compatibility" in step and any(step["compatibility"]["missing"].values()):
                    lines.append(
                        "  Declared interface gaps: " + escape(step["compatibility"]["missing"])
                    )
        if value["witness"]["truncated"]:
            lines.append("Witness output truncated at disclosed path/depth limits.")
        lines.append("")
    lines += ["## Residual references", ""]
    lines += [
        f"- {escape(ref['key'])}: {ref['state']}; still references {escape(', '.join(ref['retired_systems']))}"
        for ref in result["residual_references"]
    ] or ["None in the modeled relationships."]
    lines += [
        "",
        "Proposed relationship issues: " + escape(result["proposed_relationship_findings"]),
        "",
        "## Coverage and unresolved evidence",
        "",
    ]
    lines += [
        "Consequences detected outside the selected requirement scope: "
        + escape(result["out_of_scope_changes"]),
        "",
    ]
    for subject, coverage in result["coverage"].items():
        lines.append(
            f"- {escape(subject)}: {coverage['state']}. {escape('; '.join(coverage['reasons']) or 'Reviewed declared scope; no blanket discovery guarantee.')} Evidence: {escape(', '.join(coverage['evidence']))}"
        )
    lines += [
        "",
        "Unresolved estate facts (includes facts outside this proposal's requirement scope): "
        + escape(", ".join(result["unresolved_estate_facts"]) or "none"),
        "",
        "## Activity prerequisites",
        "",
        "Planned order: " + escape(" → ".join(result["sequence"]["order"]) or "none"),
        "",
        "Cycle members: " + escape(", ".join(result["sequence"]["cycle_members"]) or "none"),
        "",
        "Missing prerequisites: " + escape(result["sequence"]["missing_prerequisites"]),
        "",
        "Missing acceptance evidence: " + escape(result["sequence"]["missing_acceptance"]),
        "",
        "Ready to progress now: " + escape(", ".join(result["sequence"]["ready_now"]) or "none"),
        "",
        "Architecture feasibility and execution readiness are separate. Uncompleted acceptance gates remain even when declared interface gaps are closed.",
        "",
    ]
    return "\n".join(lines)
