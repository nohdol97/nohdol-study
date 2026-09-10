# Iceberg and Delta Lake: make a set of files a table

Suppose a job writes twenty Parquet files and crashes after the twelfth. A directory scan cannot tell a consumer whether those twelve files are a complete result. A table format adds metadata and commit rules so readers can identify a valid table state.

## Terms introduced in this chapter

| Term | Meaning |
|---|---|
| Snapshot or version | An identified committed state that a reader can reference |
| Manifest | Iceberg metadata describing a collection of content files |
| Catalog | A mechanism for locating tables and coordinating their metadata, depending on implementation |
| Optimistic concurrency | Prepare a change, validate against intervening changes, then commit or retry |
| Compaction | Rewriting a file layout to reduce fragmentation without changing the intended rows |
| Retention | How long versions and their supporting files remain available |

## Understand the model first

1. Read a known table state and plan a change against it.
2. Write new data or delete information using the engine's supported protocol.
3. Validate and commit metadata that makes the new state visible.
4. Let readers use a consistent supported version.
5. Reclaim obsolete files only after retention and reader/recovery requirements permit it.

In Iceberg, table metadata references snapshots; a snapshot references a manifest list; manifests describe data and delete files. Its schema uses field identities, and partition specifications can evolve. In Delta Lake, the transaction log tracks the table's committed changes. Delta's documented optimistic write sequence reads a snapshot, stages changes, then validates and commits. Those are different metadata protocols, not interchangeable directory names.

## Choose one, then compare

| Question | What to inspect |
|---|---|
| Which engines must read and write? | Connector and protocol support for the exact versions |
| Can a schema evolve safely? | Type compatibility, field identity, reader behavior, and downstream contract |
| Can a partition layout change? | How old and new files are planned together |
| How are updates and deletes represented? | Supported format features, read amplification, and maintenance needs |
| What does recovery require? | Catalog state, metadata/logs, data files, permissions, and retention |

A format feature being specified does not mean every engine implements it. Test mixed-engine read/write behavior against a fixed version matrix. Begin with Iceberg if multi-engine learning is the priority, or Delta if your immediate implementation centers on Spark and Databricks. This is a learning choice, not a universal product recommendation.

## Guided commit and recovery investigation

Prerequisites: one disposable table, one compatible engine/catalog, a documented snapshot/history query for that engine, and synthetic input. Before writing, record the table location, catalog identifier, engine version, and enabled format features.

Create a table with three known event IDs. Record version A and its row count. Append two new IDs and record version B. Query A and B through the supported time-travel interface; expect three and five rows respectively. Use the format's metadata views to explain which files are referenced. Do not manually edit metadata JSON or log files.

Next start two overlapping updates in a controlled lab. Observe whether the second operation conflicts, retries, or commits under the selected implementation. Reconcile final row values. “Both commands succeeded” is insufficient when the business invariant is one final value per event version.

Finally perform compaction using the supported maintenance operation. Compare file counts, physical size, query result, and snapshot history. Fewer files are a layout outcome; they do not prove a query got faster. Measure the intended query with comparable caching and concurrency.

## Time travel is bounded recovery

A retained metadata pointer is useless if its referenced objects were removed. Snapshot expiration, log retention, object lifecycle rules, and backup policy must agree. Protect a recovery window longer than the maximum expected incident discovery and response time, then demonstrate restore into an isolated location.

Time travel is not a separate backup: accidental loss of the catalog, metadata, or storage can remove both current and old states. A replication or backup strategy must preserve the components needed to reconstruct a readable table. Include access permissions in the restore test.

## Example results

Illustrative table-history worksheet, not product-specific SQL output.

```text
version A: e1=100, e2=250; unique_events=2; total_cents=350
version B: append e3=50; unique_events=3; total_cents=400
read version A after B: unique_events=2; total_cents=350
missing file referenced by A: read/completeness failure
```

Record the actual snapshot/version identifier from your engine. Metadata alone cannot restore a physically deleted referenced file. This worksheet does not execute snapshot expiration or vacuum.

## Explain it in your own words

Can adding a nullable column still break a consumer? Yes: a consumer may assume a fixed projection or schema even when the table protocol allows the change. Explain the difference between storage compatibility and a consumer contract. Describe why blindly deleting “unreferenced” files during a concurrent write can be unsafe.

Continue with [Spark performance](05-spark-performance.md).

<!-- source: https://iceberg.apache.org/spec/ | checked: 2026-09-10 | snapshot and manifest hierarchy -->
<!-- source: https://iceberg.apache.org/docs/latest/evolution/ | checked: 2026-09-10 | schema and partition evolution -->
<!-- source: https://docs.delta.io/concurrency-control/ | checked: 2026-09-10 | optimistic write validation -->
