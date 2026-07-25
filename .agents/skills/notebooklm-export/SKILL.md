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

   The script refuses a note whose frontmatter still says `unverified`. That
   refusal is the evidence gate, not an obstacle: resolve the claim or drop the
   note. `--include-unverified` exists only for a corpus the user explicitly
   asked to export while unresolved, and the packet then carries that status.
   Never add the flag on your own to make a failed export succeed.

7. Verify the packet still matches its own manifest before anything leaves
   the machine:

```sh
.agents/skills/notebooklm-export/scripts/verify-packet.sh \
  _workspace/notebooklm/<topic>-<timestamp>
```

   It re-hashes every listed file, refuses symlinks without reading through
   them, refuses a file in `sources/` the manifest never listed, and refuses
   an `unverified` note. A packet that fails is not uploaded. An entry beside
   `00-manifest.md` and `sources/` is surfaced as a note, not a failure, so a
   flattened upload copy is visible rather than silent.

8. Review `00-manifest.md`, then upload the files under `sources/` to
   NotebookLM. The manifest should be uploaded too. Upload the packet as
   produced; if a file must be renamed or flattened for the upload UI, record
   that in the manifest rather than creating an undocumented copy.
9. In NotebookLM, generate quizzes, flashcards, infographics, mind maps, study
   guides, or use source-grounded chat.
10. Treat every generated artifact as unverified derived material. Before
   bringing a conclusion back into `wiki/`, inspect the cited source passage
   and apply the note-writer evidence protocol.

## The optional CLI bridge is blocked

Uploading is manual on purpose. A CLI bridge (`notebooklm-py`) would remove
that step, and ADR 003 allows it only once the latest stable release contains
the audited download-redirect fix. Check where that stands:

```sh
.agents/skills/notebooklm-export/scripts/bridge-gate.sh
```

It reads release metadata and nothing else - it never installs, never
authenticates, and never sends vault content. It fails closed: an unreachable
API blocks, because "I could not tell" is not permission when the risk is a
known unfixed vulnerability. Pre-releases do not count as stable.

Measured 2026-07-25: the latest stable release is `v0.7.3`, which does not
contain the fix - the guard module is absent from that tree and the download
path still follows redirects without re-validating each hop. The fix ships
only in `v0.8.0` pre-releases. **Do not install the CLI, do not authenticate,
and do not attempt a transfer.** Passing the release gate would still not be
permission on its own: a dependency audit of the exact extras and a separate
user-run authentication step come after it.

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
