# Implementation report

## 1. Built

`martech-estate-impact` is a working Python/PostgreSQL evidence and architecture-impact system. The synthetic enterprise Marketing estate contains 24 active systems, 2 proposed replacements, 40 integration claims and 10 business capabilities. Four importers, explicit identity mapping, conflict reconciliation, coverage analysis, immutable snapshots, ALL/ANY three-state evaluation, isolated proposals, witness paths, residual references and activity gates are implemented.

## 2. Final repository tree

The approved directories are present: `src/estate_impact/` (including `importers/` and `reporting/`), `migrations/`, `config/`, `fixtures/synthetic-estate/proposals/`, `examples/generated/`, `tests/oracle/`, `scripts/`, `docs/decisions/`, `docs/evidence/` and `.github/workflows/`. Root setup includes README, package metadata, dependency lock, Compose, environment example, Git attributes/ignore rules and MIT license. See [the complete delivered file tree](repository-tree.txt).

## 3. Actual tests

**70 passed; 0 failed; 0 errors; 0 skipped** on Windows/Python 3.12.14/PostgreSQL 17.11. This includes 350 generated bounded graphs inside the independent-oracle test, metamorphic checks, actual database concurrency/rollback and the three end-to-end scenarios. Dependency checks, lint and formatting also passed. [Observed verification](../../examples/generated/verification-report.md).

## 4. Actual demo and verification

The demo ran against real PostgreSQL. Repeated generation produced identical bytes. A clean virtual environment installed the built wheel, passed the full suite and verified installed/source parity and CLI assessment identity. The current snapshot stayed unchanged across all proposals.

Retirement produced four unsupported requirements and one Unknown; registration remained supported. The incomplete replacement produced three unsupported requirements. The revised replacement produced no identified blockers within its reviewed architecture scope, with operational acceptance gates still open.

## 5. Generated artifacts

The delivery includes current-state overview and campaign diagrams, retirement assessment and impact diagram, incomplete/revised replacement assessments, target architecture and diff, JSON results, snapshot, evidence index and verification records. All four Mermaid diagrams were rendered with Mermaid 10.9.3 in headless Edge; focused views were visually inspected. Diagram Markdown wrappers are GitHub-renderable.

## 6. Important decisions

Source claims remain separate from reviewed facts. Source authority is scoped by assertion type. Data-flow edges never imply business failure. Unknown propagates instead of becoming absence. Alternatives require explicit qualification. PostgreSQL publishes append-only analytical records transactionally; Python performs deterministic reasoning. Assessments bind exact snapshots, proposals, policy and source fingerprints. No AI component was added.

## 7. Deviations and refinements

No substantial redesign. Logical domain entities use typed JSONB assertions and dedicated relational SQL views rather than a separate mutable table for every entity. Additional files support demo orchestration, review regression tests, stale-source evidence and GitHub Mermaid wrappers. Local database validation used native PostgreSQL because Docker was unavailable; Compose configuration validated, but its container execution was not observed. GitHub CI is configured, not claimed passing.

## 8. Known limitations

All business evidence and results are synthetic. Review completeness and acceptance artifacts remain trusted human inputs. Declared event/field/key compatibility does not prove operational behavior. There are no production vendor connectors, automatic exhaustive discovery, deployment actions, load benchmarks, client-outcome claims or safe-retirement/cutover guarantees. Database-owner powers are outside the append-only application's integrity boundary.

## 9. Exact local commands

From the extracted repository directory in Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps .
docker compose up -d --wait
.venv\Scripts\python.exe scripts/demo.py
.venv\Scripts\python.exe scripts/verify.py
```

These commands need Python 3.12 and a running Docker installation. For an existing PostgreSQL database, set `ESTATE_DATABASE_URL` instead of starting Compose. Migration is automatic. [Operations](../operations.md) provides details.

## 10. Recommended eight-minute presentation path

Fictional estate and decision → campaign map → unresolved claim → work-management retirement → evidence-backed shared-campaign chain → unaffected registration → seasonal Unknown → incomplete webinar offer → revised target and acceptance prerequisites → verification and migration handoff. [Timed walkthrough](../demonstration-walkthrough.md).

## 11. What the presenter must understand

Be able to explain source assertion versus conclusion versus proposal; ALL/ANY and Unknown; optional inputs and qualified alternatives; fixed-point cycles; coverage versus execution observations; residual references; transactional snapshot identity; and why a favorable architecture assessment still needs operational acceptance. Present the repository as a synthetic engineering demonstration, not client deployment history.

## 12. GitHub readiness

Ready for upload as a portfolio repository, with generated examples and local validation evidence included. No remote repository was created or published. A hosted CI result remains to be observed after upload. Keep that distinction in the README and any public presentation.
