# ADR 001 — File-based study harness Phase 1 structure

- Date: 2026-07-25
- Status: Active
- Targets: Repository skeleton, installation registry, vault connection, knowledge protocol, Claude Code·Codex hook.

## decision

| decision | detail | reason |
|---|---|---|
| Separate knowledge and harness | Only harness is tracked with Git, `vault` symlink and `REGISTRY.md` are not tracked. | Each computer has different knowledge location, content, and synchronization methods. |
| Select path is knowledge root | Create `raw/`, `wiki/`, and index/log/hot cache directly in the directory selected during installation. | Supports existing vault root and dedicated subfolders in the same model |
| Obsidian Optional | Install even if you do not have `.obsidian` and use the Markdown conventions as is. | Even without a graph UI, the core of the harness must operate through file manipulation alone. |
| No change to existing data | The installer only creates items that don't exist and does not migrate legacy notes. | Prevents contamination and data loss of user assets, including existing 245 notes |
| Markdown is the original | Wikilink is the source of the relationship and DB and visualization are derivatives. | Maintain tool neutrality and organ portability |
| Common skill source | Edit only `.agents/skills`, Claude uses symlinks, Codex uses native discovery | Prevent workflow drift between two CLIs |
| Common hook script | CLI-specific settings call the same SessionStart·Stop shell script. | Separate registration formats and manage operations in one place |
| No automatic tool installation | The Phase 1 installer only records the status and does not install Obsidian or CLI in the future. | Do not tamper with installation policy, network, or permissions. |
| vault Git local policy | Only the detection results are recorded in the registry and `git init` is not recorded. | Choices such as Google Drive, Obsidian Sync, and separate Git vary depending on the installation location. |
| Accuracy is verified on a per-claim basis | Prioritize primary sources, cross-verify important claims, record disconfirmation, uncertainty, and confirmation date | Prevents plausible misinformation from becoming knowledge assets |
| AI output is not evidence | Claude·Codex·Gemini·NotebookLM results are used only as an aid to exploration and analysis | Agreement between models is not independent observations and may share the same errors |

## result

The actual path, profile, and synchronization method selected on each computer remains only in the untracked `REGISTRY.md`, not in the public ADR.

Phase 2 adds web, paper, and video ingests after separate specifications and verification when they are actually needed. The graph index is measured after enough notes have accumulated.
