# Phase 2b external source pins

This is the only tracked file under `.tools/`. Everything beside it is an
untracked third-party checkout placed by
`.agents/skills/study-install/scripts/install-phase2b-tools.sh`.

A pin names one immutable upstream commit. The installer downloads that exact
commit, recomputes the tree hash, and refuses to place a tree whose hash
differs. Release archives can be repackaged, so the authoritative identity is
the commit plus the tree hash, never the archive bytes.

Nothing here is executed by installing it. Node dependency installation, the
dashboard, and Figma stay out of Phase 2b-A.

## Record format

`name | ref_kind | ref | repo | commit | tree_sha256 | license | runtime`

`ref_kind` is `tag` when the upstream ref must still resolve to the pinned
commit; a moved tag then fails the install. It is `commit` when the pin is a
point on a moving branch, where re-pinning is expected and only the tree hash
is enforced.

`runtime` is the heaviest requirement among the tools inside the tree. It is
reported, not enforced at install time: placing source files executes nothing,
and one tree can hold tools with different needs. `understand-anything` is the
clearest case - its knowledge parsers import only the Python standard library,
most of its scan scripts need only Node's own modules, and just the dashboard,
the Figma path, and the graph-clustering scripts need an installed dependency
set. Gating placement on the heaviest of those would withhold the lightest.

`node18` names an interpreter and no package manager, which is what a tree
needs when its generated artifacts are committed rather than built. Recording
such a tree as `node22-pnpm10` would report a missing pnpm as the reason its
tools cannot run, and that explanation is false in a way the user would act
on.

Each adapter skill therefore states what it needs and refuses to run when that
is missing, rather than the installer refusing to place the files.

<!-- pins:start -->
```text
understand-anything | tag | v2.9.0 | Egonex-AI/Understand-Anything | f08763d11d0202a8a8f52b5dedda6d1b2e2ebac8 | 0a6de55dd7aaccb8016c87a11c67184745c91556e6c93ecef6da1e1d286b0f40 | MIT | node22-pnpm10
obsidian-skills | commit | main | kepano/obsidian-skills | a1dc48e68138490d522c04cbf5822214c6eb1202 | 792741b5577333482df2729d4b5f631d04704f96531c21c9c6ad13b4c194b7b8 | MIT | none
archify | tag | v2.13.0 | tt-a1i/archify | 2c1f8ac2ca28a26d0b68043ec80c9554e20ff0e3 | 39bb264a8520de5f4c63f775c005a8f422b811afd28222c33e04593d7aaf366d | MIT | node18
```
<!-- pins:end -->

## Provenance

| name | source | observed | notes |
|---|---|---|---|
| understand-anything | <https://github.com/Egonex-AI/Understand-Anything> | 2026-07-25 | Release `v2.9.0`. Ships the nine `understand-*` skills. The repository lock reports unresolved high-severity advisories, so no dependency install and no Node execution happen in Phase 2b-A. |
| obsidian-skills | <https://github.com/kepano/obsidian-skills> | 2026-07-25 | Branch `main` at the commit dated 2026-06-08. Ships `obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`, and an upstream `defuddle` that this harness does not adopt. |
| archify | <https://github.com/tt-a1i/archify> | 2026-08-09 | Release `v2.13.0`. The skill package is the `archify/` subdirectory; the rest of the tree is documentation, benchmarks, and rendered examples. Its only declared dependency is a dev-time `ajv`, and `renderers/shared/generated-validators.mjs` is committed, so the CLI is expected to run on the interpreter alone - the `doctor` command is what confirms that on a given machine. Upstream installs with `npx skills add -g`, which section 1 of `AGENTS.md` forbids; placement here is the pinned path instead. Three commits landed after the tag, one of them a renderer measurement fix, and re-pinning waits for the next release rather than tracking `main`. |

## Re-pinning

1. Choose the new upstream commit deliberately and read what changed.
2. Download that commit and compute the tree hash with
   `.agents/skills/study-install/scripts/tree_hash.py`.
3. Update the record above in the same commit as the reason for the change.
4. Remove the old checkout so the installer places the new tree instead of
   reporting a hash conflict.
