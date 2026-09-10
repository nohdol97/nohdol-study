# ADR 008 — Subject-specific learning documents are deployed to GitHub Pages through an explicit catalog.

> Scope clarification (2026-09-10): [ADR 009](009-public-docs-root-learning-paths.md) adds learning paths and explicitly selects the Data & Observability course from docs/. Other harness guides, ADRs, and specifications remain outside the public catalog.

- Date: 2026-09-03
- Status: Partially replaced (root topic listing replaced by ADR 009)
- Subject: `docs-site/`, `.github/workflows/docs-pages.yml`, `AGENTS.md` Section 7
- Related specs: [Public Docs Gateway](../specs/2026-09-03-public-docs-gateway.md), [DevOps Public Learning Path](../specs/2026-09-03-infra-specialist-public-learning-path.md), [AIOps Public Learning Path](../specs/2026-09-03-aiops-public-learning-path.md)

> The structure of directly listing all topics on the first screen is [ADR 009](009-public-docs-root-learning-paths.md) replaced by the learning area path structure. Explicit catalog, disclosure, and Pages artifact decisions remain in effect.

## context

The first public site created showed ADR, specifications, and guides from the nohdol-study repository by topic. However, the public learning object desired by the user is not the harness itself, but a separately selected technology topic. The first topic was Kubernetes, and we had to create a learning table of contents starting from the [Kubernetes Korean document ](https://kubernetes.io/ko/docs/home/) and then expand the links specified by the user into explanations with diagrams and detailed examples. The same gateway had to be extensible to subsequent DevOps topics.

The separate local `_workspace` portal is a surface for collecting repeatedly used personal sites and is not aimed at Internet deployment. The actual knowledge root, `vault/`, may contain personal information and private learning materials and is excluded from Git, so it should not be read by GitHub Actions or automatically included in public documents.

## decision

The source of the public document site is located at `docs-site/` and maintains a gateway structure that supports multiple topics. The catalog explicitly exposes Kubernetes and subsequent topics defined by [DevOps specification](../specs/2026-09-03-infra-specialist-public-learning-path.md). Each text is written independently of `docs-site/content/<topic>/`, and the harness operation document `docs/` is not used as an open curriculum.

- The official documentation's installation, concept, task, tutorial, and reference are rearranged into 11 documents according to concept dependency.
- The new topic has an independent table of contents in `docs-site/content/<topic>/` and explicitly adds a topic card to the catalog.
- The disclosure target is specified as a storage relative path in `docs-site/catalog.json`.
- The build only allows Markdown tracked by Git and rejects `vault/`, `REGISTRY.md`, and `_workspace/` and path deviations.
- Do not duplicate the official original text or create a collection of external links. Links to the original data are used only as writing evidence, and the public text is written as an independent document with problem model, relationship and sequence diagram, execution example, detailed explanation, failure case, operational judgment, and review questions.
- Evidence URL, confirmation date, and translation warnings are tracked by leaving them in Markdown HTML comments, but the build removes them from the public body.
- The Mermaid 11.17.2 browser bundle is included in the site artifact to render diagrams internally and does not depend on an external CDN.
- If the Korean document is marked as being older than the original, re-check the current English document and API reference for content where up-to-dateness is important.
- The generated `docs-site/dist/` is not tracked and is only delivered as a Pages artifact in GitHub Actions.
- The `_workspace` portal maintains the boundary of being a local dynamic site, and `docs-site` is a tracking learning document published on the Internet.

## Add link operation

If the user gives you a link to the current topic, don't add an item that will send readers to that address. After reading and verifying the text, the closest chapter in the existing study table of contents is updated with a self-supporting explanation. Documents are added only when a link requires an independent learning step, and the catalog order reflects the concept of prerequisite. In fact, claims are confirmed in the actual text of the official page, and the source and confirmation time are left as non-disclosed metadata.

## deployment operation

This repository has constant user approval to commit and push completed and newly verified general changes to `origin/main` without separate confirmation. The deployment is complete only when the Pages workflow is successful and the public URL responds. This authorization does not include force pushes, history rewrites, destructive Git operations, releases, secrets, or other remote branches.

## Why not automatically publish vault or harness documents?

Pages deployment is a public operation. Directory scans expand the scope of disclosure simply because new files have been created. In particular, `vault/` neutralizes private knowledge boundaries, and `docs/` mixes harness implementation details that are irrelevant to the reader's Kubernetes learning goals. Explicit catalogs and dedicated content directories make public intent a code-reviewable change.

## result

- On the first screen, visitors can view the entire learning sequence of the Kubernetes and DevOps follow-up course and select a topic.
- The 47 documents then become stable locations for link-based detailed learning.
- Readers can follow concept explanations, diagrams, and run and fail labs on one screen without having to open external documents.
- Each topic has an independent content path and its public scope is limited to its catalog and Git tracked state.
- You can create the same site in CI without a local vault.
