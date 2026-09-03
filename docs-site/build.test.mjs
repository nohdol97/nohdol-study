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

  assert.equal(payload.documents.length, expectedCount);
  assert.equal(new Set(payload.documents.map((document) => document.id)).size, expectedCount);
  assert.ok(payload.documents.every((document) => document.searchText.length > 0));
  assert.ok(payload.documents.every((document) => !/^(?:vault|_workspace)(?:\/|$)/.test(document.path)));

  const index = await readFile(path.join(outputPath, 'index.html'), 'utf8');
  const content = JSON.parse(await readFile(path.join(outputPath, 'content.json'), 'utf8'));
  assert.match(index, /href="\.\/assets\/styles\.css"/);
  assert.match(index, /src="\.\/assets\/app\.js"/);
  assert.equal(content.documents.length, expectedCount);

  const mapDocument = content.documents.find((document) => document.id === 'documentation-map');
  assert.match(mapDocument.html, /href="#doc=telegram-guide"/);
  const changelog = content.documents.find((document) => document.id === 'harness-changelog');
  assert.doesNotMatch(changelog.html, /<script>/i);
  assert.match(changelog.html, /&lt;script&gt;/i);
});

test('rejects duplicate document ids', async () => {
  const directory = await temporaryDirectory();
  const catalog = await clonedCatalog();
  catalog.topics[1].documents[0].id = catalog.topics[0].documents[0].id;
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
