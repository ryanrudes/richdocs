/**
 * VS Code-accurate Shades of Purple via Shiki + the official theme JSON.
 */
import { createHighlighter } from "https://esm.sh/shiki@3.12.0";

const RICHDOCS = (typeof window !== "undefined" && window.__richdocsConfig) || {};
const RICHDOCS_THEME = RICHDOCS.theme || {};

/** Registered Shiki theme name (must match the theme JSON's `name`). */
export const THEME_NAME = RICHDOCS_THEME.shikiThemeName || "Shades of Purple";

/** A bare id resolves to a bundled theme; a path/URL is used as-is. */
function resolveThemeUrl(theme) {
  const id = theme || "shades-of-purple";
  if (id.includes("/") || id.endsWith(".json")) {
    return new URL(id, document.baseURI);
  }
  return new URL(`../themes/${id}-shiki.json`, import.meta.url);
}

const THEME_URL = resolveThemeUrl(RICHDOCS_THEME.shikiTheme);
const RICHDOCS_CODE_BG_FALLBACK = "#2d2b55";
const RICHDOCS_PAGE_BG_FALLBACK = "#1e1e3f";

const HL = RICHDOCS_THEME.highlight || {};
const DEFAULT_LANGUAGE = HL.defaultLanguage || "python";
const INLINE_ENABLED = HL.inline !== false;

const LANG_ALIASES = {
  py: "python",
  sh: "bash",
  shell: "bash",
  yml: "yaml",
  md: "markdown",
  ...(HL.aliases || {}),
};

const BASE_LANGS = HL.languages || [
  "python",
  "bash",
  "yaml",
  "toml",
  "json",
  "markdown",
  "text",
  "plaintext",
];

/** @type {Promise<import('shiki').Highlighter> | null} */
let highlighterPromise = null;

export async function getHighlighter() {
  if (!highlighterPromise) {
    highlighterPromise = (async () => {
      const theme = await fetch(THEME_URL).then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load theme: ${response.status}`);
        }
        return response.json();
      });
      const editorBg =
        theme.colors?.["editor.background"]?.toLowerCase() ?? RICHDOCS_CODE_BG_FALLBACK;
      const pageBg =
        theme.colors?.["panel.background"]?.toLowerCase() ?? RICHDOCS_PAGE_BG_FALLBACK;
      document.documentElement.style.setProperty("--rd-code-bg", editorBg);
      document.documentElement.style.setProperty("--rd-page-bg", pageBg);
      return createHighlighter({
        themes: [theme],
        langs: BASE_LANGS,
      });
    })();
  }
  return highlighterPromise;
}

/** @param {string} lang */
export function resolveLanguageId(lang) {
  const raw = String(lang || DEFAULT_LANGUAGE).toLowerCase();
  return LANG_ALIASES[raw] || raw;
}

function resolveLanguage(codeEl) {
  const match = /\blang(?:uage)?-([\w-]+)\b/i.exec(codeEl.className);
  if (match) {
    return resolveLanguageId(match[1]);
  }
  return DEFAULT_LANGUAGE;
}

function unwrapCodeHtml(html) {
  return html
    .replace(/^<pre[^>]*><code[^>]*>/i, "")
    .replace(/<\/code><\/pre>\s*$/i, "");
}

export async function ensureLanguage(highlighter, lang) {
  try {
    await highlighter.loadLanguage(lang);
    return lang;
  } catch {
    await highlighter.loadLanguage("text");
    return "text";
  }
}

async function highlightBlockCodeElement(codeEl, highlighter) {
  if (codeEl.dataset.shikiHighlighted === "true") {
    return;
  }

  const lang = await ensureLanguage(highlighter, resolveLanguage(codeEl));
  const source = codeEl.textContent ?? "";
  const html = highlighter.codeToHtml(source, { lang, theme: THEME_NAME });
  codeEl.innerHTML = unwrapCodeHtml(html);
  codeEl.classList.add("shiki");
  codeEl.dataset.shikiHighlighted = "true";

  const pre = codeEl.closest("pre");
  if (pre) {
    pre.classList.add("shiki");
  }
}

async function highlightInlineCodeElement(codeEl, highlighter) {
  if (codeEl.dataset.shikiHighlighted === "true" || codeEl.closest("pre")) {
    return;
  }

  const lang = await ensureLanguage(highlighter, resolveLanguage(codeEl));
  const source = codeEl.textContent ?? "";
  const html = highlighter.codeToHtml(source, {
    lang,
    theme: THEME_NAME,
    structure: "inline",
  });
  codeEl.innerHTML = html;
  codeEl.classList.add("shiki", "shiki-inline");
  codeEl.dataset.shikiHighlighted = "true";
}

function isMkdocstringsBadgeCode(el) {
  if (!(el instanceof HTMLElement) || el.tagName !== "CODE") {
    return false;
  }
  if (el.classList.contains("doc-symbol")) {
    return true;
  }
  return Boolean(el.closest(".doc-label, .doc-labels, .doc-label-toc"));
}

function resetMkdocstringsBadges(root) {
  for (const el of root.querySelectorAll(
    "code.doc-symbol.shiki, .doc-label code.shiki, .doc-label-toc code.shiki",
  )) {
    const text = el.textContent ?? "";
    el.classList.remove("shiki", "shiki-inline");
    delete el.dataset.shikiHighlighted;
    el.replaceChildren();
    el.textContent = text;
  }
}

async function highlightAll(root) {
  resetMkdocstringsBadges(root);
  const highlighter = await getHighlighter();
  const blockCodes = new Set();
  const inlineCodes = new Set();

  root.querySelectorAll(".md-typeset pre code").forEach((el) => blockCodes.add(el));
  if (INLINE_ENABLED) {
    root.querySelectorAll(".md-typeset code").forEach((el) => {
      if (el.closest("pre") !== null) {
        return;
      }
      if (el.closest(".highlight") !== null) {
        return;
      }
      /* mkdocstrings badges (def/class/var, property, module-attribute, …) — CSS only */
      if (isMkdocstringsBadgeCode(el)) {
        return;
      }
      inlineCodes.add(el);
    });
  }

  await Promise.all([
    ...[...blockCodes].map((el) => highlightBlockCodeElement(el, highlighter)),
    ...[...inlineCodes].map((el) => highlightInlineCodeElement(el, highlighter)),
  ]);
}

/** Re-highlight one block after live-code reset. */
export async function highlightCodeElement(codeEl) {
  const highlighter = await getHighlighter();
  delete codeEl.dataset.shikiHighlighted;
  codeEl.classList.remove("shiki");
  codeEl.closest("pre")?.classList.remove("shiki");
  await highlightBlockCodeElement(codeEl, highlighter);
}

document$.subscribe(() => {
  highlightAll(document.body)
    .then(() => {
      document.body.dispatchEvent(new CustomEvent("docs-shiki-ready"));
    })
    .catch((error) => {
      console.error("Shiki highlighting failed:", error);
      document.body.dispatchEvent(new CustomEvent("docs-shiki-ready"));
    });
});
