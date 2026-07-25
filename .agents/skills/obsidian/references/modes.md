# Obsidian modes

Shared boundaries are in `../SKILL.md`. This file holds what is specific to
each mode. The upstream workflow for a mode is at
`.tools/obsidian-skills/skills/<mode>/SKILL.md`.

---

## `obsidian-markdown` — Obsidian Flavored Markdown

Needs nothing installed.

Covers what Obsidian adds to CommonMark: wikilinks, embeds, callouts,
properties, and comments. Standard Markdown is assumed.

1. Put properties in frontmatter. In this vault the note contract in
   `AGENTS.md` decides which properties a curated note must carry, and it
   wins over upstream's examples.
2. Use `[[wikilinks]]` for notes inside the vault so renames keep working, and
   `[text](url)` for external URLs.
3. Embeds are `![[target]]`, including headings (`![[Note#Section]]`) and
   blocks (`![[Note^id]]`).
4. Callouts are `> [!type]`, optionally `+` or `-` for folded state. Use a
   type from the pinned reference; an invented type renders as a plain quote.
5. Run the validator on the file before calling it done.

Upstream references worth reading for detail: `references/PROPERTIES.md`,
`references/EMBEDS.md`, `references/CALLOUTS.md`.

---

## `obsidian-bases` — database-like views (`.base`)

Needs nothing installed.

A base is YAML describing filters, formulas, and views over the notes already
in the vault. It stores no content of its own.

1. Decide the scope first with `filters`. A base over the whole vault is
   rarely what the user meant.
2. Add `formulas` only for values that cannot be read from a property.
3. Every entry under `views` needs a `type` and a `name`.
4. Indent with spaces. A tab makes the file fail to load.
5. Run the validator. Remember it is a structural pre-check, so report the
   result as "not obviously broken", not as verified.

Upstream reference: `references/FUNCTIONS_REFERENCE.md`.

---

## `json-canvas` — canvases and knowledge maps (`.canvas`)

Needs nothing installed. Format: JSON Canvas 1.0.

1. Start from `{"nodes": [], "edges": []}`.
2. Give every node a unique 16-character hex id, a `type` of `text`, `file`,
   `link`, or `group`, and integer `x`, `y`, `width`, `height`.
3. Type-specific fields are required: `text` needs `text`, `file` needs
   `file`, `link` needs `url`.
4. Edges reference nodes by `fromNode` and `toNode`; both must exist. Sides
   are `top`, `right`, `bottom`, or `left`.
5. Lay nodes out on a grid with real spacing. Coordinates are absolute, and
   overlapping boxes are the usual failure when a canvas is generated rather
   than drawn - leave at least the node's own height between rows.
6. A `file` node pointing at a vault note is what makes a canvas a knowledge
   map rather than a picture. Prefer it over restating note text in a `text`
   node.
7. Run the validator before calling it done.

Upstream reference: `references/EXAMPLES.md`.

---

## `obsidian-cli` — drive a running vault

Needs Obsidian 1.12.7+ installed **and running**. Check with
`command -v obsidian`; when it is missing, report the mode as unavailable and
use the file-format modes instead. Never install Obsidian to satisfy this.

1. `obsidian help` lists the current commands and is more current than any
   summary here.
2. Parameters take values with `=` and are quoted when they contain spaces;
   flags are bare. `file=` resolves like a wikilink, `path=` is exact from the
   vault root.
3. Commands target the most recently focused vault unless `vault=` says
   otherwise. State which vault you are about to touch - the wrong vault is
   the expensive mistake here.
4. Before any command that creates, edits, moves, or deletes, say what will
   change. Reading needs no ceremony.
5. Plugin and theme debugging commands execute JavaScript in the running app.
   Treat that as a change to the user's environment: name what you will run
   and why before running it.
