/**
 * In-browser Python execution via Pyodide (CPython compiled to WebAssembly).
 *
 * Lets live-code blocks run on a static site (e.g. GitHub Pages) with no server.
 * Python only — shell blocks need the local Jupyter runtime. Runs on the main
 * thread (fine for short doc snippets); a Web Worker is a possible future step.
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

/** @type {Promise<any> | null} */
let runtimePromise = null;

async function loadRuntime() {
  if (!runtimePromise) {
    runtimePromise = (async () => {
      const { loadPyodide } = await import(`${INDEX_URL}pyodide.mjs`);
      const pyodide = await loadPyodide({ indexURL: INDEX_URL });
      if (PACKAGES.length) {
        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");
        await micropip.install(PACKAGES);
      }
      return pyodide;
    })().catch((error) => {
      // Allow a later run to retry loading after a transient failure.
      runtimePromise = null;
      throw error;
    });
  }
  return runtimePromise;
}

/**
 * Execute Python in the browser. Mirrors runOnKernel's contract: streams output
 * into `stream` and returns { stdout, stderr, stdoutHtml, stderrHtml }.
 *
 * @param {string} code
 * @param {string} lang
 * @param {{ appendStdout: (t: string) => void, appendStderr: (t: string) => void } | undefined} stream
 */
export async function runOnPyodide(code, lang, stream) {
  if (SHELL_LANGS.has(lang)) {
    const msg =
      "Shell blocks can't run in the browser (Pyodide). Run the docs locally with Jupyter for shell execution.";
    stream?.appendStderr(msg);
    return { stdout: "", stderr: msg, stdoutHtml: "", stderrHtml: "" };
  }

  let pyodide;
  // Pyodide's first load fetches several MB of WASM — surface that so the run
  // doesn't look frozen.
  if (runtimePromise === null) {
    stream?.appendStdout("Loading the in-browser Python runtime (first run only)…\n");
  }
  try {
    pyodide = await loadRuntime();
  } catch (error) {
    const msg = `Failed to load the in-browser Python runtime: ${error?.message ?? error}`;
    stream?.appendStderr(msg);
    return { stdout: "", stderr: msg, stdoutHtml: "", stderrHtml: "" };
  }

  let stdout = "";
  let stderr = "";
  // Pyodide's `batched` callback fires per line, without the trailing newline.
  pyodide.setStdout({
    batched: (text) => {
      stdout += text + "\n";
      stream?.appendStdout(text + "\n");
    },
  });
  pyodide.setStderr({
    batched: (text) => {
      stderr += text + "\n";
      stream?.appendStderr(text + "\n");
    },
  });

  try {
    await pyodide.runPythonAsync(code);
  } catch (error) {
    // PythonError.message holds the formatted traceback.
    const text = error?.message ?? String(error);
    stderr += text;
    stream?.appendStderr(text);
  } finally {
    pyodide.setStdout({});
    pyodide.setStderr({});
  }

  return { stdout, stderr, stdoutHtml: "", stderrHtml: "" };
}
