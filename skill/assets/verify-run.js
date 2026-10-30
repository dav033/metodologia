// «Probar»: the version's URL is shown as it is (http://localhost:<port>/…). A plain click on it submits the version's
// «Probar» form instead (new tab: stop everything of that version, start it clean, then go to the URL); a middle or
// modified click still opens the URL as is. The waiting tab polls the version and goes to its URL when every server
// answers, or shows the failed step with its log. A file, not inline: the panel's CSP runs only its own scripts.
(function () {
  "use strict";
  if (window.__btVerifyRun) return;                   // loaded by several cards on one page: one listener
  window.__btVerifyRun = true;
  document.addEventListener("click", function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a[data-vstart]") : null;
    if (!a || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    var form = document.getElementById(a.dataset.vstart);
    if (!form) return;
    ev.preventDefault();
    if (form.requestSubmit) form.requestSubmit(); else form.submit();
  });

  var run = document.querySelector(".pp-vrun");
  if (!run) return;
  var sp = run.dataset.sp;
  var said = { preparing: "Arrancando la versión desde cero…", ready: "Lista: abriendo la versión…",
               failed: "No pude arrancar la versión.",
               stopped: "Los servidores no están en marcha: vuelve a «Probar» y pulsa la dirección." };
  var cls = { preparing: "warn", ready: "ok", failed: "bad", stopped: "none" };

  function show(s) {
    var state = document.getElementById("vrun-state");
    state.textContent = said[s.state] || said.preparing;
    state.className = "pp-vstatus " + (cls[s.state] || "none");
    var step = s.step || "";
    if (s.state === "preparing" && s.elapsed) step += " (" + s.elapsed + " s)";
    document.getElementById("vrun-step").textContent = step;
    if (s.url) document.getElementById("vrun-url").textContent = s.url;
    var log = document.getElementById("vrun-log");
    log.textContent = s.log || "";
    log.hidden = !s.log;
    log.scrollTop = log.scrollHeight;                  // the last lines say why
    var retry = document.getElementById("vrun-retry");
    if (retry) retry.hidden = s.state !== "failed" && s.state !== "stopped";
    var list = document.getElementById("vrun-servers");
    list.textContent = "";
    Object.keys(s.servers || {}).forEach(function (name) {
      var item = document.createElement("li");
      var port = (s.ports || {})[name];
      item.textContent = name + (port ? " (puerto " + port + ")" : "") + ": " + (s.servers[name] ? "responde" : "arrancando…");
      list.appendChild(item);
    });
  }

  function tick() {
    fetch(location.pathname + "?format=json&sp=" + encodeURIComponent(sp), { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (s) {
        show(s);
        if (s.state === "ready" && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\//.test(s.url || "")) {
          location.replace(s.url);
          return;
        }
        if (s.state === "preparing") setTimeout(tick, 2000);
      })
      .catch(function () { setTimeout(tick, 3000); });
  }
  tick();
})();
