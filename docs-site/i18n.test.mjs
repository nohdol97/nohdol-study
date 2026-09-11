import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {localizeCatalog, message, rememberLanguage, savedLanguage} from './src/i18n.js';

test('messages translate parameters and fall back to readable English', () => {
  assert.equal(message('Search docs', 'ko'), '문서 검색');
  assert.equal(message('Search docs', 'en'), 'Search docs');
  assert.equal(message('{count} documents found.', 'ko', {count: 0}), '문서 0개를 찾았습니다.');
  assert.equal(message('{count} documents found.', 'en', {count: 12}), '12 documents found.');
  assert.equal(message('New label', 'ko'), 'New label');
  assert.equal(message('Search docs', 'unsupported'), 'Search docs');
});

test('language persistence tolerates unavailable storage and invalid preferences', () => {
  const values = new Map();
  const storage = {getItem: (key) => values.get(key), setItem: (key, value) => values.set(key, value)};
  assert.equal(savedLanguage(storage), 'en');
  rememberLanguage(storage, 'ko');
  assert.equal(savedLanguage(storage), 'ko');
  rememberLanguage(storage, 'invalid');
  assert.equal(savedLanguage(storage), 'ko');
  rememberLanguage(storage, 'en');
  assert.equal(savedLanguage(storage), 'en');
  values.set('docs-language', 'invalid');
  assert.equal(savedLanguage(storage), 'en');
  const blocked = {getItem() {throw new Error('blocked');}, setItem() {throw new Error('blocked');}};
  assert.equal(savedLanguage(blocked), 'en');
  assert.doesNotThrow(() => rememberLanguage(blocked, 'ko'));
});

test('Korean navigation covers every path and topic without mutating canonical documents', async () => {
  const catalog = JSON.parse(await readFile(new URL('./catalog.json', import.meta.url), 'utf8'));
  const original = structuredClone(catalog);
  const translated = localizeCatalog(catalog, 'ko');
  for (const field of ['paths', 'topics']) {
    assert.deepEqual(translated[field].map((item) => item.id), catalog[field].map((item) => item.id));
    for (const item of translated[field]) {
      assert.match(item.description, /[가-힣]/u, `${field}/${item.id} has a Korean description`);
    }
  }
  assert.deepEqual(catalog, original);
  assert.equal(localizeCatalog(catalog, 'en'), catalog);
  const payload = {...catalog, documents: [{id: 'example', html: '<pre>SELECT 1;</pre>', title: 'English title'}]};
  assert.equal(localizeCatalog(payload, 'ko').documents, payload.documents);
  const futureTopic = {id: 'future', title: 'Future', description: 'English fallback'};
  assert.equal(localizeCatalog({...catalog, topics: [futureTopic]}, 'ko').topics[0], futureTopic);
});
