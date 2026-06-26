/**
 * Web Worker: runs Python via Pyodide off the main thread (non-blocking UI).
 *
 * Protocol
 *   in : { type: "run", id, code, indexUrl, packages }
 *   out: { id, type: "status", state: "loading" | "running" }
 *        { id, type: "stdout" | "stderr", text }
 *        { id, type: "done" }
 */

/** @type {Promise<any> | null} */
let pyodidePromise = null;

async function ensurePyodide(indexUrl, packages) {
  if (!pyodidePromise) {
    pyodidePromise = (async () => {
      const { loadPyodide } = await import(`${indexUrl}pyodide.mjs`);
      const pyodide = await loadPyodide({ indexURL: indexUrl });
      if (packages && packages.length) {
        await pyodide.loadPackage("micropip");
        const micropip = pyodide.pyimport("micropip");
        await micropip.install(packages);
      }
      return pyodide;
    })().catch((error) => {
      pyodidePromise = null; // allow a later run to retry the load
      throw error;
    });
  }
  return pyodidePromise;
}

self.onmessage = async (event) => {
  const msg = event.data || {};
  if (msg.type !== "run") {
    return;
  }
  const { id, code, indexUrl, packages } = msg;

  let pyodide;
  try {
    // First run loads the multi-MB runtime; report it so the UI can show progress.
    self.postMessage({ id, type: "status", state: pyodidePromise ? "running" : "loading" });
    pyodide = await ensurePyodide(indexUrl, packages);
  } catch (error) {
    const text = error && error.message ? error.message : String(error);
    self.postMessage({ id, type: "stderr", text: `Failed to load the in-browser Python runtime: ${text}` });
    self.postMessage({ id, type: "done" });
    return;
  }

  self.postMessage({ id, type: "status", state: "running" });
  pyodide.setStdout({ batched: (text) => self.postMessage({ id, type: "stdout", text: text + "\n" }) });
  pyodide.setStderr({ batched: (text) => self.postMessage({ id, type: "stderr", text: text + "\n" }) });
  try {
    await pyodide.runPythonAsync(code);
  } catch (error) {
    // PythonError.message holds the formatted traceback.
    self.postMessage({ id, type: "stderr", text: error && error.message ? error.message : String(error) });
  } finally {
    pyodide.setStdout({});
    pyodide.setStderr({});
    self.postMessage({ id, type: "done" });
  }
};
