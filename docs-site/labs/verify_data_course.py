#!/usr/bin/env python3
"""Run marked course examples; optional engines use only fresh local fixtures."""

import argparse
import importlib.metadata
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
COURSE = ROOT / "docs/guides/data-observability"
EXAMPLE = re.compile(
    r"<!-- executable(?P<optional>-optional)?: (?P<name>[a-z-]+) -->\n"
    r"```python\n(?P<code>[\s\S]*?)```"
    r"[\s\S]*?Expected output[^\n]*\n\n```text\n(?P<output>[\s\S]*?)```"
)
REQUIRED = {
    "sql-windows", "python-records", "scd-history", "quality-dimensions",
    "histogram-math", "lineage-impact", "hybrid-retrieval",
}


def check_examples(optional):
    seen = set()
    for source in sorted(COURSE.glob("*.md")):
        for example in EXAMPLE.finditer(source.read_text()):
            if example["optional"] and not optional:
                continue
            name = example["name"]
            if name in seen:
                raise AssertionError(f"duplicate example: {name}")
            seen.add(name)
            result = subprocess.run(
                [sys.executable, "-I", "-c", example["code"]],
                text=True, capture_output=True, timeout=30, check=True,
            )
            if result.stdout != example["output"]:
                raise AssertionError(f"{name}: output differs\n{result.stdout}")
            print(f"{name}: PASS")
    expected = REQUIRED | ({"otel-propagation"} if optional else set())
    if seen != expected:
        raise AssertionError(f"missing/unexpected examples: {seen ^ expected}")


def check_duckdb(directory):
    import duckdb

    source = (COURSE / "03-parquet-object-storage.md").read_text()
    scripts = re.findall(r"```sql\n([\s\S]*?)```", source)
    with duckdb.connect() as db:
        for script in scripts:
            # Paths are fixed teaching filenames, redirected into this fresh lab.
            for name in ("events.parquet", "events_unsorted.parquet"):
                script = script.replace(f"'{name}'", "'" + str(directory / name).replace("'", "''") + "'")
            db.execute(script)
        for name, candidates in (("events.parquet", 1), ("events_unsorted.parquet", 13)):
            target = str(directory / name)
            assert db.execute("SELECT COUNT(*),SUM(amount_cents) FROM read_parquet(?)", [target]).fetchone() == (100000,10000000)
            assert db.execute("SELECT COUNT(*),SUM(amount_cents) FROM read_parquet(?) WHERE event_date=DATE '2026-01-02'", [target]).fetchone() == (3334,333400)
            count = db.execute("""
              SELECT COUNT(*) FROM parquet_metadata(?) WHERE path_in_schema='event_date'
              AND CAST(stats_min_value AS DATE)<=DATE '2026-01-02'
              AND CAST(stats_max_value AS DATE)>=DATE '2026-01-02'
            """, [target]).fetchone()[0]
            assert count == candidates, (name, count)
    print(f"DuckDB {duckdb.__version__}: PASS (equal rows/totals; candidate groups 1 versus 13)")


def check_dbt(directory):
    import duckdb

    project = directory / "dbt"
    for name in ("models", "seeds", "macros"):
        (project / name).mkdir(parents=True, exist_ok=True)
    (project / "dbt_project.yml").write_text(
        "name: study_depth\nversion: '1.0'\nconfig-version: 2\nprofile: study_depth\n"
        "seeds:\n  study_depth:\n    order_changes:\n      +column_types:\n"
        "        event_id: varchar\n        amount_cents: bigint\n"
        "        updated_at: timestamp\n        source_seq: bigint\n"
    )
    (project / "profiles.yml").write_text(
        "study_depth:\n  target: local\n  outputs:\n    local:\n"
        "      type: duckdb\n      path: study.duckdb\n      threads: 1\n"
    )
    (project / "models/stg_orders.sql").write_text(
        "select event_id,cast(amount_cents as bigint) amount_cents,"
        "cast(updated_at as timestamp) updated_at,cast(source_seq as bigint) source_seq "
        "from {{ ref('order_changes') }}\n"
    )
    source = (COURSE / "07-modeling-orchestration.md").read_text()
    model = re.search(r"```sql\n(\{\{ config[\s\S]*?)```", source)[1]
    macro = re.search(r"```sql\n(\{% macro[\s\S]*?)```", source)[1]
    properties = re.search(r"```yaml\n([\s\S]*?)```", source)[1]
    (project / "models/fct_orders.sql").write_text(model)
    (project / "macros/cents_to_units.sql").write_text(macro)
    (project / "models/schema.yml").write_text(properties)
    (project / "models/money_view.sql").write_text(
        "select event_id,{{ cents_to_units('amount_cents') }} as amount_units "
        "from {{ ref('fct_orders') }}\n"
    )
    env = dict(os.environ, DBT_SEND_ANONYMOUS_USAGE_STATS="false", DBT_USE_COLORS="false")
    executable = Path(sys.executable).with_name("dbt")

    def run(*args):
        result = subprocess.run(
            [str(executable), *args, "--profiles-dir", str(project), "--project-dir", str(project)],
            cwd=project, env=env, text=True, capture_output=True, timeout=90,
        )
        with (directory / "dbt-output.txt").open("a") as log:
            log.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f"dbt {' '.join(args)} failed; inspect {directory / 'dbt-output.txt'}")

    def seed(rows):
        (project / "seeds/order_changes.csv").write_text(
            "event_id,amount_cents,updated_at,source_seq\n" + "\n".join(rows) + "\n"
        )
        run("seed", "--full-refresh")

    def result():
        with duckdb.connect(str(project / "study.duckdb"), read_only=True) as db:
            return db.execute("SELECT event_id,amount_cents FROM fct_orders ORDER BY event_id").fetchall()

    seed(["e1,100,2026-09-10 01:00:00,1", "e2,250,2026-09-10 02:00:00,1"])
    run("build")
    assert result() == [("e1",100),("e2",250)]
    seed(["e1,120,2026-09-10 03:00:00,2", "e2,250,2026-09-10 02:00:00,1"])
    run("build")
    assert result() == [("e1",120),("e2",250)]
    run("build")
    assert result() == [("e1",120),("e2",250)]
    run("build", "--full-refresh")
    assert result() == [("e1",120),("e2",250)]
    with duckdb.connect(str(project / "study.duckdb"), read_only=True) as db:
        assert abs(db.execute("SELECT SUM(amount_units) FROM money_view").fetchone()[0] - 3.7) < 1e-9
    print(f"dbt-core {importlib.metadata.version('dbt-core')} / dbt-duckdb {importlib.metadata.version('dbt-duckdb')}: PASS (350 -> 370 -> 370; full rebuild equal)")

    # Reproduce the documented unsupported deletion, then demonstrate full rebuild.
    seed(["e2,250,2026-09-10 02:00:00,1"])
    run("build")
    assert result() == [("e1",120),("e2",250)]
    run("build", "--full-refresh")
    assert result() == [("e2",250)]
    print("dbt deletion boundary: CONFIRMED (incremental retains e1; full rebuild removes it)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--optional", action="store_true", help="also require installed OTel, DuckDB and dbt; no installation")
    args = parser.parse_args()
    check_examples(args.optional)
    if args.optional:
        directory = Path(tempfile.mkdtemp(prefix="study-data-depth-"))
        print(f"Local fixture receipt: {directory}", flush=True)
        check_duckdb(directory)
        check_dbt(directory)


if __name__ == "__main__":
    main()
