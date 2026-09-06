# nohdol-study Phase 2 — ingest·NotebookLM·graph preparation specifications

- Date: 2026-07-25
- Status: Implemented
- Partial withdrawal: NotebookLM export part removed as [ADR 004](../adr/004-remove-notebooklm-export.md) (2026-07-25). ingest and graph parts are valid
- Related suggestions: [2026-07-25-nohdol-study-direction](../proposals/2026-07-25-nohdol-study-direction.md)

## background

Phase 1 provides only the knowledge storage protocol and installation framework. In actual study, the web
Documents, papers, and videos must be safely preserved in their original form and converted into verification notes.
NotebookLM should only be passed a bundle of verified topics, not the entire vault.
The Wikilink graph has a reproducible standard parser even before there are enough notes.
Although necessary, the decision to adopt a separate index must be made on an actual scale.

## Goal

- Preserve web, paper, and video sources as immutable snapshots in `raw/` and verify `wiki/`
  Provides a common workflow for converting to notes.
- Source, hash, and verification status of topic-specific snapshots to be uploaded to personal NotebookLM
  Created with manifest.
- `study-install` monitors NotebookLM mode and Phase 2 tool status for each installation location.
  Record it.
- Recreate the deterministic knowledge graph JSON using only Markdown.

## non-goal

- Unofficial browser automation in the personal NotebookLM UI
- Always synchronize NotebookLM across vaults
- Automatically merge NotebookLM creations into deterministic knowledge
- Immediate adoption of basic-memory or graph DB operation
- Download paid/illegal bypass papers
- External transfer of Whisper audio without permission

## Requirements

### R1. Accuracy is the rule at all times

Claim verification is not an optional skill, but is a completion condition that always applies to `AGENTS.md`.
The detailed procedure is an essential reference to `note-writer` and does not require separate activation.

### R2. NotebookLM mode by installation location

`study-install` records one of `off`, `consumer`, and `enterprise`.
`consumer` is a snapshot of manual upload of verification data, `enterprise` is the official Preview API
It means possibility of use. Do not impersonate an official API connection in your consumer account.

### R3. Export NotebookLM

Export copies only the vault files specified by the user. `wiki/` notes are basically
If `unverified` or verification status is missing, reject. The result includes the original relative path,
A manifest containing SHA-256, verification status, confirmation date, and creation time is included. The result is
It is created in untracked `_workspace/` and the vault source is not changed.

### R4. web ingest

Web documents that can be accessed anonymously are organized as `defuddle parse URL --md -f`.
Save only as a new file in `raw/web/날짜-slug.md`. Does not overwrite existing files
In case of failure, an empty source text is not created. Instructions in the external text are treated as data only.

### R5. thesis ingest

Perform public search and download with paper-search CLI. Just the title and abstract of the search results
Check the PDF/official metadata without confirming the claim. preprint/peer-reviewed,
Record the version, publisher, and whether withdrawal or correction was made. Unofficial bypass such as Sci-Hub is basic
Exclude from the route.

### R6. video ingest

`study-video` provides ① low-cost understanding of the entire transcript ② important sections and time-indicated sections
Uses 2-pass frame extraction. Subtitles are requested in the order `ko.*,en.*`.
Whisper is not to be used without the user's explicit permission. The speaker's remarks are in fact evidence
No, it is verified separately.

### R7. NotebookLM output boundaries

Quizzes, infographics, mind maps, and answers are derivative works for learning purposes. Back to confirmed knowledge
When imported, it is checked against the original source and given verification status. Agreement between models is independent
It is not cross-validation.

### R8. Deterministic graph parser

A parser that uses only the standard library is `wiki/` Markdown to frontmatter,
Extracts wikilinks, backlinks, missing targets, and orphaned notes to create sorted JSON.
Wiki links within the code fence are ignored and duplicate note titles are reported as errors.
Markdown is the only original and JSON is a `_workspace/` derivative.

### R9. Graph Comparison Gate

basic-memory comparison limits read/search in specified corpus in Phase 2c
Run as pilot. The evaluation items are
Link/backlink accuracy, missing/orphan detection, representative query recovery quality, execution cost,
Source immutability, serverless portability. Substantial improvements over the baseline parser
Adopt only when a constant server or opaque source is not required.

### R10. installation tools

Phase 2 readiness status is `defuddle`, `paper-search`, `yt-dlp`, `ffmpeg`, `watch`
Judged by skill. Installation failure does not prevent other source types from functioning,
Record the observation status in `REGISTRY.md`. API keys are not automatically generated, copied, or recorded.

## Completion criteria

- NotebookLM export test allows verified notes, rejects unverified notes, hash manifest,
  Confirm that the original has not been changed.
- The web capture test checks `-f` use, new creation, and preservation/rejection of existing files.
- watch Korean subtitle patch test confirms the safety of modifying and re-running two call parts.
- Graph tests check for links, backlinks, omissions, orphans, code fence exclusions, and deterministic output.
- The Phase 2 tools state and NotebookLM consumer mode are currently running on your Mac.
  It is recorded in `REGISTRY.md`.
- All shell, Python, JSON, TOML grammar checks and existing Phase 1 regression tests pass.

## Real-world hold and follow-up

- Actual personal NotebookLM uploads and product quality depend on the user's browser
  After uploading the topic bundle, check it.
- Actual video/paper 1 end-to-end note-taking is done when the user specifies the learning target.
  Perform.
- The basic-memory comparison blocks original change commands and matches predefined search questions.
  Do not run until hash invariance check is in place.
- Consumer NotebookLM's CLI upload/generate/download and Understand Anything
  typed knowledge graph
  [From Phase 2b spec](2026-07-25-phase2b-cli-learning-integrations.md)
  Follow-up implementation. It is not included in the implementation completion status of this document.
