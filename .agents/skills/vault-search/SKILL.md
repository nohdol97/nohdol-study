---
name: vault-search
description: Find curated notes by meaning rather than wording, using a local embedding index over wiki/ that never leaves this machine. Use when you do not know the exact words a note used, when checking whether a concept is already written down before adding a note, 비슷한 노트 찾아, 이거 이미 정리했나, 관련 노트, 의미 검색, and semantic search over the vault. Do NOT treat a result as evidence, do NOT use it for exact strings or filenames (that is rg), and do NOT use it to rebuild the wikilink graph (that is knowledge-graph).
---

# vault-search — Semantic search over curated notes

## Why

Keyword search finds a note only when you already guess its wording. Two of
this vault's recurring failures come from that gap: a concept gets written
twice under different words, and a question gets answered from the model's own
memory because the search that would have found the existing note used the
wrong term.

Embeddings close the gap and open a different one. A similarity score says two
passages sit near each other in a vector space — not that either is true, and
not that the relationship is the one you had in mind. So this skill searches;
it never concludes.

## Boundary

| Looking for | Use |
|---|---|
| An exact string, path, or filename | `rg` |
| A concept whose wording you do not know | this skill |
| What links to what, orphans, broken links | `knowledge-graph` |
| Whether a claim is true | the note itself, then the source it cites |

## Commands

```sh
# Ask a question in whatever words you have. This is the only command needed
# in normal use — it re-embeds notes that changed since the last run, then
# searches.
python3 .agents/skills/vault-search/scripts/semantic.py query --vault vault "에이전트 평가를 어떻게 게이트로 걸지"

# What the index knows and what has drifted
python3 .agents/skills/vault-search/scripts/semantic.py status --vault vault

# Full build. Needed once after install, or after changing the model.
python3 .agents/skills/vault-search/scripts/semantic.py build --vault vault
```

There is no rebuild step to remember. A rebuild that someone has to trigger is
one that quietly stops happening, and a stale index fails in the worst way
available — it returns plausible hits that omit the note just written, which
reads as "the vault does not have this." So `query` catches up first, embedding
only the notes whose content hash changed: a second or two after a writing
session, nothing at all when nothing moved. Use `--no-refresh` when you
deliberately want the index as it stands.

## Procedure

1. Query with the words you have. Do not pre-translate the question into what
   you guess the note's vocabulary is — that reintroduces the problem.
2. Read the ranked list as candidates. A score near the top of a small vault
   still may not be about your question.
3. **Open the notes you intend to use.** The excerpt in the output is there to
   help you choose which file to open, not to be quoted.
4. Confirm any factual claim in the note and in the source the note cites,
   exactly as if you had found the note by hand.
5. Do not schedule or script a rebuild. `query` handles drift; `status` is for
   when you want to see it. The index is derived, so losing it costs only the
   rebuild.

## Gates

- **A result is never evidence.** Ranked pointers are navigation. This is the
  same rule the knowledge graph carries, for the same reason: a derived
  artifact explains or locates, and does not establish.
- **Nothing leaves the machine.** The vault holds career material and private
  notes. The script refuses any endpoint that is not loopback rather than
  leaving that to configuration, and the index is written under `_workspace/`,
  outside the synced knowledge root.
- **An empty result is not a gap.** `query` refreshes changed notes first, so
  the index is normally current — but a concept can still be present under
  wording the embedding did not place nearby. Fall back to `rg` and
  `vault/index.md` before telling the user the vault does not cover something.
- **Do not add a note on the strength of an empty result alone.** Empty means
  the embedding found nothing near; check by hand before deciding the concept
  is new.

## Requirements

An embedding server on loopback, installed by `study-install`. Without it the
script says so and names the command to start it; it never silently degrades
to a worse search.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Finding a note | Requires guessing its wording | Found by meaning, in the asker's words |
| Duplicate notes | Same concept re-written under new words | Near-duplicates surface before writing |
| Privacy | An API-backed search would ship notes off-box | Loopback-only, refused otherwise |
| Result status | Ranked hit reads as an answer | Ranked hit is a pointer; the note is still opened |
