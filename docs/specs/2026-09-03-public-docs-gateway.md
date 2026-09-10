# Public Docs Gateway Specification

> Scope clarification (2026-09-10): this is the initial gateway specification. [The Data & Observability extension](2026-09-10-data-observability-learning-path.md) explicitly publishes its selected docs/ course; the original exclusion still applies to other harness guides, ADRs, and specifications.

- Date: 2026-09-03
- Status: Implemented
- Related Decision: [ADR 008](../adr/008-public-docs-gateway.md)

## Goal

- GitHub Pages provides an English static site for learning selected technology topics.
- The initial implementation of the gateway starts with Kubernetes alone and provides a full roadmap and 10 chapters that reorganize the official documentation into order of understanding. Subsequent topic extensions are defined by [DevOps Public Learning Path](2026-09-03-infra-specialist-public-learning-path.md) and [AIOps Public Learning Path](2026-09-03-aiops-public-learning-path.md).
- Afterwards, the official link provided by the user is read as source material, and instead of linking to external links, self-supporting explanations, diagrams, implementation examples, and failure cases are accumulated in the relevant chapters.
- Prevent accidental exposure of personal vault and harness operation documents by explicitly selecting documents to be disclosed.

## non-goal

- Providing nohdol-study itself as a learning topic
- Posting `docs/`'s ADR, specifications, and guides as an open curriculum
- Ability to automatically post study notes in `vault/`
- Replicating the entire Kubernetes official documentation or creating a translation mirror
- Alternative to private document hosting or local `_workspace` portal that requires authentication

## Requirements

### R1. Extensible topic gateway and current scope

The first screen provides the site purpose, full document search, and study area cards registered in the catalog. When you select an area, the subject cards for that area appear in prerequisite order. New topics have independent content directories and tables of contents and are placed in exactly one area. When you select the Kubernetes card in the initial catalog, the following 11 documents appear in this order, and you can return to the zones and topic gateways at any time.

1. Full Learning Roadmap
2. Why Kubernetes and your first cluster
3. API and objects
4. Cluster architecture and control loop
5. Pods and workloads
6. Service and networking
7. Storage and application configuration
8. Scheduling and resource/autoscaling
9. Security and Policy
10. Observation and troubleshooting
11. Production operations and expansion

### R2. Independent learning content by topic

The public text is separated by topic under `docs-site/content/<topic>/`. The initial Kubernetes body is placed in `docs-site/content/kubernetes/`. Each document identifies the relationship between prerequisites and subsequent chapters. When detailing links, use one-sentence models, relationship and sequence diagrams, minimal running examples, detailed explanations, failure examples and recovery, operational judgments, and review questions as the basic structure.

Original data URL, confirmation date, and translation warnings are recorded in Markdown HTML comments and removed from the built text. A learning link to the Kubernetes official page is not created in the public text, and must be able to be understood and labed independently.

If a Korean page is flagged as possibly being an outdated translation, check the current English original text or API reference for APIs/versions/operations where up-to-dateness is important.

### R3. Reading and searching documents

The public interface, catalog titles and summaries, article prose, and diagram labels are English. The page declares `lang="en"`; search, reading-time labels, accessibility text, loading and error states, and diagram controls use English. Language changes preserve document IDs, routes, executable examples, link targets, and evidence-check metadata. Build tests reject Korean text in the published interface and content payload.

Documents display the title, summary, estimated reading time, and source path. It searches the title, summary, and body at once and renders Markdown titles, lists, tables, codes, citations, and internal links into readable HTML. `mermaid` code blocks are rendered as relationship diagrams and sequence diagrams SVG. Topics and documents can be opened directly by URL hash, and browser back and mobile one-column layouts work.

### R4. public range gate

The catalog path must be a Git traceable Markdown inside the repository. Absolute paths, `..`, duplicate IDs, non-existent files, `vault/`, `REGISTRY.md`, and `_workspace/` are treated as build failures. The build process does not traverse vault symlinks.

### R5. Reproducible static builds

Install dependencies with lock file in Node.js 22 and create `docs-site/dist/`. Copy the Mermaid 11.17.2 browser bundle to the artifact and do not use an external CDN. The site's URL and assets must be relative URLs that also work in the project Pages subpath.

### R6. Pages deployment

GitHub Actions workflow, which responds to `main`'s public document/site changes and manual execution, deploys Pages artifacts through testing and building. The deployment job additionally uses only `pages: write` and `id-token: write`.

### R7. direct delivery

Completed and newly verified general changes are committed and pushed to `origin/main` without a separate approval step. Check the success of the workflow and the HTTP response of the public URL. Force pushes, history rewrites, destructive Git operations, releases, secrets, other remotes or branches are out of scope.

## Completion criteria

- Currently, the catalog only has one topic, `kubernetes`, and 11 documents in the specified order, and the gateway can render additional topics.
- All open source paths are Git trace Markdown under `docs-site/content/kubernetes/`.
- Search data includes title, summary, and body text, and does not include harness topics and private path documents.
- Relative Markdown links in the roadmap are replaced with links to internal site documents.
- The public document HTML lacks Kubernetes external learning links and evidence annotations, and Mermaid code blocks are converted to render targets.
- The overall roadmap and first cluster document contain relationships/sequences, executable YAML, normal/failure observations, and review questions.
- Deterministic tests reject invalid paths, untracked files and duplicate IDs.
- Check gateways, topics, documents, search and mobile layouts on your local HTTP server.
- The entire harness verification passes.
- After the push, the Pages workflow succeeds and the public URL returns HTTP 200.
