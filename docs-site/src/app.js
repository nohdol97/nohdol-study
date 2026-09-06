const main = document.querySelector('#main-content');
const searchInput = document.querySelector('#site-search');
const themeButton = document.querySelector('.theme-toggle');
const diagramViewer = document.querySelector('#diagram-viewer');
const diagramCanvas = diagramViewer.querySelector('[data-diagram-canvas]');
const diagramZoomOutput = diagramViewer.querySelector('[data-diagram-zoom]');

let content;
let documentsById;
let topicsById;
let pathsById;
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
  if (parameters.has('path')) return { view: 'path', id: parameters.get('path') };
  return { view: 'home' };
}

function topicDocuments(topic) {
  return topic.documentIds.map((id) => documentsById.get(id)).filter(Boolean);
}

function pathTopics(learningPath) {
  return learningPath.topicIds.map((id) => topicsById.get(id)).filter(Boolean);
}

function documentCard(document, index) {
  return `
    <a class="document-card" href="#doc=${encodeURIComponent(document.id)}">
      <span class="document-index">${String(index + 1).padStart(2, '0')}</span>
      <span class="document-card-copy">
        <strong>${escapeHtml(document.title)}</strong>
        <span>${escapeHtml(document.summary)}</span>
      </span>
      <span class="reading-time">${document.readingMinutes} min</span>
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
        <h1>Learn operations.<br /><em>Go deeper.</em></h1>
        <p class="hero-description">${escapeHtml(content.site.description)}</p>
        <button class="hero-search-trigger" type="button" data-focus-search>
          <span>Search a topic or keyword</span>
          <kbd>/</kbd>
        </button>
      </div>
      <div class="hero-orbit" aria-hidden="true">
        <div class="orbit-ring orbit-ring-one"></div>
        <div class="orbit-ring orbit-ring-two"></div>
        <span class="orbit-core">S</span>
        <span class="orbit-label orbit-label-one">learn</span>
        <span class="orbit-label orbit-label-two">connect</span>
        <span class="orbit-label orbit-label-three">operate</span>
      </div>
      <div class="hero-stats" aria-label="Documentation overview">
        <div><strong>${content.paths.length}</strong><span>learning paths</span></div>
        <div><strong>${content.topics.length}</strong><span>topics</span></div>
        <div><strong>${documentCount}</strong><span>documents</span></div>
      </div>
    </section>
    <section class="topics-section shell" aria-labelledby="topics-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow"><span></span>CHOOSE A PATH</p>
          <h2 id="topics-title">Choose your learning path</h2>
        </div>
        <p>Connect DevOps request and data flows with AIOps models and platforms through observability, diagnosis, and recovery.</p>
      </div>
      <div class="path-grid">
        ${content.paths
          .map(
            (learningPath) => {
              const topics = pathTopics(learningPath);
              const pathDocumentCount = topics.reduce((total, topic) => total + topic.documentIds.length, 0);
              return `
            <a class="topic-card path-card accent-${escapeHtml(learningPath.accent)}" href="#path=${encodeURIComponent(learningPath.id)}">
              <div class="topic-card-top">
                <span class="topic-number">${escapeHtml(learningPath.number)}</span>
                <span class="topic-label">${escapeHtml(learningPath.label)}</span>
                <span class="topic-arrow" aria-hidden="true">↗</span>
              </div>
              <div class="topic-card-body">
                <h3>${escapeHtml(learningPath.title)}</h3>
                <p>${escapeHtml(learningPath.description)}</p>
              </div>
              <div class="topic-card-footer">
                <span>${topics.length} topics · ${pathDocumentCount} documents</span>
                <span class="topic-line"></span>
              </div>
            </a>`;
            },
          )
          .join('')}
      </div>
    </section>
    <section class="principle-strip">
      <div class="shell principle-inner">
        <p>Build operational judgment through essential terms, working examples, failures, and recovery.</p>
        <strong>Problem → Key terms → Baseline → Failure → Recovery → Operational judgment</strong>
        <span>Start with plain explanations and connect technical terms to observable evidence.</span>
      </div>
    </section>`;
}

function renderPath(learningPath) {
  document.title = `${learningPath.title} — ${content.site.title}`;
  const topics = pathTopics(learningPath);
  main.innerHTML = `
    <section class="topic-hero accent-${escapeHtml(learningPath.accent)}">
      <div class="shell">
        <a class="back-link" href="#"><span aria-hidden="true">←</span> All learning paths</a>
        <div class="topic-hero-grid">
          <div>
            <p class="eyebrow"><span></span>${escapeHtml(learningPath.number)} / ${escapeHtml(learningPath.label)}</p>
            <h1>${escapeHtml(learningPath.title)}</h1>
          </div>
          <div class="topic-intro">
            <p>${escapeHtml(learningPath.description)}</p>
            <span>${topics.length} topics · ${topics.reduce((total, topic) => total + topic.documentIds.length, 0)} documents</span>
          </div>
        </div>
      </div>
    </section>
    <section class="topics-section shell" aria-labelledby="path-topics-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow"><span></span>CHOOSE A TOPIC</p>
          <h2 id="path-topics-title">${escapeHtml(learningPath.title)} learning path</h2>
        </div>
        <p>Each topic moves from problems and terms to observing a baseline, isolating failures, verifying recovery, and making operational decisions.</p>
      </div>
      <ol class="learning-ladder" aria-label="Learning stages from foundations to operational judgment">
        <li><strong>1. Problems and terms</strong><span>Understand the problem and unpack unfamiliar terms.</span></li>
        <li><strong>2. Observe the baseline</strong><span>Run a small example and record evidence of normal behavior.</span></li>
        <li><strong>3. Isolate the failure</strong><span>Change one condition and find where the flow stops.</span></li>
        <li><strong>4. Verify recovery</strong><span>Check that the expected user outcome has been restored.</span></li>
        <li><strong>5. Operational judgment</strong><span>Explain tradeoffs in security, reliability, performance, and cost.</span></li>
      </ol>
      <div class="topic-grid">
        ${topics
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
              <div class="topic-card-footer"><span>${topic.documentIds.length} documents</span><span class="topic-line"></span></div>
            </a>`,
          )
          .join('')}
      </div>
    </section>`;
}

function renderTopic(topic) {
  document.title = `${topic.title} — ${content.site.title}`;
  const learningPath = pathsById.get(topic.pathId);
  const documents = topicDocuments(topic);
  main.innerHTML = `
    <section class="topic-hero accent-${escapeHtml(topic.accent)}">
      <div class="shell">
        <a class="back-link" href="#path=${encodeURIComponent(learningPath.id)}"><span aria-hidden="true">←</span> ${escapeHtml(learningPath.title)}</a>
        <div class="topic-hero-grid">
          <div>
            <p class="eyebrow"><span></span>${escapeHtml(topic.number)} / ${escapeHtml(topic.label)}</p>
            <h1>${escapeHtml(topic.title)}</h1>
          </div>
          <div class="topic-intro">
            <p>${escapeHtml(topic.description)}</p>
            <span>${documents.length} documents · About ${documents.reduce((sum, item) => sum + item.readingMinutes, 0)} min</span>
          </div>
        </div>
      </div>
    </section>
    <section class="topic-documents shell" aria-labelledby="topic-documents-title">
      <div class="section-heading compact">
        <div>
          <p class="eyebrow"><span></span>READING ORDER</p>
          <h2 id="topic-documents-title">Follow this reading order</h2>
        </div>
        <p>Start with the roadmap, then work through the concepts and labs in order.</p>
      </div>
      <div class="document-list">
        ${documents.map(documentCard).join('')}
      </div>
    </section>`;
}

function renderDocument(currentDocument) {
  const topic = topicsById.get(currentDocument.topicId);
  const learningPath = pathsById.get(currentDocument.pathId);
  const documents = topicDocuments(topic);
  const currentIndex = documents.findIndex((item) => item.id === currentDocument.id);
  const previous = documents[currentIndex - 1];
  const next = documents[currentIndex + 1];
  document.title = `${currentDocument.title} — ${content.site.title}`;

  main.innerHTML = `
    <div class="reader-shell shell">
      <aside class="reader-sidebar" aria-label="${escapeHtml(topic.title)} documents">
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
          <p class="article-kicker">${escapeHtml(learningPath.title)} · ${escapeHtml(topic.title)}</p>
          <h1>${escapeHtml(currentDocument.title)}</h1>
          <p class="article-summary">${escapeHtml(currentDocument.summary)}</p>
          <div class="article-meta">
            <span>About ${currentDocument.readingMinutes} min</span>
            <span>${escapeHtml(currentDocument.path)}</span>
            <a href="${escapeHtml(content.site.repository)}/blob/main/${encodeURI(currentDocument.path)}">Markdown source ↗</a>
          </div>
        </header>
        <div class="markdown-body">${currentDocument.html}</div>
        <nav class="article-pagination" aria-label="Previous and next documents">
          ${
            previous
              ? `<a class="previous" href="#doc=${encodeURIComponent(previous.id)}"><span>Previous document</span><strong>← ${escapeHtml(previous.title)}</strong></a>`
              : '<span></span>'
          }
          ${
            next
              ? `<a class="next" href="#doc=${encodeURIComponent(next.id)}"><span>Next document</span><strong>${escapeHtml(next.title)} →</strong></a>`
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
  node.title = 'Click to expand';
  const button = document.createElement('button');
  button.className = 'diagram-expand-button';
  button.type = 'button';
  button.innerHTML = '<span aria-hidden="true">↗</span> Expand';
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
  enlargedDiagram.setAttribute('aria-label', 'Enlarged diagram');
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
  const terms = query.toLocaleLowerCase('en').split(/\s+/).filter(Boolean);
  if (!terms.length) return [];
  return content.documents
    .map((document) => {
      const title = document.title.toLocaleLowerCase('en');
      const summary = document.summary.toLocaleLowerCase('en');
      const body = document.searchText.toLocaleLowerCase('en');
      if (!terms.every((term) => title.includes(term) || summary.includes(term) || body.includes(term))) return null;
      const score = terms.reduce(
        (total, term) => total + (title.includes(term) ? 4 : 0) + (summary.includes(term) ? 2 : 0) + (body.includes(term) ? 1 : 0),
        0,
      );
      return { document, score };
    })
    .filter(Boolean)
    .sort((left, right) => right.score - left.score || left.document.title.localeCompare(right.document.title, 'en'))
    .map(({ document }) => document);
}

function renderSearch(query) {
  const results = searchDocuments(query);
  document.title = `“${query}” search — ${content.site.title}`;
  main.innerHTML = `
    <section class="search-results shell">
      <a class="back-link" href="#"><span aria-hidden="true">←</span> Gateway</a>
      <div class="search-results-heading">
        <p class="eyebrow"><span></span>SEARCH ALL DOCUMENTS</p>
        <h1>“${escapeHtml(query)}”</h1>
        <p>${results.length} documents found.</p>
      </div>
      <div class="search-result-list">
        ${
          results.length
            ? results
                .map((document) => {
                  const topic = topicsById.get(document.topicId);
                  const learningPath = pathsById.get(document.pathId);
                  return `
                    <a class="search-result" href="#doc=${encodeURIComponent(document.id)}">
                      <span class="search-result-topic">${escapeHtml(learningPath.title)} · ${escapeHtml(topic.title)}</span>
                      <strong>${escapeHtml(document.title)}</strong>
                      <p>${escapeHtml(document.summary)}</p>
                      <span class="reading-time">About ${document.readingMinutes} min</span>
                    </a>`;
                })
                .join('')
            : `<div class="empty-state"><strong>No matching documents.</strong><p>Try different wording or a shorter keyword.</p></div>`
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
  else if (route.view === 'path' && pathsById.has(route.id)) renderPath(pathsById.get(route.id));
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
    pathsById = new Map(content.paths.map((learningPath) => [learningPath.id, learningPath]));
    document.querySelectorAll('[data-repository-link]').forEach((link) => {
      link.href = content.site.repository;
      link.target = '_blank';
      link.rel = 'noreferrer';
    });
    renderRoute();
  } catch (error) {
    main.innerHTML = `<div class="error-state"><strong>Could not load the documents.</strong><p>${escapeHtml(error.message)}</p></div>`;
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
