# Run and inspect the change console

Use a disposable local environment. The launchers do not connect to a real enterprise estate. Keep generated credentials, PostgreSQL files and private logs under ignored `work/`.

## Docker Compose

Install Python 3.12 and Docker Compose v2. The credential preparation uses only the Python standard library.

```sh
python scripts/prepare_change.py
docker compose -p change-assurance-qa -f compose.change.yml up --build -d --wait
```

Open [the local console](http://127.0.0.1:8594/). The finite seed job publishes the synthetic estate and proposals, records a scoped acceptance/rejection, and exits. Only a restricted reader configuration is shared with the console. PostgreSQL has no host port. The console is published on loopback; the application containers use a non-root identity, read-only root filesystem and dropped capabilities.

Inspect and remove this exact disposable project:

```sh
python scripts/check_change_compose.py --output work/compose-security.json
docker compose -p change-assurance-qa -f compose.change.yml down --volumes --remove-orphans
python scripts/check_change_compose.py --clean --output work/compose-teardown.json
```

`down --volumes` removes this disposable demonstration's database and reader configuration. It is not an archival command for a real estate. The original `docker-compose.yml` remains unchanged and separate from this console environment.

## Native PostgreSQL

Install Python 3.12 and PostgreSQL server binaries. `PG_BIN` must point to the directory containing `initdb` and `pg_ctl`; alternatively put those binaries on PATH. Use a fresh workspace name for each launch.

```sh
python -m venv .venv
# Activate .venv using the command appropriate for your shell.
python -m pip install -r requirements.lock -r requirements-change.lock
python -m pip install --no-build-isolation --no-deps -e .
python -m playwright install chromium
python scripts/local_change.py --workspace work/console-01 --port 8594
```

The launcher creates a loopback-only, password-authenticated TCP cluster with Unix sockets disabled, publishes actual computed results, creates a separate reader and starts the console. Stop it with Ctrl+C; the owning launcher stops its own PostgreSQL cluster. Generated files remain in the private workspace for inspection. Use a new workspace to repeat; do not reuse another database directory.

On Windows PowerShell, a typical binary setting is `$env:PG_BIN='C:/Program Files/PostgreSQL/17/bin'`. On Linux it may be `export PG_BIN=/usr/lib/postgresql/17/bin`. These are examples; inspect your actual installation. Do not run `initdb` as root.

## Execute full verification

```sh
python scripts/check_change.py
python scripts/verify_change.py --workspace work/verify-01 --output work/verify-output-01 --check-package
```

The complete runner executes the original suite separately from the additive suite, regenerates the original demo twice into fresh output, creates a new native synthetic estate, compares requirement outcomes with an independent oracle, tests the real browser and builds/verifies wheel contents. It stops its owned database after capture. Public output excludes private runtime configuration and raw test logs.

For CI only, `CHANGE_TEST_DATABASE_URL` can identify a dedicated empty local test database whose trusted owner may create schemas and disposable login roles. Hostnames are restricted to loopback or the Compose service `postgres`; the runner rejects a previously seeded database. This variable is never needed for the default native launcher and must not point at a real or shared estate.

## Controlled operator review

The browser has no approval endpoint. A trusted local publisher uses `estate_change.service.submit(id, expected_revision, proposal)` to persist a new revision bound to the current snapshot. `estate_change.service.publish(prepared, snapshot, catalog, expected=current_snapshot)` advances evidence atomically; retries cannot silently overwrite another revision.

An enabled reviewer connects using its own database login and calls:

```sql
SELECT ca_decide('proposal-id', 1, 'ACCEPT', 'Specific scoped review reason');
```

`REJECT` is also supported. Acceptance requires current evidence, current revision, current reviewer authority and every readiness gate. The owner configures `ca_reviewer` and grants only schema USAGE and function EXECUTE to a reviewer; direct inserts into the decision ledger are not required or permitted. The examples create only synthetic local review identities. Do not pass an administrator credential to the console.

Publication recovery is tested both with transactional exceptions and actual child-process death before commit. A staged immutable snapshot may remain; the authoritative pointer stays on the last committed version. Retry with the last observed revision, then read back the pointer and record. No external technology is changed.

The versioned source fixture has a 2026-10-27 collection clock. Its review expiry is deliberate: after 2026-11-26 UTC, a trusted operator must publish freshly collected synthetic evidence with new source revisions before new acceptance. Do not disable expiry or relabel the archived observations as current. The immutable recorded demonstrations remain inspectable independently of a later live review.
