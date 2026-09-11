import {marked} from 'marked';

const meaningful = (tokens) => tokens.filter((token) => token.type !== 'space' && !(token.type === 'html' && /^<!--[\s\S]*-->$/.test(token.raw.trim())));
const fail = (location, message) => { throw new Error(`translation mismatch at ${location}: ${message}`); };

export function renderParallel(english, korean, renderEnglish, renderKorean, location = 'article') {
  function pair(enTokens, koTokens, at) {
    const en = meaningful(enTokens), ko = meaningful(koTokens);
    if (en.length !== ko.length) fail(at, `block count ${en.length} != ${ko.length}`);
    return en.map((a, index) => {
      const b = ko[index], here = `${at}/${index}`;
      if (a.type !== b.type) fail(here, `${a.type} != ${b.type}`);
      if (a.type === 'code') {
        if (a.text !== b.text || a.lang !== b.lang) fail(here, 'code or result changed');
        return renderEnglish(a.raw);
      }
      if (a.type === 'hr') return renderEnglish(a.raw);
      if (a.type === 'heading') {
        if (a.depth !== b.depth) fail(here, 'heading level');
        if (a.depth === 1) return '';
      }
      if (a.type === 'list') {
        if (a.ordered !== b.ordered || a.start !== b.start || a.items.length !== b.items.length) fail(here, 'list structure');
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
      const enHtml = renderEnglish(a.raw), koHtml = renderKorean(b.raw);
      const links = (html) => [...html.matchAll(/href="([^"]*)"/g)].map((match) => match[1]).sort();
      if (JSON.stringify(links(enHtml)) !== JSON.stringify(links(koHtml))) fail(here, 'link destinations');
      const translation = a.type === 'heading'
        ? `<div class="reading-ko" lang="ko">${koHtml}</div>`
        : `<details class="reading-ko korean-explanation" lang="ko" open><summary>한국어 설명</summary>${koHtml}</details>`;
      return `<div class="language-pair" data-pair="${here}"><div class="reading-en" lang="en">${enHtml}</div>${translation}</div>`;
    }).join('\n');
  }
  return pair(marked.lexer(english), marked.lexer(korean), location);
}

export function articleTerms(english, korean) {
  const en = marked.lexer(english).filter((token) => token.type === 'table');
  const ko = marked.lexer(korean).filter((token) => token.type === 'table');
  const clean = (value) => value.replaceAll('`', '').replace(/\*\*([^*]+)\*\*/g, '$1').trim();
  const tables = en.flatMap((table, index) => {
    if (!/^(?:term|new term|concept|word)$/i.test(clean(table.header[0]?.text ?? ''))) return [];
    return table.rows.filter((row) => row.length === 2).map((row, n) => ({
      term: clean(row[0].text), english: clean(row[1].text),
      korean: clean(ko[index].rows[n][1].text),
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
      if (a) lists.push({term: clean(a[1]), english: clean(a[2]), korean: clean(b[2])});
    }
  }
  return [...tables, ...lists];
}
