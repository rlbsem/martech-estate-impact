"""Bounded recursive proof search, independent from the production worklist.

Only the small Boolean dependency sublanguage is modeled. No production imports.
Back-edges have no proof unless another branch provides an external foundation.
"""


def reference(definitions, systems):
    def prove(node, ancestors):
        if node.startswith("sys:"):
            value = systems.get(node[4:])
            return "?" if value is None else "T" if value == "active" else "F"
        key = node[4:]
        if key in ancestors or key not in definitions:
            return "?"
        operator, children = definitions[key]
        answers = [prove(child, ancestors | {key}) for child in children]
        if not answers:
            return "?"
        if operator == "ALL":
            if any(a == "F" for a in answers):
                return "F"
            return "T" if all(a == "T" for a in answers) else "?"
        if any(a == "T" for a in answers):
            return "T"
        return "F" if all(a == "F" for a in answers) else "?"

    translation = {"T": "SUPPORTED", "F": "UNSUPPORTED", "?": "UNKNOWN"}
    return {key: translation[prove("req:" + key, set())] for key in definitions}
