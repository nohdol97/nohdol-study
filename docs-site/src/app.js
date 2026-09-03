const main = document.querySelector('#main-content');
const searchInput = document.querySelector('#site-search');
const themeButton = document.querySelector('.theme-toggle');

let content;
let documentsById;
let topicsById;
let activeQuery = '';

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function parseRoute() {
  const parameters = new URLSearchParams(window.location.hash.slice(1));
  if (parameters.has('doc')) return { view: 'document', id: parameters.get('doc') };
  if (parameters.has('topic')) return { view: 'topic', id: parameters.get('topic') };
  return { view: 'home' };
}

function topicDocuments(topic) {
  return topic.documentIds.map((id) => documentsById.get(id)).filter(Boolean);
}

function documentCard(document, index) {
  return `
    <a class="document-card" href="#doc=${encodeURIComponent(document.id)}">
      <span class="document-index">${String(index + 1).padStart(2, '0')}</span>
      <span class="document-card-copy">
        <strong>${escapeHtml(document.title)}</strong>
        <span>${escapeHtml(document.summary)}</span>
      </span>
      <span class="reading-time">${document.readingMinutes}분</span>
      <span class="arrow" aria-hidden="true">↗</span>
    </a>`;
}

function renderHome() {
  document.title = content.site.title;
  const documentCount = content.documents.length;
  main.innerHTML = `
    <section class="hero shell">
      <div class="hero-copy">
        <p class="eyebrow"><span></span>${escapeHtml(content.site.eyebrow)}</p>
        <h1>무엇을<br /><em>공부할까요?</em></h1>
        <p class="hero-description">${escapeHtml(content.site.description)}</p>
        <button class="hero-search-trigger" type="button" data-focus-search>
          <span>궁금한 키워드로 찾아보기</span>
          <kbd>/</kbd>
        </button>
      </div>
      <div class="hero-orbit" aria-hidden="true">
        <div class="orbit-ring orbit-ring-one"></div>
        <div class="orbit-ring orbit-ring-two"></div>
        <span class="orbit-core">N</span>
        <span class="orbit-label orbit-label-one">collect</span>
        <span class="orbit-label orbit-label-two">verify</span>
        <span class="orbit-label orbit-label-three">connect</span>
      </div>
      <div class="hero-stats" aria-label="문서 사이트 현황">
        <div><strong>${content.topics.length}</strong><span>topics</span></div>
        <div><strong>${documentCount}</strong><span>documents</span></div>
        <div><strong>1</strong><span>source of truth</span></div>
      </div>
    </section>
    <section class="topics-section shell" aria-labelledby="topics-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow"><span></span>CHOOSE A PATH</p>
          <h2 id="topics-title">관심 주제로 시작하세요</h2>
        </div>
        <p>순서대로 읽어도 좋고, 지금 필요한 주제부터 골라도 좋습니다.</p>
      </div>
      <div class="topic-grid">
        ${content.topics
          .map(
            (topic) => `
            <a class="topic-card accent-${escapeHtml(topic.accent)}" href="#topic=${encodeURIComponent(topic.id)}">
              <div class="topic-card-top">
                <span class="topic-number">${escapeHtml(topic.number)}</span>
                <span class="topic-label">${escapeHtml(topic.label)}</span>
                <span class="topic-arrow" aria-hidden="true">↗</span>
              </div>
              <div class="topic-card-body">
                <h3>${escapeHtml(topic.title)}</h3>
                <p>${escapeHtml(topic.description)}</p>
              </div>
              <div class="topic-card-footer">
                <span>${topic.documentIds.length}개 문서</span>
                <span class="topic-line"></span>
              </div>
            </a>`,
          )
          .join('')}
      </div>
    </section>
    <section class="principle-strip">
      <div class="shell principle-inner">
        <p>이 사이트는 문서를 복제하지 않습니다.</p>
        <strong>Tracked Markdown → explicit catalog → GitHub Pages</strong>
        <span>개인 vault는 빌드 범위 밖에 있습니다.</span>
      </div>
    </section>`;
}

function renderTopic(topic) {
  document.title = `${topic.title} — ${content.site.title}`;
  const documents = topicDocuments(topic);
  main.innerHTML = `
    <section class="topic-hero accent-${escapeHtml(topic.accent)}">
      <div class="shell">
        <a class="back-link" href="#"><span aria-hidden="true">←</span> 모든 주제</a>
        <div class="topic-hero-grid">
          <div>
            <p class="eyebrow"><span></span>${escapeHtml(topic.number)} / ${escapeHtml(topic.label)}</p>
            <h1>${escapeHtml(topic.title)}</h1>
          </div>
          <div class="topic-intro">
            <p>${escapeHtml(topic.description)}</p>
            <span>${documents.length}개 문서 · 약 ${documents.reduce((sum, item) => sum + item.readingMinutes, 0)}분</span>
          </div>
        </div>
      </div>
    </section>
    <section class="topic-documents shell" aria-labelledby="topic-documents-title">
      <div class="section-heading compact">
        <div>
          <p class="eyebrow"><span></span>READING ORDER</p>
          <h2 id="topic-documents-title">이 순서로 읽어보세요</h2>
        </div>
        <p>각 문서는 원본 Markdown에서 빌드됩니다.</p>
      </div>
      <div class="document-list">
        ${documents.map(documentCard).join('')}
      </div>
    </section>`;
}

function renderDocument(currentDocument) {
  const topic = topicsById.get(currentDocument.topicId);
  const documents = topicDocuments(topic);
  const currentIndex = documents.findIndex((item) => item.id === currentDocument.id);
  const previous = documents[currentIndex - 1];
  const next = documents[currentIndex + 1];
  document.title = `${currentDocument.title} — ${content.site.title}`;

  main.innerHTML = `
    <div class="reader-shell shell">
      <aside class="reader-sidebar" aria-label="${escapeHtml(topic.title)} 문서 목록">
        <a class="back-link" href="#topic=${encodeURIComponent(topic.id)}"><span aria-hidden="true">←</span> ${escapeHtml(topic.title)}</a>
        <p class="reader-sidebar-label">${escapeHtml(topic.number)} / ${escapeHtml(topic.label)}</p>
        <nav>
          ${documents
            .map(
              (item, index) => `
              <a href="#doc=${encodeURIComponent(item.id)}" ${item.id === currentDocument.id ? 'aria-current="page"' : ''}>
                <span>${String(index + 1).padStart(2, '0')}</span>
                ${escapeHtml(item.title)}
              </a>`,
            )
            .join('')}
        </nav>
      </aside>
      <article class="reader-article">
        <header class="article-header">
          <p class="article-kicker">${escapeHtml(topic.title)}</p>
          <h1>${escapeHtml(currentDocument.title)}</h1>
          <p class="article-summary">${escapeHtml(currentDocument.summary)}</p>
          <div class="article-meta">
            <span>약 ${currentDocument.readingMinutes}분</span>
            <span>${escapeHtml(currentDocument.path)}</span>
            <a href="${escapeHtml(content.site.repository)}/blob/main/${encodeURI(currentDocument.path)}">원본 Markdown ↗</a>
          </div>
        </header>
        <div class="markdown-body">${currentDocument.html}</div>
        <nav class="article-pagination" aria-label="이전 및 다음 문서">
          ${
            previous
              ? `<a class="previous" href="#doc=${encodeURIComponent(previous.id)}"><span>이전 문서</span><strong>← ${escapeHtml(previous.title)}</strong></a>`
              : '<span></span>'
          }
          ${
            next
              ? `<a class="next" href="#doc=${encodeURIComponent(next.id)}"><span>다음 문서</span><strong>${escapeHtml(next.title)} →</strong></a>`
              : '<span></span>'
          }
        </nav>
      </article>
    </div>`;

  document.querySelectorAll('.markdown-body a[href^="http"]').forEach((link) => {
    link.target = '_blank';
    link.rel = 'noreferrer';
  });
}

function searchDocuments(query) {
  const terms = query.toLocaleLowerCase('ko').split(/\s+/).filter(Boolean);
  if (!terms.length) return [];
  return content.documents
    .map((document) => {
      const title = document.title.toLocaleLowerCase('ko');
      const summary = document.summary.toLocaleLowerCase('ko');
      const body = document.searchText.toLocaleLowerCase('ko');
      if (!terms.every((term) => title.includes(term) || summary.includes(term) || body.includes(term))) return null;
      const score = terms.reduce(
        (total, term) => total + (title.includes(term) ? 4 : 0) + (summary.includes(term) ? 2 : 0) + (body.includes(term) ? 1 : 0),
        0,
      );
      return { document, score };
    })
    .filter(Boolean)
    .sort((left, right) => right.score - left.score || left.document.title.localeCompare(right.document.title, 'ko'))
    .map(({ document }) => document);
}

function renderSearch(query) {
  const results = searchDocuments(query);
  document.title = `“${query}” 검색 — ${content.site.title}`;
  main.innerHTML = `
    <section class="search-results shell">
      <a class="back-link" href="#"><span aria-hidden="true">←</span> 게이트웨이</a>
      <div class="search-results-heading">
        <p class="eyebrow"><span></span>SEARCH ALL DOCUMENTS</p>
        <h1>“${escapeHtml(query)}”</h1>
        <p>${results.length}개의 문서를 찾았습니다.</p>
      </div>
      <div class="search-result-list">
        ${
          results.length
            ? results
                .map((document) => {
                  const topic = topicsById.get(document.topicId);
                  return `
                    <a class="search-result" href="#doc=${encodeURIComponent(document.id)}">
                      <span class="search-result-topic">${escapeHtml(topic.number)} · ${escapeHtml(topic.title)}</span>
                      <strong>${escapeHtml(document.title)}</strong>
                      <p>${escapeHtml(document.summary)}</p>
                      <span class="reading-time">약 ${document.readingMinutes}분</span>
                    </a>`;
                })
                .join('')
            : `<div class="empty-state"><strong>일치하는 문서가 없습니다.</strong><p>다른 표현이나 더 짧은 키워드로 찾아보세요.</p></div>`
        }
      </div>
    </section>`;
}

function renderRoute() {
  if (activeQuery.trim()) {
    renderSearch(activeQuery.trim());
    return;
  }

  const route = parseRoute();
  if (route.view === 'document' && documentsById.has(route.id)) renderDocument(documentsById.get(route.id));
  else if (route.view === 'topic' && topicsById.has(route.id)) renderTopic(topicsById.get(route.id));
  else renderHome();
  window.scrollTo({ top: 0, behavior: 'instant' });
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('docs-theme', theme);
}

function initializeTheme() {
  const saved = localStorage.getItem('docs-theme');
  if (saved === 'light' || saved === 'dark') setTheme(saved);
}

async function initialize() {
  try {
    const response = await fetch('./content.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    content = await response.json();
    documentsById = new Map(content.documents.map((document) => [document.id, document]));
    topicsById = new Map(content.topics.map((topic) => [topic.id, topic]));
    document.querySelectorAll('[data-repository-link]').forEach((link) => {
      link.href = content.site.repository;
      link.target = '_blank';
      link.rel = 'noreferrer';
    });
    renderRoute();
  } catch (error) {
    main.innerHTML = `<div class="error-state"><strong>문서를 불러오지 못했습니다.</strong><p>${escapeHtml(error.message)}</p></div>`;
  }
}

window.addEventListener('hashchange', () => {
  activeQuery = '';
  searchInput.value = '';
  renderRoute();
});

searchInput.addEventListener('input', (event) => {
  activeQuery = event.target.value;
  renderRoute();
});

document.addEventListener('keydown', (event) => {
  if (event.key === '/' && document.activeElement !== searchInput) {
    event.preventDefault();
    searchInput.focus();
  }
  if (event.key === 'Escape' && document.activeElement === searchInput) {
    searchInput.value = '';
    activeQuery = '';
    searchInput.blur();
    renderRoute();
  }
});

document.addEventListener('click', (event) => {
  if (event.target.closest('[data-focus-search]')) searchInput.focus();
});

themeButton.addEventListener('click', () => {
  const current = document.documentElement.dataset.theme;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  setTheme(current ? (current === 'dark' ? 'light' : 'dark') : prefersDark ? 'light' : 'dark');
});

initializeTheme();
initialize();
