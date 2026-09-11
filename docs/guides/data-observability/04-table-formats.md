# Iceberg and Delta Lake: make a set of files a table

Suppose a job writes twenty Parquet files and crashes after the twelfth. A directory scan cannot tell a consumer whether those twelve files are a complete result. A table format adds metadata and commit rules so readers can identify a valid table state.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| Snapshot or version | An identified committed state that a reader can reference | Reproduce a query or recovery decision against an identified committed table state. |
| Manifest | Iceberg metadata describing a collection of content files | Plan Iceberg reads using recorded file metadata instead of discovering table membership from directory contents. |
| Catalog | A mechanism for locating tables and coordinating their metadata, depending on implementation | Locate the authoritative table metadata and coordinate updates under the catalog's commit contract. |
| Optimistic concurrency | Prepare a change, validate against intervening changes, then commit or retry | Allow concurrent preparation while rejecting or retrying changes that conflict at commit. |
| Compaction | Rewriting a file layout to reduce fragmentation without changing the intended rows | Reduce excessive small-file overhead while preserving the intended table contents. |
| Retention | How long versions and their supporting files remain available | Keep enough history for replay, investigation, and recovery without assuming storage can be unlimited. |

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

## Walk an Iceberg snapshot from catalog to rows

The catalog resolves a table name to its current metadata location. That metadata JSON includes schema and partition-spec identities and identifies the current snapshot. The snapshot points to a manifest list. Each manifest-list entry describes a manifest, including partition summaries useful for planning. A manifest records content-file entries and their metadata. Finally, data files hold rows; applicable delete files affect which rows a reader returns.

For a query on September 10, the planner can eliminate manifests and files using metadata before reading Parquet pages. A million files still create planning and maintenance work even if each query returns few rows. A catalog lookup, manifest scan, object read, and Parquet decode belong to different latency stages; identify the expensive stage before changing worker count.

Schema field IDs let a format distinguish a renamed field from a new field reusing a historical name. Partition-spec IDs let old daily-partitioned files coexist with newer hourly-partitioned files. Changing the spec changes the layout of future writes; it does not automatically rewrite all old data. The reader interprets files under their respective specs. Consumer contracts still decide whether a renamed or nullable field is acceptable to applications.

### Inspect real metadata instead of hand-editing JSON

The following is an engine exercise for Spark with a configured Iceberg catalog named `lab` and a writable disposable namespace `study`. It requires a compatible Iceberg runtime and catalog configuration; it is not SQL for a plain Spark session. Run in a fresh namespace or choose a unique table name. No cloud execution is claimed.

```sql
CREATE TABLE lab.study.orders (
  event_id STRING, event_time TIMESTAMP, amount_cents BIGINT
) USING iceberg PARTITIONED BY (days(event_time));

INSERT INTO lab.study.orders VALUES
  ('e1', TIMESTAMP '2026-09-10 01:00:00', 100),
  ('e2', TIMESTAMP '2026-09-10 02:00:00', 250);

SELECT snapshot_id, parent_id, operation
FROM lab.study.orders.snapshots ORDER BY committed_at;
SELECT content, file_path, record_count, file_size_in_bytes
FROM lab.study.orders.files;
SELECT partition_spec_id, added_data_files_count, existing_data_files_count
FROM lab.study.orders.manifests;

INSERT INTO lab.study.orders VALUES
  ('e3', TIMESTAMP '2026-09-11 01:00:00', 50);
SELECT COUNT(*), SUM(amount_cents) FROM lab.study.orders;
```

Expected logical result is three rows and 400 cents. Actual snapshot IDs, paths, sizes, and number of files are runtime-dependent. Copy the first snapshot ID into the supported `VERSION AS OF <snapshot_id>` query and expect two rows and 350 cents. Inspect that older snapshot's metadata views where supported. A parent relationship explains history; a filename timestamp is not an authoritative version identifier.

## Commit conflict: two writers read the same base

Suppose writer A and writer B both plan from version 7. A prepares a correction to e1; B prepares a correction to the same record. A commits version 8. B must validate against the intervening change. If the operations conflict under the selected engine/protocol, B cannot simply publish its stale candidate as though version 8 never existed. It must reread/recompute or fail. Two disjoint appends may be compatible; not every concurrent operation must fail.

ACID becomes concrete here: atomicity hides incomplete publication; consistency depends on enforced format and application invariants; isolation controls what concurrent readers/writers observe; durability depends on committed metadata and objects remaining available. Snapshot isolation is not a guarantee that arbitrary cross-table business invariants hold. A “unique event ID” rule still needs an implementation when the engine does not enforce it.

### Delta transaction log and supported time travel

Delta records actions such as adding or removing logical files in its transaction log. Removing a file from the current table state differs from immediately deleting its physical object. Log checkpoints summarize state to reduce replay work; they are not Spark streaming checkpoints. Delta's reader/writer protocol capabilities also matter: enabling a feature can exclude older clients even when the underlying files remain Parquet.

For a Spark session configured with compatible Delta extensions, this separate fresh-table lab exposes the version boundary:

```sql
CREATE TABLE study_orders_delta (event_id STRING, amount_cents BIGINT) USING DELTA;
INSERT INTO study_orders_delta VALUES ('e1',100),('e2',250);
DESCRIBE HISTORY study_orders_delta;
INSERT INTO study_orders_delta VALUES ('e3',50);
SELECT COUNT(*), SUM(amount_cents) FROM study_orders_delta;
```

Record the version after the first insert from `DESCRIBE HISTORY`; use it in `SELECT COUNT(*), SUM(amount_cents) FROM study_orders_delta VERSION AS OF <recorded_version>`. The current answer is `(3,400)` and the recorded earlier answer is `(2,350)`. Do not assume the first insert has version zero: table creation may itself produce a log version.

## Deletes, compaction, and read amplification

Copy-on-write rewrites affected data files to represent a change. Merge-on-read approaches retain data and additional delete/change information that readers combine. In Iceberg v2, position deletes identify file positions, while equality deletes identify matching field values; applicability also depends on sequence and schema metadata. Supported later format features and engine implementations can differ. Measure reader work as well as write latency when choosing an update strategy.

Compaction rewrites many small files into fewer larger files and may consolidate accumulated delete work through supported maintenance. It competes with ingestion for compute and can conflict with concurrent rewrites. Compare count, keyed values, and aggregate totals before/after; count alone misses a changed amount. Old files can remain referenced by retained snapshots, so storage usage need not fall immediately after successful compaction.

Use Trino as a second reader when learning interoperability. Its Iceberg connector must resolve the same catalog and understand the table's enabled format features; pointing at the same bucket is insufficient. Compare the same recorded snapshot and consumer query across engines. If totals differ, first investigate snapshot selection, delete support, timestamp interpretation, and permissions before blaming floating-point arithmetic or the optimizer.

## Guided commit and recovery investigation

Prerequisites: one disposable table, one compatible engine/catalog, a documented snapshot/history query for that engine, and synthetic input. Before writing, record the table location, catalog identifier, engine version, and enabled format features.

Create a table with two known event IDs. Record version A and its row count. Append one new ID and record version B. Query A and B through the supported time-travel interface; expect two and three rows respectively, matching the examples above and the worksheet below. Use the format's metadata views to explain which files are referenced. Do not manually edit metadata JSON or log files.

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
<!-- source: https://iceberg.apache.org/docs/latest/spark-queries/ | checked: 2026-09-10 | metadata tables and time-travel query syntax -->
<!-- source: https://docs.delta.io/delta-batch/ | checked: 2026-09-10 | versioned reads, schema and log checkpoints -->
<!-- source: https://trino.io/docs/current/connector/iceberg.html | checked: 2026-09-10 | engine/catalog/format compatibility -->
