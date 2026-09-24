import csv
import io

from estate_impact.contracts import required


def parse(text):
    result = []
    for line, row in enumerate(csv.DictReader(io.StringIO(text)), 2):
        required(row, ["integration", "count", "start", "end"])
        result.append(
            dict(
                key=f"execution:{row['integration']}",
                kind="execution",
                subject=row["integration"],
                location=f"line:{line}",
                value={"count": int(row["count"]), "start": row["start"], "end": row["end"]},
            )
        )
    return result
