# Feed scraper reference implementation

This directory contains the portable engine, source catalog, example configuration, and tests. Runtime copies belong under `_workspace/feed_scraper/`.

Follow the [feed scraper guide](../../docs/guides/feed-scraper.md) for first-time setup, expected diagnostics, copy updates, and scheduling. Setup refuses an existing destination so local selections are not overwritten.

| Pipeline | Model calls | Main limitation |
|---|---|---|
| `feed` | None; it still fetches public RSS over HTTP | Titles and links are a reading queue, not verified notes |
| `geeknews` | Gemini summarization and classification | Generated summaries require source verification |

Running collection writes to the connected knowledge root. Review source selection and output paths first. Inject model credentials externally; do not create a workspace `.env` or paste secrets into a shell command. Marker deduplication covers sequential reruns, not concurrent writers.

```sh
python3 examples/feed_scraper/scrape_test.py
sh examples/feed_scraper/run_scraper_test.sh
```

Passing tests verifies the local fixtures, not live source availability or factual quality.
