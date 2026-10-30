// «Probar»: the version's URL and the pages its test names are plain links (http://localhost:<port>/…). On a running
// version a click opens the page as it is; otherwise it submits the version's restart form with that page (new tab: stop
// everything of that version, start it clean, then land on that page). A middle or modified click opens the URL as is. The waiting tab polls the version and goes to its URL when every server
// answers, or shows the failed step with its log. A file, not inline: the panel's CSP runs only its own scripts.
(function () {
  "use strict";
  if (window.__btVerifyRun) return;                   // loaded by several cards on one page: one listener
  window.__btVerifyRun = true;
  // «copiar puente»: the SSH bridge command of the version to the clipboard (D-201)
  document.addEventListener("click", function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest("button.pp-vcopy") : null;
    if (!b) return;
    var text = b.dataset.copy || "";
    var done = function () { var was = b.textContent; b.textContent = "copiado ✓"; setTimeout(function () { b.textContent = was; }, 1500); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { window.prompt("Copia el puente:", text); });
    } else {
      window.prompt("Copia el puente:", text);
    }
  });

  // «en mi computador ↗»: the Windows opener (bitacora://) bridges the port and opens the page on the owner's computer.
  // A version that is not running is restarted clean here first (the same form, sent in the background), and the
  // opener is called once every server answers (D-201).
  document.addEventListener("click", function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a.pp-vwin") : null;
    if (!a || ev.button !== 0) return;
    var box = a.closest(".pp-vtry");
    if (!box || box.dataset.state === "ready") return;  // running: the opener link works as it is
    var form = document.getElementById(a.dataset.vstart);
    if (!form) return;
    ev.preventDefault();
    var status = box.querySelector(".pp-vstatus");
    var data = new FormData(form);
    data.set("path", a.dataset.path || "/");
    var sp = data.get("anchor");
    var poll = form.action.replace(/\/verify-run$/, "/verify-run") + "?format=json&sp=" + encodeURIComponent(sp);
    if (status) { status.textContent = "Arrancando la versión desde cero…"; status.className = "pp-vstatus warn"; }
    fetch(form.action, { method: "POST", body: new URLSearchParams(data), credentials: "same-origin" })
      .then(function () {
        (function tick() {
          fetch(poll, { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (s) {
            if (status) {
              status.textContent = s.state === "ready" ? "Lista: abriendo en tu computador…" :
                s.state === "failed" ? "No pude arrancar la versión. " + (s.step || "") : "Arrancando: " + (s.step || "…");
              status.className = "pp-vstatus " + (s.state === "ready" ? "ok" : s.state === "failed" ? "bad" : "warn");
            }
            if (s.state === "ready") { box.dataset.state = "ready"; window.location.href = a.href; return; }
            if (s.state !== "failed") setTimeout(tick, 2000);
          }).catch(function () { setTimeout(tick, 3000); });
        })();
      });
  });

  document.addEventListener("click", function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a[data-vstart]") : null;
    if (a && a.classList.contains("pp-vwin")) return;    // handled above
    if (!a || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    var box = a.closest(".pp-vtry");
    if (box && box.dataset.state === "ready") return;  // running: the link opens the page as it is (D-200)
    var form = document.getElementById(a.dataset.vstart);
    if (!form) return;
    ev.preventDefault();
    var page = form.querySelector('input[name="path"]');
    if (page) page.value = a.dataset.path || "/";     // the new tab lands on the page whose link was clicked
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
          var origin = s.url.replace(/^(https?:\/\/[^\/]+).*$/, "$1");
          var page = /^\/[A-Za-z0-9_\-.\/\[\]]*$/.test(run.dataset.path || "") ? run.dataset.path : "/";
          location.replace(origin + page);
          return;
        }
        if (s.state === "preparing") setTimeout(tick, 2000);
      })
      .catch(function () { setTimeout(tick, 3000); });
  }
  tick();
})();
