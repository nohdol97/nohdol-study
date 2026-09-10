# Optional local documentation checks

These checks use synthetic fixtures and separately installed local tools. They do not connect to a cloud account or an existing database. Run the standard `npm test` suite from docs-site/ for catalog, link, JSON, and self-contained Python checks.

## Data and Observability detail labs

Run the seven marked standard-library examples directly from their course Markdown:

```sh
python3 docs-site/labs/verify_data_course.py
```

The checker compares actual stdout with documented output for SQL windows/recursion, Python record validation, SCD history, quality dimensions, histogram math, cycle-safe lineage traversal, and hybrid retrieval. No packages or network are required.

For optional local engine checks, use a scratch virtual environment with `opentelemetry-sdk==1.44.0`, `duckdb==1.5.0`, `dbt-duckdb==1.11.0`, and `dbt-core==1.12.4` installed. The verifier installs nothing:

```sh
python docs-site/labs/verify_data_course.py --optional
```

It executes actual OTel propagation through an in-memory exporter, both documented Parquet layouts, and the dbt model/macro/property files extracted from the modeling chapter. A fresh temporary dbt project checks initial publication, correction, identical retry, and full-rebuild equality. It also reproduces the documented deletion limitation: the incremental model retains a removed source row until a full rebuild. Anonymous dbt usage reporting is disabled. All tables/files are synthetic and local; no broker, cloud account, model API, or external telemetry destination is used. The temporary receipt directory is retained for inspection.

## PostgreSQL

Supply the directory of a complete PostgreSQL 18 installation, including `postgres`, `initdb`, `pg_ctl`, `psql`, and backup tools. A client-only libpq package is insufficient.

```sh
python3 docs-site/labs/verify_postgresql.py --bin /path/to/postgresql/bin
```

The script extracts SQL from the backend, messaging, and PostgreSQL chapters. It creates a fresh temporary cluster with TCP disabled, verifies conditional writes, event identity, duplicate delivery, rollback/retry, a blocked transaction, and dump/restore with constraint rejection, then stops the cluster. It retains the temporary receipt directory and prints its path. Do not run as root. macOS may require permission for PostgreSQL shared memory and its local Unix socket.

Expected summary lines include `Backend: PASS`, `Lock observer: PASS`, and `PostgreSQL: PASS`. The first output line records the actual server version. No production RPO or failover behavior is tested.

## Prometheus rules

In a fresh scratch directory, save the complete rules fence from [the SLO lab](../content/observability-sre/02-correlation-and-alert-lab.md) as `sample-api.rules.yml` and copy `slo-tests.json` from this directory next to it. Run your installed promtool there:

```sh
promtool check rules sample-api.rules.yml
promtool test rules slo-tests.json
```

Expected results are `SUCCESS: 3 rules found` and `SUCCESS`. The six series fixtures test sustained 2% errors, the 0.1% target error rate, recovery after a burst, counter resets, zero traffic, and missing series. The last two must not fire this fast-burn alert; separate coverage rules are still required. No pager or monitoring server is configured.
