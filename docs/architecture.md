# Architecture and boundaries

## Processing flow

1. Four parsers validate source formats and produce typed claims. Malformed artifacts fail before persistence. Identity ambiguity is retained in quarantine, never resolved by fuzzy matching.
2. `prepare` assigns content-addressed artifact and assertion identities. PostgreSQL imports each artifact and its claims in one transaction. Concurrent identical imports converge through the artifact primary key; losers wait for the winning transaction, then return unchanged.
3. A snapshot selects an explicit artifact set. It does not read an implicit “latest row” universe. Type-specific policy admits current source evidence; mutually contradictory admissible values remain Unknown. An explicit review accepts assertion IDs and records why other claims were rejected.
4. Snapshot publication atomically writes the payload, typed fact projection and evidence dispositions. An exception rolls back parent and child rows. Database triggers reject row updates and deletes. Application content hashes reject a modified snapshot. Database owners can still alter/drop/truncate objects: this is an integrity boundary for a trusted local operator, not a hostile-administrator security guarantee.
5. Each proposal binds an exact snapshot, is applied to a deep copy and yields typed target facts. Retirement/activation, integration rewiring and relationship addition/removal are explicit actions. No code changes infrastructure.
6. The requirement evaluator derives both current and proposed outcomes. Integration reachability is a candidate view only. Residual-reference checks and coverage checks are independent of the requirement result. New failures detected outside the selected requirement scope are surfaced and prevent a clean disposition.
7. Reporting projects this same scenario into Markdown, JSON and Mermaid. Assessment identities include proposal, snapshot, policy, implementation version and Python-source fingerprint. Proposed witness evidence refers to a proposal action; observed evidence refers to a retained assertion.

## Data representation

`source_artifact` and `assertion` retain the evidence record. `identity_quarantine` retains unresolved source identities. `estate_snapshot`, `snapshot_fact` and `snapshot_assertion` retain each reviewed analytical state. `assessment` retains the bound proposal and derived result.

The finite assertion kinds correspond to systems, ownership, teams, capabilities, interface contracts, integrations, requirements, dependency groups, authority claims and execution observations. Payloads use JSONB to preserve heterogeneous evidence; this is not an unrestricted triple store. Python contracts validate typed payloads, PostgreSQL constrains record identity, kind, disposition and provenance. Typed views expose systems, business accountability, capabilities, workflow groups, interfaces, data flows, authority and evidence without requiring a Python session. Crosswalk, collection reviews, policy and resolution records are embedded in the hashed snapshot rather than overwritten global lookup rows.

Logical ALL/ANY groups belong to workflow requirements and refer to dependency assertion keys. A dependency names a typed `sys:`, `int:` or `req:` provider. A data flow separately names source, destination and execution runtime. A capability groups outcomes; it does not automatically confer substitutability on its systems. Authority claims record field/domain stewardship metadata; no automatic data-authority conflict resolver is claimed.

## Why this boundary

The difficult decision is evidence-backed architecture impact, not graph storage or orchestration. PostgreSQL provides transactions and inspectable joins; Python implements bounded graph traversal and fixed-point evaluation. No external graph service is required. At larger scale, precomputed adjacency and incremental evaluation could reduce full-snapshot work, but would need benchmark and consistency evidence before being adopted.

The runtime is local and trusted. No SaaS connector, SSO, tenant isolation, credential store, sensitive customer data or network discovery is included. Source files describe synthetic metadata, not tokens or payload-level customer records. Production adoption would need access controls, retention, backup/restore drills, export permissions and organizational review ownership.
