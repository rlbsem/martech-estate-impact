import csv
import io

from estate_impact.contracts import required


def parse(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    claims = []
    for line, row in enumerate(rows, 2):
        required(row, ["external_id", "label", "lifecycle", "operator", "owner", "environment"])
        subject = row["external_id"]
        for kind, value in [
            ("system", {k: row[k] for k in ("label", "lifecycle", "operator", "environment")}),
            ("ownership", {"team": row["owner"]}),
        ]:
            claims.append(
                dict(
                    key=f"{kind}:{subject}",
                    kind=kind,
                    subject=subject,
                    value=value,
                    location=f"line:{line}",
                    external_subject=True,
                )
            )
    if not rows:
        raise ValueError("empty inventory")
    return claims
