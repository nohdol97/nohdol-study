# Public learning guide

This English learning gateway presents DevOps and AIOps as separate paths on GitHub Pages. It starts with application developers who can create files and run basic shell commands, then connects terminology, normal behavior, failure, recovery, and operational judgment. The catalog contains 20 topics and 77 documents: 15 DevOps topics with 57 documents, and 5 AIOps topics with 20 documents.

- Public URL: <https://nohdol97.github.io/nohdol-study/>
- Public content: `docs-site/content/<topic>/`
- Catalog: `docs-site/catalog.json`

The harness ADRs and specifications in `docs/` and the personal `vault/` are outside the site's publication scope. Vault notes may help identify topics, but public articles are written separately under `docs-site/content/` after checking facts against official documentation and primary sources.

## Expanding topics and articles

When a user provides an official documentation link, read the source and expand the appropriate chapter in the topic's learning sequence. Each article combines verified facts with an independently written explanation, comparisons, and examples. Consult the official documentation for exact version-specific APIs and the complete set of options.

1. Start with a familiar problem that explains why the technology is needed.
2. Introduce technical terms with plain-language definitions and their official English names.
3. Trace an input through the steps that produce a result.
4. Specify prerequisites and establish a working baseline.
5. Change one condition to cause a failure and compare observations before and after it.
6. Explain what the command output proves and what remains unknown.
7. Verify the user outcome and remaining resources after recovery and cleanup.
8. Include comprehension questions and operational decisions about security, reliability, performance, and cost.
9. Preserve source metadata, the evidence-check date, and version or translation freshness limitations.

If an official Korean translation is marked as outdated, check the current English documentation and API reference for claims where freshness matters. Write explanations and examples independently; plain-language definitions, analogies, scenarios, and comparison tables are teaching syntheses rather than quotations. Keep source URLs and evidence-check dates in Markdown HTML comments, which the build removes from published articles. Translating an existing article does not change its evidence-check date or establish that its technical claims have been reverified.

Markdown `mermaid` blocks render using the Mermaid bundle shipped with the site. Diagrams and sequences appear within the article without an external CDN.

The root presents the `infra` and `aiops` learning paths. Each path orders its topics by prerequisites. Every topic has its own roadmap and articles under `docs-site/content/<topic>/`, is explicitly registered in `catalog.json`, and belongs to exactly one path. Relative Markdown links connect prerequisites and follow-up reading across topics and become internal document routes during the build.

DevOps implements the [DevOps public learning path specification](../docs/specs/2026-09-03-infra-specialist-public-learning-path.md); AIOps implements the [AIOps public learning path specification](../docs/specs/2026-09-03-aiops-public-learning-path.md). Smaller topics provide a roadmap, conceptual model, and guided lab. Broader topics provide chapters for each module. DevOps connects traffic control with backend requests, transactions, capacity, distributed workflows, caching, and compatible deployments. AIOps connects AI Specialist topics—LLMs, vision, on-device models, time series, recommendation, and RAG/MCP—with AI Transformation platforms—GPUs, MLOps/LLMOps, AI DevOps/FinOps, and enterprise agents—through operational evidence, diagnosis, and approved remediation.

## Run locally

Node.js 20 or later is required; CI uses Node.js 22.

```sh
cd docs-site
npm ci
npm test
npm run build
npm run preview
```

Open `http://127.0.0.1:4174/` in your browser.

## Publication and deployment

The catalog accepts only Git-tracked Markdown within the repository. The build rejects `vault/`, `REGISTRY.md`, `_workspace/`, absolute paths, and parent-directory traversal.

Changes on `main` trigger `.github/workflows/docs-pages.yml`, which tests and builds the site, then deploys a Pages artifact. The repository's **Settings → Pages → Build and deployment → Source** must be `GitHub Actions`.

This repository has standing authorization to commit and push completed, freshly verified changes to `origin/main` without separate confirmation. That authorization excludes force pushes, history rewrites, releases, and other remotes or branches.

`dist/` is generated output and must not be committed.
