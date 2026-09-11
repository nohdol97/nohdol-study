# Bilingual article reading and terminology

Status: implemented

Every selected article supports Korean, English, and paired reading. Paired reading is the default: English precedes its Korean explanation, which readers can collapse to check comprehension. Code, commands, output fixtures, and diagrams appear once. Interface language remains an independent preference.

## Acceptance criteria

1. Every article explicitly selects a Git-tracked Korean Markdown translation with a title and summary. Translations pass the same path, tracking, and realpath restrictions as English sources.
2. Each translation binds to its current English source's SHA-256. Stale bindings, incompatible block structures, and changed fenced examples reject the build. Translation does not advance factual evidence-review dates.
3. Three reading modes preserve the route and preference across reloads. Paired paragraphs, lists, headings, and tables remain readable on mobile. Korean explanations support individual and collective disclosure without duplicating examples.
4. Search finds both languages. Navigation localizes article titles and summaries while preserving IDs and destinations.
5. In-article terminology, including CDC and dbt, explains purpose, a small example, distinctions from adjacent tools, and primary sources. Terms are not inserted into code or links.
6. Checks cover the entire catalog, negative publication gates, modes, storage failure, keyboard interaction, terminology, search, diagrams, and deployment. No external translation service receives article or vault content.

## Maintenance

Recover historical Korean only for English passages unchanged since the English migration. Translate revised passages and the expanded Data course from current text. Review structure, identifiers, links, numerical conditions, and failure/recovery boundaries. Future source changes require reviewing Korean before refreshing its binding; hashes do not substitute for translation review.

## Verification

The 20 site tests cover all 94 translations, shared fenced code/results/diagrams, source-comment preservation, internal destinations, structural drift, stale source bindings, private and untracked paths, escaping symlinks, and reading preferences. Existing executable course fixtures also pass. The glossary extracts 403 chapter definitions with 375 distinct labels and adds 14 core technology explainers with examples and role comparisons; chapter definitions retain their local context rather than merging ambiguous meanings.

Chrome checks render every article and all 108 diagrams, then exercise Korean, English, and paired modes, individual and collective disclosure, interface-language independence, route/reload persistence, Korean search, and diagram zoom. CDC and dbt dialogs pass keyboard activation, Escape, and focus return. All 94 articles are checked at 320 and 390 pixels, with additional 768-pixel samples. Blocked storage retains the selection during navigation in the current session. Screenshots are inspected for article, terminology, and theme legibility. These checks verify the reading interface and preserved examples; they do not establish execution of cloud or cluster labs.
