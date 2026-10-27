// Injected by the server into every Designer mockup (bt_mockup_bridge): lets the plan page list the mockup's views, states and
// dialogs and drive them from outside. The mockup runs sandboxed (no shared origin), so everything goes through postMessage.
(function () {
  if (window.__ppBridge) return;
  window.__ppBridge = true;
  var KEYS = { view: ['view', 'vista', 'screen'], state: ['state', 'estado'], scene: ['scene', 'dialog', 'dialogo', 'dialog-select'], theme: ['theme', 'tema'] };
  var LABEL = { view: /vista|view|pantalla|screen/i, state: /estado|state/i, scene: /di[aá]logo|dialog|escena|scene/i, theme: /tema|theme/i };
  function labelOf(sel) {
    var l = (sel.id && document.querySelector('label[for="' + sel.id + '"]')) || sel.closest('label') || sel.previousElementSibling;
    return (l && l.textContent || sel.getAttribute('aria-label') || '').trim();
  }
  function find(kind) {
    var i, el;
    for (i = 0; i < KEYS[kind].length; i++) { el = document.getElementById(KEYS[kind][i]); if (el && el.tagName === 'SELECT') return el; }
    var all = [].slice.call(document.querySelectorAll('select'));
    for (i = 0; i < all.length; i++) if (LABEL[kind].test(labelOf(all[i]))) return all[i];
    return null;
  }
  var sel = {};
  function bind() { Object.keys(KEYS).forEach(function (k) { sel[k] = find(k); }); }
  function opts(s) { return s ? [].map.call(s.options, function (o) { return { value: o.value, label: o.textContent.trim(), disabled: o.disabled }; }) : []; }
  function report() {
    bind();
    var cur = {};
    Object.keys(sel).forEach(function (k) { cur[k] = sel[k] ? sel[k].value : ''; });
    try {
      parent.postMessage({ pp: 'mockup', views: opts(sel.view), states: opts(sel.state), scenes: opts(sel.scene), themes: opts(sel.theme), current: cur }, '*');
    } catch (e) { /* no parent to tell */ }
  }
  function set(kind, value) {
    var s = sel[kind] || find(kind);
    if (!s || s.value === value) return;
    s.value = value;
    s.dispatchEvent(new Event('input', { bubbles: true }));
    s.dispatchEvent(new Event('change', { bubbles: true }));
  }
  // the plan page shows its own view/state/dialog/theme controls: hide the mockup's duplicates (they keep working underneath)
  function hideOwn() {
    bind();
    Object.keys(sel).forEach(function (k) {
      var s = sel[k];
      if (!s) return;
      var w = s.closest('label') || s.parentElement;
      while (w && w.parentElement && w.parentElement !== document.body && w.parentElement.querySelectorAll('select').length === 1) w = w.parentElement;
      if (w && w.querySelectorAll('select').length === 1) w.style.display = 'none';
    });
  }
  window.addEventListener('message', function (ev) {
    var d = ev.data;
    if (!d || d.pp !== 'set' || ev.source !== parent) return;
    bind();
    if (d.hideOwn) { hideOwn(); return; }
    ['view', 'state', 'scene', 'theme'].forEach(function (k) { if (d[k] != null) { set(k, d[k]); bind(); } });
    setTimeout(report, 60);
  });
  document.addEventListener('change', function () { setTimeout(report, 60); }, true);
  // a thumbnail (?thumb=1) or the full-screen preview (?preview=1) shows the app, not the planning chrome around it: hide the
  // top-level block that holds the selectors (when it does not hold the app itself), the short notice after it and any footer
  // that talks about the mockup
  function crop() {
    var preview = /[?&]preview=1\b/.test(location.search);
    if (!preview && !/[?&]thumb=1\b/.test(location.search)) return;
    bind();
    var APP = 'main, #app, #root, [role=main]';
    var head = sel.view;
    while (head && head.parentElement && head.parentElement !== document.body) head = head.parentElement;
    if (head && head !== document.body && !head.querySelector(APP) && !head.matches(APP)) head.style.display = 'none';
    else {                                          // the selectors live inside the app: hide just their smallest container
      var el = sel.view;
      while (el && el !== document.body && el.querySelectorAll('select').length < 2) el = el.parentElement;
      if (el && el !== document.body && el !== document.documentElement && !el.querySelector(APP)) el.style.display = 'none';
    }
    [].forEach.call(document.body.children, function (n) {
      if (n.style.display === 'none' || n.matches(APP) || n.querySelector(APP)) return;
      var txt = (n.textContent || '').trim();
      if (txt.length && txt.length < 400 && /ficticio|mockup|maqueta|simulan|planificaci/i.test(txt) && !/^(SCRIPT|STYLE|DIALOG)$/.test(n.tagName)) n.style.display = 'none';
    });
  }
  function start() { bind(); crop(); report(); setTimeout(report, 400); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
