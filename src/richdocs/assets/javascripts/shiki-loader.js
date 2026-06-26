/* Loads the Shiki highlighter module (MkDocs only injects classic scripts). */
(function () {
  const scope = typeof __md_scope !== "undefined" ? __md_scope : new URL(".", location);
  const script = document.createElement("script");
  script.type = "module";
  script.src = new URL("javascripts/shiki-highlight.mjs?v=20260530b", scope).href;
  document.head.appendChild(script);
})();
