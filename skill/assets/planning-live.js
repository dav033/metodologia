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
  // «nuevo» since the owner's last visit, per subplan, remembered by this browser only (bt_page_subplan_control).
  var SEEN = 'bt-sc-seen:' + location.pathname, baseline = {};
  function seen() { try { return JSON.parse(localStorage.getItem(SEEN) || 'null'); } catch (err) { return null; } }
  function remember(map) { try { localStorage.setItem(SEEN, JSON.stringify(map)); } catch (err) { /* private mode */ } }
  function marks() {
    var map = seen(), first = map === null, block = root.querySelector('.sc[data-sc-sp]');
    map = map || {};
    if (first) {          // first visit ever: what exists now is not news
      root.querySelectorAll('[data-sc-latest]').forEach(function (n) { if (n.dataset.scLatest) map[n.dataset.scSp] = n.dataset.scLatest; });
    }
    var open = block ? block.dataset.scSp : '';
    if (block) {
      if (!(open in baseline)) baseline[open] = map[open] || '';
      var since = baseline[open], count = 0;
      block.querySelectorAll('.sc-news li[data-at]').forEach(function (li) {
        var fresh = !!since && li.dataset.at > since;
        li.classList.toggle('is-new', fresh);
        if (fresh) count++;
      });
      var badge = block.querySelector('[data-sc-newcount]');
      if (badge) { badge.hidden = !count; badge.textContent = count === 1 ? '1 nueva' : count + ' nuevas'; }
      var latest = block.dataset.scLatest || '';
      if (latest && latest > (map[open] || '')) map[open] = latest;
    }
    remember(map);
    root.querySelectorAll('.sc-fresh[data-sc-sp]').forEach(function (n) {
      var latest = n.dataset.scLatest || '';
      n.hidden = n.dataset.scSp === open || !latest || latest <= (map[n.dataset.scSp] || '');
    });
  }
  function apply(html, force) {
    var t = document.createElement('template');
    t.innerHTML = html;
    var fresh = blocks(t.content), old = blocks(root);
    var keys = function (list) { return list.map(function (n) { return n.dataset.k; }).join('|'); };
    if (force || keys(fresh) !== keys(old)) {
      if (!force && old.some(busy)) return;
      root.replaceChildren(t.content);
      render(root);
      marks();
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
      // live status blocks (the agent strip, its text box, the Designer's progress card, the subplan's control block)
      // change every few seconds: no flash
      if (['bar', 'agent', 'agent-say'].indexOf(n.dataset.k) < 0 && n.dataset.k.indexOf('control-') !== 0 &&
          !n.querySelector('.pp-dprog')) flash(n);
    });
    marks();
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
    var direction = ev.target.closest('[data-direction-show]');
    if (direction) {
      var chooser = direction.closest('.pp-directions');
      chooser.querySelectorAll('[data-direction-card]').forEach(function (card) {
        card.hidden = direction.dataset.directionShow !== 'all' && card.dataset.directionCard !== direction.dataset.directionShow;
      });
      chooser.querySelectorAll('[data-direction-show]').forEach(function (button) {
        button.setAttribute('aria-pressed', button === direction ? 'true' : 'false');
      });
      return;
    }
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
  // the model popover of a task's complexity closes on an outside click or Escape
  function closePops(except) {
    Array.prototype.forEach.call(document.querySelectorAll('.pp-cxpop[open]'), function (d) { if (d !== except) d.removeAttribute('open'); });
  }
  document.addEventListener('click', function (ev) { closePops(ev.target.closest && ev.target.closest('.pp-cxpop')); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') closePops(null); });
  window.addEventListener('popstate', function () { go(location.href, false); });
  render(root);
  marks();
  setInterval(function () { if (!document.hidden) load(false); }, 4000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) load(false); });
})();
