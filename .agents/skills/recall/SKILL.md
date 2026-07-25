---
name: recall
description: Turn verified notes into spaced-repetition cards that stay traceable to the passage they came from, and check that every card still resolves. Use for 복습, 플래시카드, 암기 카드, 반복 학습, 퀴즈 만들어줘, and keeping earlier study from fading. Do NOT make cards from an unverified note, do NOT write a card whose answer is not in the note it cites, and do NOT treat card review as evidence that a claim is still true.
---

# recall — Cards that can be traced back

## Why

Understanding fades on a schedule, and spaced repetition is the cheapest fix
known. It is also the point where knowledge is most compressed, and compression
is where evidence gets lost: a card is a claim stripped of everything that made
it checkable.

So a card here names the note and the passage it came from. That makes it
possible, months later, to ask not only "did I remember this" but "was this
right", which is the question that matters when the source turns out to be
wrong.

## Make cards only from notes that earned it

- The note's `verification` must be better than `unverified`. Memorising an
  unchecked claim is worse than not memorising it, because recall feels like
  knowing.
- One card, one idea. A card that needs a paragraph to answer is a note that
  has not been split yet - fix the note first.
- Ask for what the note actually establishes. If the note says a study found
  something under specific conditions, the card asks that, not the general
  claim it resembles.
- Do not make a card for something the user will meet often enough to learn
  anyway.

## Format

Cards live in the vault beside the notes, in the multi-line format the
Obsidian spaced-repetition plugin reads:

```markdown
Why does a physical mistake matter more than a software one?
?
It causes harm in the world rather than a wrong screen.
<!-- from: physical-ai.md#Safety -->
```

The provenance comment is required. It names a note in `wiki/` and an anchor
inside it - a heading, or a phrase that appears literally in the note. The
review plugin appends its own scheduling comment (`<!--SR:...-->`); leave it
alone, and never hand-edit a schedule.

## Check before filing

```sh
python3 .agents/skills/recall/scripts/cards.py --wiki vault/wiki CARDS.md
```

It resolves every card's provenance: the note must exist in the wiki and the
anchor must resolve inside it, using the same anchor rule the knowledge graph
applies to inferred records. A card whose anchor resolves nowhere is refused,
because that is the shape a card takes when its answer drifted away from what
the note says.

Run it again after editing the notes. An anchor breaks when the passage it
named is rewritten, and that is exactly when the card should be re-examined.

## Review is not verification

Recalling a card correctly means you remember what the note said. It says
nothing about whether the note is still true. When a card matters and time has
passed, follow its provenance to the note, then the note to its source, and
apply the evidence rules. Update the note first and the card second - the card
is downstream.

Scheduling belongs to the review tool, not to this skill: `obsidian-spaced-
repetition` keeps the state in the file, and `Obsidian_to_Anki` can export the
same cards if the user prefers Anki. Either way the cards stay Markdown in the
vault, so nothing here depends on a plugin being installed.

## With / without

| Metric | Without this skill | What this adds |
|---|---|---|
| Traceability | A card is an orphan claim | Provenance to note and passage, checked |
| Drift | A rewritten note leaves stale cards | The anchor breaks and the card resurfaces |
| Source quality | Cards made from any note | Only from notes past `unverified` |
| Meaning of a pass | Remembering read as knowing | Recall and truth kept apart |
