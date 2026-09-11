import {marked} from 'marked';

const meaningful = (tokens) => tokens.filter((token) => token.type !== 'space' && !(token.type === 'html' && /^<!--[\s\S]*-->$/.test(token.raw.trim())));
const fail = (location, message) => { throw new Error(`translation mismatch at ${location}: ${message}`); };

export function renderParallel(english, korean, renderEnglish, renderKorean, location = 'article') {
  const inline = (text, render) => render(text).trim().replace(/^<p>([\s\S]*)<\/p>$/, '$1');
  const languages = (en, ko, className = '') => `<div class="reading-ko ${className}" lang="ko">${renderKorean(ko)}</div><div class="reading-en ${className}" lang="en">${renderEnglish(en)}</div>`;
  const field = (enLabel, koLabel, en, ko) => `<div class="term-field"><p class="term-field-label"><span class="reading-ko" lang="ko">${koLabel}</span><span class="reading-en" lang="en">${enLabel}</span></p>${languages(en, ko)}</div>`;
  const koreanName = (term) => term.koreanTerm.replace(/\s*\(([^()]*)\)$/, (full, name) => name.toLowerCase() === term.term.toLowerCase() ? '' : full);
  const checkLinks = (enHtml, koHtml, at) => {
    const links = (html) => [...html.matchAll(/href="([^"]*)"/g)].map((match) => match[1]).sort();
    if (JSON.stringify(links(enHtml)) !== JSON.stringify(links(koHtml))) fail(at, 'link destinations');
  };
  function glossary(rawEn, rawKo) {
    checkLinks(renderEnglish(rawEn), renderKorean(rawKo), `${location}/glossary`);
    const terms = articleTerms(rawEn, rawKo);
    validateTermPurposes(terms, location); validateTermScenarios(terms, location);
    return `<div class="term-definitions">${terms.map((term) => `<details class="term-entry"><summary><span class="term-entry-name">${term.koreanTerm ? `<span class="reading-ko" lang="ko">${inline(koreanName(term), renderKorean)}</span><span class="reading-en" lang="en">${inline(term.term, renderEnglish)}</span>` : inline(term.term, renderEnglish)}</span><span class="term-entry-meaning reading-ko" lang="ko">${inline(term.korean, renderKorean)}</span><span class="term-entry-meaning reading-en" lang="en">${inline(term.english, renderEnglish)}</span></summary><div class="term-entry-body">${field('Why use it?', '왜 필요한가요?', term.whyEn, term.whyKo)}<p class="term-example-label"><span class="reading-ko" lang="ko">예를 들어 · 가상 상황</span><span class="reading-en" lang="en">An illustrative example</span></p>${['Situation', 'Apply', 'Check'].map((label, i) => field(label, ['상황', '적용', '확인'][i], term.exampleEn.split(' → ')[i], term.exampleKo.split(' → ')[i])).join('')}</div></details>`).join('')}</div>`;
  }
  function pair(enTokens, koTokens, at) {
    const en = meaningful(enTokens), ko = meaningful(koTokens);
    if (en.length !== ko.length) fail(at, `block count ${en.length} != ${ko.length}`);
    let inTerms = false;
    return en.map((a, index) => {
      const b = ko[index], here = `${at}/${index}`;
      if (a.type !== b.type) fail(here, `${a.type} != ${b.type}`);
      if (a.type === 'code') {
        if (a.text !== b.text || a.lang !== b.lang) fail(here, 'code or result changed');
        return renderEnglish(a.raw);
      }
      if (a.type === 'hr') return renderEnglish(a.raw);
      if (a.type === 'heading') {
        inTerms = a.text === 'Terms introduced in this chapter';
        if (a.depth !== b.depth) fail(here, 'heading level');
        if (a.depth === 1) return '';
      }
      if (a.type === 'list') {
        if (a.ordered !== b.ordered || a.start !== b.start || a.items.length !== b.items.length) fail(here, 'list structure');
        if (inTerms && !a.ordered && a.items.every((item) => /^\*\*[^*]+\*\*:/.test(item.text))) {
          return glossary(`## Terms introduced in this chapter\n\n${a.raw}`, `## 이 장의 용어\n\n${b.raw}`);
        }
        const tag = a.ordered ? 'ol' : 'ul';
        const start = a.ordered ? ` start="${a.start}"` : '';
        return `<${tag}${start}>${a.items.map((item, n) => {
          if (item.task !== b.items[n].task || item.checked !== b.items[n].checked) fail(here, 'task state');
          const check = item.task ? `<input type="checkbox" disabled${item.checked ? ' checked' : ''}> ` : '';
          return `<li>${check}${pair(item.tokens, b.items[n].tokens, `${here}/item${n}`)}</li>`;
        }).join('')}</${tag}>`;
      }
      if (a.type === 'blockquote') return `<blockquote>${pair(a.tokens, b.tokens, here)}</blockquote>`;
      if (a.type === 'table' && (a.header.length !== b.header.length || a.rows.length !== b.rows.length || a.rows.some((row, n) => row.length !== b.rows[n].length))) fail(here, 'table shape');
      if (a.type === 'table' && /^(?:term|new term|concept|word)$/i.test(a.header[0]?.text ?? '') && a.header[2]?.text === 'Why it matters / when to use it') return glossary(a.raw, b.raw);
      const enHtml = renderEnglish(a.raw), koHtml = renderKorean(b.raw);
      checkLinks(enHtml, koHtml, here);
      const original = a.type === 'heading'
        ? `<div class="reading-en" lang="en">${enHtml}</div>`
        : `<details class="reading-en english-explanation" lang="en" open><summary>English</summary>${enHtml}</details>`;
      return `<div class="language-pair" data-pair="${here}"><div class="reading-ko" lang="ko">${koHtml}</div>${original}</div>`;
    }).join('\n');
  }
  return pair(marked.lexer(english), marked.lexer(korean), location);
}

export function articleTerms(english, korean) {
  const en = marked.lexer(english).filter((token) => token.type === 'table');
  const ko = marked.lexer(korean).filter((token) => token.type === 'table');
  const clean = (value) => value.replaceAll('`', '').replace(/\*\*([^*]+)\*\*/g, '$1').trim();
  const purposeAndExample = (enText, koText) => {
    const [whyEn, exampleEn] = enText.split(' **Concrete situation (illustrative):** ');
    const [whyKo, exampleKo] = koText.split(' **구체적인 상황(가상 예시):** ');
    return {whyEn: clean(whyEn), whyKo: clean(whyKo),
      ...(exampleEn !== undefined || exampleKo !== undefined ? {exampleEn: clean(exampleEn ?? ''), exampleKo: clean(exampleKo ?? '')} : {}),
    };
  };
  const tables = en.flatMap((table, index) => {
    if (!/^(?:term|new term|concept|word)$/i.test(clean(table.header[0]?.text ?? ''))) return [];
    return table.rows.filter((row) => row.length === 2 || clean(table.header[2]?.text ?? '') === 'Why it matters / when to use it').map((row, n) => ({
      term: clean(row[0].text), english: clean(row[1].text),
      korean: clean(ko[index].rows[n][1].text),
      ...(clean(ko[index].rows[n][0].text).toLowerCase() !== clean(row[0].text).toLowerCase() ? {koreanTerm: clean(ko[index].rows[n][0].text)} : {}),
      ...(clean(table.header[2]?.text ?? '') === 'Why it matters / when to use it'
        ? purposeAndExample(row[2]?.text ?? '', ko[index].rows[n][2]?.text ?? '') : {}),
    }));
  });
  const enBlocks = meaningful(marked.lexer(english)), koBlocks = meaningful(marked.lexer(korean));
  const lists = [];
  let inTerms = false;
  for (const [index, block] of enBlocks.entries()) {
    if (block.type === 'heading') inTerms = block.text === 'Terms introduced in this chapter';
    if (!inTerms || block.type !== 'list' || block.ordered) continue;
    for (const [n, item] of block.items.entries()) {
      const a = item.text.match(/^\*\*([^*]+)\*\*:\s*(.+)$/s);
      const b = koBlocks[index].items[n].text.match(/^\*\*([^*]+)\*\*:\s*(.+)$/s);
      if (a && !b) fail('terminology', 'missing paired definition');
      if (a) {
        const [enMeaning, whyEn] = a[2].split(' **Why it matters / when to use it:** ');
        const [koMeaning, whyKo] = b[2].split(' **왜 필요한가요 · 언제 쓰나요:** ');
        lists.push({term: clean(a[1]), english: clean(enMeaning), korean: clean(koMeaning),
          ...(clean(a[1]) !== clean(b[1]) ? {koreanTerm: clean(b[1])} : {}),
          ...(whyEn !== undefined || whyKo !== undefined ? purposeAndExample(whyEn ?? '', whyKo ?? '') : {}),
        });
      }
    }
  }
  return [...tables, ...lists];
}

export function validateTermPurposes(terms, location) {
  for (const term of terms) {
    if (typeof term.whyEn !== 'string' || term.whyEn.trim().length < 20 || !/[A-Za-z]/.test(term.whyEn)
      || typeof term.whyKo !== 'string' || term.whyKo.trim().length < 20 || !/[가-힣]/u.test(term.whyKo)) {
      throw new Error(`missing bilingual term purpose: ${location}: ${term.term}`);
    }
  }
}

export function validateTermScenarios(terms, location) {
  for (const term of terms) {
    for (const [field, alphabet] of [['exampleEn', /[A-Za-z]/], ['exampleKo', /[가-힣]/u]]) {
      const steps = typeof term[field] === 'string' ? term[field].split(' → ') : [];
      if (steps.length !== 3 || steps.some((step) => step.trim().length < 10 || !alphabet.test(step))) {
        throw new Error(`missing bilingual term scenario (situation → apply → check): ${location}: ${term.term}: ${field}`);
      }
    }
  }
}
