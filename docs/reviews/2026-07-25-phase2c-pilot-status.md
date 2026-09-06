# Phase 2c pilot — prerequisite ground truth and current verdict

- Date: 2026-07-25
- Target: basic-memory (basicmachines-co), PaperQA2 (Future-House)
- Related: [ADR 003](../adr/003-cli-learning-integrations.md);
  [Additional Tool Review](2026-07-25-additional-tools-review.md),
  [Task handover](../handoffs/2026-07-25-next-session.md)
- Verdict: **PaperQA2 = Impossible to run (prerequisites not met)**, **basic-memory = Pilot completed, not adopted due to read-only conditions not met**

## Why this document?

Phase 2c plans to run both tools “only when there is a corpus/provider specified by the user.”
This is a limited pilot. As a result of receiving the request to proceed and measuring the premise, we can now run both.
Because I don't have it, I leave a list of what I can't do because I don't have it and what I made in advance.

## Actual measurement (2026-07-25)

| item | observed value |
|---|---|
| `basic-memory` CLI | Not installed (`uv` is available and can be installed) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | All three are unset |
| `vault/wiki` (curation tier) | 1 note |
| `vault/raw/papers` | 1 PDF |
| Legacy Markdown from the Knowledge Root | `GeekNews` 169, `공부` 30, `AX` 18, `도서` 9, `경제` 2 |
| `~/study` (legacy outside harness) | 881 |

## PaperQA2 — not executable

It is blocked in two layers.

1. **Absence of provider.** PaperQA2 requires LLM and embedding provider, but there is no key.
   does not exist. Even if a key is created, the body of the paper is exported as an external model, so according to AGENTS Section 5
   Explicit approval for each execution comes first.
2. **No corpus.** Since there is only one preserved paper, “in-depth inquiry” comparison is not possible.

Therefore, it was not installed and no installation procedure was created. A tool that cannot be returned once made
This means writing down the usage instructions without verifying them.

Reexamination trigger: User collects paper corpus, specifies provider, and sends externally.
When approving.

## basic-memory — Pilot run results (not adopted)

The user specified `vault/공부` as the corpus and executed it. Not the original, but a scratch
I ran it from a copy, and that decision decided the outcome (B2 below).

### execution conditions

The original `vault/공부` is a total of 194 files, including 30 mds, and among the mds, frontmatter is
There are 4, and there are only 4 wiki links. That is, a legacy that does not follow the note contract of this harness.
It is a corpus. After re-checking the original after the pilot, `permalink` insertion was 0, frontmatter
There are still 4 of them and they are **completely pollution free**.

### B1. Installation portability — 3 attempts

Python 3.12.4 of venv created by `uv tool install basic-memory` is
Even project registration failed because `sqlite3.enable_load_extension` is not supported.
(`'sqlite3.Connection' object has no attribute 'enable_load_extension'`).
Python 3.11 does not meet version requirements (0.14.0b1 prerelease only),
It worked only after specifying and reinstalling `--python /opt/homebrew/bin/python3` (3.14.6).
It depends on the Python build of the installer, and the baseline uses only the standard library.

### B2. Index Modifies Notes — Crucial Reason

`reindex` (103 seconds, 190 entity) **edited all 30 markdowns**. before each file
Rewrite frontmatter:

```yaml
---
title: 명령어
type: note
permalink: study-pilot/docker/myeongryeongeo
---
```

Korean titles are converted to Roman permalinks. Search presupposes an index, and an index presupposes writing.
Therefore, **there is no mode that does not touch the original while using a search.** This means that this pilot
This means that the premise (“prohibit automatic writing, check original hash”) cannot be structurally met.

If you went directly to the original, 30 personal notes in Google Drive would have been modified.

### B3. There are no external transfers — OK

The embeddings are local `fastembed`/`bge-small-en-v1.5` and `cloud_api_key: None`.
There was no violation of AGENTS Section 5. However, **the English model is used in the Korean corpus**
This remains a limitation in search quality.

### B4. Search is actually useful

Find related documents using pre-written questions: `GitOps` →
`04-ci-cd-gitops`(score 0.845), `MSA` → `msa-communication`, `FastAPI` →
`fast-api`. Files with the same name in different folders are also distinguished by permalinks with namespace.

One bug: The `total` field in the response is `0` even if there are 10 entries in `results`. Shame
You shouldn't believe it as it is.

### B5. The baseline fails outright in this corpus.

The deterministic graphs have duplicate titles of `Docker/명령어.md` and `Kubernetes/명령어.md`.
A hard failure occurs and the graph cannot be created. If you delete one and run it again, it will be deleted from 29 notes.
There are 6 edges, **52 broken links, and 23 orphans** (0.19 seconds).

This is not a flaw in the baseline, but **scope**. Curated by wikilink and frontmatter
It was created for `wiki/`, and the structure cannot be found in legacy notes that do not follow its conventions.
There is nothing. In contrast, basic-memory provides searching in such a corpus.

### verdict

**The two are not in competition.** The baseline determines the structure of the curated notes.
Measure, basic-memory provides search in uncurated piles.

The reason for not adopting now is **ownership**, not search quality. basic-memory is
Make the frontmatter of the note your own. It's up to the user to decide whether to pay that price.
It's nothing to hide - it's a useful legacy note search tool if you decide to use it.

### Reexamination trigger

- When the user decides, "I want to retrieve legacy notes and I don't mind if the frontmatter changes."
  In that case, the target is limited to the legacy directory, not `wiki/`.
- When basic-memory provides a read-only indexing mode that does not modify the original.

## Premade — pilot harness

In order to be able to run immediately once the corpus is determined, the valid parts regardless of the corpus are first
Implemented: `.agents/skills/knowledge-graph/scripts/pilot.py`.

- Snapshot all Markdowns in the corpus as SHA-256 before and after execution, even if only one
  If additions, deletions or modifications are made, the candidate will be disqualified. It is irrelevant what the candidate reported.
- Instructions with segments such as `write`·`format`·`reset`·`sync` are **before execution**
  I refuse. Since it is viewed in hyphen units, `write-note` is caught, and `rm` in `format` is
  No false positives.
- Deterministic baselines (nodes, edges, missing, orphans, runtime) are measured and placed in the same table.
- **Candidate commands are received as arguments.** The command line of the CLI that has not been installed and has not read the help
  Don't write it down from memory — the very unverification that this harness prohibits elsewhere.
  Because it is a claim.

The effectiveness of each invariant was confirmed through mutation (change detection, pre-blocking, addition/deletion)
Detection/Temporary output organization).

## installation status

`basic-memory` 0.22.1 is installed on this machine (`uv tool`, Homebrew Python 3.14).
The pilot project registration was canceled and the default project was returned to `main`. not adopted
Since it is not used, harness does not call this tool. If you don't need it
It is okay to remove it with `uv tool uninstall basic-memory`.

## Change history

| date | Changes | reason |
|---|---|---|
| 2026-07-25 | Premise measurement/judgment record, pilot harness implementation | Request to proceed with Phase 2c — Confirm that both tools cannot be implemented due to unmet prerequisites, and first implement effective safety devices regardless of corpus |
| 2026-07-25 | basic-memory pilot execution/non-adoption decision | User specifies `vault/공부` as corpus. When run on a copy of scratch, we see that the index modifies all 30 markdowns — the read-only premise is structurally unsatisfactory. The search itself is valid, no external transmission |
