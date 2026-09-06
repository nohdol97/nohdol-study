# Feed Scraper Guide

It is a tool that automatically collects RSS sources into a connected vault. The reference implementation is
[It is at `examples/feed_scraper/`](../../examples/feed_scraper/), and the actual execution is
This is done in `_workspace/feed_scraper/`, a non-tracking area.

## Why this structure

The collection tool is **the code is the same on all computers, but what it collects varies from computer to computer**.
If you put these two in one file, you will have to modify the code every time you move it to another machine, and the changes will be
When committed to a harness, your personal choices are mixed into the trace file.

So we divided it into three.

| what | where | tracking |
|---|---|---|
| Engine and Source Catalog | `examples/feed_scraper/scrape.py` | O |
| Select this computer | `_workspace/feed_scraper/sources.local.toml` | X |
| Credential/Collection Status | `_workspace/feed_scraper/{.env,data/}` | X |

Even if it is in the catalog, it will not be collected if it is not in `enabled`. On laptops, only the robot source is available.
Even GeekNews on the desktop — the same code can be run differently.

### Once you have modified the code, copy it as a copy.

The cost of this structure is that **the engines are in two places**. What turns around is always `_workspace/`
Since it is a copy, the old code will continue to run unless you edit and copy the trace copy of `examples/`.
That actually happened on 2026-08-03 — the output was split into two layers: `raw/` and `wiki/`.
Since changes were not made to the copy, the entire day's collection was accumulated in `wiki/`, and the log was
They said it was normal.

```bash
cp -p examples/feed_scraper/scrape.py _workspace/feed_scraper/scrape.py
```

Even if you forget to copy, it will not pass quietly. Every time `run_scraper.sh` runs
Compare the SHA-256 of `scrape.py`·`run_scraper.sh`·`requirements.txt` with the traceback,
If there is a discrepancy, the file name and correction command are left at the beginning of the log. Even if it's off, it won't stop
No — The judgment is that running with old code is better than losing collection. manuscript
In some cases, the page is corrected first, so the direction of copying is determined by the person.

`README.md` and `sources.local.example.toml` do not collate. Collect even if divided
If the results do not change but the warnings become more frequent, the warnings themselves will not be read. Just take a copy
If you place it somewhere else (if `examples/` is not visible), the test will be quietly skipped.

## two pipelines

| pipeline | What you do | External API | output |
|---|---|---|---|
| `feed` | Just build titles and links | doesn't exist | 1 listing document per source |
| `geeknews` | Scoring → Summary and classification of those that pass the standard | Gemini | Original by date + month index + 7 topic documents |

### Why is the output divided into two layers?

There is only one standard — **Was human judgment involved?**

| output | location | Created by |
|---|---|---|
| Original by date | `vault/raw/geeknews/<연월>/<날짜>.md` | automatic |
| month index | `vault/raw/geeknews/<연월> 인덱스.md` | automatic |
| 7 topic documents | `vault/wiki/GeekNews/` | Classification is automatic, **you have to decide what to leave and which atomic note** |
| `feed` List by Source | `vault/wiki/<카탈로그의 path>` | automatic |

The original by date is an immutable capture of several unrelated posts in one day, and the monthly index is just a list of links created by scanning the folder. Since both have no curation judgment, they are stacked at `raw/`. If you place it in `wiki/`, all indicators that count atomic notes — orphan notes, `status` distribution, knowledge graph — will be swept away by the collection. In fact, before 2026-08-02, 177 of the 305 notes in `wiki/` were captured here, and 61% of `status: seed` were captured here.

Only subject documents remain in `wiki/GeekNews/`. So there are no subdirectories — if you dig `주제/` one more layer into a folder with only one type, the path will only get longer.

Obsidian resolves wikilinks by name throughout the vault, so the links remain the same even if the floors are different. The same goes for `[[2026-08-01]]` in the index and `[[2026.8 인덱스]]` in the hub.

> The table at `GeekNews 큐레이션 허브`, which contains a list of month indexes, is **maintained by hand.** The scraper creates the index but does not add any rows to the hub table, so when the month changes, no one points to the new index.

### Why `feed` does not summarize

Since the body is not read, the API call is 0. No matter how many sources you add, there is a free tier limit and
It is irrelevant. If you add a summary, the limit must be divided for each source, and the summary is not verified.
Because it is an unused product, it cannot be used as evidence. The title is enough to determine whether or not you will read it.

### Why `geeknews` summarizes

GeekNews has poll scores so the site is already measuring “what’s worth reading.”
Since only 8 to 12 cases per day pass through the 5P gate, the summary cost is covered. Up to topic classification
It is received in the same call and sent to the topic document.

## installation

```bash
mkdir -p _workspace/feed_scraper
cp -p examples/feed_scraper/* _workspace/feed_scraper/
cd _workspace/feed_scraper

python3 -m venv .venv                      # Python 3.11+ (tomllib)
.venv/bin/pip install -r requirements.txt

cp sources.local.example.toml sources.local.toml
$EDITOR sources.local.toml                 # 켤 소스 고르기

echo 'GEMINI_API_KEY=...' > .env           # geeknews를 켰을 때만
./run_scraper.sh
```

There are quite a few vault paths. The script goes up and has a symlink of `vault`.
Find the harness root. Only when running outside of the standard layout
Write `study_root` in `sources.local.toml`.

## Autorun (macOS launchd)

```bash
launchctl load -w ~/Library/LaunchAgents/com.user.study.feedscraper.plist
launchctl list | grep feedscraper
```

`ProgramArguments` should point to `_workspace/feed_scraper/run_scraper.sh`.
Since the wrapper derives the log/venv path from its location, the plist only needs that one line.
Enough.

### execution time

If you turn on `geeknews`, the time has meaning. Gemini daily limit (RPD) is Pacific
It resets at midnight**, which is **KST 16:00 based on PDT. Execution at 06:00 and 08:00 is based on Pacific
Since it is the same day, the limit is shared, and executions after 17:00 KST are allocated the next day.

If you only use the `feed` source, the time is probably good because there is no call. Feed window is 4 days
These sauces are more effective, so once a day is enough.

## add source

Add an entry to `SOURCES` in `scrape.py`, and to `enabled` in `sources.local.toml`.
Write down your key. Measure two things before adding them.

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
    'hub': "로봇과 피지컬 AI 정보 소스",
    'window_days': 14,
},
```

The measuring method and eliminated candidates (arXiv cs.RO, hnrss, etc.) are listed in the vault.
It's in the `[[로봇과 피지컬 AI 정보 소스]]` note.

### Filter feeds that are not topic-specific

If you give `title_filter`, you will only get items with one of those words in the title. Hugging
Used in feeds with some topics of interest, such as the Face blog — Among the 831 cases in the actual measurement, robot-related
There are 23 items (2.8%), so if you don't filter them, the rest will cover the list.

```python
'title_filter': ["robot", "lerobot", "embodied", "manipulat"],
```

Only the title is checked, not the body. If you look at the main text, there are many articles where the topic has passed by.
I got caught, and the article I was looking for already had that word in the title on GeekNews' list of favorites.
confirmed sea. Instead, the **word list is the recall**, so if you feel like you're missing something,
The list expands, but different topics are mixed in.

## current catalog

| key | sauce | pipeline | daily average | feed window |
|---|---|---|---|---|
| `geeknews` | GeekNews | `geeknews` | 8~12 (after gate) | 33 hours |
| `ieee-robotics` | IEEE Spectrum Robotics | `feed` | 0.4 | 67 days |
| `the-robot-report` | The Robot Report | `feed` | 3.7 | 4.1 day |
| `ros-discourse` | ROS Discourse | `feed` | 6.7 | 4.5 days |
| `robohub` | Robohub | `feed` | 0.4 | 191 days |
| `nvidia-robotics` | NVIDIA Robotics | `feed` | 0.2 | 118 days |
| `huggingface-robotics` | Hugging Face (Robot) | `feed` | 2.8% of 0.35 | broadness |

The daily average and window are actual measurements from 2026-07-26. It changes as the issuance cycle changes.

## Duplicate and Redo

All entries are saved with a marker — `feed` is `<!-- src:키:링크 -->`,
`geeknews` is `<!-- gn:topic_id -->`. No matter how many times you read it in a day, you will see the same article twice.
Since it does not enter, you can simply rerun the failed execution.

`geeknews` additionally caches the score in `data/pending/`. Summary is blocked at 429
Even if it is interrupted, the next run does not ask for the score again and only continues with the summary.

## problem solving

| symptoms | cause | action |
|---|---|---|
| `설정이 없습니다` | `sources.local.toml` not created | copy example |
| `켜진 소스가 없습니다` | `enabled` is empty or completely commented out | write down the key |
| `카탈로그에 없는 소스` | Typo in `enabled` | Matches catalog keys |
| `venv python not found` | Virtual environment not created | Above installation procedure |
| `GEMINI_API_KEY가 없어 건너뜁니다` | `.env` None | Insert key or turn off `geeknews` |
| 0 specific sources only | Change feed URL or outside window | Open the RSS directly to check |

## The product is not knowledge

The collected list is **a queue for picking things to read**, not knowledge. `feed` document
Each line is just a published title, and the one-line summary of `geeknews` is an unverified AI
It is a product. In both cases, it cannot be used as evidence for a claim. What I read and understood
Write it down in an atomic note as `note-writer`, and that note holds the evidence.
