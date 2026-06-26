/**
 * In-browser Python execution via Pyodide — runs in a Web Worker (off the main
 * thread, so the page stays responsive) and streams output back.
 *
 * Lets live-code blocks run on a static site (e.g. GitHub Pages) with no server.
 * Python only — shell blocks need the local Jupyter runtime.
 *
 * Configured via `window.__richdocsConfig.jupyter.pyodide`:
 *   { version, indexUrl, packages: [...] }   // packages installed via micropip
 */

const RICHDOCS = (typeof window !== "undefined" && window.__richdocsConfig) || {};
const PY = (RICHDOCS.jupyter && RICHDOCS.jupyter.pyodide) || {};
const VERSION = PY.version || "0.27.2";
const INDEX_URL = PY.indexUrl || `https://cdn.jsdelivr.net/pyodide/v${VERSION}/full/`;
const PACKAGES = PY.packages || [];

const SHELL_LANGS = new Set(["bash", "sh", "shell", "zsh", "console"]);

/** @type {Worker | null} */
let worker = null;
let nextId = 1;
/** @type {Map<number, { stream: any, onStatus?: (s: string) => void, stdout: string, stderr: string, resolve: (r: any) => void }>} */
const pending = new Map();

function ensureWorker() {
  if (worker) {
    return worker;
  }
  worker = new Worker(new URL("./live-code-pyodide-worker.mjs", import.meta.url), { type: "module" });
  worker.onmessage = (event) => {
    const m = event.data || {};
    const entry = pending.get(m.id);
    if (!entry) {
      return;
    }
    if (m.type === "stdout") {
      entry.stdout += m.text;
      entry.stream?.appendStdout(m.text);
    } else if (m.type === "stderr") {
      entry.stderr += m.text;
      entry.stream?.appendStderr(m.text);
    } else if (m.type === "status") {
      entry.onStatus?.(m.state);
    } else if (m.type === "done") {
      pending.delete(m.id);
      entry.resolve({ stdout: entry.stdout, stderr: entry.stderr, stdoutHtml: "", stderrHtml: "" });
    }
  };
  worker.onerror = (event) => {
    const message = `In-browser Python runtime crashed: ${event.message || "worker error"}`;
    for (const [id, entry] of pending) {
      entry.stream?.appendStderr(message);
      entry.resolve({ stdout: entry.stdout, stderr: entry.stderr + message, stdoutHtml: "", stderrHtml: "" });
      pending.delete(id);
    }
    worker?.terminate();
    worker = null; // recreated on the next run
  };
  return worker;
}

/**
 * Execute Python in the browser (via the worker). Mirrors runOnKernel's contract:
 * streams output into `stream`, returns { stdout, stderr, stdoutHtml, stderrHtml }.
 * `onStatus("loading" | "running")` lets the caller drive a status indicator.
 *
 * @param {string} code
 * @param {string} lang
 * @param {{ appendStdout: (t: string) => void, appendStderr: (t: string) => void } | undefined} stream
 * @param {((state: string) => void) | undefined} onStatus
 */
export async function runOnPyodide(code, lang, stream, onStatus) {
  if (SHELL_LANGS.has(lang)) {
    const msg =
      "Shell blocks can't run in the browser (Pyodide). Run the docs locally with Jupyter for shell execution.";
    stream?.appendStderr(msg);
    return { stdout: "", stderr: msg, stdoutHtml: "", stderrHtml: "" };
  }

  let w;
  try {
    w = ensureWorker();
  } catch (error) {
    const msg = `Could not start the in-browser Python runtime: ${error?.message ?? error}`;
    stream?.appendStderr(msg);
    return { stdout: "", stderr: msg, stdoutHtml: "", stderrHtml: "" };
  }

  const id = nextId++;
  return new Promise((resolve) => {
    pending.set(id, { stream, onStatus, stdout: "", stderr: "", resolve });
    w.postMessage({ type: "run", id, code, indexUrl: INDEX_URL, packages: PACKAGES });
  });
}
