# SQL and Python: prove the result before scaling it

An order contains three items. After joining orders to items, a query counts three orders instead of one. Adding more machines will only compute the wrong answer faster.

First decide what one row represents. Then use small SQL and Python examples to check duplicates, missing data, and historical changes.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| Grain | What one row means: for example, one order, one order item, or one day's total. | Prevent double counting and invalid joins by stating exactly what each row represents. **Concrete situation (illustrative):** Joining order headers to line items doubles a reported count. → Declare and preserve the intended grain. → Reconcile totals using the correct row identities. |
| Cardinality | How many values or rows there are. For a join, it describes how many rows can match on each side. | Predict join expansion and detect unintended many-to-many matches before trusting totals. **Concrete situation (illustrative):** A supposedly one-to-one join produces extra rows. → Count matches on both join keys. → Detect duplicate keys before trusting aggregates. |
| Window function | A calculation over related rows that keeps each row in the result, such as ranking a customer's orders. | Calculate rankings, running totals, or neighboring values while keeping individual rows visible. **Concrete situation (illustrative):** An analyst needs each customer's latest order without losing its other columns. → Rank orders within each customer by a deterministic ordering. → Verify one selected row per customer, including timestamp ties. |
| Query plan | The steps an engine plans to take to read data and produce a query result. | Explain scans, joins, exchanges, and estimates before deciding which query optimization to try. **Concrete situation (illustrative):** A report becomes slow after its table grows. → Inspect the query plan for scans, joins, and estimated row counts. → Compare actual work before and after a targeted change. |
| Idempotence | Repeating the same logical operation leaves the same intended result as performing it once. | Retry or replay an uncertain operation without changing its intended business result. **Concrete situation (illustrative):** A network timeout causes a payment event to be delivered twice. → Deduplicate using a stable business event identity. → Replay the event and confirm the balance changes only once. |

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

## Example results

Output from the self-contained Python/SQLite fixture:

```text
[('c1', 350)]
```

The raw c1 rows sum to 450 cents; deduplicating the identical e1 retry produces 350. Removing deduplication must trip the assertion. Conflicting payloads require the capstone's separate conflict gate.

## How to interpret the results

The correct eligible total is 350 cents. A naive sum for `c1` is 450 because it counts the retry. The null customer is excluded deliberately, so this query does not prove that all input orders reached a consumer. Track exclusions separately.

Change the second `e1` to 120 cents. The same event ID now has conflicting payloads; the grouping no longer deduplicates it. A production contract must either reject that conflict or define versions and a deterministic winner. Silently choosing `MAX(amount_cents)` would invent a business rule.

Add a uniqueness assertion for the dimension before joining. Next test an absent dimension key and compare inner versus left join results. Count unmatched rows explicitly. A successful query only proves the database executed it, not that every business entity was represented.

## Go deeper in SQL

### JOIN: row multiplication comes before engine choice

If an input key occurs `m` times on the left and `n` times on the right, an equality join contributes `m × n` matches for that key. Three orders joined to two customer history versions produce six rows. A hash join, merge join, and indexed nested loop all preserve that logical multiplicity; changing the algorithm cannot repair it.

An inner join removes unmatched orders. A left join preserves them with null dimension fields, but `WHERE dimension.region = 'KR'` then removes those null-extended rows. Put the condition in `ON` when the requirement is to preserve every order and match only Korean dimension rows. Use `NOT EXISTS` to find missing dimensions: `NOT IN` has a surprising unknown result if its subquery contains null. Before tuning, compare input rows, output rows, distinct fact keys, and unmatched counts.

### Window functions: ranking, peers, and explicit frames

`GROUP BY` reduces many input rows to one output per group. A window computes a value alongside each input row. `PARTITION BY customer_id` starts independent calculations; the window's `ORDER BY` orders that calculation and does not order the final result. Add an outer `ORDER BY` when displaying results.

For current-state deduplication, use `ROW_NUMBER()` over an explicitly authoritative version sequence. A timestamp alone can tie. For a running total, specify `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` and a deterministic order. A range frame includes peers with equal ordering values, which can advance several rows' totals at once. `LAG` compares with a preceding row; it does not imply that the preceding row occurred one calendar day earlier.

Run this separate in-memory SQLite example with Python 3. It demonstrates a tie, an explicit row frame, and a recursive CTE. The version rule is an input contract for this fixture; conflicts sharing the same `(event_id, source_seq)` must be rejected before this query.

<!-- executable: sql-windows -->
```python
import sqlite3

with sqlite3.connect(":memory:") as db:
    db.executescript("""
    CREATE TABLE changes(event_id TEXT, source_seq INT, amount INT);
    INSERT INTO changes VALUES ('e1',1,100),('e1',2,120),('e2',1,250);
    CREATE TABLE payments(id INT, minute INT, amount INT);
    INSERT INTO payments VALUES (1,10,100),(2,10,250),(3,11,50);
    """)
    current = db.execute("""
      WITH ranked AS (
        SELECT *, ROW_NUMBER() OVER (
          PARTITION BY event_id ORDER BY source_seq DESC
        ) AS position FROM changes
      )
      SELECT event_id, amount FROM ranked WHERE position=1 ORDER BY event_id
    """).fetchall()
    frames = db.execute("""
      SELECT id,
        SUM(amount) OVER (ORDER BY minute RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
        SUM(amount) OVER (ORDER BY minute,id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
      FROM payments ORDER BY id
    """).fetchall()
    depth = db.execute("""
      WITH RECURSIVE steps(n) AS (
        SELECT 1 UNION ALL SELECT n+1 FROM steps WHERE n<4
      ) SELECT SUM(n) FROM steps
    """).fetchone()[0]
    assert current == [('e1',120),('e2',250)]
    assert frames == [(1,350,100),(2,350,350),(3,400,400)]
    assert depth == 10
    print('current:', current)
    print('id, range_total, rows_total:', frames)
    print('recursive_sum:', depth)
```

Expected output:

```text
current: [('e1', 120), ('e2', 250)]
id, range_total, rows_total: [(1, 350, 100), (2, 350, 350), (3, 400, 400)]
recursive_sum: 10
```

The first payment's range total is already 350 because both minute-10 payments are peers. Remove the recursive `WHERE` and the query loses its termination condition. For graph traversal, additionally track visited identities or constrain depth so a cycle cannot expand indefinitely. A CTE names a query expression; it is not universally a cached temporary table. Check the engine's materialization behavior when a costly CTE is reused.

### Aggregation: subtotals and missing values

`GROUPING SETS ((region, day), (region), ())` asks for daily regional totals, all-day regional totals, and a grand total in one expression. Use `GROUPING(region)` and `GROUPING(day)` to distinguish a subtotal's placeholder null from a real missing value. `SUM` ignores null inputs; a group containing only null amounts yields null, not evidence of zero revenue. `COUNT(*)` counts rows, while `COUNT(amount)` counts non-null amounts. SQLite lacks `GROUPING SETS`; use DuckDB or PostgreSQL for that extension.

For money, define `DECIMAL(precision, scale)` or a fixed integer unit and a currency. Addition across currencies is invalid before conversion. For time, preserve a source offset or normalize a known instant to UTC, then derive the reporting day in the consumer's business zone. A local clock time during a daylight-saving transition can be ambiguous; a string with no zone cannot recover the missing offset.

### Read a query plan from the largest avoidable work

Consider `events JOIN users USING (user_id)` with an event-date filter. First estimate the surviving event rows after partition pruning. Then project the columns needed for the join and result. Predicate pushdown moves supported filters toward the scan; column pruning avoids unrelated column chunks; a distributed shuffle moves surviving rows between workers by key. These remove different kinds of work.

For PostgreSQL, `EXPLAIN (ANALYZE, BUFFERS)` executes the query and reports observed rows and loops. A node with 5,000 rows per loop and 1,000 loops is roughly five million row visits, not 5,000. Find the first major estimate/actual mismatch: stale statistics or correlated columns can cause a poor join choice. A selective OLTP query may benefit from a B-tree index and random lookups; a query reading most of a table can favor a sequential or columnar scan. Index maintenance also adds write work.

Read transactions separately from plans. PostgreSQL Read Committed can see different committed data in two statements of one transaction; Repeatable Read uses a stable transaction snapshot but can still require application logic for cross-row invariants. Serializable execution can reject a transaction that must be retried as a whole. For an order publication, define whether reconciliation and candidate selection must share one source snapshot. Otherwise two individually correct queries can describe different input populations.

## Python as pipeline infrastructure

### Typing, dataclasses, and serialization boundaries

Annotations document the record shape for readers and static checkers. A dataclass generates object methods; neither validates incoming JSON automatically. Validate at deserialization, before arithmetic. In Python, `isinstance(True, int)` is true, so a money field may need `type(value) is int`. Serialize a schema version and unit; JSON itself does not preserve a Python dataclass, decimal type, or timestamp zone. Use explicit conversion rules, and never deserialize an untrusted pickle as a record format.

### Iterators, generators, and context managers

A generator suspends at `yield`, allowing downstream code to consume one row or bounded batch at a time. This bounds the in-flight batch, not every other data structure: an unbounded deduplication set still grows with unique identities. `list(generator)` materializes all rows. A context manager's exit path runs during exception unwinding, so use it for file closure and transactions. SQLite's connection context manages commit/rollback; call `close()` or use `contextlib.closing` when connection lifetime itself must end there.

This fixture separates parsing from consumption and keeps a visible rejected count. It uses only Python's standard library.

<!-- executable: python-records -->
```python
import json
from dataclasses import dataclass
from itertools import islice

@dataclass(frozen=True)
class Event:
    event_id: str
    amount_cents: int

def parse(line: str) -> Event:
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError('record must be an object')
    key, amount = value.get('event_id'), value.get('amount_cents')
    if not isinstance(key, str) or not key or type(amount) is not int or amount < 0:
        raise ValueError('invalid identity or amount')
    return Event(key, amount)

def batches(rows, size):
    if size < 1:
        raise ValueError('positive batch size required')
    iterator = iter(rows)
    while batch := tuple(islice(iterator, size)):
        yield batch

lines = [
    '{"event_id":"e1","amount_cents":100}',
    '{"event_id":"bad","amount_cents":true}',
    '{"event_id":"e2","amount_cents":250}'
]
accepted, rejected = [], 0  # Small fixture; stream accepted records in production.
for line in lines:
    try:
        accepted.append(parse(line))
    except (ValueError, TypeError):
        rejected += 1
sizes = [len(batch) for batch in batches(iter(accepted), 1)]
assert (len(accepted), rejected, sizes) == (2, 1, [1, 1])
assert sum(row.amount_cents for row in accepted) == 350
print('accepted=2 rejected=1 total_cents=350 batch_sizes=[1, 1]')
```

Expected output:

```text
accepted=2 rejected=1 total_cents=350 batch_sizes=[1, 1]
```

Change the Boolean to a negative integer or a string and it must still be rejected. Production rejection handling should retain a controlled reason and identity without dumping the complete input into logs.

### Async, multiprocessing, memory, and tests

`asyncio` overlaps waits when the network/database client yields control. Calling a blocking client inside a coroutine still blocks that event loop. Bound concurrency with a semaphore or a fixed worker queue, apply timeouts, and decide how cancellation affects an already accepted remote write. A retry after timeout can repeat that write; use its stable idempotency identity. `TaskGroup` gives related tasks a shared lifetime, but creating a million tasks still allocates a million task objects.

For CPU-heavy Python transforms, processes can run work independently of one interpreter's execution lock on conventional CPython builds. Include process startup, pickling, and interprocess transfer in the measurement; transferring a large DataFrame for every tiny calculation can cost more than the work. Keep process worker functions importable and put the entry point behind `if __name__ == '__main__':` for spawn-based execution.

Use `tracemalloc` snapshots to identify Python allocation growth, and process RSS to see the broader footprint; native array buffers need not appear fully in Python allocation traces. Compare a streaming parser with `list(...)` on the same input, recording peak memory and elapsed time. Package the transform as an importable module with a CLI entry point and declared dependencies, so tests and the scheduled job execute the same code. In pytest, parametrize null, duplicate, conflict, empty, and boundary-time fixtures; compare incremental output with a full recomputation, rather than merely testing that a function returned.

Structured logging should include operation, code revision, run ID, and reason. Linux tools connect a job to CPU, RSS, disk space, file descriptors, and sockets; Git connects its behavior to a revision and diff. Capture those alongside the query plan when diagnosing a slow or changed result.

## Explain it in your own words

Why do integer cents help this fixture but not define a universal money model? The example has one fixed unit; real datasets need a currency, decimal scale, rounding policy, and potentially conversion-time semantics. Explain why a test with four rows can expose correctness while telling you little about distributed throughput.

Continue with [Parquet and object storage](03-parquet-object-storage.md).

<!-- source: https://docs.python.org/3/library/sqlite3.html | checked: 2026-09-10 | standard-library API; fixture independently executable -->
<!-- source: https://www.postgresql.org/docs/current/using-explain.html | checked: 2026-09-10 | estimates and execution plans -->
<!-- source: https://www.postgresql.org/docs/current/tutorial-window.html | checked: 2026-09-10 | windows and peers -->
<!-- source: https://www.postgresql.org/docs/current/queries-with.html | checked: 2026-09-10 | recursive CTEs and materialization -->
<!-- source: https://www.postgresql.org/docs/current/transaction-iso.html | checked: 2026-09-10 | isolation levels -->
<!-- source: https://docs.python.org/3/library/asyncio-task.html | checked: 2026-09-10 | task lifetime and concurrency -->
<!-- source: https://docs.python.org/3/library/tracemalloc.html | checked: 2026-09-10 | allocation tracing scope -->
