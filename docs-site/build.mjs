import { execFileSync } from 'node:child_process';
import { mkdir, readFile, rm, writeFile, copyFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { marked, Renderer } from 'marked';

const SITE_ROOT = path.dirname(fileURLToPath(import.meta.url));
const REPOSITORY_ROOT = path.resolve(SITE_ROOT, '..');
const DEFAULT_CATALOG = path.join(SITE_ROOT, 'catalog.json');
const DEFAULT_OUTPUT = path.join(SITE_ROOT, 'dist');
const BLOCKED_PATHS = ['vault', 'vault/', 'REGISTRY.md', '_workspace', '_workspace/'];
const REQUIRED_SITE_FIELDS = ['title', 'eyebrow', 'description', 'repository'];
const REQUIRED_TOPIC_FIELDS = ['id', 'number', 'label', 'title', 'description', 'accent', 'documents'];
const REQUIRED_DOCUMENT_FIELDS = ['id', 'title', 'summary', 'path'];
const SAFE_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const SAFE_ACCENTS = new Set(['lime', 'blue', 'orange', 'violet', 'pink', 'teal']);

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

function isBlocked(relativePath) {
  return BLOCKED_PATHS.some((blocked) =>
    blocked.endsWith('/') ? relativePath.startsWith(blocked) : relativePath === blocked,
  );
}

function isExternalLink(href) {
  return /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href);
}

function normalizeRepositoryPath(value) {
  invariant(typeof value === 'string' && value.length > 0, 'document path must be a non-empty string');
  invariant(!path.posix.isAbsolute(value), `absolute document path is forbidden: ${value}`);
  invariant(!value.split('/').includes('..'), `document path traversal is forbidden: ${value}`);
  const normalized = path.posix.normalize(value);
  invariant(normalized === value && normalized !== '.', `document path is not normalized: ${value}`);
  invariant(normalized.endsWith('.md'), `only Markdown documents can be published: ${value}`);
  invariant(!isBlocked(normalized), `private or generated path is forbidden: ${value}`);
  return normalized;
}

function trackedByGit(relativePath, repositoryRoot) {
  try {
    execFileSync('git', ['ls-files', '--error-unmatch', '--', relativePath], {
      cwd: repositoryRoot,
      stdio: 'ignore',
    });
    return true;
  } catch {
    return false;
  }
}

function resolveDocumentLink(href, sourcePath, documentIdByPath, repositoryUrl) {
  if (!href) return href;
  invariant(!/^(?:javascript|vbscript|data):/i.test(href.trim()), `unsafe link protocol in ${sourcePath}`);
  if (isExternalLink(href)) return href;

  const [hrefPath, fragment = ''] = href.split('#', 2);
  if (!hrefPath) return href;

  const decodedPath = decodeURIComponent(hrefPath);
  const targetPath = path.posix.normalize(path.posix.join(path.posix.dirname(sourcePath), decodedPath));
  const targetId = documentIdByPath.get(targetPath);
  if (targetId) return `#doc=${encodeURIComponent(targetId)}`;

  const suffix = fragment ? `#${fragment}` : '';
  return `${repositoryUrl}/blob/main/${encodeURI(targetPath)}${suffix}`;
}

function plainText(markdown) {
  return markdown
    .replace(/^---[\s\S]*?---\s*/u, '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[`*_>#|~-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function readingMinutes(text) {
  return Math.max(1, Math.ceil(text.length / 700));
}

function renderMarkdown(source, sourcePath, documentIdByPath, repositoryUrl) {
  const renderer = new Renderer();
  const renderCode = renderer.code.bind(renderer);
  renderer.code = (token) => {
    if (token.lang?.trim().toLowerCase() === 'mermaid') {
      return `<pre class="mermaid">${escapeHtml(token.text)}</pre>\n`;
    }
    return renderCode(token);
  };
  renderer.html = ({ text }) => {
    if (/^<!--[\s\S]*-->$/u.test(text.trim())) return '';
    return text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  };
  return marked.parse(source, {
    gfm: true,
    renderer,
    walkTokens(token) {
      if (token.type === 'link') {
        token.href = resolveDocumentLink(token.href, sourcePath, documentIdByPath, repositoryUrl);
      }
    },
  });
}

export async function loadCatalog({
  catalogPath = DEFAULT_CATALOG,
  repositoryRoot = REPOSITORY_ROOT,
  requireTracked = true,
} = {}) {
  const raw = await readFile(catalogPath, 'utf8');
  const catalog = JSON.parse(raw);

  invariant(catalog && typeof catalog === 'object', 'catalog must be an object');
  invariant(catalog.site && typeof catalog.site === 'object', 'catalog.site is required');
  for (const field of REQUIRED_SITE_FIELDS) {
    invariant(typeof catalog.site[field] === 'string' && catalog.site[field], `catalog.site.${field} is required`);
  }
  invariant(Array.isArray(catalog.topics) && catalog.topics.length > 0, 'catalog.topics must not be empty');

  const topicIds = new Set();
  const documentIds = new Set();
  const documentPaths = new Set();

  for (const topic of catalog.topics) {
    for (const field of REQUIRED_TOPIC_FIELDS) invariant(field in topic, `topic.${field} is required`);
    invariant(SAFE_ID.test(topic.id), `invalid topic id: ${topic.id}`);
    invariant(!topicIds.has(topic.id), `duplicate topic id: ${topic.id}`);
    invariant(SAFE_ACCENTS.has(topic.accent), `invalid topic accent: ${topic.accent}`);
    invariant(Array.isArray(topic.documents) && topic.documents.length > 0, `topic has no documents: ${topic.id}`);
    topicIds.add(topic.id);

    for (const document of topic.documents) {
      for (const field of REQUIRED_DOCUMENT_FIELDS) invariant(field in document, `document.${field} is required`);
      invariant(SAFE_ID.test(document.id), `invalid document id: ${document.id}`);
      invariant(!documentIds.has(document.id), `duplicate document id: ${document.id}`);
      document.path = normalizeRepositoryPath(document.path);
      invariant(!documentPaths.has(document.path), `duplicate document path: ${document.path}`);
      if (requireTracked) {
        invariant(trackedByGit(document.path, repositoryRoot), `document is not tracked by Git: ${document.path}`);
      }
      documentIds.add(document.id);
      documentPaths.add(document.path);
    }
  }

  return catalog;
}

export async function buildSite({
  catalogPath = DEFAULT_CATALOG,
  outputPath = DEFAULT_OUTPUT,
  repositoryRoot = REPOSITORY_ROOT,
  checkOnly = false,
  requireTracked = true,
} = {}) {
  const catalog = await loadCatalog({ catalogPath, repositoryRoot, requireTracked });
  const repositoryReal = await realpath(repositoryRoot);
  const documentIdByPath = new Map();
  for (const topic of catalog.topics) {
    for (const document of topic.documents) documentIdByPath.set(document.path, document.id);
  }

  const documents = [];
  for (const topic of catalog.topics) {
    for (const document of topic.documents) {
      const absolutePath = path.resolve(repositoryRoot, document.path);
      const sourceReal = await realpath(absolutePath);
      invariant(
        sourceReal === repositoryReal || sourceReal.startsWith(`${repositoryReal}${path.sep}`),
        `document resolves outside repository: ${document.path}`,
      );
      const source = await readFile(sourceReal, 'utf8');
      const text = plainText(source);
      documents.push({
        ...document,
        topicId: topic.id,
        readingMinutes: readingMinutes(text),
        searchText: text,
        html: renderMarkdown(source, document.path, documentIdByPath, catalog.site.repository),
      });
    }
  }

  const payload = {
    site: catalog.site,
    topics: catalog.topics.map(({ documents: topicDocuments, ...topic }) => ({
      ...topic,
      documentIds: topicDocuments.map((document) => document.id),
    })),
    documents,
  };

  if (!checkOnly) {
    await rm(outputPath, { recursive: true, force: true });
    await mkdir(path.join(outputPath, 'assets'), { recursive: true });
    await Promise.all([
      copyFile(path.join(SITE_ROOT, 'src', 'index.html'), path.join(outputPath, 'index.html')),
      copyFile(path.join(SITE_ROOT, 'src', 'styles.css'), path.join(outputPath, 'assets', 'styles.css')),
      copyFile(path.join(SITE_ROOT, 'src', 'app.js'), path.join(outputPath, 'assets', 'app.js')),
      copyFile(
        path.join(SITE_ROOT, 'node_modules', 'mermaid', 'dist', 'mermaid.min.js'),
        path.join(outputPath, 'assets', 'mermaid.min.js'),
      ),
      writeFile(path.join(outputPath, 'content.json'), `${JSON.stringify(payload)}\n`, 'utf8'),
      writeFile(path.join(outputPath, '.nojekyll'), '', 'utf8'),
    ]);
  }

  return payload;
}

function parseArguments(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--check') options.checkOnly = true;
    else if (value === '--out') options.outputPath = path.resolve(argv[++index]);
    else if (value === '--catalog') options.catalogPath = path.resolve(argv[++index]);
    else throw new Error(`unknown argument: ${value}`);
  }
  return options;
}

const invokedDirectly = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (invokedDirectly) {
  try {
    const payload = await buildSite(parseArguments(process.argv.slice(2)));
    const mode = process.argv.includes('--check') ? 'check' : 'build';
    process.stdout.write(
      `docs site ${mode}: PASS (${payload.topics.length} topics, ${payload.documents.length} documents)\n`,
    );
  } catch (error) {
    process.stderr.write(`docs site: FAIL — ${error.message}\n`);
    process.exitCode = 1;
  }
}
