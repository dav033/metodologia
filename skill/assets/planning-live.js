// Plan tab while planning (bt_page_planning). A live region: poll the fragment and swap only the blocks ([data-k])
// whose digest (data-h) changed, so the conversation's edits, the Designer's drafts and the translation appear
// without a reload. A block holding a comment being typed, or the open approval dialog, waits. Links marked
// [data-nav] (subplans, tabs, language, versions) navigate in place; [data-width] resizes the mockup;
// [data-open]/[data-close] drive the dialog; [data-reply] starts a reply to a Designer question.
(function () {
  var root = document.getElementById('planning');
  if (!root || !window.fetch) return;
  var width = '';
  function api(href) {
    var u = new URL(href, location.href);
    return root.dataset.api + u.search;
  }
  var current = api(location.href);
  function blocks(n) { return Array.prototype.slice.call(n.querySelectorAll('[data-k]')); }
  function busy(n) {
    if (n.matches('dialog[open]') || n.querySelector('dialog[open]')) return true;
    return Array.prototype.some.call(n.querySelectorAll('textarea'), function (t) {
      return t === document.activeElement || t.value.trim() !== '';
    });
  }
  function opened(n) {
    return Array.prototype.map.call(n.querySelectorAll('details'), function (d) { return d.open; });
  }
  function flash(n) {
    n.classList.add('flash-new');
    setTimeout(function () { n.classList.remove('flash-new'); }, 1700);
  }
  function setWidth(scope) {
    Array.prototype.forEach.call(scope.querySelectorAll('.pp-frame iframe'), function (f) {
      f.style.width = width ? width + 'px' : '';
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-width]'), function (b) {
      var on = b.dataset.width === width;
      b.classList.toggle('on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }
  function render(n) { if (window.renderMarkdown) window.renderMarkdown(n); setWidth(n); }
  function apply(html, force) {
    var t = document.createElement('template');
    t.innerHTML = html;
    var fresh = blocks(t.content), old = blocks(root);
    var keys = function (list) { return list.map(function (n) { return n.dataset.k; }).join('|'); };
    if (force || keys(fresh) !== keys(old)) {
      if (!force && old.some(busy)) return;
      root.replaceChildren(t.content);
      render(root);
      return;
    }
    fresh.forEach(function (n, i) {
      var o = old[i];
      if (o.dataset.h === n.dataset.h) { o.classList.remove('pl-waiting'); return; }
      if (busy(o)) { o.classList.add('pl-waiting'); return; }
      var keep = opened(o);
      o.replaceWith(n);
      Array.prototype.forEach.call(n.querySelectorAll('details'), function (d, j) { if (keep[j]) d.open = true; });
      render(n);
      if (n.dataset.k !== 'bar') flash(n);
    });
  }
  function load(force) {
    var asked = current;
    return fetch(asked, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        if (asked !== current || !d.html) return;
        apply(d.html, force);
        var live = document.getElementById('pl-live');
        if (live) live.classList.remove('off');
      })
      .catch(function () {
        var live = document.getElementById('pl-live');
        if (live) { live.classList.add('off'); live.textContent = 'sin conexión'; }
      });
  }
  function go(href, push) {
    current = api(href);
    if (push) history.pushState(null, '', href);
    load(true).then(function () {
      var top = root.getBoundingClientRect().top;
      if (top < 0) root.scrollIntoView({ block: 'start' });
    });
  }
  root.addEventListener('click', function (ev) {
    var nav = ev.target.closest('a[data-nav]');
    if (nav && root.contains(nav) && !ev.ctrlKey && !ev.metaKey && !ev.shiftKey && ev.button === 0) {
      ev.preventDefault();
      var inDialog = nav.closest('dialog');
      if (inDialog) inDialog.close();
      go(nav.href, true);
      return;
    }
    var w = ev.target.closest('[data-width]');
    if (w) { width = w.dataset.width; setWidth(root); return; }
    var open = ev.target.closest('[data-open]');
    if (open) {
      var dlg = document.getElementById(open.dataset.open);
      if (dlg && dlg.showModal) dlg.showModal();
      return;
    }
    var close = ev.target.closest('[data-close]');
    if (close) { var d = close.closest('dialog'); if (d) d.close(); return; }
    var reply = ev.target.closest('[data-reply]');
    if (reply) {
      var scope = reply.closest('.pp-detail, .pp-review') || root;
      var box = scope.querySelector('.pp-composer textarea');
      if (box) {
        box.value = 'Sobre «' + reply.dataset.reply + '»: ';
        box.focus();
        box.setSelectionRange(box.value.length, box.value.length);
      }
    }
  });
  window.addEventListener('popstate', function () { go(location.href, false); });
  render(root);
  setInterval(function () { if (!document.hidden) load(false); }, 4000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) load(false); });
})();
