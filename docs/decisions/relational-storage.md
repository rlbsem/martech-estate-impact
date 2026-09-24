# ADR 001: PostgreSQL with typed projections

Status: accepted and implemented.

The central requirements are durable provenance, transactional publication, immutable analytical versions and inspectable evidence. The fixture-sized graph operations are bounded traversal, fixed-point evaluation and topological ordering. They do not require a separate graph database.

Use relational tables for artifacts, assertions, quarantine, snapshots, fact projections, dispositions and assessments. Preserve heterogeneous payloads in JSONB, with a finite typed contract and dedicated SQL views for systems, ownership, capabilities, interfaces, integrations and requirements. Keep algorithmic semantics in Python, where independent reference testing is straightforward.

This avoids a second persistence system and cross-store consistency boundary. It sacrifices database-native graph traversal and fine-grained relational constraints for every nested payload field. Application contracts and semantic tests therefore remain necessary; SQL constraints alone do not establish valid architecture. Full snapshots duplicate some evidence projections and are not optimized for very large estates. Reconsider adjacency indexing or a graph store only with measured workloads and a demonstrated query need.
