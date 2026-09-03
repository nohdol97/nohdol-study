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

  const expectedTopicIds = [
    'kubernetes',
    'linux',
    'networking',
    'aws-foundations',
    'terraform-aws',
    'helm-gitops',
    'observability-sre',
    'postgresql',
    'nosql',
    'infrastructure-security',
    'messaging',
    'reliability-finops',
    'karpenter',
  ];
  assert.deepEqual(payload.topics.map((topic) => topic.id), expectedTopicIds);
  assert.equal(expectedCount, 47);
  assert.equal(payload.documents.length, expectedCount);
  assert.equal(new Set(payload.documents.map((document) => document.id)).size, expectedCount);
  assert.ok(payload.documents.every((document) => document.searchText.length > 0));
  assert.ok(payload.documents.every((document) => document.path.startsWith('docs-site/content/')));
  assert.ok(payload.documents.every((document) => !/^(?:vault|_workspace)(?:\/|$)/.test(document.path)));

  const index = await readFile(path.join(outputPath, 'index.html'), 'utf8');
  const app = await readFile(path.join(outputPath, 'assets', 'app.js'), 'utf8');
  const mermaidBundle = await readFile(path.join(outputPath, 'assets', 'mermaid.min.js'), 'utf8');
  const content = JSON.parse(await readFile(path.join(outputPath, 'content.json'), 'utf8'));
  assert.match(index, /href="\.\/assets\/styles\.css"/);
  assert.match(index, /src="\.\/assets\/app\.js"/);
  assert.match(index, /id="diagram-viewer"/);
  assert.match(index, /data-diagram-action="zoom-in"/);
  assert.doesNotMatch(index, /src="\.\/assets\/mermaid\.min\.js"/);
  assert.match(app, /script\.src = '\.\/assets\/mermaid\.min\.js'/);
  assert.match(app, /diagramViewer\.showModal\(\)/);
  assert.match(app, /Math\.min\(3, Math\.max\(0\.35, nextScale\)\)/);
  assert.match(app, /let mermaidRenderQueue = Promise\.resolve\(\)/);
  assert.match(app, /node\.dataset\.processed !== 'true'/);
  assert.match(app, /인프라를/);
  assert.match(app, /Infra Specialist 학습 경로/);
  assert.match(app, /문제와 용어/);
  assert.match(app, /정상 관찰/);
  assert.match(app, /복구 증명/);
  assert.match(app, /운영 판단/);
  assert.doesNotMatch(app, /쿠버네티스 학습 목차/);
  assert.match(mermaidBundle, /globalThis\["mermaid"\]/);
  assert.equal(content.documents.length, expectedCount);

  const roadmap = content.documents.find((document) => document.id === 'kubernetes-roadmap');
  const firstCluster = content.documents.find((document) => document.id === 'kubernetes-first-cluster');
  assert.match(roadmap.html, /href="#doc=kubernetes-first-cluster"/);
  assert.match(roadmap.html, /href="#doc=kubernetes-api-objects"/);
  assert.match(roadmap.html, /처음 보는 사람을 위한 출발점/);
  assert.match(roadmap.html, /처음 이해했는지 확인/);
  assert.match(roadmap.html, /운영 판단으로 확장하기/);
  assert.equal([...roadmap.html.matchAll(/<pre class="mermaid">/g)].length, 2);
  assert.equal([...firstCluster.html.matchAll(/<pre class="mermaid">/g)].length, 2);
  const detailedChapters = content.documents.filter((document) => /^0[2-9]\. |^10\. /.test(document.title));
  assert.equal(detailedChapters.length, 9);
  for (const chapter of detailedChapters) {
    assert.ok(
      [...chapter.html.matchAll(/<pre class="mermaid">/g)].length >= 2,
      `${chapter.id} must contain at least two diagrams`,
    );
    assert.match(chapter.html, /스스로 설명해 보기/);
    assert.match(chapter.html, /language-(?:yaml|bash)/);
    assert.doesNotMatch(chapter.html, /목차 단계|예정 실습|예정 다이어그램|예정 산출물/);
  }
  assert.match(firstCluster.html, /language-yaml/);
  assert.match(firstCluster.html, /ImagePullBackOff/);
  assert.doesNotMatch(roadmap.html, /language-mermaid/);
  assert.doesNotMatch(roadmap.html, /source:/);
  assert.doesNotMatch(firstCluster.html, /source:/);
  const addedTopics = payload.topics.filter((topic) => topic.id !== 'kubernetes');
  for (const topic of addedTopics) {
    const topicDocuments = content.documents.filter((document) => document.topicId === topic.id);
    assert.equal(topicDocuments.length, 3, `${topic.id} must publish three complete documents`);
    assert.equal(topic.documentIds[0], `${topic.id}-roadmap`);
    assert.ok(
      topicDocuments.reduce((total, document) => total + [...document.html.matchAll(/<pre class="mermaid">/g)].length, 0) >= 2,
      `${topic.id} must contain useful relationship diagrams`,
    );
    assert.ok(
      topicDocuments.some((document) => /language-(?:bash|yaml|hcl|sql|json|promql)/.test(document.html)),
      `${topic.id} must contain an executable or reviewable example`,
    );
    for (const document of topicDocuments) {
      const source = await readFile(path.join(REPOSITORY_ROOT, document.path), 'utf8');
      assert.match(source, /<!-- source: https:\/\/[^|]+ \| checked: 2026-09-03/);
      assert.match(document.html, /스스로 설명해 보기|운영 판단으로 확장하기/);
      assert.doesNotMatch(document.html, /source:/);
      if (/\/00-roadmap\.md$/.test(document.path)) {
        assert.match(source, /## 처음 보는 사람을 위한 출발점/);
        assert.match(source, /\| 처음 만나는 말 \| 학습용 쉬운 뜻 \|/);
        assert.match(source, /## 처음 이해했는지 확인/);
        assert.match(source, /## 운영 판단으로 확장하기/);
        assert.ok(
          source.indexOf('## 처음 보는 사람을 위한 출발점') < source.indexOf('## 완료'),
          `${document.id} must establish beginner context before completion criteria`,
        );
      }
      if (/\/(?:01|02)-/.test(document.path)) {
        assert.match(document.html, /먼저 이해하기/);
        assert.match(document.html, /<table>/);
        assert.ok(source.length >= 3000, `${document.id} must explain the model with enough context`);
      }
      if (/\/01-/.test(document.path)) {
        assert.match(source, /## 이 장에서 처음 쓰는 말/);
        assert.match(source, /\n1\. .+\n2\. /);
        assert.ok(
          source.indexOf('## 이 장에서 처음 쓰는 말') < source.indexOf('## 먼저 이해하기'),
          `${document.id} must define terms before using the detailed model`,
        );
      }
      if (/\/02-/.test(document.path)) {
        assert.match(source, /## 실습 전에 준비할 것/);
        assert.ok(
          source.indexOf('## 실습 전에 준비할 것') < source.indexOf('## 먼저 이해하기'),
          `${document.id} must establish prerequisites before the exercise model`,
        );
        assert.match(document.html, /결과를 이렇게 읽는다/);
        assert.ok(source.length >= 3500, `${document.id} must explain how to interpret the exercise`);
      }
    }
  }
  const observabilityRoadmap = content.documents.find((document) => document.id === 'observability-sre-roadmap');
  const postgresqlRoadmap = content.documents.find((document) => document.id === 'postgresql-roadmap');
  const karpenterRoadmap = content.documents.find((document) => document.id === 'karpenter-roadmap');
  assert.match(observabilityRoadmap.html, /href="#doc=kubernetes-roadmap"/);
  assert.match(postgresqlRoadmap.html, /href="#doc=reliability-finops-roadmap"/);
  assert.match(karpenterRoadmap.html, /href="#doc=kubernetes-scheduling-scaling"/);
  assert.ok(content.documents.every((document) => !/<script>/i.test(document.html)));
  assert.ok(content.documents.every((document) => !/href="https:\/\/(?:kubernetes\.io|docs\.aws\.amazon\.com|developer\.hashicorp\.com|helm\.sh|www\.postgresql\.org|redis\.io|karpenter\.sh)/i.test(document.html)));
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
