# Workspace Site Portal Specifications

- Date: 2026-08-16
- Status: Implemented
- Related Decision: [ADR 007](../adr/007-single-workspace-site-portal.md)

## Goal

- `_workspace` provides one entry point to the dynamic site for users.
- Eliminates site-specific HTTP servers and port operations.
- Allows the next agent to reproduce the same path/manifest contract without tracking the actual local site.

## non-goal

- Portal replaces vault Markdown
- Automatic exposure of internal analytes and tool dashboards
- Integrate site bundles into one framework or build system
- Internet public, authentication, remote hosting

## Requirements

### R1. single document root

The user site is under `_workspace/sites/<slug>/`, and `_workspace` is the HTTP document root. During normal use, no site-specific server process is required.

### R2. explicit manifest

`_workspace/sites.json` is a version 1 object, and `slug`, `title`, `description`, `href`, `category`, `tags`, `updated`, and `status` are placed on each site. `href` only points to actual files under `sites/<slug>/`.

### R3. portal navigation

`_workspace/index.html` shows the non-archived site of the manifest as a card and provides title, description, classification, tag search and classification filter. Each card opens a site entry with a relative URL.

### R4. Secure initialization and update

`portal.py init` only creates portal files that do not exist and does not overwrite existing local edits. `register` updates the same slug without creating duplicates. Rejects absolute paths, `..`, entries outside the slug, and entries that do not exist.

### R5. Separate tracked and untracked

Template·manager·test·rules are tracked in Git. The created `_workspace/index.html`, `sites.json`, and the actual site will continue to be excluded from Git. The absolute path to the installation location is not recorded in the trace file.

### R6. derivative border

Portals and registration sites are not knowledge evidence. Internal scratches and analysis results are not registered in the manifest unless the user requests exposure.

## Completion criteria

- In the empty temporary workspace, init creates 4 portal files and overwrites 0 when rerun.
- Normal site registration, same slug update, and duplicate tag normalization pass.
- Path traversal and entries outside the slug are rejected.
- When deleting the registered entry file, the check fails.
- In fact, the `_workspace` portal check passes with only one registration at the Robot AI Systems Academy.
- On a single portal server, `/`, `/sites.json`, Academy entry and core assets return HTTP 200.
