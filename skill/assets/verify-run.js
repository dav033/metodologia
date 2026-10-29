// «Probar»: a link to a running test version goes through the panel itself (http://p<port>.localhost:<panel port>/…),
// so the one SSH tunnel to the panel reaches every version (bt_version_proxy). The waiting tab polls the version's
// servers and opens it when all of them answer. A file, not inline: the panel's CSP runs only its own scripts.
(function () {
  "use strict";
  function viaPanel(port, path) {
    return location.protocol + "//p" + port + ".localhost" + (location.port ? ":" + location.port : "") + (path || "/");
  }

  function rewrite() {
    document.querySelectorAll("a[data-vport]").forEach(function (a) {
      var href = viaPanel(a.dataset.vport, a.dataset.vpath);
      var text = (a.dataset.vprefix || "") + href + (a.dataset.vsuffix || "");
      if (a.getAttribute("href") !== href) a.setAttribute("href", href);
      if (a.textContent !== text) a.textContent = text;          // unchanged text: no new mutation, no loop
    });
  }

  rewrite();
  new MutationObserver(rewrite).observe(document.body, { childList: true, subtree: true });

  var run = document.querySelector(".pp-vrun");
  if (!run) return;
  var sp = run.dataset.sp;
  var said = { preparing: "Preparando la versión…", failed: "Un servidor se detuvo al arrancar; abajo está su salida.",
               stopped: "Los servidores no están en marcha: vuelve a «Probar» y pulsa «Probar esta versión»." };

  function show(s) {
    document.getElementById("vrun-state").textContent = said[s.state] || said.preparing;
    document.getElementById("vrun-log").textContent = s.log || "";
    var list = document.getElementById("vrun-servers");
    list.textContent = "";
    Object.keys(s.servers || {}).forEach(function (name) {
      var item = document.createElement("li");
      item.textContent = name + ": " + (s.servers[name] ? "responde" : "arrancando…");
      list.appendChild(item);
    });
  }

  function tick() {
    fetch(location.pathname + "?format=json&sp=" + encodeURIComponent(sp))
      .then(function (r) { return r.json(); })
      .then(function (s) {
        var url = /^https?:\/\/[^/:]+:(\d+)(\/.*)?$/.exec(s.url || "");
        if (s.state === "ready" && url) { location.replace(viaPanel(url[1], url[2] || "/")); return; }
        show(s);
        if (s.state === "preparing") setTimeout(tick, 2000);
      })
      .catch(function () { setTimeout(tick, 3000); });
  }
  tick();
})();
