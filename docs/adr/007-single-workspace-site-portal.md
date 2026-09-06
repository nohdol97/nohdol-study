# ADR 007 — Dynamic site for users opens from single portal `_workspace`

- Date: 2026-08-16
- Status: Active
- Subject: `AGENTS.md` Section 7, `examples/workspace_portal/`, `_workspace/sites/`
- Related specs: [Workspace Site Portal](../specs/2026-08-16-workspace-site-portal.md)

## context

Robot AI Systems Academy was initially created on the premise of an independent root called `_workspace/robot-ai-expert-academy/` and a dedicated HTTP server. In the future, as the number of sites such as simulators, dashboards, and learning maps increases, you will need to launch a separate server in each directory and remember the port. The files were all under the same `_workspace`, but only the entry point and execution life cycle were different.

`_workspace/` is an untracked output for each installation site, so the actual site cannot be entered into Git. Conversely, if you do not track the path and registration method at all, the next agent creates another independent server. Therefore, **policies and creation tools are tracked, portal and site data are not**.

## decision

Dynamic HTML sites that users repeatedly use in their browsers are subject to the following agreement.

```text
_workspace/
├── index.html
├── sites.json
├── assets/
└── sites/
    └── <slug>/
        └── index.html
```

- The site is placed under `_workspace/sites/<slug>/`.
- The relative entry point must be registered in `_workspace/sites.json` and searchable and accessible in `_workspace/index.html`.
- The server displays `_workspace` as the document root only once. Do not create servers and ports for each site.
- The site's internal assets and page URLs use relative paths that do not break even when moved under the portal root.
- `examples/workspace_portal/portal.py` is responsible for initialization, registration, and inspection. This tool does not overwrite existing portal files and rejects path traversal and non-existent entry points.
- Internal outputs such as Understand analysis results, build cache, temporary reports, and tool dashboards are not automatically registered. It is registered only when the user requests that it be exposed as a site to be used repeatedly.

Currently, Robot AI Systems Academy moves to `_workspace/sites/robot-ai-expert-academy/` and registers as the first portal entry.

## Why not just one giant SPA

The data structure, UI, and life cycle are different for each site. When combined into a single application bundle, even small modifications expand the scope of deployment and regression for all sites. The portal only provides discovery and a common server root, and each site maintains independent static assets and tests.

## Why not an automatic directory scan?

There are many directories in `_workspace/` that should not be visible to the user or are not entry points, such as knowledge graph, embedding index, transcript, and test output. When you create a directory as an automatic card, internal output is blended into the public UI. An explicit manifest reveals what the site treats as user-facing.

## Source of truth and preservation boundaries

Portals and sites are derivatives of Markdown knowledge and are not evidence. Since `_workspace/` is excluded from knowledge synchronization with Git, knowledge that requires long-term preservation is continuously recorded in the vault. If the site creation code is worth reusing, place a template/generator in the tracking area, but do not include the installation path or actual manifest.

## result

- Users only need to open `http://127.0.0.1:4173/`.
- New sites are discovered simply by creating a directory and registering a manifest.
- Each site develops independently, but has one server life cycle.
- If the portal does not exist or the entry is broken, the deterministic check fails.
