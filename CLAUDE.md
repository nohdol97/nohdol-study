@AGENTS.md

# Claude Code anchors

- Respond to the user in Korean unless they request another language.
- When installation state is missing, route to `study-install`.
- Search existing knowledge before answering; use `note-writer` for durable notes.
- Route harness changes through `metaskill`.
- Route selected sources through `ingest`; keep `/watch` frame analysis and NotebookLM export explicit-use only.
- Apply the always-on evidence rules before presenting or retaining material claims.
