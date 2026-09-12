# nohdol-study skill guide

This English guide maps each skill's purpose, triggers, and boundaries. Execution rules live in each directory's `SKILL.md`; this guide has one section per skill. New or renamed skills are reliably discovered in the next CLI session. The historical `README.ko.md` filename is retained to preserve existing links. Korean trigger aliases remain available as functional inputs.

The public [Data & Observability course](../../docs/guides/data-observability/00-roadmap.md) is a learning resource, not a new skill. Use existing study routing for guided learning and source verification. All 94 articles support Korean, English, and paired reading. Paired mode puts Korean first and lets readers collapse English passages. Compact glossary entries expand to reveal purpose and illustrative situation/application/check steps in both languages. The Data course starts with concrete situations and plain-language definitions. See the [bilingual reading specification](../../docs/specs/2026-09-11-bilingual-reading.md).

Its [technical depth specification](../../docs/specs/2026-09-10-data-course-depth.md) covers individual stack mechanisms, worked examples, and executable local checks. The detailed source-topic map is in the course's source-review chapter; local fixture success remains separate from managed-platform or distributed-system evidence.

Public lab results distinguish local fixtures, expected environment-dependent outputs, and synthetic review receipts. The [documentation review](../../docs/reviews/2026-09-10-full-documentation-review.md) records verification limits; these examples create no new skills and are not knowledge evidence.

All 20 Data and Observability/SRE translations have also received a [Korean explanation review](../../docs/reviews/2026-09-12-data-observability-korean-readability.md), covering definitions, mechanisms, and exercise interpretation. This editorial review does not change skill routing.

## archify

- **One-line role**: Create architecture, workflow, sequence, data flow, and lifecycle diagrams into **single-executable HTML** with the pinned Archify CLI. This is a one-shot output for presentation and sharing.
- **When to use**: When a user directly points to archify or requests a diagram that is interactive, clickable, shareable, or presentation-ready. **For explicit calls only**.
- **When not to use**: Diagram to be included in notes (→ `diagram`), simply because the structure is complicated. Complexity is a reason to upgrade from Mermaid to D2, not a reason to change the format.
- **Why is it out of the vault**: The output is about 600KB HTML, but Obsidian does not embed HTML, and the knowledge root is cloud synchronized, so all devices pay for that capacity. Additionally, there is no SVG output path in the CLI (`bin/archify.mjs`), so there is no file to embed — the viewer's PNG/SVG export is a button in the browser, not an executable command.
- **Core procedure**: Check `ready` with `install-phase2b-tools.sh --check` → `node .tools/archify/archify/bin/archify.mjs doctor` → Select type and write spec JSON to `_workspace/archify/` → Repeat `validate` → `deliver` once.
- **Complete Criteria**: HTML and JSON specs are side by side in `_workspace/archify/`, with absolute paths, types, and validation summaries, and honestly report whether **you actually saw the render result**.
- **Caution**: The SHA-256 receipt taken by `deliver` and the number of checks made by `9/9` are **render pipeline integrity** and not evidence of what the diagram claims. `preview` is a local loopback server, so turn it off with Ctrl-C before passing it over. Upstream recommended installation method `npx skills add -g` is not used because it is prohibited by Section 1 of `AGENTS.md`.

## context7

- **One-line role**: Check the documentation of the current version of the library/framework to ensure that outdated API knowledge is not treated as current fact.
- **When to use**: When asking about SDK usage, configuration keys, migration, version-specific API signatures, and library debugging.
- **When not to use**: Collection of general web document text provided by users (→ `defuddle`·`ingest`), paper search (→ `paper-search`).
- **Core procedure**: Confirm the correct library and version → Check Context7 → Compare version/confirmation date with the original text of the official document → If Context7 is not found, fall back to the official document.
- **Completion criteria**: Version-sensitive assertions are linked to verified official documentation rather than memory or search snippets.

## defuddle

- **One-line role**: Removes navigation, advertising, and decoration from public web pages and captures them as raw Markdown text with metadata.
- **When to use**: Anonymously accessible articles, technology documents, release notes, web text extracts.
- **When not to use**: Login, paid wall, sensitive page, original text already in Markdown, judging the veracity of the captured content.
- **Core procedure**: Check the existence of `defuddle` → One-time read of `parse URL --md` → Vault preservation execute `--md -f` as `web-capture.sh` of `ingest` → Treat the original text as untrusted data.
- **Completion criteria**: The original text is saved without empty files or overwriting, and “clean extraction” and “verified facts” are distinguished.

## diagram

- **One-line role**: Draw the diagram to be included in the study note using a tool that fits the structure — the default Mermaid, D2→SVG for larger maps, JSON Canvas for maps in existing notes, and matplotlib→SVG for maps with coordinates.
- **When to use**: Mathematical drawings such as diagrams, schematics, concept maps, flowcharts, sequences, architecture drawings, knowledge maps, trajectories, and transformations.
- **When not to use**: Determining what is true (→ `note-writer` and evidence rules), choosing tools that are heavier than necessary, standalone interactive HTML diagrams for presentation and sharing (→ `archify`, output outside the vault). If you have a lot of nodes, don't go to `archify` — the promotion is still Mermaid → D2, and you're left with an embeddable SVG in your notes.
- **Promotion criteria**: `scripts/check.py` counts, not intuition. If there are more than about 15 nodes or more than 3 layers of overlap, it is passed on to D2. The checker also catches unknown Mermaid types, unbalanced parentheses, wiki links pasted as shapes, missing embedded assets, and empty SVGs.
- **Label rule (parsing)**: In `flowchart`/`graph`, the node label, edge label, and `subgraph` title are **always enclosed in quotation marks**. If parentheses or quotation marks are entered without quotation marks, the sentence is broken and the entire diagram changes to `Error parsing Mermaid diagram!`. Since the parentheses are matched, they cannot be detected by the count test. If the checker references the `subgraph` title as a node ID along with this failure, it also catches the missing `end`. `sequenceDiagram` does not have this restriction, so the rule does not apply.
- **Label Rule (Render)**: Quotation marks only fix the parsing, not the render. Mermaid passes labels as markdown, supporting only paragraphs, bold, italics, and inline HTML, and discards the rest — the Obsidian bundled version puts the text `Unsupported markdown: list` in place of the label. Therefore, the label does not start with a markdown symbol: `1. `·`1) `·`01. ` are all ordered lists, so just changing the number punctuation is useless, so write them as `①` or `1 · ` (the `1\. ` escape is not a solution because other renderers delete it). `- `·`* `·`+ ` at the beginning are bullets, `# ` is the title, `> ` is a quotation, and if the entire label is `---`, it is a dividing line, and backtick pairs and `[텍스트](주소)` also disappear. **Only `<br/>` is used for line breaks** — In the markdown label, `\n` appears as two characters: a backslash and `n`. However, `<br/>` **only starts a new block and does not break the inline range** — the backtick or link bracket opened at the front is closed across the line break and takes the entire label with it (bold and italic are supported types, so it is safe to cross them).
- **Wiki link in diagram**: `id[[텍스트]]` is Mermaid's **subroutine diagram grammar**, and its source is letter-by-character identical to the Obsidian wiki link. So when I paste `[[노트 이름]]` into a diagram, it is parsed without error and the note title is drawn as a double bounding box, but Obsidian doesn't interpret the links inside the code fence — **they appear to be connected, but the actual connection is 0 and is not visible in the render** (the box shape is as intended). A quotation mark separates the two: Write `["노트 이름"]` in a plain box **Put the link in the text** (The only edge is the text — `knowledge-graph` only reads the text of the note and not the front matter, so links that only exist in `related` are nowhere to be seen in the graph·`vault-gardening`·Stop hook arrival check). If you really need the subroutine geometry, write it as `[["노트 이름"]]`. For this one shape only, the validator also requires quotes in the label, which Mermaid simply parses.
- **Limitations**: Mermaid parser is JS, so it is **only a preliminary check** due to the principle of no dependency. Even if it passes, rendering may fail, so check it visually in Obsidian.
- **Asset convention**: Place the source and SVG with the same name in `assets/` next to the note. Render results without a source cannot be corrected and the only way to do this is to redraw. If `d2` is not present, do not install it and leave it as Mermaid.
- **Completion criteria**: Maintain that the diagram is an explanation, not evidence (the relationship is not established just because it is drawn), and record in the notes that the created image is for source and explanation purposes only.

## ingest

- **One-line role**: Send study materials to a capture path appropriate for the type of web, paper, or video, and connect from the immutable original text to verification notes.
- **When to use**: “Save data”, “Making notes on web documents”, “Bring papers”, “Study videos”, “Build up knowledge in vault”.
- **When not to use**: Organize already captured concepts into notes (→ `note-writer`), install harness (→ `study-install`).
- **Core procedure**: Source type determination → `defuddle` for web, `paper-search` for paper, `study-video` for video → New snapshot in `raw/` → Check/verify actual original text → `note-writer` → index/log/hot update.
- **Batch mode**: For amounts that do not fit into one context, such as compressed folders or lecture materials, the progress is viewed as `scripts/queue.py --vault vault --raw raw/courses/이름`. Progress is calculated based on **whether the note actually cites the file**, rather than a checkbox, so even if the session is interrupted, it is resumed from the note as is. **Copy** the path to the waiting list and put it in `sources:` — the path I retyped from memory was actually wrong in 6 cases.
- **Arrangement is sequential**: Even if the topic is different, sessions are not divided and run in parallel. For a link to work properly, the current state of both notes must be in one context.
- **Completion criteria**: Capture path, source, and verification status remain, and a simple download is not mistaken for completion of learning. Just because you're on the waiting list doesn't mean you have to write notes (normally configuration files and build output are not cited).

## knowledge-graph

- **One-line role**: `wiki/` Deterministically regenerates the article·topic·source type graph in Markdown, and accepts entity·claims inferred by the model only when the evidence is actually interpreted.
- **When to use**: Recreate the knowledge graph, check broken links, backlinks, and orphan notes, check topic classification, and verify evidence of inference items.
- **When not to use**: Edit JSON directly or use it as a knowledge source, comparing it to other indexes without checking the range or original hash.
- **Core procedure**: Run the standard library parser → Resolve duplicate title errors first → Review `missing_targets`·`orphans` → Modify Markdown and regenerate. Inference items are separately entered and verified as `--semantic`.
- **`raw/` capture is not a broken link**: If you give `--raw vault/raw`, the link interpreted as the **file name** of `raw/` is subtracted from `missing_targets`. Obsidian interprets wiki links throughout the vault, so links in notes that cite capture by name work normally in the app, but graphs that only view `wiki/` reported this as broken (**2 out of 3 actual vault cases were false positives**). It only reads the name, nothing inside becomes a node, and the body is not parsed.
- **Code is not a link**: Wikilinks in fence blocks and inline code are not edges. Since code spans **are not closed at the end of a line** but are closed by backticks of the same length on the next line, links within spans that span line breaks are also considered code (if you read them line by line, you won't see the closing backticks, so otherwise healthy notes will be reported as broken links). An empty line breaks a block, so the span does not extend beyond it.
- **Type**: `article` (note), `topic` (category of `index.md` — no wikilinks, only top-level items with links below), `source` (frontmatter `sources`, `raw/` paths are real or not). Edge is `links_to`, `categorized_under`, and `cites`, so even if there is only one note, a valid graph appears.
- **evidence discipline**: Inference records require `source_path`·`evidence_anchor`·`extractor`·`confidence`·`verification`, and if the anchor is not interpreted in the citation note, it is **discarded** rather than left due to low confidence. `verified` and `inferred` are counted separately.
- **Comparison of other indices**: `scripts/pilot.py --corpus PATH --candidate '읽기 전용 명령'` compares the corpus hash before and after execution and **disqualifies the candidate** if even one changes. Instructions with segments `write`·`format`·`reset`·`sync` are rejected before execution. Candidate commands are accepted as arguments — Do not memorize command lines from the CLI that you have not installed and read help for.
- **Key deliverables**: Untracked `_workspace/knowledge-graph.json`; The same input produces the same bytes, the note body is not included, and only the anchor and excerpt hash remain as evidence.

## metaskill

- **One-line role**: Creates and improves the `nohdol-study` harness's own AGENTS rules, skills, hooks, installers, ADR, and specifications in a consistent manner.
- **When to use**: “metaskill”, “harness improvement”, “create/reinforce skills”, porting different harness patterns, changing triggers/rules/installation procedures.
- **When not to use**: Writing general study notes (→ `note-writer`), collecting data (→ `ingest`), resetting the installation location (→ `study-install`).
- **Core procedures**: `REGISTRY.md` personal/in-house gate → Observation of current documents/tests → Placement of regular rules/selection procedures → Testing priority for behavior changes → Synchronization of README, rules summary, MOC, and change history → Full verification.
- **Completion criteria**: Skills frontmatter, boundary, reason, command, with/without are met, and new session and external service status that are not actually running are reported as unverified.

## note-writer

- **One-line role**: Executes flat YAML, wikilinks, per-argument evidence, uncertainty, and index/log/hot matching while creating atomic notes of understanding for reuse.
- **When to use it**: “Record it”, “Organize it”, “Make notes”, “Save it as knowledge”, when the study results can be used in the next session as well.
- **When not to use**: One-off conversations, when there are already enough notes with the same meaning, material that the user does not want to keep.
- **Core procedure**: Search existing notes → Select improvement/new atomic notes → Preserve required original text `raw/` → Apply evidence protocol → Create `wiki/`/two-way link → Update index/log/hot → Recheck schema/source → Check line breaks → If diagram exists, run check `diagram`.
- **Line breaks**: Paragraphs, list items, and quotations are **one per line**. Don't fold the text at specific columns — In Markdown, line breaks inside paragraphs are rendered as spaces, so it doesn't make any difference to the reading side, and only the writing side pays (if you change a single word, the entire paragraph is refolded, the diff is covered with refold noise, and the Obsidian editor folds back to the window width anyway, misaligning the file and the screen). Line breaks are used **only** in structures such as titles, lists, tables, code blocks, front matter keys, and explicit hard breaks (two spaces or backslashes at the end). Inspection is `python3 .agents/skills/note-writer/scripts/unwrap.py --vault vault`, application is `--write`.
- **index policy**: Follows `references/index-policy.md`. Since the index is not a list but an entry point, only **one line of hub notes per topic** is inserted and atomic notes are reached through the hub. When you create a bundle of notes, instead of increasing the index line, you create a hub note (`type: topic`). “Recent update” is truncated to around five lines and the source of truth is specified as `log.md`. Deleting the index line does not delete the knowledge, but only changes the directions.
- **Diagram**: If there is a picture or embed in the note, run `python3 .agents/skills/diagram/scripts/check.py "vault/wiki/노트.md"` before finishing. The broken diagram is either rendered as `Error parsing Mermaid diagram!` or `Unsupported markdown: list` is stamped in place of the label. In both cases, the source appears to be fine, so it is not captured in other steps.
- **Complete Criteria**: There is confirmed evidence or explicit unconfirmed, inferred, hypothesis, or disputed states for each important claim, there are no non-existent citations or relationships, the diagram is rendered as a picture rather than an error block, and `unwrap.py` does not report merge lines.

## obsidian

- **One-line role**: Write and verify Obsidian native formats (Markdown extension, Bases, JSON Canvas) and manipulate the running vault with the official CLI. Internal routing in 4 modes.
- **When to use**: Creating wiki link, callout, embed, and front matter properties, creating canvas, mind map, and knowledge map, `.base` table and card views and filters, and reading and changing vault with Obsidian CLI.
- **When not to use**: Judging the veracity of note content (→ `note-writer` and evidence rules), regenerating the knowledge graph (→ `knowledge-graph`), writing CLI without saying what will change.
- **Routing**: `obsidian-markdown` (note syntax), `obsidian-bases` (view), and `json-canvas` (canvas) **operate without Obsidian**, and only `obsidian-cli` does not require app execution, so if it is not required, it is reported as `unavailable`. Procedures for each mode are in `references/modes.md`.
- **Core procedure**: Check pin status → select mode → perform upstream workflow within the boundary → complete after verification with `scripts/validate.py`.
- **Verification Scope**: Canvas is JSON Canvas 1.0 (node ​​type, coordinates, id duplicate, edge points to actual node), Markdown is unclosed, empty wiki link and unknown callout type (list is read from pinned reference and synchronized with upstream), `.base` is structural error causing load failure. **The base check is not a YAML verifier but a structural pre-check**, so it is reported as "not obviously broken."
- **Completion criteria**: The created file passes verification, regular notes are not arbitrarily modified to fit the format, and the target vault and file are revealed before writing the CLI.

## paper-search

- **One-line role**: Search, download, and text extract papers from open academic sources, check publication status, version, correction, and withdrawal, and link them to notes.
- **When to use**: Search for papers, find the latest research, search literature based on arXiv, DOI, author, and topic, and make notes on paper PDFs.
- **When not to use**: Confirming conclusion only with title and abstract, marking preprint as reviewed paper, bypassing unofficial information such as Sci-Hub.
- **Key Steps**: Check `sources` → Narrow multi-source `search` → Select correct ID → Preserve PDF with `download`·`read` assist extraction → Official metadata·PDF method/limit collation → `note-writer`.
- **Complete Criteria**: Actual PDF or legal access limits, identifier, version, venue, peer-review status, and scope of evidence for significant claims are recorded.

## recall

- **One-Line Role**: Turn verified notes into spaced repetition cards, but keep each card looping back to the notes and passages that came with it.
- **When to use**: Review, making flashcards/memorization cards, repeated study, when what you studied before becomes blurry.
- **When not to use**: `unverified` Create a card with notes, use a card with answers that are not in the quote note, and treat passing the card as evidence that the claim is still true.
- **Format**: Markdown next to the note. Question / `?` / Answer / `<!-- from: 노트.md#앵커 -->`. The source comment is required, and the schedule comment (`<!--SR:...-->`) is a review tool, so do not touch it.
- **Check**: `scripts/cards.py --wiki vault/wiki CARDS.md` interprets the origin of all cards — the note must be in the wiki and the anchor must actually be caught in it (as per the anchor rules for the knowledge graph), otherwise it is rejected. After correcting the note, run it again. The moment the anchor breaks is the time to reexamine the card.
- **Complete Criteria**: Cards are fully traceable, and review passes are read only as “remembered” and distinguished from “still true.”

## study-install

- **One-line role**: Select a different knowledge root, profile, and synchronization method for each computer and securely initialize vault symlinks and local tool states.
- **When to use**: First installation, missing `REGISTRY.md`/`vault`, connecting knowledge storage location, linking Obsidian vault, installing Phase 2·2b tools and checking status.
- **When not to use**: Bulk migration of existing vault, vault Git initialization/remote configuration, installation of Obsidian/credentials without authorization, running upstream global installer.
- **Core procedure**: Observe existing path/symlink/conflict → Knowledge root/individual/in-house/sync interview → create-if-missing bootstrap → Phase 2 tool check/install → Phase 2b source pin check/install → Symlink/standard file/Git non-tracking verification.
- **Complete Criteria**: Existing knowledge is preserved, installation location information is located only in the untracked `REGISTRY.md`, and missing tools and unverified items in the real world are specified.
- **Phase 2b pin**: `install-phase2b-tools.sh` receives the correct upstream commit to the untracked `.tools/` and deploys it only when the tree hash matches, and dependency installation and build are automatically carried out according to the user's constant approval decision. Global skills and vaults are not touched. Hash mismatch·unsatisfied runtime·unparsable pin·`python3` Absence is fail-closed, and if the existing checkout is different, it is reported without overwriting. Moved tags are also blocked, but since this is a tampering signal, if the API is not reached, it is reported before proceeding. Obsidian's absence is not a failure, but a `unavailable` record.
- **Local Embedding Server**: `install-embedding.sh --check|--install` installs the embedding server for `vault-search`. You can choose a model according to your installed memory, report what you chose, and overwrite it with `--model`. **The standard is not the hardware, but the note language** — When measuring the 8 Korean questions that know the correct answer note, the English-centered `nomic-embed-text` was ranked in the top 10 in **2 out of 8** (MRR 0.067), and GeekNews' "How to prevent customer churn" was ranked higher than "How to automatically prevent customer churn before deployment" (not meaning, but `막다`). So, if memory allows, the multilingual model is the default, and the small English model is a fallback that reports weaknesses without hiding them. **Do not install with `brew services`** — That plist forces `OLLAMA_KV_CACHE_TYPE=q8_0`, but the encoder model does not have that cache, so `/api/version` is answered, and the model will never be loaded (it seems like a hardware limitation, but it is not). The script is verified with the **actual embedding response**, not the port.
- **Colab MCP Server (Profile Gate)**: Check the official `googlecolab/colab-mcp` as a selection. Since the code and data are externally transmitted and run on Google Runtime, it is not installed and registered at the `corporate` installation location, but is recorded as `blocked-by-profile`, and explicit consent is received only from `personal`, registered as `claude mcp add --scope user`, and the decision is left at `REGISTRY.md`. OAuth authorization is granted on first use, and the tool is reflected from the next session. The vault contents are not sent to this server.
- **Optional Local Automation**: The reference implementations below `examples/` (`feed_scraper`, `telegram_bot`, which is a read-only query surface) are provided only and are not installed by default. It is copied and configured as `_workspace/` only when requested, and the automation actually run by this installation is recorded in `REGISTRY.md`. The feed scraper only tracks the source catalog, and non-tracking `sources.local.toml` determines which sources to turn on.

## study-video

- **One-line role**: Understand the entire lecture/technology video with only subtitles, and only when a question that needs to be answered appears on the screen, check the frame at that point and make a note.
- **When to use**: When learning the lecture structure, explanations, demos, and diagrams from video URLs/local videos and making permanent notes.
- **When not to use**: Expensive frame analysis not requested by the user, sending Whisper audio externally without permission, storing frames for illustration purposes.
- **Core procedure**: `watch`·Media tool preflight → `--detail transcript --no-whisper` (subtitles only, video not downloaded) → Read the entire transcript → **Only when the screen has a question to answer** Check only that point with `--timestamps` → Only the transcript is saved in `raw/` and the frame is discarded after leaving the confirmation result as a sentence → Separated from the speaker's claim and external → `note-writer`.
- **Completion criteria**: `ko.*,en.*` Subtitle priority, original timestamp, transcription method used, and verification limits are left in the notes.

## study-session

- **One-line role**: Teach by asking instead of explaining — one question at a time, starting with what the user can already reconstruct, and filling in the gaps only after revealing them.
- **When to use**: “Let’s study”, “Teach”, comprehension check, quiz, Feynman technique, when you want to understand enough to write.
- **When not to use**: Just a fact check that needs an answer (answer it right away), or turning it into a quiz that the user can't escape.
- **Core procedure**: Search existing notes first → One question at a time, starting from a point that can be reorganized → Move deeper while following the answers → If you get something wrong, don’t correct it right away, but ask questions that show contradictions → Explain only the parts you couldn’t reach → Confirm with application → Record unresolved questions → If it is worth preserving, suggest `note-writer`.
- **Honesty Rules**: Don't count fluent restatements as understanding (ask for applications, boundary cases, and predictions), don't ask ungradable questions, don't hide answers to questions, and don't make up wrong answers to try to catch the user. The rules of evidence also apply to claims that fill in the gaps.
- **Complete Criteria**: The user is the one who assembled the answer, can stop at any time, and the remaining questions are recorded.

## understand

- **One-line role**: Analyzes the code base and Markdown knowledge base by internally routing the 9 pinned Understand Anything entry points in one skill.
- **When to use**: Understanding the codebase/architecture, locating features, explaining concepts/flow, onboarding sequence, change impact scope, domain perspective, knowledge base typed extraction, graph visualization, approved Figma analysis.
- **When not to use**: This vault's definitive wikilink graph (→ `knowledge-graph`), the fact that the source file has not been opened, the answer, running the dashboard or sending Figma without an explicit request this turn.
- **Routing**: Choose a mode for the request purpose — `understand` (create graph), `-chat` (find location), `-explain` (description), `-onboard` (training sequence), `-diff` (change impact), `-domain` (domain), `-knowledge` (Knowledge Base), `-dashboard` (Viewer), `-figma` (Design). If it's ambiguous, first state the mode you chose and the reason, and if you ask multiple questions, choose the cheapest one that provides the answer.
- **Common boundary**: `references/adapter-contract.md` is carried by one — the graph is a means of exploration, not evidence. In fact, the answer is completed only after checking the source file, the vault analysis is run by `_workspace/understand-anything/`, and dashboard and Figma are subject to explicit request and approval for each execution. Procedures for each mode are in `references/modes.md`.
- **Runtime layer**: `-knowledge` runs only with `python3`, the five graph consumption types require a graph created first, and `understand`·`-figma`·`-dashboard` require built dependencies. (Depending on the user's decision to approve permanent dependency installation, NPM dependencies are automatically installed and built during `study-install`.) If runtime does not work, an alternative is presented without imitating the tool output.
- **Complete Criteria**: The selected mode and evidence are revealed, factual answers are evidenced in the opened files and lines, and unmet runtimes are reported as unavailable without an installation attempt.

## vault-gardening

- **One-line role**: Reports deviations from the knowledge root — links without targets, **notes pointing to no one**, frontmatter breaking note contracts, citation sources not in `raw/`, session caches over budget, indexes bloated with lists.
- **When to use**: Vault check, find broken links and orphaned notes, check index bloat, check note status, and periodically organize.
- **When not to use**: Automatically adding links or editing notes, reading blank reports as evidence that “knowledge is correct.”
- **Core procedure**: Execute `scripts/garden.py --vault vault` → Judge each item one by one → Match the changes to index/log/hot with `note-writer`.
- **Scope**: Only check the existence of `wiki/`·3 derived files·`raw/` and **`raw/` file name**. **Do not traverse the rest of the knowledge root** — There are irrelevant directories in the actual vault, and full traversal in cloud storage is slow and pointless. Reading the name `raw/` is to avoid mistaking the link pointing to the capture as broken.
- **Definition of Reachability**: A note must **point to** to be reachable — a backlink or index topic classification. Since the links you send are irrelevant to discoverability, notes that cite six places but cite no one are also reported. Even names listed in the index’s “Recent Updates” are not considered evidence — the list is pushed down to only a few items.
- **Judgment Principle**: Orphans only connect when there is a real relationship. **Do not add links to empty the list** — Cosmetic links are worse than honest orphans because they make the graph lie. `checked` If the date is missing, check again and correct it instead of using today's date. If the number of index links is exceeded (`--index-link-budget`, default 15), rather than correcting the number by deleting the item, it is solved by giving a hub note to the topic and moving it to the back. Links written as grammar examples (including fences, code spans, and spans spanning line breaks) are not entry paths and do not count — they count as text as the graph reads them.
- **Complete Criteria**: Maintain that the report only describes the structure — Whether the content is true or up-to-date is determined by re-reading the original text using the evidence rule.

## using-study

- **One-line role**: In each study session, existing knowledge is retrieved first, new inferences are distinguished from stored knowledge, and only valuable understanding is selectively retained.
- **When to use it**: Any study session with knowledge questions, concept explanations, learning material, “What do you know?”, and requests for memory, organization, and notes.
- **When not to use**: It does not replace the harness structure change (→ `metaskill`) or installation (→ `study-install`) itself.
- **Core procedure**: Search index/wiki first → Secondary search of legacy notes → Explanation by revealing contradictions, assumptions, and loopholes → Always apply evidence rules to important claims → `note-writer` only when it is worth reusing → Synchronize index/log/hot.
- **If it is a conceptual question, `vault-search`**: If you have to guess what word the note used to run grep, use semantic search. It is impossible to distinguish between what a keyword search misses and what you do not have knowledge about, and answering from memory at that point is the failure that this rule is trying to prevent.
- **Completion criteria**: Inference from existing knowledge, new data, and models is not mixed, and `hot.md` is treated as a discovery cache rather than an authority.

## vault-search

- **One-line role**: Find note `wiki/` **by meaning**. It uses a local embedding index and the notes never leave this computer.
- **When to use**: When you don't know the words written in a note, check "Have I already organized it?" before writing a new note, find similar and related notes, and check if the concept covered by an external source is in the vault.
- **When not to use**: Exact strings, paths, file names (→ `rg`), links, backlinks, orphan notes (→ `knowledge-graph`), determining what is true (→ the original text of the note and the sources it cites).
- **Key Step**: All you need is `semantic.py query --vault vault "질문"` — **changed notes are re-embedded first and then retrieved**, so you don't have to remember to rebuild them. The result is a list of candidates, so **open and read the notes you want to write**. View the index status with `status`.
- **Results are not evidence**: The similarity score means that two paragraphs are close in the embedding space, not that one is true. This is the same rule as the knowledge graph. Do not assume that you have no knowledge just because the result is empty, but check with `rg` and `index.md`.
- **Does not go out**: Since the vault contains turnover data and private notes, non-loopback endpoints are **rejected** by the script, not set. The index is placed at `_workspace/` outside the synchronized knowledge root.
- **Complete Criteria**: If there is no embedding server, it will not silently fall back on a bad search, but will say so and tell you the command to run it.
