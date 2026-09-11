import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile, mkdtemp, writeFile, symlink, mkdir, unlink} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {marked} from 'marked';
import {buildSite, loadCatalog} from './build.mjs';
import {renderParallel, articleTerms, validateTermPurposes, validateTermScenarios} from './bilingual.mjs';
import {savedReadingMode} from './src/reading.js';
import {CORE_TERMS, configureTerms, termsForDocument} from './src/terms.js';

const root = fileURLToPath(new URL('../', import.meta.url));
const parallel = (en, ko) => renderParallel(en, ko, (s) => marked.parse(s), (s) => marked.parse(s));

test('all 94 translations preserve examples, source records and document destinations', async () => {
  const payload = await buildSite({checkOnly: true});
  const ids = new Set(payload.documents.map((d) => d.id));
  configureTerms(payload.documents);
  assert.equal(payload.documents.flatMap((doc) => doc.terms).length, 403, 'no definition may disappear during purpose extraction');
  for (const doc of payload.documents) {
    const en = await readFile(path.join(root, doc.path), 'utf8');
    const ko = await readFile(path.join(root, doc.translation.path), 'utf8');
    const fences = (s) => [...s.matchAll(/^```[^\n]*\n[\s\S]*?^```/gm)].map((m) => m[0]);
    const sources = (s) => [...s.matchAll(/<!-- source:[\s\S]*?-->/g)].map((m) => m[0]);
    assert.deepEqual(fences(ko), fences(en), `${doc.id}: code, output and diagrams`);
    assert.deepEqual(sources(ko), sources(en), `${doc.id}: source-review history`);
    assert.match(doc.koreanSearchText, /[가-힣]/u);
    assert.equal([...doc.parallelHtml.matchAll(/<pre\b/g)].length, [...doc.html.matchAll(/<pre\b/g)].length, `${doc.id}: shared examples appear once`);
    assert.ok(termsForDocument(doc).length > 0, `${doc.id}: terminology available`);
    assert.equal([...doc.parallelHtml.matchAll(/class="term-entry"/g)].length, doc.terms.length, `${doc.id}: every definition has a compact entry`);
    for (const term of termsForDocument(doc)) {
      assert.doesNotThrow(() => validateTermPurposes([term], doc.id));
      assert.doesNotThrow(() => validateTermScenarios([term], doc.id));
      assert.notEqual(term.whyEn, term.english, `${doc.id}: purpose must add context beyond the definition`);
      assert.notEqual(term.whyKo, term.korean);
    }
    for (const term of doc.terms) {
      assert.ok(en.includes(term.whyEn), `${doc.id}: English purpose must remain in Markdown`);
      assert.ok(ko.includes(term.whyKo), `${doc.id}: Korean purpose must remain in Markdown`);
      assert.ok(en.includes(term.exampleEn), `${doc.id}: English situation must remain in Markdown`);
      assert.ok(ko.includes(term.exampleKo), `${doc.id}: Korean situation must remain in Markdown`);
      assert.notEqual(term.exampleEn, term.whyEn);
      assert.notEqual(term.exampleKo, term.whyKo);
    }
    for (const m of doc.parallelHtml.matchAll(/href="#doc=([^"&]+)[^"]*"/g)) assert.ok(ids.has(m[1]), `${doc.id}: ${m[1]}`);
    assert.doesNotMatch(doc.parallelHtml, /<script\b|<!-- source:/i);
  }
  for (const term of CORE_TERMS) {
    assert.ok(ids.has(term.chapter));
    for (const field of ['english', 'korean', 'whyEn', 'whyKo', 'exampleEn', 'exampleKo', 'distinctionEn', 'distinctionKo']) assert.ok(term[field], `${term.term}: ${field}`);
  }
});

test('table and list purposes are extracted separately from their bilingual definitions', () => {
  const reason = {whyEn: 'Locate the current process before inspecting its resources.', whyKo: '자원을 조사하기 전에 현재 실행 중인 프로세스를 찾는 데 쓴다.'};
  const expected = [{term: 'PID', english: 'Process identifier', korean: '프로세스 식별자', ...reason}];
  assert.deepEqual(articleTerms(`| Term | Meaning | Why it matters / when to use it |\n|---|---|---|\n| PID | Process identifier | ${reason.whyEn} |`, `| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |\n|---|---|---|\n| PID | 프로세스 식별자 | ${reason.whyKo} |`), expected);
  assert.deepEqual(articleTerms(`## Terms introduced in this chapter\n\n- **PID**: Process identifier **Why it matters / when to use it:** ${reason.whyEn}`, `## 이 장의 용어\n\n- **PID**: 프로세스 식별자 **왜 필요한가요 · 언제 쓰나요:** ${reason.whyKo}`), expected);
  for (const partial of [{}, {whyEn: reason.whyEn}, {whyKo: reason.whyKo}, {...reason, whyKo: ''}]) assert.throws(() => validateTermPurposes([{term: 'PID', ...partial}], 'fixture'), /missing bilingual term purpose.*PID/);
});

test('a published chapter cannot omit purpose copy in either language', async () => {
  const dir = await mkdtemp(path.join(tmpdir(), 'term-purpose-'));
  const catalog = JSON.parse(await readFile(new URL('./catalog.json', import.meta.url), 'utf8'));
  catalog.paths = [{...catalog.paths[0], topicIds: [catalog.topics[0].id]}];
  catalog.topics = [{...catalog.topics[0], documents: [catalog.topics[0].documents[0]]}];
  const doc = catalog.topics[0].documents[0];
  const source = `# ${doc.title}\n\n| Term | Meaning | Why it matters / when to use it |\n|---|---|---|\n| PID | Process identifier | Locate the current process before inspecting its resources. |\n`;
  const {createHash} = await import('node:crypto');
  doc.path = 'english.md'; doc.translation.path = 'korean.md'; doc.translation.sourceSha256 = createHash('sha256').update(source).digest('hex');
  await writeFile(path.join(dir, doc.path), source);
  await writeFile(path.join(dir, doc.translation.path), `# ${doc.translation.title}\n\n| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |\n|---|---|---|\n| PID | 프로세스 식별자 | |\n`);
  const catalogPath = path.join(dir, 'catalog.json'); await writeFile(catalogPath, JSON.stringify(catalog));
  await assert.rejects(() => buildSite({catalogPath, repositoryRoot: dir, requireTracked: false, checkOnly: true}), /missing bilingual term purpose.*PID/);
});

test('table and list scenarios preserve meaning and purpose while enforcing three bilingual steps', () => {
  const term = {term: 'PID', english: 'Process identifier', korean: '프로세스 식별자',
    whyEn: 'Locate the current process before inspecting its resources.', whyKo: '자원을 조사하기 전에 현재 실행 중인 프로세스를 찾는 데 쓴다.',
    exampleEn: 'A worker uses unexpected CPU. → Identify its PID before inspecting it. → Confirm the process identity still matches.',
    exampleKo: '워커가 예상보다 CPU를 많이 사용한다. → 조사 전에 PID로 해당 프로세스를 찾는다. → 프로세스 신원이 여전히 같은지 확인한다.',
  };
  const enTail = `${term.whyEn} **Concrete situation (illustrative):** ${term.exampleEn}`;
  const koTail = `${term.whyKo} **구체적인 상황(가상 예시):** ${term.exampleKo}`;
  assert.deepEqual(articleTerms(`| Term | Meaning | Why it matters / when to use it |\n|---|---|---|\n| PID | ${term.english} | ${enTail} |`, `| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |\n|---|---|---|\n| PID | ${term.korean} | ${koTail} |`), [term]);
  assert.deepEqual(articleTerms(`## Terms introduced in this chapter\n\n- **PID**: ${term.english} **Why it matters / when to use it:** ${enTail}`, `## 이 장의 용어\n\n- **PID**: ${term.korean} **왜 필요한가요 · 언제 쓰나요:** ${koTail}`), [term]);
  assert.doesNotThrow(() => validateTermScenarios([term], 'fixture'));
  for (const [en, ko] of [
    [`| Term | Meaning | Why it matters / when to use it |\n|---|---|---|\n| PID | ${term.english} | ${enTail} |`, `| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |\n|---|---|---|\n| PID | ${term.korean} | ${koTail} |`],
    [`## Terms introduced in this chapter\n\n- **PID**: ${term.english} **Why it matters / when to use it:** ${enTail}`, `## 이 장의 용어\n\n- **PID**: ${term.korean} **왜 필요한가요 · 언제 쓰나요:** ${koTail}`],
  ]) {
    const html = parallel(en, ko);
    assert.match(html, /<details class="term-entry"><summary>/);
    assert.doesNotMatch(html, /<table|term-entry" open| → /);
    assert.ok(html.indexOf(term.korean) < html.indexOf(term.english), 'Korean meaning precedes English');
    for (const text of [term.whyEn, term.whyKo, ...term.exampleEn.split(' → '), ...term.exampleKo.split(' → ')]) assert.ok(html.includes(text), text);
    assert.throws(() => parallel(en.replace(term.english, '[Definition](https://example.com/one)'), ko.replace(term.korean, '[뜻](https://example.com/two)')), /link destinations/);
  }
  for (const invalid of [
    {exampleEn: undefined}, {exampleKo: undefined}, {exampleEn: ''}, {exampleKo: ''},
    {exampleEn: term.whyEn}, {exampleKo: '상황 → 적용 → 확인'},
    {exampleEn: `${term.exampleEn} → Extra unintended step`}, {exampleKo: term.exampleEn},
  ]) assert.throws(() => validateTermScenarios([{...term, ...invalid}], 'fixture'), /missing bilingual term scenario.*PID/);
});

test('publishing rejects absent or malformed situations in either language', async () => {
  const dir = await mkdtemp(path.join(tmpdir(), 'term-scenario-'));
  const catalog = JSON.parse(await readFile(new URL('./catalog.json', import.meta.url), 'utf8'));
  catalog.paths = [{...catalog.paths[0], topicIds: [catalog.topics[0].id]}];
  catalog.topics = [{...catalog.topics[0], documents: [catalog.topics[0].documents[0]]}];
  const doc = catalog.topics[0].documents[0];
  doc.path = 'english.md'; doc.translation.path = 'korean.md';
  const {createHash} = await import('node:crypto');
  const enExample = 'A worker uses unexpected CPU. → Identify its PID before inspecting it. → Confirm the process identity still matches.';
  const koExample = '워커가 예상보다 CPU를 많이 사용한다. → 조사 전에 PID로 해당 프로세스를 찾는다. → 프로세스 신원이 여전히 같은지 확인한다.';
  for (const [en, ko] of [[null, koExample], [enExample, null], [enExample, '상황만 있고 적용과 확인은 없는 예시다.']]) {
    const source = `# ${doc.title}\n\n| Term | Meaning | Why it matters / when to use it |\n|---|---|---|\n| PID | Process identifier | Locate the current process before inspecting its resources.${en === null ? '' : ' **Concrete situation (illustrative):** ' + en} |\n`;
    doc.translation.sourceSha256 = createHash('sha256').update(source).digest('hex');
    await writeFile(path.join(dir, doc.path), source);
    await writeFile(path.join(dir, doc.translation.path), `# ${doc.translation.title}\n\n| 용어 | 의미 | 왜 필요한가요 · 언제 쓰나요 |\n|---|---|---|\n| PID | 프로세스 식별자 | 자원을 조사하기 전에 현재 실행 중인 프로세스를 찾는 데 쓴다.${ko === null ? '' : ' **구체적인 상황(가상 예시):** ' + ko} |\n`);
    const catalogPath = path.join(dir, 'catalog.json'); await writeFile(catalogPath, JSON.stringify(catalog));
    await assert.rejects(() => buildSite({catalogPath, repositoryRoot: dir, requireTracked: false, checkOnly: true}), /missing bilingual term scenario.*PID/);
  }
});

test('paired lists, headings, tables, and quoted text keep shared code once', () => {
  const en = '# Title\n\n## Model\n\n1. Read\n2. Run\n\n   ```sh\n   echo PASS\n   ```\n\n> Result\n\n| Term | Meaning |\n|---|---|\n| CDC | Change capture |\n';
  const ko = '# 제목\n\n## 모델\n\n1. 읽기\n2. 실행\n\n   ```sh\n   echo PASS\n   ```\n\n> 결과\n\n| 용어 | 의미 |\n|---|---|\n| CDC | 변경 수집 |\n';
  const html = parallel(en, ko);
  assert.doesNotMatch(html, /<h1>/);
  assert.match(html, /lang="en"/); assert.match(html, /lang="ko"/);
  assert.match(html, /<details[^>]+open>/);
  assert.match(html, /english-explanation/);
  assert.doesNotMatch(html, /korean-explanation/);
  assert.ok(html.indexOf('모델') < html.indexOf('Model'), 'Korean heading precedes English');
  assert.equal([...html.matchAll(/echo PASS/g)].length, 1);
  assert.equal([...html.matchAll(/<li>/g)].length, 2);
  assert.deepEqual(articleTerms(en, ko), [{term: 'CDC', english: 'Change capture', korean: '변경 수집'}]);
  assert.deepEqual(articleTerms('| Term | Meaning |\n|---|---|\n| `trace_id` | Shares a trace_id |', '| 용어 | 의미 |\n|---|---|\n| `trace_id` | trace_id를 공유한다 |'), [{term: 'trace_id', english: 'Shares a trace_id', korean: 'trace_id를 공유한다'}]);
});

test('rejects structural drift, changed outputs and changed links', () => {
  for (const [en, ko] of [
    ['One\n\nTwo', '하나'], ['## Heading', '### 제목'],
    ['- One\n- Two', '- 하나'], ['- One', '1. 하나'],
    ['```text\nPASS\n```', '```text\nFAIL\n```'],
    ['```sh\necho PASS\n```', '```text\necho PASS\n```'],
    ['| A | B |\n|---|---|\n| x | y |', '| 가 |\n|---|\n| x |'],
    ['[Source](https://example.com/a)', '[출처](https://example.com/b)'],
  ]) assert.throws(() => parallel(en, ko), /translation mismatch/);
});

test('reading preference defaults to paired and tolerates storage failure', () => {
  for (const value of ['ko', 'en', 'both']) assert.equal(savedReadingMode({getItem: () => value}), value);
  for (const value of [null, 'other', '']) assert.equal(savedReadingMode({getItem: () => value}), 'both');
  assert.equal(savedReadingMode({getItem() {throw Error('blocked');}}), 'both');
});

test('terminology uses whole terms and preserves chapter-specific definitions', () => {
  assert.equal(termsForDocument({title: 'notdbt', searchText: 'CDCatalog Sparkle'}, []).length, 0);
  const terms = termsForDocument({id: 'test', topicId: 'data', title: 'CDC and DBT', searchText: 'grain', terms: [{term: 'CDC', english: 'local', korean: '지역'}]}, [{term: 'grain', english: 'row meaning', korean: '행 의미', topicId: 'data', chapter: 'source'}]);
  assert.deepEqual(terms.map((t) => t.term), ['CDC', 'dbt', 'grain']);
  assert.match(terms[0].english, /Change Data Capture/);
  assert.equal(terms[2].chapter, 'source');
});

test('translation selection rejects private, untracked, stale and missing sources', async () => {
  const original = JSON.parse(await readFile(new URL('./catalog.json', import.meta.url), 'utf8'));
  for (const [mutate, pattern] of [
    ...['vault/wiki/private.md', '_workspace/private.md', 'REGISTRY.md', '../outside.md', '/tmp/outside.md'].map((value) => [(d) => {d.translation.path = value;}, /forbidden/]),
    [(d) => {d.translation.path = 'docs-site/translations/ko/untracked.md';}, /not tracked by Git/],
    [(d) => {d.translation.sourceSha256 = '0'.repeat(64);}, /stale Korean translation/],
    [(d) => {delete d.translation;}, /translation/],
  ]) {
    const dir = await mkdtemp(path.join(tmpdir(), 'bilingual-test-'));
    const catalog = structuredClone(original); mutate(catalog.topics[0].documents[0]);
    const catalogPath = path.join(dir, 'catalog.json'); await writeFile(catalogPath, JSON.stringify(catalog));
    await assert.rejects(() => buildSite({catalogPath, checkOnly: true}), pattern);
  }
});

test('translation realpath cannot escape the repository through a symlink', async () => {
  const dir = await mkdtemp(path.join(tmpdir(), 'bilingual-root-'));
  const outside = await mkdtemp(path.join(tmpdir(), 'bilingual-outside-'));
  const catalog = JSON.parse(await readFile(new URL('./catalog.json', import.meta.url), 'utf8'));
  catalog.paths = [{...catalog.paths[0], topicIds: [catalog.topics[0].id]}];
  catalog.topics = [{...catalog.topics[0], documents: [catalog.topics[0].documents[0]]}];
  const doc = catalog.topics[0].documents[0];
  const source = await readFile(path.join(root, doc.path));
  doc.path = 'english.md'; doc.translation.path = 'translation.md';
  await writeFile(path.join(dir, doc.path), source);
  await writeFile(path.join(outside, 'private.md'), '# Private\n');
  await symlink(path.join(outside, 'private.md'), path.join(dir, doc.translation.path));
  const catalogPath = path.join(dir, 'catalog.json'); await writeFile(catalogPath, JSON.stringify(catalog));
  await assert.rejects(() => buildSite({catalogPath, repositoryRoot: dir, checkOnly: true, requireTracked: false}), /resolves outside repository/);
  await unlink(path.join(dir, doc.translation.path));
  await mkdir(path.join(dir, '_workspace'));
  await writeFile(path.join(dir, '_workspace', 'private.md'), '# Private\n');
  await symlink(path.join(dir, '_workspace', 'private.md'), path.join(dir, doc.translation.path));
  await assert.rejects(() => buildSite({catalogPath, repositoryRoot: dir, checkOnly: true, requireTracked: false}), /private or generated path is forbidden/);
});
