/* david-ui stand-in behaviour for static mockups (optional, no network). Inlined by inline.py next to the kit CSS.
   - select#theme / select#motion (or ?theme= / ?motion=) set <html data-theme|data-motion>.
   - [data-kit-open="id"] opens a layer (dialog overlay, sheet, menu, popover, listbox); [data-kit-close] closes the nearest
     one; Escape and a click outside close the top one; focus moves into the layer and back to its opener.
   - [role=tablist] switches tabs (click, arrows); [data-kit-toast="template-id"] shows a toast for 5 s;
     .combobox filters its .listbox-item by the input; [data-kit-sidebar] toggles the mobile sidebar of .app.
   - Mockup switcher: an element with data-show-view="login reset", data-show-state="error", data-hide-state="loading" or
     data-show-scene="confirm" is shown only while select#view / #state / #scene hold one of those values.
   - A parent page may post {kit: 'set', theme, motion}; the kit applies it and syncs the selects. */
(function () {
  if (window.__kit) return;
  window.__kit = true;
  var root = document.documentElement, stack = [];
  var FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function apply(kind, value) {
    if (!value) return;
    root.setAttribute('data-' + kind, value);
    var sel = document.getElementById(kind);
    if (sel && sel.tagName === 'SELECT' && sel.value !== value && [].some.call(sel.options, function (o) { return o.value === value; })) {
      sel.value = value;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }
  function bindSelect(kind) {
    var sel = document.getElementById(kind);
    if (!sel || sel.tagName !== 'SELECT') return;
    sel.addEventListener('change', function () { root.setAttribute('data-' + kind, sel.value); });
    if (!root.getAttribute('data-' + kind) || root.getAttribute('data-' + kind) !== sel.value) root.setAttribute('data-' + kind, sel.value);
  }

  function open(layer, opener) {
    if (!layer) return;
    layer.hidden = false;
    layer.setAttribute('data-state', 'open');
    if (opener) opener.setAttribute('aria-expanded', 'true');
    stack.push({ layer: layer, opener: opener });
    var target = layer.querySelector('[autofocus]') || layer.querySelector(FOCUSABLE);
    if (target && layer.matches('.dialog-overlay, .sheet-overlay, .sheet-content, [role=dialog], [role=alertdialog]')) target.focus();
  }
  function close(layer) {
    for (var i = stack.length - 1; i >= 0; i--) {
      if (stack[i].layer !== layer) continue;
      var item = stack.splice(i, 1)[0];
      layer.hidden = true;
      layer.setAttribute('data-state', 'closed');
      var sheet = layer.id && document.querySelector('[data-kit-pair="' + layer.id + '"]');
      if (sheet) { sheet.hidden = true; }
      if (item.opener) { item.opener.setAttribute('aria-expanded', 'false'); item.opener.focus(); }
      return;
    }
    layer.hidden = true;
  }
  function layerOf(el) { return el.closest('[data-kit-layer]'); }

  document.addEventListener('click', function (ev) {
    var t = ev.target.closest('[data-kit-open], [data-kit-close], [data-kit-toast], [data-kit-sidebar]');
    if (t && t.hasAttribute('data-kit-open')) {
      var layer = document.getElementById(t.getAttribute('data-kit-open'));
      if (layer && !layer.hidden) close(layer); else open(layer, t);
      var pair = layer && document.querySelector('[data-kit-pair="' + layer.id + '"]');
      if (pair) pair.hidden = layer.hidden;
      ev.preventDefault();
      return;
    }
    if (t && t.hasAttribute('data-kit-close')) { var l = layerOf(t); if (l) close(l); ev.preventDefault(); return; }
    if (t && t.hasAttribute('data-kit-toast')) { toast(t.getAttribute('data-kit-toast')); return; }
    if (t && t.hasAttribute('data-kit-sidebar')) {
      var app = document.querySelector('.app');
      if (app) app.setAttribute('data-sidebar', app.getAttribute('data-sidebar') === 'open' ? 'closed' : 'open');
      return;
    }
    var app2 = document.querySelector('.app[data-sidebar="open"]');
    if (app2 && !ev.target.closest('.sidebar')) app2.setAttribute('data-sidebar', 'closed');
    if (!stack.length) return;
    var top = stack[stack.length - 1].layer;
    if (ev.target === top && top.matches('.dialog-overlay, .sheet-overlay')) { close(top); return; }
    if (!top.contains(ev.target) && !top.matches('.dialog-overlay, .sheet-overlay, .sheet-content')) close(top);
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && stack.length) { close(stack[stack.length - 1].layer); return; }
    var tab = ev.target.closest && ev.target.closest('[role=tab]');
    if (tab && (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft')) {
      var tabs = [].slice.call(tab.closest('[role=tablist]').querySelectorAll('[role=tab]:not([disabled])'));
      var next = tabs[(tabs.indexOf(tab) + (ev.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      select(next); next.focus(); ev.preventDefault();
    }
  });

  function select(tab) {
    var list = tab.closest('[role=tablist]');
    [].forEach.call(list.querySelectorAll('[role=tab]'), function (t) {
      var on = t === tab;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      var panel = t.getAttribute('aria-controls') && document.getElementById(t.getAttribute('aria-controls'));
      if (panel) panel.hidden = !on;
    });
  }
  document.addEventListener('click', function (ev) {
    var tab = ev.target.closest('[role=tab]');
    if (tab && !tab.disabled) select(tab);
  });

  function toast(templateId) {
    var tpl = document.getElementById(templateId);
    if (!tpl) return;
    var host = document.querySelector('.toaster');
    if (!host) { host = document.createElement('section'); host.className = 'toaster'; host.setAttribute('aria-label', 'Notificaciones'); document.body.appendChild(host); }
    host.setAttribute('aria-live', 'polite');
    var node = (tpl.content ? tpl.content.firstElementChild : tpl).cloneNode(true);
    node.hidden = false;
    host.appendChild(node);
    while (host.children.length > 3) host.removeChild(host.firstElementChild);
    var close = node.querySelector('[data-kit-dismiss]');
    if (close) close.addEventListener('click', function () { node.remove(); });
    setTimeout(function () { node.remove(); }, 5000);
  }

  document.addEventListener('input', function (ev) {
    var box = ev.target.closest && ev.target.closest('.combobox');
    if (!box || ev.target.tagName !== 'INPUT') return;
    var q = ev.target.value.trim().toLowerCase(), list = box.querySelector('.listbox'), shown = 0;
    if (!list) return;
    list.hidden = false;
    ev.target.setAttribute('aria-expanded', 'true');
    [].forEach.call(list.querySelectorAll('.listbox-item'), function (item) {
      var hit = !q || item.textContent.toLowerCase().indexOf(q) >= 0;
      item.hidden = !hit; if (hit) shown++;
    });
    var empty = list.querySelector('.listbox-empty');
    if (empty) empty.hidden = shown > 0;
  });

  window.addEventListener('message', function (ev) {
    var d = ev.data;
    if (!d || d.kit !== 'set' || ev.source !== window.parent) return;
    apply('theme', d.theme); apply('motion', d.motion);
  });

  // mockup switcher: [data-show-view|data-show-state|data-hide-state|data-show-scene]="a b" follow the planning selects
  function val(id) { var s = document.getElementById(id); return s && s.tagName === 'SELECT' ? s.value : ''; }
  function inList(list, v) { return (' ' + list + ' ').indexOf(' ' + v + ' ') >= 0; }
  function switcher() {
    var v = val('view'), s = val('state'), c = val('scene');
    root.setAttribute('data-view', v); root.setAttribute('data-mock-state', s); root.setAttribute('data-scene', c);
    [].forEach.call(document.querySelectorAll('[data-show-view], [data-show-state], [data-hide-state], [data-show-scene]'), function (el) {
      var a = el.getAttribute.bind(el);
      el.hidden = !((!el.hasAttribute('data-show-view') || inList(a('data-show-view'), v)) &&
        (!el.hasAttribute('data-show-state') || inList(a('data-show-state'), s)) &&
        (!el.hasAttribute('data-hide-state') || !inList(a('data-hide-state'), s)) &&
        (!el.hasAttribute('data-show-scene') || (c && inList(a('data-show-scene'), c))));
    });
  }
  document.addEventListener('change', function (ev) {
    if (ev.target && /^(view|state|scene)$/.test(ev.target.id)) switcher();
  });

  function start() {
    bindSelect('theme'); bindSelect('motion');
    switcher();
    var q = new URLSearchParams(location.search);
    apply('theme', q.get('theme')); apply('motion', q.get('motion'));
    [].forEach.call(document.querySelectorAll('[role=tablist]'), function (list) {
      var on = list.querySelector('[role=tab][aria-selected="true"]') || list.querySelector('[role=tab]');
      if (on) select(on);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
