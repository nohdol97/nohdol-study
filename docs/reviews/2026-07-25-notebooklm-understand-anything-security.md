# NotebookLM CLI·Understand Anything Security Review

> Historical security review: findings apply to the exact versions and audit date below. [ADR 004](../adr/004-remove-notebooklm-export.md) subsequently withdrew NotebookLM export and its bridge. The historical allow table is not current execution authorization or a fresh dependency audit.

- Date: 2026-07-25
- Review Scope:
  - `teng-lin/notebooklm-py` stable release `v0.7.3`
    (`a6c54417058bd5e43e0162dd93a390308d2f99f6`) and main
    (`45fd4258e608fbb9685496f26cfcea48810c44ee`)
  - `Egonex-AI/Understand-Anything` stable release `v2.9.0`
    (`f08763d11d0202a8a8f52b5dedda6d1b2e2ebac8`) and
    `/understand-knowledge`
- verdict:
  - NotebookLM: **Conditional adoption, currently pending automatic installation of v0.7.3**
  - Understand Anything: Adoption of all 9 skills, upstream global installer
    Requires project-local safe adapter without using

## How to check

- Check release·commit·security policy·installation document
- Authentication storage, path validation, source upload, download redirect, sharing/delete
  Review verification code
- `notebooklm-py` frozen lock and current allowable dependency respectively
  Scan with `pip-audit`
- Understand Anything v2.9.0 installer, 9 skills, parser, merge,
  Review analyzer, dashboard·Figma boundaries, and locks
- Run upstream knowledge parser test: `8 passed, 1 skipped`
- Running the upstream parser in the current vault: `md_count=1` failed as intended,
  No changes to the original

## NotebookLM findings

### N1. Unofficial internal API — High, needs acceptance

It uses consumer NotebookLM RPC, which Google does not document. API is announced
Rate limits or account restrictions may occur due to broken or abnormal use. official
It should not be expressed as a consumer API or Google's security guarantee.

### N2. Authentication file has bearer credential — high, mitigable

Anyone with `storage_state.json` can impersonate a user in the NotebookLM scope.
there is. The code is POSIX profile directory `0700`, credential file `0600`, atomic
Implement write. However, it is not file encryption, so storage, vault, and Google Drive
It must be placed in a dedicated external profile.

browser-cookie import reads the existing Google cookie storage in Chrome/Firefox.
macOS Chrome may require Keychain access. Automatic installation and automatic refresh
One-time authentication where the user approves the correct browser profile without execution
Limited to work.

The master-token implementation also requires upstream code to be “full-account, durable,
It warns, “infostealer-grade.” It is prohibited in the personal default path.

### N3. v0.7.3 download redirect Missing defenses — high, blocking installation

v0.7.3 checks for HTTPS and Google host in the initial URL, but
Each hop after `follow_redirects=True` is not rechecked. edit commit
`0a6e28a0522b3542695e6666054e88060ef3de48` is in main but has not been reviewed.
There is no v0.7.3 tag. Google redirects affected by attackers target random hosts
When pointed, the response byte can be written to the specified output path. cookie is domain
Separate from the upstream analysis that it is scoped and is not transmitted to a non-Google host,
This request using artifact download requires a release gate.

### N4. dependency status — medium

- From `click 8.3.1` in v0.7.3 frozen lock
  One case of `PYSEC-2026-2132` was confirmed. Do not re-install as is.
- Browser set and cookies reinterpreted the allowable range of v0.7.3 as of 2026-07-25
  The set had 0 known vulnerabilities in each `pip-audit`.
- “0 current vulnerabilities” does not guarantee future security. exact before actual installation
  The lock must be recreated and audited.

### N5. Good basic defense — check

- Prevention of profile path traversal and atomic credential write
- Default deny symlink in CLI file upload
- localhost·private·link-local source URL default deny
- Google host allowlist in artifact download and per-hop guard in main
- Confirmation of delete and two-step confirmation of MCP
- Temporary download files and cleanup on failure

### N6. Autonomy of upstream skills is excessive — medium

The upstream skill automatically executes notebook creation and source addition without confirmation.
Allowed. In nohdol-study, both are external state changes, and source add is Google
Because it is a transfer, no automatic rules are imported. public sharing is in v0.7.3 CLI
It can be activated without separate confirmation, so it is placed outside the wrapper allowlist.

### N7. safe form of use

- Upload only the existing `notebooklm-export` packet
- Since the vault is a symlink, do not pass `vault/...` directly
- `--follow-symlinks`, `--allow-internal`, master-token, MCP/server,
  impersonate extra prohibited
- Approval before executing external transmission and mutation
- The product is recovered at `_workspace/` and is not used as independent evidence.

## Understand Anything Discoveries

### U1. All 9 skills fall under nohdol-study learning scope — adopted

`understand`·`chat`·`diff`·`domain`·`explain`·`onboard` are codes and products
It provides a different perspective to study the domain. `knowledge` is Markdown knowledge
Base, `figma` can be used for design, and `dashboard` can be used for visual exploration of large graphs.
Since this project is not limited to knowledge notes, all nine are adopted.

However, graph-derived explanations are not definitive evidence. chat·domain·explain·onboard·
The diff's answer must be compared by reopening the relevant source file.

### U2. Overall installer coverage is excessive — high

The installer clones or pulls the main branch and places multiple items under `~/.agents/skills` and other locations.
Connect the Understand Anything skill to `ln -sfn`. There is no exact release pin
Can cover up existing name conflicts. The problem is not the skill scope, but the installation scope and
It is reproducibility. Use project-local checkout and adapter of exact commit.

### U3. The knowledge parser itself is non-dependent and deterministic — good

Parser and merge use only the Python standard library and shell commands.
Do not run it in the text. The upstream parser test also passed. explicit
The wikilink·backlink·category base is a good foundation for expanding the current standard parser.

### U4. Implementation and documentation vary in scope of format support — Medium

The design documentation speaks of automatic detection of several Markdown formats, including Obsidian, but in v2.9.0
The actual skill supports only the Karpathy pattern. `index.md` and 3 or more Markdown
I demand it. Currently, nohdol-study vault fails because there is only 1 `wiki/`. “Obsidian
Documenting that “it works right away with vault” is incorrect information.

### U5. A copy of the body remains in the final graph — High

The parser puts the first 3,000 characters of each article into `knowledgeMeta.content` and merges them.
This is preserved until the final graph. Once `.ua/` is in the Google Drive vault
private note Some parts are unnecessarily duplicated and synchronized. The nohdol-study adapter is
We need to change the output to `_workspace/` and remove the body from the final graph.

### U6. Lack of evidence tracking for model inference — High

article-analyzer specifies conservative extraction and ignores prompt-injection, but
Entity·claim·implicit edge schema includes source span, evidence anchor,
There is no verification state. Merge is also allowed and only checks the type and node existence.
To meet the accuracy that users value, abandon claims without evidence and use inferred and
Verified must be separated.

### U7. dashboard · Figma · Organize Delete Boundary — Medium

The skill automatically runs the dashboard after completion and changes `.ua/intermediate` to `rm -rf`.
Organize. Adopt the dashboard function itself, but remove automatic execution and allow the user to
Open the loopback viewer only when requested. Intermediates must be explicitly cleanup or replaced
Manage with temp directory whenever possible.

Figma skill requires external calls `FIGMA_TOKEN` and `api.figma.com`. token is
Rather than storing it in the storage/vault, the file key to be analyzed and the purpose of transmission are specified by execution.
Get approved.

### U8. Full monorepo dependency audit — high, evidence blocking entire install

In the production audit of v2.9.0 lock, 21 cases, including 10 high cases, were reported.
This has a mix of homepage/dashboard/build layer dependencies, so all skills
This does not mean that each vulnerability will be reached. But rather than just doing `pnpm install`
Only packages that are actually needed should be separated and audited using exact lock. unresolved
Node paths with high vulnerabilities are not automatically installed.

## final gate

| item | allow now | blocking conditions |
|---|---|---|
| Original deterministic `knowledge-graph` | Yes | doesn't exist |
| Developed 9 UA project-local adapters | Yes | main automatic pull/overwrite global skill |
| Actual use of UA Node-based skills | Behind the dependency gate | high vulnerability/inconsistency lock |
| UA semantic enrichment | opt-in after adapter | Execute claim/prompt without evidence |
| UA dashboard | In explicit request/loopback | Automatic open/external bind |
| UA Figma | After approval of token·file transmission | Token storage/unauthorized transmission |
| UA upstream installer | No | main tracking/global symlink |
| NotebookLM manual export | Yes | manifest/hash mismatch |
| Notebooklm-py installation and actual use | Not yet | Unfixed release, vulnerable to exact lock |
| browser-cookie authentication | Upon explicit approval behind installation gate | Automatic execution, unknown profile, poor permissions |
| master-token/MCP/server/public share | No | Not allowed in default route |

## external evidence

- NotebookLM CLI: <https://github.com/teng-lin/notebooklm-py>
- NotebookLM security policy:
  <https://github.com/teng-lin/notebooklm-py/blob/main/SECURITY.md>
- NotebookLM redirect fix:
  <https://github.com/teng-lin/notebooklm-py/pull/1532>
- Understand Anything:
  <https://github.com/Egonex-AI/Understand-Anything>
- Understand Anything v2.9.0:
  <https://github.com/Egonex-AI/Understand-Anything/releases/tag/v2.9.0>
