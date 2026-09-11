import {attachTerms} from './terms.js';

export const READING_MODES = ['ko', 'en', 'both'];
let sessionMode;
export function savedReadingMode(storage) {
  try { const value = storage.getItem('docs-reading-mode'); return READING_MODES.includes(value) ? value : 'both'; }
  catch { return 'both'; }
}

export function initializeReading(article, currentDocument, {language, t}) {
  const storage = {getItem: (key) => localStorage.getItem(key), setItem: (key, value) => localStorage.setItem(key, value)};
  let mode = sessionMode ?? savedReadingMode(storage);
  const controls = article.querySelector('[data-reading-controls]');
  controls.className = 'reading-controls';
  controls.setAttribute('role', 'group');
  controls.setAttribute('aria-label', t('Article reading mode'));
  const label = document.createElement('span'); label.textContent = t('Read in'); controls.append(label);
  const buttons = new Map();
  const applyMode = () => {
    article.dataset.readingMode = mode;
    for (const [value, button] of buttons) button.setAttribute('aria-pressed', String(value === mode));
    if (mode === 'en') article.querySelectorAll('.english-explanation').forEach((node) => {node.open = true;});
  };
  for (const value of READING_MODES) {
    const button = document.createElement('button'); button.type = 'button'; button.dataset.readingMode = value;
    button.textContent = {ko: '한국어', en: 'English', both: '한·영 함께'}[value];
    button.lang = value === 'en' ? 'en' : 'ko';
    button.addEventListener('click', () => {
      mode = value; sessionMode = value; applyMode();
      try {storage.setItem('docs-reading-mode', mode);} catch { /* Reading remains available without storage. */ }
    });
    buttons.set(value, button); controls.append(button);
  }
  for (const [open, text] of [[false, 'Hide English text'], [true, 'Show English text']]) {
    const button = document.createElement('button'); button.type = 'button'; button.className = 'explanation-action';
    button.textContent = t(text); button.dataset.explanations = open ? 'show' : 'hide';
    button.addEventListener('click', () => article.querySelectorAll('.english-explanation').forEach((node) => {node.open = open;}));
    controls.append(button);
  }
  applyMode();
  attachTerms(article, currentDocument, {language, t});
}
