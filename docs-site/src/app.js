const main = document.querySelector('#main-content');
const searchInput = document.querySelector('#site-search');
const themeButton = document.querySelector('.theme-toggle');
const diagramViewer = document.querySelector('#diagram-viewer');
const diagramCanvas = diagramViewer.querySelector('[data-diagram-canvas]');
const diagramZoomOutput = diagramViewer.querySelector('[data-diagram-zoom]');

let content;
let documentsById;
let topicsById;
let activeQuery = '';
let mermaidRuntime;
let mermaidLoadPromise;
let mermaidRenderQueue = Promise.resolve();
let diagramScale = 1;
let diagramNaturalWidth = 0;
let enlargedDiagram;

function loadMermaid() {
  if (mermaidRuntime) return Promise.resolve(mermaidRuntime);
  if (mermaidLoadPromise) return mermaidLoadPromise;

  mermaidLoadPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = './assets/mermaid.min.js';
    script.onload = () => {
      mermaidRuntime = globalThis.mermaid;
      if (!mermaidRuntime) {
        reject(new Error('Mermaid runtime did not initialize'));
        return;
      }
      mermaidRuntime.initialize({
        startOnLoad: false,
        securityLevel: 'strict',
        theme: 'base',
        themeVariables: {
          fontFamily: 'Inter, Pretendard, sans-serif',
          primaryColor: '#e8f1ff',
          primaryBorderColor: '#326ce5',
          primaryTextColor: '#17211b',
          lineColor: '#526159',
          secondaryColor: '#f6f4ed',
          tertiaryColor: '#fffef9',
          actorBkg: '#e8f1ff',
          actorBorder: '#326ce5',
          actorTextColor: '#17211b',
          signalColor: '#17211b',
          signalTextColor: '#17211b',
          noteBkgColor: '#fff4d6',
          noteBorderColor: '#d2a53d',
          noteTextColor: '#17211b',
        },
      });
      resolve(mermaidRuntime);
    };
    script.onerror = () => reject(new Error('Mermaid bundle could not be loaded'));
    document.head.append(script);
  });

  return mermaidLoadPromise;
}

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
        <h1>인프라를<br /><em>쉽게, 깊게</em></h1>
        <p class="hero-description">${escapeHtml(content.site.description)}</p>
        <button class="hero-search-trigger" type="button" data-focus-search>
          <span>궁금한 키워드로 찾아보기</span>
          <kbd>/</kbd>
        </button>
      </div>
      <div class="hero-orbit" aria-hidden="true">
        <div class="orbit-ring orbit-ring-one"></div>
        <div class="orbit-ring orbit-ring-two"></div>
        <span class="orbit-core">I</span>
        <span class="orbit-label orbit-label-one">design</span>
        <span class="orbit-label orbit-label-two">operate</span>
        <span class="orbit-label orbit-label-three">recover</span>
      </div>
      <div class="hero-stats" aria-label="문서 사이트 현황">
        <div><strong>${content.topics.length}</strong><span>topics</span></div>
        <div><strong>${documentCount}</strong><span>documents</span></div>
        <div><strong>6</strong><span>learning phases</span></div>
      </div>
    </section>
    <section class="topics-section shell" aria-labelledby="topics-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow"><span></span>CHOOSE A PATH</p>
          <h2 id="topics-title">Infra Specialist 학습 경로</h2>
        </div>
        <p>각 주제는 쉬운 문제 상황과 용어에서 시작해 정상 관찰, 실패·복구, 운영 판단 순서로 깊어집니다.</p>
      </div>
      <ol class="learning-ladder" aria-label="초심자에서 전문가 판단까지의 학습 단계">
        <li><strong>1. 문제와 용어</strong><span>왜 필요한지 보고 낯선 말을 먼저 풉니다.</span></li>
        <li><strong>2. 정상 관찰</strong><span>작은 예제를 실행하고 정상 상태의 증거를 남깁니다.</span></li>
        <li><strong>3. 실패 분리</strong><span>조건 하나를 바꾸고 어느 단계에서 멈췄는지 찾습니다.</span></li>
        <li><strong>4. 복구 증명</strong><span>명령 성공이 아니라 사용자 결과가 돌아왔는지 확인합니다.</span></li>
        <li><strong>5. 운영 판단</strong><span>보안·신뢰성·성능·비용의 선택 근거를 설명합니다.</span></li>
      </ol>
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
        <p>처음 만나는 용어부터 정상 실행·실패·복구를 거쳐 전문가의 판단 순서를 배웁니다.</p>
        <strong>문제 상황 → 쉬운 용어 → 정상 관찰 → 실패 → 복구 → 운영 판단</strong>
        <span>쉬운 설명은 출발점이고, 전문 용어는 실제 증거와 연결해 익힙니다.</span>
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
        <p>로드맵의 초심자 설명부터 읽고, 개념과 실습을 순서대로 진행하세요.</p>
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

  renderMermaidDiagrams(document.querySelector('.markdown-body'));
}

async function renderMermaidDiagrams(root) {
  const nodes = [...root.querySelectorAll('.mermaid')];
  if (!nodes.length) return;

  try {
    const runtime = await loadMermaid();
    mermaidRenderQueue = mermaidRenderQueue
      .catch(() => {})
      .then(async () => {
        const pendingNodes = nodes.filter((node) => node.isConnected && node.dataset.processed !== 'true');
        if (!pendingNodes.length) return;
        await runtime.run({ nodes: pendingNodes });
        pendingNodes.filter((node) => node.isConnected).forEach(decorateDiagram);
      });
    await mermaidRenderQueue;
  } catch (error) {
    nodes.forEach((node) => {
      if (!node.dataset.processed) node.classList.add('diagram-error');
    });
    console.error('Mermaid diagram rendering failed', error);
  }
}

function decorateDiagram(node) {
  if (node.querySelector('.diagram-expand-button')) return;
  node.classList.add('diagram-interactive');
  node.title = '클릭해서 크게 보기';
  const button = document.createElement('button');
  button.className = 'diagram-expand-button';
  button.type = 'button';
  button.innerHTML = '<span aria-hidden="true">↗</span> 크게 보기';
  button.addEventListener('click', (event) => {
    event.stopPropagation();
    openDiagramViewer(node);
  });
  node.addEventListener('click', (event) => {
    if (event.target.closest('a')) return;
    openDiagramViewer(node);
  });
  node.append(button);
}

function diagramWidth(svg) {
  const viewBox = svg.viewBox?.baseVal;
  if (viewBox?.width) return viewBox.width;
  return Math.max(svg.getBoundingClientRect().width, 640);
}

function updateDiagramScale(nextScale) {
  if (!enlargedDiagram) return;
  diagramScale = Math.min(3, Math.max(0.35, nextScale));
  enlargedDiagram.style.width = `${diagramNaturalWidth * diagramScale}px`;
  diagramZoomOutput.value = `${Math.round(diagramScale * 100)}%`;
  diagramZoomOutput.textContent = diagramZoomOutput.value;
}

function fitDiagram() {
  if (!enlargedDiagram) return;
  const availableWidth = Math.max(diagramCanvas.clientWidth - 48, 280);
  updateDiagramScale(Math.min(1, availableWidth / diagramNaturalWidth));
  diagramCanvas.scrollTo({ top: 0, left: 0 });
}

function openDiagramViewer(node) {
  const svg = node.querySelector('svg');
  if (!svg) return;
  enlargedDiagram = svg.cloneNode(true);
  enlargedDiagram.removeAttribute('style');
  enlargedDiagram.setAttribute('aria-label', '확대된 다이어그램');
  diagramNaturalWidth = diagramWidth(svg);
  diagramCanvas.replaceChildren(enlargedDiagram);
  if (!diagramViewer.open) diagramViewer.showModal();
  requestAnimationFrame(() => {
    fitDiagram();
    diagramCanvas.focus({ preventScroll: true });
  });
}

function closeDiagramViewer() {
  if (diagramViewer.open) diagramViewer.close();
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
  closeDiagramViewer();
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

diagramViewer.addEventListener('click', (event) => {
  const action = event.target.closest('[data-diagram-action]')?.dataset.diagramAction;
  if (action === 'zoom-out') updateDiagramScale(diagramScale - 0.2);
  if (action === 'zoom-in') updateDiagramScale(diagramScale + 0.2);
  if (action === 'fit') fitDiagram();
  if (action === 'close') closeDiagramViewer();
  if (event.target === diagramViewer) closeDiagramViewer();
});

diagramCanvas.addEventListener('wheel', (event) => {
  if (!event.ctrlKey && !event.metaKey) return;
  event.preventDefault();
  updateDiagramScale(diagramScale + (event.deltaY < 0 ? 0.15 : -0.15));
}, { passive: false });

themeButton.addEventListener('click', () => {
  const current = document.documentElement.dataset.theme;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  setTheme(current ? (current === 'dark' ? 'light' : 'dark') : prefersDark ? 'light' : 'dark');
});

initializeTheme();
initialize();
