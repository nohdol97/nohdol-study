# Feed scraper guide

The reference implementation in [examples/feed_scraper](../../examples/feed_scraper/README.md) collects selected public feeds. Run an installation copy under `_workspace/feed_scraper/`; source selections and collection state are machine-specific.

## What it reads and writes

| Pipeline | External requests | Output |
|---|---|---|
| `feed` | RSS HTTP requests; no model API calls | Source-specific title/link lists under `wiki/` |
| `geeknews` | Feed/article requests and Gemini summarization/classification | Daily captures and monthly indexes under `raw/geeknews/`; topic queues under `wiki/GeekNews/` |

These outputs are reading queues and generated summaries, not verified atomic knowledge. The existing writer does not perform the complete note-writer evidence review or update the master index, log, and hot cache for every generated entry. Running it authorizes actual knowledge-root writes; review the selected paths and obtain installation-specific authorization before enabling collection. Promote useful material through `ingest` and `note-writer`.

The monthly index is derivative and regenerated; the daily capture is normally preserved once present. Do not set `GEEKNEWS_OVERWRITE` on retained captures as a routine retry. The curated hub's month links are maintained separately.

## First-time setup

Use Python 3.11 or later. Run this only when the target copy does not exist; updating an existing installation requires a diff so local configuration is preserved.

```bash
test ! -e _workspace/feed_scraper || exit 1
mkdir -p _workspace/feed_scraper
cp -p examples/feed_scraper/* _workspace/feed_scraper/
cd _workspace/feed_scraper
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp sources.local.example.toml sources.local.toml
```

Edit `sources.local.toml` before the first run:

```toml
enabled = ["ieee-robotics", "the-robot-report"]
```

Catalog entries in `SOURCES` are available choices; only `enabled` entries run. The script discovers the harness through its parent directories. A custom layout may specify `study_root` in the local configuration.

If enabling `geeknews`, inject `GEMINI_API_KEY` through your machine's credential manager or a protected launcher outside the harness, vault, and workspace. Never put the key in a tracked file, a workspace `.env`, shell history, or chat. The loader supports externally provided environment variables even though legacy `.env` loading remains in the implementation.

Once source selection, write scope, and any model transmission are approved:

```bash
./run_scraper.sh
```

This command fetches sources and can change the connected knowledge root. There is no documented dry-run switch.

## Example results and interpretation

Representative diagnostic lines from the implementation; normal collection counts vary with publication times and filters.

```text
켜진 소스가 없습니다. sources.local.toml의 enabled를 확인하세요.
GEMINI_API_KEY가 없어 건너뜁니다
```

The first means no source is selected. The second means the model-dependent pipeline cannot run; feed-only collection needs no Gemini key. A zero new-item count can mean no recent matching publications or that all items are already present, so inspect the feed window and markers before diagnosing a failure.

Success means the expected selected-source entries appeared at the reviewed paths, duplicates were suppressed on a sequential rerun, and no unexpected file changed. It does not mean the titles or generated summaries have been fact-checked.

## Updating the installation copy

The wrapper compares SHA-256 for `scrape.py`, `run_scraper.sh`, and `requirements.txt` with the reference copy when available. Drift is logged but does not stop collection. Compare changes before copying a reviewed file:

```bash
diff -u examples/feed_scraper/scrape.py _workspace/feed_scraper/scrape.py
```

A diff exit of 1 means differences. Stop the installation's scheduled run before replacing executable files, then rerun the reference tests and a bounded collection check. Never overwrite `sources.local.toml`, local state, or credentials during an update.

## Adding a source

Add the catalog definition to `SOURCES`, then explicitly enable its key in the local configuration. Inspect the live feed for parseable publication dates and retention window. A `window_days` setting cannot recover entries already removed by the publisher.

```python
'my-source': {
    'name': "My Source",
    'pipeline': 'feed',
    'rss': "https://example.com/feed.xml",
    'path': "Physical AI/My Source.md",  # Relative to wiki/.
    'tags': ["robotics", "feed"],
    'hub': "로봇과 피지컬 AI 정보 소스",
    'window_days': 14,
    'title_filter': ["robot", "lerobot", "embodied"],
},
```

This is a catalog fragment, not a standalone Python program. The URL is a placeholder. Title filtering trades coverage for relevance; measure missed titles before claiming complete coverage. Source publication rates and historical feed-window measurements are not permanent guarantees.

## Scheduling, retries, and cleanup

Use one scheduler for each installation copy. A launchd job needs a machine-specific label, absolute executable path, schedule, working environment, and log handling; the reference repository does not install a complete personal plist. Validate those locally before enabling it.

Markers such as `<!-- src:key:link -->` and `<!-- gn:topic_id -->` suppress repeated entries in ordinary sequential runs. They are not a concurrency lock or an atomic multi-file transaction. Avoid overlapping manual and scheduled runs; inspect partially written output before retrying. Gemini quotas and reset times must be checked in the selected provider account rather than inferred from an old schedule.

To retire collection, unload only its owned scheduler job. Preserve captured sources and local selection/state unless their deletion is separately intended. Test fixtures belong in a disposable directory, never in a production vault.

## Verification

```sh
python3 examples/feed_scraper/scrape_test.py
sh examples/feed_scraper/run_scraper_test.sh
```

The tests exercise fixtures and wrapper behavior. They do not prove live feed availability, successful provider authentication, correct factual summaries, or a running scheduler.
