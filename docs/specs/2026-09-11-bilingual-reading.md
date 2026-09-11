# Bilingual article reading and terminology

Status: implemented

Every selected article supports Korean, English, and paired reading. Paired reading is the default: Korean comes first, followed by English that readers can collapse individually or together. Code, commands, output fixtures, and diagrams appear once. Interface language remains an independent preference.

## Acceptance criteria

1. Every article explicitly selects a Git-tracked Korean Markdown translation with a title and summary. Translations pass the same path, tracking, and realpath restrictions as English sources.
2. Each translation binds to its current English source's SHA-256. Stale bindings, incompatible block structures, and changed fenced examples reject the build. Translation does not advance factual evidence-review dates.
3. Three reading modes preserve the route and preference across reloads. Paired paragraphs, lists, headings, and tables remain readable on mobile. English passages support individual and collective disclosure without duplicating examples. Selecting English-only mode opens all English passages. Korean-only mode reads as ordinary prose.
4. Search finds both languages. Navigation localizes article titles and summaries while preserving IDs and destinations.
5. Every glossary entry explains why it matters and when to use it in both languages, separately from its definition. Each also includes an illustrative situation, application, and verification step; dialogs label and pair these steps. Chapter purposes and scenarios remain in Markdown definition tables or lists. Core entries, including CDC and dbt, also include distinctions from adjacent tools and source/context links. Missing English or Korean purpose, missing scenarios, and scenarios without three substantive steps reject publication. Terms are not inserted into code or links.
6. Checks cover the entire catalog, negative publication gates, modes, storage failure, keyboard interaction, terminology, search, diagrams, and deployment. No external translation service receives article or vault content.
7. Glossary tables and lists render as closed, keyboard-operable entries with immediately visible meanings. Expanding one reveals purpose and individually labeled situation/application/check paragraphs. Retain localized term names, and check bilingual link destinations in these entries just as in ordinary prose. Comparison tables remain tables. Dialog close controls remain reachable while scrolling.
8. Prefer concrete actors and verbs to chains of abstract nouns. Introductions start with a recognizable problem. Korean prose uses familiar Korean words for general concepts while preserving technical names, identifiers, code, source records, and links. Layout does not substitute for an editorial review.

## Maintenance

Recover historical Korean only for English passages unchanged since the English migration. Translate revised passages and the expanded Data course from current text. Review structure, identifiers, links, numerical conditions, and failure/recovery boundaries. Future source changes require reviewing Korean before refreshing its binding; hashes do not substitute for translation review.

## Verification

The 24 site tests cover all 94 translations, shared fenced code/results/diagrams, source-comment preservation, internal destinations, structural drift, stale source bindings, private and untracked paths, escaping symlinks, and reading preferences. Existing executable course fixtures also pass. The glossary extracts 403 chapter definitions with 375 distinct labels and adds 14 core technology explainers with role comparisons. All entries have bilingual purpose copy and three-part illustrative scenarios. Tests check separate extraction of meaning, purpose, and scenario, Markdown retention, complete coverage, and rejection of missing or malformed copy in either language. Chapter definitions retain their local context rather than merging ambiguous meanings. Coverage checks do not establish scenario accuracy or execution of its hypothetical actions.

Chrome checks render every article and all 108 diagrams, then exercise Korean, English, and paired modes, individual and collective disclosure, interface-language independence, route/reload persistence, Korean search, and diagram zoom. CDC and dbt dialogs pass keyboard activation, Escape, and focus return. All 94 articles are checked at 320 and 390 pixels, with additional 768-pixel samples. Blocked storage retains the selection during navigation in the current session. Screenshots are inspected for article, terminology, and theme legibility. These checks verify the reading interface and preserved examples; they do not establish execution of cloud or cluster labs.

The readability revision checks all 403 compact body entries and all 1,157 term dialogs offered across the 94 article routes. Expanded entries retain purpose and all three bilingual scenario steps. The dialog count includes definitions reused in related chapters. Editorial work rewrites 17 Data-course introductions and 88 definitions, and replaces unnecessary general English words in 76 Korean documents while preserving protected code, links, and source records. Fresh executable fixtures and translation checks verify the preserved technical examples; they do not measure human comprehension.
