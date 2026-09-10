# SQL and Python: prove the result before scaling it

A distributed engine can multiply an incorrect join very efficiently. Begin by defining what one row means and how repeated, missing, or historical data should affect the answer.

## Terms introduced in this chapter

| Term | Meaning |
|---|---|
| Grain | What a single row represents, such as one order line |
| Cardinality | The number of values or rows; in a join, how many matches each side can produce |
| Window function | A calculation across related rows without collapsing them into one aggregate row |
| Query plan | The engine's steps for obtaining the result |
| Idempotence | Repeating the same logical operation preserves the intended outcome |

## Understand the model first

1. State the grain and keys of each input.
2. Define the business outcome, including nulls, currencies, cancellations, and event versions.
3. Build fixtures small enough to calculate by hand.
4. Inspect the result before investigating performance.
5. Read the plan and measure which work grows with input size.

A customer dimension with two historical rows per customer doubles joined orders unless the join selects the appropriate version. `DISTINCT` may hide the symptom while removing legitimate equal-valued orders. Fix the relationship and its time boundary.

## Lab prerequisites

Use Python 3 with its standard-library SQLite module. Run this in a scratch directory. It uses an in-memory database, synthetic values, and no network or credentials.

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE orders (
  event_id TEXT, customer_id TEXT, amount_cents INTEGER
);
INSERT INTO orders VALUES
  ('e1', 'c1', 100), ('e1', 'c1', 100),
  ('e2', 'c1', 250), ('e3', NULL, 50);
""")

# This fixture defines duplicates as identical retries of one event.
result = db.execute("""
WITH unique_events AS (
  SELECT event_id, customer_id, amount_cents
  FROM orders
  GROUP BY event_id, customer_id, amount_cents
)
SELECT customer_id, SUM(amount_cents)
FROM unique_events
WHERE customer_id IS NOT NULL
GROUP BY customer_id
""").fetchall()
assert result == [("c1", 350)], result
print(result)
db.close()
```

## How to interpret the results

The correct eligible total is 350 cents. A naive sum for `c1` is 450 because it counts the retry. The null customer is excluded deliberately, so this query does not prove that all input orders reached a consumer. Track exclusions separately.

Change the second `e1` to 120 cents. The same event ID now has conflicting payloads; the grouping no longer deduplicates it. A production contract must either reject that conflict or define versions and a deterministic winner. Silently choosing `MAX(amount_cents)` would invent a business rule.

Add a uniqueness assertion for the dimension before joining. Next test an absent dimension key and compare inner versus left join results. Count unmatched rows explicitly. A successful query only proves the database executed it, not that every business entity was represented.

## Go deeper in SQL

Study joins, grouping sets, window frames, CTEs, recursive traversal, null logic, decimal precision, timestamps and time zones. For each construct, write an edge-case fixture. Use window functions for ranked deduplication only after specifying how equal timestamps are ordered, such as by an immutable source sequence.

Read `EXPLAIN` for scan, filter, join, sort, and aggregation steps. Distinguish an OLTP index lookup from analytical partition or column pruning. An estimated row count is a model; an actual execution measurement is stronger evidence for that run. Record cold and warm measurements separately. Do not compare a cached query with an uncached one as though only the SQL changed.

## Python as pipeline infrastructure

Use type hints and dataclasses to express records, but validate external values at runtime. Type annotations alone do not reject a malformed message. Iterators and generators let a transformation consume bounded batches; accumulating their results into one list removes that memory benefit. Context managers ensure files and connections close on exceptions.

Learn serialization, logging, packaging, pytest, memory profiling, timeouts, and retry classification. Use asynchronous I/O for concurrent waits when the client supports it; evaluate processes for CPU-heavy Python work with serialization overhead included. Put stable event and run identities in structured logs, and keep secrets and full payloads out of default logs.

Linux practice should connect a process to CPU, resident memory, open files, disk space, and listening ports. Git practice should reconstruct the exact revision used for an output. Together these turn “it worked yesterday” into an inspectable difference.

## Explain it in your own words

Why do integer cents help this fixture but not define a universal money model? The example has one fixed unit; real datasets need a currency, decimal scale, rounding policy, and potentially conversion-time semantics. Explain why a test with four rows can expose correctness while telling you little about distributed throughput.

Continue with [Parquet and object storage](03-parquet-object-storage.md).

<!-- source: https://docs.python.org/3/library/sqlite3.html | checked: 2026-09-10 | standard-library API; fixture independently executable -->
<!-- source: https://www.postgresql.org/docs/current/using-explain.html | checked: 2026-09-10 | estimates and execution plans -->
