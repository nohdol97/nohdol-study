---
name: notebooklm-export
description: Build a topic-scoped, evidence-preserving snapshot for manual upload to consumer NotebookLM, including selected vault sources, SHA-256 hashes, verification states, checked dates, and a manifest. Use when the user wants NotebookLM quizzes, flashcards, infographics, mind maps, study guides, or source-grounded Q&A from their study notes. Triggers include NotebookLM, 노트북LM, 퀴즈로 공부, 인포그래픽, 학습 자료 묶음, and RAG처럼 질문.
---

# notebooklm-export — Verified study packet

## Why

Uploading the whole vault leaks unrelated context and makes source freshness
opaque. A narrow, hashed snapshot makes the learning set reviewable and
reproducible while keeping NotebookLM downstream of the vault.

## Boundary

NotebookLM is a derived learning workspace, not the vault source of truth.
Consumer mode uses explicit snapshots and manual upload. Do not automate the
consumer web UI or claim continuous sync.

## Procedure

1. Confirm `REGISTRY.md` records `NotebookLM: consumer` or `enterprise`.
2. Define one narrow notebook topic and learning goal. Do not export the whole
   vault.
3. Search `vault/wiki/` and select only notes materially relevant to that goal.
4. Apply the mandatory evidence rules in `AGENTS.md`. Resolve central
   `unverified` claims or exclude those notes.
5. Include the primary `raw/` sources needed to inspect evidence. Prefer
   source-preserving selection over lossy compression.
6. Run:

```sh
.agents/skills/notebooklm-export/scripts/export.sh \
  --name topic-slug \
  vault/wiki/relevant-note.md \
  vault/raw/relevant-source.pdf
```

7. Review `00-manifest.md`, then upload the files under `sources/` to
   NotebookLM. The manifest should be uploaded too.
8. In NotebookLM, generate quizzes, flashcards, infographics, mind maps, study
   guides, or use source-grounded chat.
9. Treat every generated artifact as unverified derived material. Before
   bringing a conclusion back into `wiki/`, inspect the cited source passage
   and apply the note-writer evidence protocol.

## Refresh

The export is a timestamped snapshot. When a source version or note meaning
changes, create a new packet; do not silently edit a previously uploaded packet
and assume NotebookLM refreshed it.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Scope | Whole-vault upload | Explicit topic files only |
| Provenance | Notebook sources drift silently | Relative paths, hashes, dates, status |
| Knowledge return | Generated answer may be trusted | Underlying source rechecked before retention |
