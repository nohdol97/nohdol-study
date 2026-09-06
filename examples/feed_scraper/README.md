# Feed Scraper Reference Implementation (Feed Scraper)

This is a script that automatically collects RSS sources into a connected vault. This directory is **reference**,
The actual execution is done in `_workspace/feed_scraper/`, an untracked area.

Full background and operating instructions are at [docs/guides/feed-scraper.md](../../docs/guides/feed-scraper.md).

## two pipelines

| pipeline | What you do | External API |
|---|---|---|
| `feed` | Only titles and links are stacked in a list document by source. | doesn't exist |
| `geeknews` | Scores are scored and only those that pass the standard are summarized and classified. | Gemini |

`feed` does not read the body, so the API call is 0. Free tier no matter how many sources you add
It has nothing to do with the limit. The person decides whether to read or not by looking at the title.

## installation

```bash
# 1. Copy to workspace
mkdir -p _workspace/feed_scraper
cp -p examples/feed_scraper/* _workspace/feed_scraper/
cd _workspace/feed_scraper

# 2. Virtual environment (Python 3.11+ — tomllib is used for configuration parsing)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Select the source to turn on
cp sources.local.example.toml sources.local.toml
$EDITOR sources.local.toml

# 4. API key (if you have geeknews enabled)
echo 'GEMINI_API_KEY=...' > .env

# 5. Run
./run_scraper.sh
```

`sources.local.toml`, `.env`, `.venv`, `data/`, `scraper.log` are all not tracked.
No. This is because it is a choice and qualification for each installation.

## Turn sources on and off

`SOURCES` of `scrape.py` is **catalog**, and `enabled` of `sources.local.toml` is
It is **choice**. Even if it is in the catalog, it will not be collected if it is not in `enabled`. per computer
We split the two because we had different interests.

```toml
enabled = ["ieee-robotics", "the-robot-report"]
```

## Add sources

Add one item to `SOURCES` in `scrape.py`. Before that, two things are measured.

1. **Availability of `published_parsed`** — If not, the date cannot be written, so it is skipped.
2. **Feed Window** — Time span from oldest to newest. `window_days`
   You need to hold more than that so you don't miss out on running it once a day.

```python
'my-source': {
    'name': "My Source",
    'pipeline': 'feed',
    'rss': "https://example.com/feed.xml",
    'path': "Robotics/My Source.md",     # vault/wiki/ 기준 상대 경로
    'tags': ["robotics", "feed"],
    'hub': "로봇과 피지컬 AI 정보 소스",   # 이 문서의 related가 가리킬 허브
    'window_days': 14,
    # Optional: Filter non-topic feeds by title.
    # 'title_filter': ["robot", "lerobot", "embodied"],
},
```

The measuring method and eliminated candidates are in `[[로봇과 피지컬 AI 정보 소스]]` in the vault.

## Autorun (macOS)

Use the `launchd` user agent. `ProgramArguments`
Just point it to `_workspace/feed_scraper/run_scraper.sh`.

If you have `geeknews` on, the execution time makes sense — Gemini daily limit is Pacific
It is reset at midnight (16:00 KST based on PDT), so execution after 17:00 KST is the same as execution before that.
Receive another assignment. If you only use the `feed` source, the time is good because there is no call.

## test

```sh
python3 examples/feed_scraper/scrape_test.py   # 엔진
sh examples/feed_scraper/run_scraper_test.sh   # 실행 래퍼의 어긋남 검사
```

Wrapper tests run in a temporary directory without venv, so neither the network nor the vault are touched.
No.

## Duplicate and Redo

All entries are saved with a marker at the end (`<!-- src:키:링크 -->`, GeekNews
`<!-- gn:id -->`). No matter how many times a day you turn, the same text will never be entered twice.
If the execution fails, just run it again.
