# Understand Anything modes

One skill routes to all nine upstream entry points. This file holds what is
specific to each mode; the rules they share live in `adapter-contract.md`.

Each mode's upstream workflow is at
`.tools/understand-anything/understand-anything-plugin/skills/<name>/SKILL.md`.
Read that file for the mode you selected, and follow it inside the contract.

---

## `understand` — build the code graph

The entry point that produces what the consumer modes read: file, symbol,
dependency, and architecture layers plus a dependency-ordered tour.

Runtime: **built package**.

1. State the target repository root, whether `.ua/` is ignored there, and what
   the run will write. Confirm before the first write.
2. Report what the graph covers and what its ignore rules excluded.
3. The result is a map for reading, not a substitute for it.

Unavailable alternative: read the code with the harness search tools, or use
`knowledge-graph` for this vault's curated notes.

---

## `understand-chat` — locate behavior, then read it

Runtime: **graph consumer**.

1. Query only the part of the graph the question needs; never load a whole
   graph file into context.
2. Open the candidate files. The answer is finished only after this, and it
   names the file and line it rests on.
3. If reading shows the candidates were wrong, say the graph misled you rather
   than shaping the answer to fit it.

---

## `understand-explain` — source-first explanation

Runtime: **graph consumer**.

1. Use the graph to choose the smallest set of files carrying the concept.
2. Quote signatures, conditions, and data shapes verbatim instead of
   paraphrasing them into something tidier.
3. Explain in dependency order: what it receives, decides, and emits.
4. Name what you did not read, and hand back the reading order so the user can
   follow the same path.

---

## `understand-onboard` — dependency-ordered learning path

Runtime: **graph consumer**.

1. Cut the dependency order down to a path a person can finish.
2. Open each step's entry file before writing that step. A walkthrough
   pointing at code nobody opened is where a stale graph does the most damage.
3. Record for each step why it comes here, what to open, and what the reader
   should be able to explain afterwards.
4. Mark where the path stops. When it is worth keeping, hand it to
   `note-writer` with the commit it came from.

---

## `understand-diff` — change impact overlay

Runtime: **graph consumer**. Freshness matters most here: the very edits being
analyzed are the ones the graph does not know about.

1. State both the diff scope and the graph's base version.
2. Overlay changed files to list touched components and their dependents.
3. Open the changed files and the dependents that matter. Reachability is not
   evidence that behavior breaks.
4. Report impact as confirmed by reading, suspected and unread, or outside
   what the graph covers. The overlay alone is never a review verdict.

---

## `understand-domain` — business domain view

Runtime: **graph consumer**, plus `python3` for the bundled extraction script.

1. Derive candidate actors, workflows, and rules from the graph.
2. Drop every candidate with no code reference. A plausible domain term that no
   file implements is invention.
3. Open the implementing files and confirm the behavior matches the name.
4. Separate what the code enforces from what a naming convention suggests.
5. Record open questions where intent is not decidable from code.

---

## `understand-knowledge` — Markdown knowledge extraction

Runtime: **Python only**. The one mode that runs with no dependency install.

Input condition: the upstream parser expects `index.md` and several Markdown
files. A knowledge root with one or two notes is refused by design - report
that as a data condition and keep using `knowledge-graph`, which is valid from
the first note.

1. Send output to `_workspace/understand-anything/`, never inside the vault.
2. Confirm the vault is unchanged: Markdown paths and hashes must match before
   and after.
3. Report the deterministic layer (links, backlinks, categories) apart from the
   inferred layer (entities, claims, implicit relations).
4. Write inferred items as `records` with `kind`, `label`, `source_path`,
   `evidence_anchor`, `extractor`, `confidence`, and `verification`, then
   validate them with `knowledge-graph --semantic`. It resolves every anchor
   inside the cited note and drops what does not hold.
5. An accepted record is still a candidate. Promote it through `note-writer`
   only after reading the note and its source.

---

## `understand-dashboard` — loopback viewer

Runtime: **built package**.

1. Run only when the user asked for the dashboard in this turn. Upstream opens
   it automatically after an analysis; that is not adopted.
2. Never run a dependency install to satisfy the runtime.
3. Bind to loopback only. Give the URL and how to stop it, and stop it when
   the exploration is done.
4. Anything read off the dashboard is navigation, confirmed in the file before
   it goes anywhere.

Unavailable alternative: explore the same graph through CLI or JSON queries.

---

## `understand-figma` — approved design file analysis

Runtime: **built package**.

1. Confirm the user named the file in this turn. Never infer a file key from
   context or history.
2. State what leaves the machine - the file key, that content is fetched from
   `api.figma.com`, and what the analysis keeps - and get approval first.
3. The token comes from the environment for that run only. Do not search for
   one, copy it, or record it in this repository, the vault, or `REGISTRY.md`.
4. Write output to `_workspace/understand-anything/`.
5. Approval covers this run and this file. A later file needs a new one.
