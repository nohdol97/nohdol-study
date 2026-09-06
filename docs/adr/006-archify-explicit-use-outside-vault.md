# ADR 006 — archify is an explicit call only, output is placed outside the vault

- Date: 2026-08-09
- Status: Active
- Target: New `.agents/skills/archify/`, `.tools/PINS.md`,
  `node18` runtime value of `install-phase2b-tools.sh`, `diagram` skill boundary,
  `AGENTS.md` Section 8
- Relationship: [ADR 003](003-cli-learning-integrations.md)'s exact-pin installation method
  Applies directly to Phase 3 series tools. `diagram` does not have reduced functionality.

## context

archify(<https://github.com/tt-a1i/archify>, MIT) is architecture·workflow·sequence·
Render data flow/lifecycle diagrams as standalone HTML. nothing outside
It is not sent, has schema, tests, and CI, and the upstream is active. The quality of the tool itself is
There was no reason to prevent adoption.

What is blocked is **the shape of the output**. Three things overlap.

1. Obsidian does not embed HTML files. The diagram is not visible in the notes.
2. One file is about 600KB and the root of knowledge for this installation is cloud synchronization. every
   The device pays for its capacity.
3. **There is no SVG output path in CLI.** The command for `bin/archify.mjs` is `render`,
   `compare`, `deliver`, `preview`, `validate`, `inspect`, `check`, `guide`,
   `examples`, `doctor`, `demo`, and there is no `.svg` string in the entire file. README
   Speaking PNG/SVG export is a viewer when the generated HTML is opened in a browser.
   It is a button, not a callable command. In other words, there is no way to circumvent the capacity problem.

The third is decisive. If it were only 1 and 2, the answer would have been “Extract it as SVG and put it in the notebook.”

## decision

Adopt but **do not put in note pipeline**

- **For explicit calls only**. Users point to archify or use it for interactive/sharing purposes.
  Route only when a presentation diagram is requested. The complexity of the structure means that routing
  That's not a reason — the complexity progression path is still Mermaid → D2, and that's in the notes.
  Leaves an embedded SVG.
- **The output is only used in `_workspace/archify/`.** The knowledge root includes HTML, specification JSON,
  Export is also not included. It doesn't even go below `.tools/` — if you add the file there
  The tree hash that the installer verifies is broken.
- Leave the spec JSON and HTML **together**. How many kilobytes is the spec, and that's all it takes to make a diagram.
  It can be fixed.

## Why not a global install?

The upstream recommended installation method is `npx skills add tt-a1i/archify -g`. `AGENTS.md` Section 1
Prohibits running upstream installers and linking to global skill directories. So the path is
There is only one — pin `.tools/PINS.md` with commit and tree hash and the Phase 2b installer starts.
Verify and deploy the hash. The pin is release `v2.13.0`. One of the three commits after the tag
Render measurement fix, but re-pin it in the next release instead of following `main`.

## Why the new runtime value `node18`

The existing values ​​were only `none` and `node22-pnpm10`. archify requires Node 18 or higher
There is no need for a package manager — the only declared dependency is `ajv` for dev and the product
`renderers/shared/generated-validators.mjs` is committed.

If you write this tree as `node22-pnpm10`, the installer says **the tool cannot be used because pnpm is missing**.
Report. The explanation is false, and the user will install pnpm based on that falsehood. so
The value was increased. The installer still does not prevent deployment, it just reports it, the actual rejection is due to the adapter
Do it.

## What is not evidence

`deliver` captures the SHA-256 and byte count of the specifications and output, and `9/9` passes the check. upstream
The document's vocabulary is strong and reads like verification, but what it proves is the render pipeline's
Integrity — that this byte produced that output and passed the configuration check. the diagram
It has nothing to do with the claims made about the system. `AGENTS.md` Section 8 “Derivatives are illustrative only.
“It does not constitute evidence” still applies. The adapter skill specifies this distinction.

The same goes for the upstream repository evidence function. Read the code and refine the diagram
It is useful, but if the facts from there need to be included in the note, `note-writer` and evidence
The original file must be opened and cited through the protocol.

## Actual measurement (2026-08-10)

The pin was placed and confirmed. The installer verifies the tree hash and changes `archify` to `ready`.
reported, `node bin/archify.mjs doctor` exits 0 **without installing dependencies**
Passed 14 items (Node v26.5.0, all including committed standalone validator `ok`).
This means that the `node18` value matches the reality.

The output created by `demo` is **one 597.6KB HTML piece**. The capacity of this ADR as isolated evidence is
These are numbers, not estimates.

## Limits — state them

`--install` does not end with just archify. The block at the end of the installer is node and pnpm.
If it is equipped and has `understand-anything/package.json` **even if it is an already deployed tree**
Run `pnpm install` and `pnpm -r build` again. This time, even the dashboard was rebuilt.
Since this is an existing behavior unrelated to archify, it was not touched in this change, but one pin was added.
If you call `--install` to add it, it will be an additional cost, so write it down.

There was no visual review. Without checking in the browser whether the `demo` output is opened.
Since we only looked at file existence and size, there is no evidence to make claims about render quality.

## Conditions for review

If the upstream outputs SVG directly from CLI, it is a candidate to replace the D2 position of `diagram`.
See you again. Until then, this boundary is not a matter of taste but a constraint of format.

Conversely, if it is observed that note requests are leaking even though it is only for explicit calls, raise the boundary.
Instead of writing more as an explanation, let's first fix the routing text on the `diagram` side.
