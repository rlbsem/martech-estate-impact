# Local operations

## Setup and migrations

Use Python 3.12 and a dedicated PostgreSQL database. Follow the five commands after virtual-environment creation in the [README](../README.md). Compose binds PostgreSQL to `127.0.0.1:55439`, with synthetic local credentials `estate/estate`. The application reads `ESTATE_DATABASE_URL` from the process environment; it does not load arbitrary `.env` files automatically. Its default matches Compose.

For another database, set the environment in PowerShell:

```powershell
$env:ESTATE_DATABASE_URL = 'postgresql://estate:estate@127.0.0.1:55439/estate'
python -m estate_impact.cli init
```

`init`, the demo and verification apply `migrations/001_estate_model.sql` under a transaction-scoped advisory lock. The initial migration is idempotent. Future schema changes should use new, ordered migrations; this version does not claim a general migration-runner framework.

The local validation recorded in this repository used a separate native PostgreSQL 17.11 process because Docker was unavailable. No SQLite substitution was made. Compose is configured but not execution-verified here. A PostgreSQL connection failure stops the scripts and tests; core database tests are not skipped.

## Imports and snapshot selection

`config/sources.json` identifies each fixture artifact, parser, timestamp, scope and collection status. Importers are callable independently:

```python
from pathlib import Path
from estate_impact import db
from estate_impact.demo import read
from estate_impact.identity import index_crosswalk
from estate_impact.importers import prepare

root = Path.cwd()
source = read(root / "config/sources.json")[0]
mapping = index_crosswalk(read(root / "config/crosswalk.json"))
artifact = prepare((root / "fixtures/synthetic-estate" / source["artifact"]).read_text(), source, mapping)
db.store_artifact(artifact)
```

The demo uses `load_inputs`, imports each prepared artifact, then retrieves only those artifact IDs from PostgreSQL. `snapshots.build` accepts assertions, selected artifacts, collection manifests, crosswalk, policy, explicit review timestamp and resolutions. `db.publish` publishes atomically. Failed collections persist artifact metadata without inventing claims. Malformed artifacts roll back or fail before persistence. Neither partial imports nor later imports erase evidence from existing snapshots.

For other estates, use the same parser contracts and Python interfaces with a separately reviewed artifact list; the CLI's `demo` intentionally targets the bundled synthetic-estate fixture. There is no hidden “latest snapshot” alias. A caller must choose an exact published ID.

## Assessment and reports

The demo prints and writes the exact snapshot ID. Supply it to the CLI:

```text
python -m estate_impact.cli assess --snapshot PASTE_SNAPSHOT_ID --proposal fixtures/synthetic-estate/proposals/replace-webinar-revised.json --output revised-assessment.json
```

The CLI explicitly binds that requested snapshot to the proposal and stores the assessment. Programmatic callers must provide `base_snapshot` themselves; mismatches fail. `reporting.markdown.assessment`, `reporting.mermaid.topology` and `reporting.mermaid.impact` render the analyzed result and scenario. `scripts/demo.py` regenerates the complete examples set; `scripts/verify.py` regenerates verification evidence too.

The JSON files retain full evidence and outcome structure. Generated Markdown diagram wrappers contain GitHub Mermaid fences; `.mmd` files retain the corresponding source. Scoped views disclose filtering. Unknown integrations are shown as uncertain candidate flows; proposed relations are dashed, and retired systems are red. No HTML script content from labels is copied into diagrams.

## Inspectable SQL

```sql
SELECT fact_key, source, collected_at, source_location, disposition
FROM evidence_trace
WHERE snapshot_id = 'PASTE_SNAPSHOT_ID' AND fact_key = 'dependency:seasonal:0';

SELECT s.system_id, s.technical_operator, b.accountable_team, b.state
FROM system_instances s
JOIN business_accountability b USING (snapshot_id, system_id)
WHERE s.snapshot_id = 'PASTE_SNAPSHOT_ID';

SELECT consumer, provider, qualified, optional, state
FROM dependency_requirements WHERE snapshot_id = 'PASTE_SNAPSHOT_ID';
```

## Troubleshooting and lifecycle

- Connection refused: check `docker compose ps`, PostgreSQL health and whether port 55439 is already occupied. To use a different port, change both Compose's host port and the application's URL.
- Permission denied creating a schema: verification needs a dedicated database role with schema creation permission. It uses a random `estate_test_...` schema and drops only that schema after tests.
- Old installed code: reinstall with `python -m pip install --no-build-isolation --no-deps .`. Verification compares the installed package with repository sources and refuses stale-package evidence.
- A new input produces Unknown: inspect dispositions, reviewed dates, crosswalk quarantine and coverage before changing requirement logic. Do not delete an inconvenient assertion.
- Generated files differ: inspect snapshot, proposal and implementation hashes. Changing source bytes can change content-addressed evidence IDs; do not equate that with a semantic regression without comparing outcomes and paths.

`docker compose down` stops the service and retains the named data volume. Repeated demo runs reuse identical artifacts and snapshots; changed inputs append new records. No automatic retention job or database deletion command is supplied. In production, operators would need a reviewed retention policy and tested database backups. Verification output under `work/` is disposable local run data and excluded from delivery.
