// «Probar»: the version's URL and the pages its test names are plain links (http://localhost:<port>/…). On a running
// version a click opens the page as it is; otherwise it submits the version's restart form with that page (new tab: stop
// everything of that version, start it clean, then land on that page). A middle or modified click opens the URL as is. The waiting tab polls the version and goes to its URL when every server
// answers, or shows the failed step with its log. A file, not inline: the panel's CSP runs only its own scripts.
(function () {
  "use strict";
  if (window.__btVerifyRun) return;                   // loaded by several cards on one page: one listener
  window.__btVerifyRun = true;
  // «Entras como»: every link of the block signs in as the chosen test account; remembered per browser (D-205)
  function account(select) {
    var box = select.closest(".pp-vtry");
    if (!box) return;
    box.querySelectorAll("a[data-go]").forEach(function (a) {
      var go = a.dataset.go.replace(/([?&])account=[^&]*/, "$1account=" + encodeURIComponent(select.value));
      if (go.indexOf("account=") < 0) go += "&account=" + encodeURIComponent(select.value);
      a.dataset.go = go;
      if (a.classList.contains("pp-vurl")) a.href = go;
    });
  }
  document.querySelectorAll(".pp-vaccount select").forEach(function (select) {
    try {
      var kept = localStorage.getItem("bt-verify-account");
      if (kept && Array.prototype.some.call(select.options, function (o) { return o.value === kept; })) select.value = kept;
    } catch (e) { /* no storage: the default account */ }
    account(select);
    select.addEventListener("change", function () {
      try { localStorage.setItem("bt-verify-account", select.value); } catch (e) { /* kept for this page only */ }
      account(select);
    });
  });

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
    if (a.dataset.go) {                                  // D-205: session cookie first, then the opener (same browser)
      ev.preventDefault();
      var said = box && box.querySelector(".pp-vstatus");
      (function cookie() {
        fetch(a.dataset.go + "&mode=cookie", { cache: "no-store", credentials: "same-origin" })
          .then(function (r) { return r.json(); })
          .then(function (s) {
            if (s.state !== "ready") {
              if (said) { said.textContent = "Arrancando la versión desde cero…"; said.className = "pp-vstatus warn"; }
              setTimeout(cookie, 3000);
              return;
            }
            if (said) { said.textContent = s.login ? "Sesión iniciada como " + s.account + ": abriendo en tu computador…" :
                                                   "Abriendo en tu computador…"; said.className = "pp-vstatus ok"; }
            window.location.href = a.href;
          })
          .catch(function () { setTimeout(cookie, 3000); });
      })();
      return;
    }
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
    if (a && a.dataset.go) return;                      // through the panel: it starts the version and signs in (D-205)
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

  // «Rechazar…» with images (D-258): the plain file input works without this; here a pasted or dropped image on the note
  // joins it, a preview shows what goes, and the server's limits are checked before sending. The server checks again
  // (by the bytes) and records nothing on a refusal. Delegated: the panel is swapped in live.
  var KINDS = ["image/png", "image/jpeg", "image/webp", "image/gif"];
  function filesOf(form) { return form && form.querySelector('input[type="file"][name="images"]'); }
  function problem(input) {
    var files = Array.prototype.slice.call(input.files || []), total = 0;
    var most = +input.dataset.maxImages || 8, each = (+input.dataset.maxMb || 10) * 1048576,
        all = (+input.dataset.maxTotalMb || 30) * 1048576;
    if (files.length > most) return "Adjuntaste " + files.length + " imágenes; el máximo es " + most + " por rechazo.";
    for (var i = 0; i < files.length; i++) {
      if (files[i].type && KINDS.indexOf(files[i].type) < 0) return "«" + files[i].name + "» no es una imagen PNG, JPEG, WebP ni GIF.";
      if (files[i].size > each) return "«" + files[i].name + "» pesa más de " + input.dataset.maxMb + " MB.";
      total += files[i].size;
    }
    return total > all ? "Las imágenes pesan más de " + input.dataset.maxTotalMb + " MB en total." : "";
  }
  function preview(input) {
    var form = input.form, list = form.querySelector(".pp-vpreview"), error = form.querySelector(".pp-vfiles-error");
    if (list) {
      list.textContent = "";
      Array.prototype.forEach.call(input.files || [], function (file, i) {
        var item = document.createElement("li");
        if (KINDS.indexOf(file.type) >= 0 && window.FileReader) {   // a data: URL: the panel's CSP allows no blob:
          var img = document.createElement("img");
          img.alt = "Imagen " + (i + 1) + ": " + file.name;
          var reader = new FileReader();
          reader.onload = function () { img.src = reader.result; };
          reader.readAsDataURL(file);
          item.appendChild(img);
        } else {
          item.textContent = file.name;
        }
        list.appendChild(item);
      });
    }
    var said = problem(input);
    if (error) { error.textContent = said; error.hidden = !said; }
    return said;
  }
  function add(input, files) {
    var images = Array.prototype.filter.call(files || [], function (f) { return KINDS.indexOf(f.type) >= 0; });
    if (!images.length || !window.DataTransfer) return false;
    var both = new DataTransfer();
    Array.prototype.forEach.call(input.files || [], function (f) { both.items.add(f); });
    images.forEach(function (f, i) {
      var name = f.name && f.name !== "image.png" ? f.name : "pegada-" + (Date.now() + i) + "." + f.type.split("/")[1];
      both.items.add(new File([f], name, { type: f.type }));
    });
    input.files = both.files;
    preview(input);
    return true;
  }
  document.addEventListener("change", function (ev) {
    if (ev.target && ev.target.matches && ev.target.matches('input[type="file"][name="images"]')) preview(ev.target);
  });
  document.addEventListener("paste", function (ev) {
    var area = ev.target && ev.target.closest ? ev.target.closest("form.pp-vform.note textarea") : null;
    var input = area && filesOf(area.form);
    if (input && ev.clipboardData && add(input, ev.clipboardData.files)) ev.preventDefault();   // text pastes as text
  });
  ["dragover", "dragleave", "drop"].forEach(function (type) {
    document.addEventListener(type, function (ev) {
      var area = ev.target && ev.target.closest ? ev.target.closest("form.pp-vform.note textarea") : null;
      if (!area || !filesOf(area.form)) return;
      var files = ev.dataTransfer && Array.prototype.indexOf.call(ev.dataTransfer.types || [], "Files") >= 0;
      if (!files) return;
      ev.preventDefault();
      area.classList.toggle("pp-vdrop", type === "dragover");
      if (type === "drop") add(filesOf(area.form), ev.dataTransfer.files);
    });
  });
  document.addEventListener("submit", function (ev) {
    var input = filesOf(ev.target);
    if (input && preview(input)) ev.preventDefault();             // the message is shown next to the input
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
    fetch((run.dataset.poll || location.pathname) + "?format=json&sp=" + encodeURIComponent(sp), { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (s) {
        show(s);
        if (s.state === "ready" && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\//.test(s.url || "")) {
          var origin = s.url.replace(/^(https?:\/\/[^\/]+).*$/, "$1");
          var page = /^\/[A-Za-z0-9_\-.\/\[\]]*$/.test(run.dataset.path || "") ? run.dataset.path : "/";
          if (/^\/p\//.test(run.dataset.next || "")) { location.replace(run.dataset.next); return; }  // sign in, then land (D-205)
          location.replace(origin + page);
          return;
        }
        if (s.state === "preparing") setTimeout(tick, 2000);
      })
      .catch(function () { setTimeout(tick, 3000); });
  }
  tick();
})();
