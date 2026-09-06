# ADR 002 — Phase 2 Collection·NotebookLM·Graph Maintain Derived Workflow

- Date: 2026-07-25
- Status: Active
- Target: Web/paper/video ingest, NotebookLM, deterministic graph, accuracy rules

## decision

| decision | detail | reason |
|---|---|---|
| Accuracy always applied | Verification of important claims is subject to the completion of `AGENTS.md`, and only detailed procedures are referred to `note-writer`. | Separate `evidence-check` skills may be missing verification the moment they are not routed. |
| Separate capture and knowledge | External data is stored as `raw/` immutable snapshot, and analysis is stored as `wiki/` verification note. | Prevents the risk of altering the original text to fit the conclusion and loss of sources. |
| NotebookLM consumer mode | The packet that only related files are exported along with the hash manifest is taken as the default boundary. | Both manual upload and subsequent CLI bridge reproduce the same scope and version. |
| NotebookLM output is a derivative work | Quizzes, pictures, and answers are not recognized as evidence until they are compared to the original source. | Model products are training aids, not independent observations |
| Enterprise Separation | `gcloud`·Project·License·API·Only installation sites with confirmed certification use the official API path. | Permissions models are different for private consumer workflows and Cloud managed APIs |
| Open thesis path | Only use paper-search's open sources as the default path. | Maintain reproducibility and legal access boundaries |
| Video 2-pass | First, understand the entire subtitle and then view only important timestamps as frames. | Reduces the image token cost of long videos and compensates for missing visual information |
| Whisper express approval | The default is `--no-whisper`; Use only after approval for external audio transmission of the video. | Prioritize data transmission boundaries over transcription convenience. |
| Deterministic graph criteria | Recreate JSON from Markdown with the Python standard library | Creates the same results in both CLIs without a server or MCP and protects the original authority. |
| basic-memory gate | The pilot is limited by the specified corpus, search question, and original hash invariant conditions, not the number of notes. | Measure actual search utility and non-destructiveness instead of arbitrary scale criteria |

## Determination of installation location status

`study-install` is NotebookLM mode and whether local export is ready, `defuddle`,
Untracked by observing skills `paper-search`, `yt-dlp`, `ffmpeg`, and global `watch`
Record in `REGISTRY.md`. Consumer account login and actual upload are local files
Since it cannot be confirmed through inspection alone, it is left as `account-unverified`.

API key, Cloud project, and NotebookLM account information are not written to storage or vault.
Installation failure does not prevent other source types, and does not prevent actual usable executables.
Check again to determine the status.

## result

Phase 2 adds the ability to take materials and pass them on to learning tools, but
The original is still Markdown. `_workspace/`'s NotebookLM packet and graph JSON are
Even if deleted, it can be recreated.

Personal NotebookLM's optional CLI bridge and the full Understand Anything skill.
Consolidation is separately restricted at [ADR 003](003-cli-learning-integrations.md).
