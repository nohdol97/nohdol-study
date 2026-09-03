import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

import { buildSite, loadCatalog } from './build.mjs';

const SITE_ROOT = path.dirname(fileURLToPath(import.meta.url));
const REPOSITORY_ROOT = path.resolve(SITE_ROOT, '..');
const CATALOG_PATH = path.join(SITE_ROOT, 'catalog.json');

async function temporaryDirectory() {
  return mkdtemp(path.join(os.tmpdir(), 'nohdol-docs-site-'));
}

async function clonedCatalog() {
  return JSON.parse(await readFile(CATALOG_PATH, 'utf8'));
}

async function writeCatalog(directory, catalog) {
  const target = path.join(directory, 'catalog.json');
  await writeFile(target, JSON.stringify(catalog), 'utf8');
  return target;
}

test('builds every catalog document into a relative-path Pages artifact', async () => {
  const outputPath = await temporaryDirectory();
  const payload = await buildSite({ outputPath });
  const expectedCount = payload.topics.reduce((total, topic) => total + topic.documentIds.length, 0);

  assert.equal(payload.topics.length, 1);
  assert.equal(payload.topics[0].id, 'kubernetes');
  assert.equal(expectedCount, 11);
  assert.equal(payload.documents.length, expectedCount);
  assert.equal(new Set(payload.documents.map((document) => document.id)).size, expectedCount);
  assert.ok(payload.documents.every((document) => document.searchText.length > 0));
  assert.ok(payload.documents.every((document) => document.path.startsWith('docs-site/content/kubernetes/')));
  assert.ok(payload.documents.every((document) => !/^(?:vault|_workspace)(?:\/|$)/.test(document.path)));

  const index = await readFile(path.join(outputPath, 'index.html'), 'utf8');
  const app = await readFile(path.join(outputPath, 'assets', 'app.js'), 'utf8');
  const mermaidBundle = await readFile(path.join(outputPath, 'assets', 'mermaid.min.js'), 'utf8');
  const content = JSON.parse(await readFile(path.join(outputPath, 'content.json'), 'utf8'));
  assert.match(index, /href="\.\/assets\/styles\.css"/);
  assert.match(index, /src="\.\/assets\/app\.js"/);
  assert.doesNotMatch(index, /src="\.\/assets\/mermaid\.min\.js"/);
  assert.match(app, /script\.src = '\.\/assets\/mermaid\.min\.js'/);
  assert.match(mermaidBundle, /globalThis\["mermaid"\]/);
  assert.equal(content.documents.length, expectedCount);

  const roadmap = content.documents.find((document) => document.id === 'kubernetes-roadmap');
  const firstCluster = content.documents.find((document) => document.id === 'kubernetes-first-cluster');
  assert.match(roadmap.html, /href="#doc=kubernetes-first-cluster"/);
  assert.match(roadmap.html, /href="#doc=kubernetes-api-objects"/);
  assert.equal([...roadmap.html.matchAll(/<pre class="mermaid">/g)].length, 2);
  assert.equal([...firstCluster.html.matchAll(/<pre class="mermaid">/g)].length, 2);
  assert.match(firstCluster.html, /language-yaml/);
  assert.match(firstCluster.html, /ImagePullBackOff/);
  assert.doesNotMatch(roadmap.html, /language-mermaid/);
  assert.doesNotMatch(roadmap.html, /source:/);
  assert.doesNotMatch(firstCluster.html, /source:/);
  assert.ok(content.documents.every((document) => !/<script>/i.test(document.html)));
  assert.ok(content.documents.every((document) => !/href="https:\/\/kubernetes\.io/i.test(document.html)));
  assert.equal(content.documents.some((document) => document.id === 'project-overview'), false);
  assert.equal(content.documents.some((document) => document.id === 'operating-rules'), false);
});

test('rejects duplicate document ids', async () => {
  const directory = await temporaryDirectory();
  const catalog = await clonedCatalog();
  catalog.topics[0].documents[1].id = catalog.topics[0].documents[0].id;
  const catalogPath = await writeCatalog(directory, catalog);

  await assert.rejects(
    () => loadCatalog({ catalogPath, repositoryRoot: REPOSITORY_ROOT, requireTracked: false }),
    /duplicate document id/,
  );
});

test('rejects private paths and path traversal', async () => {
  for (const badPath of ['vault/wiki/private.md', '../outside.md', 'REGISTRY.md']) {
    const directory = await temporaryDirectory();
    const catalog = await clonedCatalog();
    catalog.topics[0].documents[0].path = badPath;
    const catalogPath = await writeCatalog(directory, catalog);
    await assert.rejects(
      () => loadCatalog({ catalogPath, repositoryRoot: REPOSITORY_ROOT, requireTracked: false }),
      /forbidden/,
    );
  }
});

test('rejects Markdown that Git does not track', async () => {
  const directory = await temporaryDirectory();
  const catalog = await clonedCatalog();
  catalog.topics[0].documents[0].path = 'docs/not-a-tracked-document.md';
  const catalogPath = await writeCatalog(directory, catalog);

  await assert.rejects(
    () => loadCatalog({ catalogPath, repositoryRoot: REPOSITORY_ROOT }),
    /not tracked by Git/,
  );
});
