import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
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

test('publishes the complete data and observability course from explicitly selected docs', async () => {
  const payload = await buildSite({ checkOnly: true });
  const learningPath = payload.paths.find((item) => item.id === 'data-observability');
  assert.deepEqual(learningPath.topicIds, ['data-observability-engineering']);
  const documents = payload.documents.filter((item) => item.pathId === learningPath.id);
  assert.equal(documents.length, 17);
  const selectedPaths = new Set(payload.documents.map((item) => item.path));
  let diagramCount = 0;
  for (const document of documents) {
    assert.ok(document.path.startsWith('docs/guides/data-observability/'));
    const source = await readFile(path.join(REPOSITORY_ROOT, document.path), 'utf8');
    assert.ok(source.startsWith(`# ${document.title}\n`));
    assert.match(source, /checked: 2026-09-10/);
    assert.match(document.html, /Explain it in your own words|Develop operational judgment/);
    assert.doesNotMatch(document.html, /<!--|source:|turn\d+(?:search|view)\d+|memcite/);
    for (const match of source.matchAll(/\]\(([^)]+\.md)(?:#[^)]*)?\)/g)) {
      const target = path.posix.normalize(path.posix.join(path.posix.dirname(document.path), match[1]));
      assert.ok(selectedPaths.has(target), `${document.id}: missing published target ${target}`);
    }
    for (const match of source.matchAll(/```json\n([\s\S]*?)```/g)) {
      assert.doesNotThrow(() => JSON.parse(match[1]), document.id);
    }
    diagramCount += [...document.html.matchAll(/<pre class="mermaid">/g)].length;
  }
  assert.ok(diagramCount >= 6);
  const byId = new Map(documents.map((item) => [item.id.replace('data-observability-engineering-', ''), item]));
  assert.match(byId.get('roadmap').html, /#doc=data-observability-engineering-capstone/);
  assert.match(byId.get('roadmap').html, /#doc=observability-sre-roadmap/);
  assert.match(byId.get('kafka-cdc-streaming').html, /at-least-once/);
  assert.match(byId.get('quality-contracts-slos').html, /interval still belongs in the denominator/);
  assert.match(byId.get('opentelemetry').html, /In-memory queues can disappear on restart/);
  assert.match(byId.get('cloud-platforms').html, /Enterprise Edition/);
  assert.match(byId.get('ai-ready-data-evaluation').html, /held-out evaluation set/);
  assert.match(byId.get('source-review').html, /chatgpt|shared conversation/);
});

test('the documented local SQL and capstone correctness fixtures execute successfully', async () => {
  const examples = [
    ['02-sql-python-foundations.md', /350/],
    ['15-capstone.md', /PASS: replay, totals, invalid values, conflicts, missing input, ordering/],
  ];
  for (const [filename, expected] of examples) {
    const source = await readFile(path.join(REPOSITORY_ROOT, 'docs/guides/data-observability', filename), 'utf8');
    const code = source.match(/```python\n([\s\S]*?)```/);
    assert.ok(code, `missing runnable fixture: ${filename}`);
    const output = execFileSync('python3', ['-c', code[1]], { encoding: 'utf8', timeout: 10000 });
    assert.match(output, expected);
  }
});

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
    'traffic-resilience',
    'backend-engineering',
    'ai-specialist-core',
    'ai-transformation-platform',
    'aiops-foundations',
    'aiops-diagnosis',
    'aiops-remediation',
    'data-observability-engineering',
  ];
  assert.deepEqual(payload.paths.map((learningPath) => learningPath.id), ['infra', 'aiops', 'data-observability']);
  assert.deepEqual(payload.paths.map((learningPath) => learningPath.title), ['DevOps', 'AIOps', 'Data & Observability']);
  assert.equal(payload.paths[0].topicIds.length, 15);
  assert.equal(payload.paths[1].topicIds.length, 5);
  assert.deepEqual(payload.topics.map((topic) => topic.id), expectedTopicIds);
  assert.equal(expectedCount, 94);
  assert.equal(payload.documents.length, expectedCount);
  assert.equal(new Set(payload.documents.map((document) => document.id)).size, expectedCount);
  assert.ok(payload.documents.every((document) => document.searchText.length > 0));
  assert.ok(payload.documents.every((document) => document.path.startsWith('docs-site/content/') || document.path.startsWith('docs/guides/data-observability/')));
  assert.ok(payload.documents.every((document) => !/^(?:vault|_workspace)(?:\/|$)/.test(document.path)));

  const index = await readFile(path.join(outputPath, 'index.html'), 'utf8');
  const app = await readFile(path.join(outputPath, 'assets', 'app.js'), 'utf8');
  const mermaidBundle = await readFile(path.join(outputPath, 'assets', 'mermaid.min.js'), 'utf8');
  const content = JSON.parse(await readFile(path.join(outputPath, 'content.json'), 'utf8'));
  assert.match(index, /href="\.\/assets\/styles\.css"/);
  assert.match(index, /src="\.\/assets\/app\.js"/);
  assert.match(index, /id="diagram-viewer"/);
  assert.match(index, /<html lang="en">/);
  const styles = await readFile(path.join(outputPath, 'assets', 'styles.css'), 'utf8');
  assert.doesNotMatch(index + app + styles + JSON.stringify(content), /[\u3131-\u318e\uac00-\ud7a3]/u);
  assert.match(index, /placeholder="Search docs"/);
  assert.match(index, /aria-label="Diagram zoom controls"/);
  assert.match(index, /data-diagram-action="zoom-in"/);
  assert.doesNotMatch(index, /src="\.\/assets\/mermaid\.min\.js"/);
  assert.match(app, /script\.src = '\.\/assets\/mermaid\.min\.js'/);
  assert.match(app, /diagramViewer\.showModal\(\)/);
  assert.match(app, /Math\.min\(3, Math\.max\(0\.35, nextScale\)\)/);
  assert.match(app, /let mermaidRenderQueue = Promise\.resolve\(\)/);
  assert.match(app, /node\.dataset\.processed !== 'true'/);
  assert.match(app, /Learn operations/);
  assert.match(app, /Choose your learning path/);
  assert.match(app, /content\.paths/);
  assert.match(app, /#path=/);
  assert.match(app, /Problems and terms/);
  assert.match(app, /Observe the baseline/);
  assert.match(app, /Verify recovery/);
  assert.match(app, /Operational judgment/);
  assert.doesNotMatch(app, /Kubernetes learning contents/);
  assert.match(mermaidBundle, /globalThis\["mermaid"\]/);
  assert.equal(content.documents.length, expectedCount);

  const roadmap = content.documents.find((document) => document.id === 'kubernetes-roadmap');
  const firstCluster = content.documents.find((document) => document.id === 'kubernetes-first-cluster');
  const apiObjects = content.documents.find((document) => document.id === 'kubernetes-api-objects');
  assert.match(roadmap.html, /href="#doc=kubernetes-first-cluster"/);
  assert.match(roadmap.html, /href="#doc=kubernetes-api-objects"/);
  assert.match(roadmap.html, /Starting point for beginners/);
  assert.match(roadmap.html, /Check your understanding/);
  assert.match(roadmap.html, /Develop operational judgment/);
  assert.equal([...roadmap.html.matchAll(/<pre class="mermaid">/g)].length, 2);
  assert.equal([...firstCluster.html.matchAll(/<pre class="mermaid">/g)].length, 2);
  assert.match(apiObjects.html, /What does a Namespace separate/);
  assert.match(apiObjects.html, /does not establish a security boundary by itself/);
  assert.match(apiObjects.html, /kubectl api-resources --namespaced=true/);
  assert.match(apiObjects.html, /namespace-demo-a/);
  assert.match(apiObjects.html, /ResourceQuota and LimitRange/);
  const detailedChapters = content.documents.filter((document) => /^0[2-9]\. |^10\. /.test(document.title));
  assert.equal(detailedChapters.length, 9);
  for (const chapter of detailedChapters) {
    assert.ok(
      [...chapter.html.matchAll(/<pre class="mermaid">/g)].length >= 2,
      `${chapter.id} must contain at least two diagrams`,
    );
    assert.match(chapter.html, /Explain it in your own words/);
    assert.match(chapter.html, /language-(?:yaml|bash)/);
    assert.doesNotMatch(chapter.html, /Outline stage|Planned lab|Planned diagram|Planned deliverable/);
  }
  assert.match(firstCluster.html, /language-yaml/);
  assert.match(firstCluster.html, /ImagePullBackOff/);
  assert.doesNotMatch(roadmap.html, /language-mermaid/);
  assert.doesNotMatch(roadmap.html, /source:/);
  assert.doesNotMatch(firstCluster.html, /source:/);
  const addedTopics = payload.topics.filter((topic) => !['kubernetes', 'data-observability-engineering'].includes(topic.id));
  let parsedJsonExamples = 0;
  for (const topic of addedTopics) {
    const topicDocuments = content.documents.filter((document) => document.topicId === topic.id);
    const isExpandedHub = ['backend-engineering', 'ai-specialist-core', 'ai-transformation-platform'].includes(topic.id);
    assert.ok(topicDocuments.length >= 3, `${topic.id} must publish a complete learning unit`);
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
      for (const match of source.matchAll(/```json\n([\s\S]*?)```/g)) {
        assert.doesNotThrow(() => JSON.parse(match[1]), `${document.id} must contain valid JSON examples`);
        parsedJsonExamples += 1;
      }
      assert.match(source, /<!-- source: https:\/\/[^|]+ \| checked: 2026-09-03/);
      assert.match(document.html, /Explain it in your own words|Develop operational judgment/);
      assert.doesNotMatch(document.html, /source:/);
      if (/\/00-roadmap\.md$/.test(document.path)) {
        assert.match(source, /## Starting point for beginners/);
        assert.match(source, /\| New term \| Plain-language meaning \|/);
        assert.match(source, /## Check your understanding/);
        assert.match(source, /## Develop operational judgment/);
        assert.ok(
          source.indexOf('## Starting point for beginners') < source.indexOf('## Completion criteria'),
          `${document.id} must establish beginner context before completion criteria`,
        );
      }
      if (!/\/00-roadmap\.md$/.test(document.path)) {
        assert.match(document.html, /Understand the model first/);
        assert.match(document.html, /<table>/);
        assert.ok(source.length >= 3000, `${document.id} must explain the model with enough context`);
      }
      if (/\/01-/.test(document.path) || (isExpandedHub && !/\/00-roadmap\.md$/.test(document.path))) {
        assert.match(source, /## Terms introduced in this chapter/);
        assert.match(source, /\n1\. .+\n2\. /);
        assert.ok(
          source.indexOf('## Terms introduced in this chapter') < source.indexOf('## Understand the model first'),
          `${document.id} must define terms before using the detailed model`,
        );
      }
      if (/\/02-/.test(document.path) && !isExpandedHub) {
        assert.match(source, /## Lab prerequisites/);
        assert.ok(
          source.indexOf('## Lab prerequisites') < source.indexOf('## Understand the model first'),
          `${document.id} must establish prerequisites before the exercise model`,
        );
        assert.match(document.html, /How to interpret the results/);
        assert.ok(source.length >= 3500, `${document.id} must explain how to interpret the exercise`);
      }
    }
  }
  assert.ok(parsedJsonExamples >= 6, 'the AIOps path must include multiple valid incident and operation records');
  const observabilityRoadmap = content.documents.find((document) => document.id === 'observability-sre-roadmap');
  const postgresqlRoadmap = content.documents.find((document) => document.id === 'postgresql-roadmap');
  const karpenterRoadmap = content.documents.find((document) => document.id === 'karpenter-roadmap');
  const trafficRoadmap = content.documents.find((document) => document.id === 'traffic-resilience-roadmap');
  const aiopsFoundationsRoadmap = content.documents.find((document) => document.id === 'aiops-foundations-roadmap');
  const aiopsDiagnosisRoadmap = content.documents.find((document) => document.id === 'aiops-diagnosis-roadmap');
  const aiopsRemediationRoadmap = content.documents.find((document) => document.id === 'aiops-remediation-roadmap');
  const backendRoadmap = content.documents.find((document) => document.id === 'backend-engineering-roadmap');
  const aiSpecialistRoadmap = content.documents.find((document) => document.id === 'ai-specialist-core-roadmap');
  const aiTransformationRoadmap = content.documents.find((document) => document.id === 'ai-transformation-platform-roadmap');
  assert.match(observabilityRoadmap.html, /href="#doc=kubernetes-roadmap"/);
  assert.match(postgresqlRoadmap.html, /href="#doc=reliability-finops-roadmap"/);
  assert.match(karpenterRoadmap.html, /href="#doc=kubernetes-scheduling-scaling"/);
  assert.match(trafficRoadmap.html, /href="#doc=aiops-remediation-roadmap"/);
  assert.match(aiopsFoundationsRoadmap.html, /href="#doc=observability-sre-roadmap"/);
  assert.match(aiopsDiagnosisRoadmap.html, /href="#doc=aiops-foundations-roadmap"/);
  assert.match(aiopsRemediationRoadmap.html, /href="#doc=traffic-resilience-roadmap"/);
  assert.match(backendRoadmap.html, /href="#doc=traffic-resilience-roadmap"/);
  assert.match(backendRoadmap.html, /href="#doc=aiops-remediation-roadmap"/);
  assert.match(aiSpecialistRoadmap.html, /href="#doc=ai-transformation-platform-roadmap"/);
  assert.match(aiSpecialistRoadmap.html, /href="#doc=aiops-foundations-roadmap"/);
  assert.match(aiTransformationRoadmap.html, /href="#doc=ai-specialist-core-llm"/);
  assert.match(aiTransformationRoadmap.html, /href="#doc=aiops-foundations-evidence-graph"/);
  for (const term of [
    'HTTP/2·HTTP/3',
    'TLA+',
    'eBPF·io_uring·zero-copy',
    'CDC·CQRS·Event Sourcing',
    'fleet device registry',
    'memory hierarchy·storage latency',
    'insertion-based idempotence of incremental aggregates',
    'risk of re-identification from aggregate headcounts',
    'guarantees at each stage of the OpenTelemetry pipeline',
  ]) {
    assert.match(backendRoadmap.html, new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  for (const term of [
    'MLA low-rank KV compression',
    'Gated DeltaNet',
    'Stable Diffusion',
    'GPTQ·AWQ',
    'HNSW·DiskANN',
  ]) {
    assert.match(aiSpecialistRoadmap.html, new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  for (const term of [
    'Ray distributed compute',
    'Kueue quota·gang scheduling',
    'LiteLLM gateway',
    'Temporal durable execution',
    'A2A task lifecycle',
    'OPA/Rego policy',
  ]) {
    assert.match(aiTransformationRoadmap.html, new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
  assert.doesNotMatch(index + app + JSON.stringify(content.site) + JSON.stringify(content.paths), /Infra Specialist/);
  assert.ok(content.documents.every((document) => !/<script>/i.test(document.html)));
  assert.ok(content.documents
    .filter((document) => document.id !== 'data-observability-engineering-source-review')
    .every((document) => !/href="https:\/\/(?:kubernetes\.io|docs\.aws\.amazon\.com|developer\.hashicorp\.com|helm\.sh|www\.postgresql\.org|redis\.io|karpenter\.sh)/i.test(document.html)));
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

test('rejects missing, duplicate, and unknown path topic assignments', async () => {
  for (const mutate of [
    (catalog) => catalog.paths[0].topicIds.pop(),
    (catalog) => catalog.paths[1].topicIds.push(catalog.paths[0].topicIds[0]),
    (catalog) => catalog.paths[1].topicIds.push('missing-topic'),
  ]) {
    const directory = await temporaryDirectory();
    const catalog = await clonedCatalog();
    mutate(catalog);
    const catalogPath = await writeCatalog(directory, catalog);
    await assert.rejects(
      () => loadCatalog({ catalogPath, repositoryRoot: REPOSITORY_ROOT, requireTracked: false }),
      /not assigned|more than one path|unknown topic/,
    );
  }
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
