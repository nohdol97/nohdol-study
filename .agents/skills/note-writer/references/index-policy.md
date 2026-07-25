# Index policy

`vault/index.md` is the entry point to the knowledge root. Its job is to answer
"where do I start", not "what exists".

## The failure this prevents

An index that names every note grows at the same rate as the vault. At twenty
notes it still reads; at two hundred it is a wall nobody scans, and the one
surface meant to orient a reader becomes the surface they skip. The size of an
index must track the number of **topics**, not the number of notes.

## Rules

1. **One hub per topic.** A topic gets one line naming its hub note. The hub
   carries that topic's atomic notes; the index does not repeat them.
2. **Never list atomic notes in the index.** If a topic has no hub yet and holds
   more than two or three notes, write the hub (`type: topic`) instead of adding
   lines to the index. Creating a note cluster means creating its map.
3. **Cap the recent-change section.** Keep roughly the five most recent lines and
   say plainly that `log.md` is the record. `log.md` is append-only and complete;
   a second, hand-trimmed copy in the index only drifts from it.
4. **A dangling entry is reported, not hidden.** If the index names a note that
   does not exist, either write the note, mark the entry as having no note, or
   remove it. Leaving a broken `[[wikilink]]` in the entry point is worse than
   either.
5. **Deleting an index line never deletes knowledge.** Collapsing a topic behind
   a hub, or dropping a stale entry, only changes navigation. The notes and their
   sources stay where they are.

## Writing a hub note

A hub is a map, not evidence. It uses `type: topic` and states up front that
facts and their verification live in the notes it links, not in the map. Useful
sections: what the topic's axis is, a table of "which note answers what", a
suggested reading order, and the open questions the whole cluster shares.

Every note in the cluster should link the hub back through `related`, so the hub
is reachable from any member.

## Mechanized check

`vault-gardening` reports an index that has started to list rather than orient:

```sh
python3 .agents/skills/vault-gardening/scripts/garden.py --vault vault
```

It counts distinct wikilink targets in `index.md` (embedded assets excluded) and
reports when they exceed `--index-link-budget`, default 15. The budget is a
smell threshold, not a law: a vault with genuinely many topics can raise it. What
it should never do is grow because atomic notes were added to the index.
