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
  function render(n) { if (window.renderMarkdown) window.renderMarkdown(n); setWidth(n); flowFrames(n); }
  // the subplan's Flow (bt_page_planning_run.flow_frame): as tall as the Flow itself, open or closed as left
  var FLOW_OPEN = 'bt-flowtop-open';
  function flowFrames(scope) {
    Array.prototype.forEach.call(scope.querySelectorAll('details.pp-flowtop'), function (d) {
      if (d.dataset.wired) return;
      d.dataset.wired = '1';
      try { if (localStorage.getItem(FLOW_OPEN) === '0') d.open = false; } catch (err) { /* private mode */ }
      d.addEventListener('toggle', function () {
        try { localStorage.setItem(FLOW_OPEN, d.open ? '1' : '0'); } catch (err) { /* private mode */ }
      });
      var frame = d.querySelector('iframe.pp-flowtop-frame');
      if (!frame) return;
      frame.addEventListener('load', function () {
        var doc = frame.contentDocument;
        if (!doc || !window.ResizeObserver) return;
        var fit = function () { frame.style.height = doc.documentElement.scrollHeight + 'px'; };
        new ResizeObserver(fit).observe(doc.body);
        fit();
      });
    });
  }
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
  // The subplan list scrolls on its own (planning.css). Swapping it for a fresh copy, navigating, or the reload after a
  // form (confirm, approve) would bring it back to the top: each keeps where the owner left it, and arriving on another
  // subplan brings that one into sight.
  var LIST = 'bt-pp-list:' + location.pathname;
  function listTop() { var l = root.querySelector('.pp-list'); return l ? l.scrollTop : null; }
  function openId() { var on = root.querySelector('.pp-list .pp-item.on .pp-id'); return on ? on.textContent : ''; }
  function keepList(top) { var l = root.querySelector('.pp-list'); if (l && top !== null && l.scrollTop !== top) l.scrollTop = top; }
  function showOpen() {
    var l = root.querySelector('.pp-list'), on = l && l.querySelector('.pp-item.on');
    if (!on) return;
    var r = on.getBoundingClientRect(), box = l.getBoundingClientRect();
    if (r.top < box.top || r.bottom > box.bottom) l.scrollTop += r.top - box.top - (box.height - r.height) / 2;
  }
  function apply(html, force) {
    var t = document.createElement('template');
    t.innerHTML = html;
    var fresh = blocks(t.content), old = blocks(root), top = listTop();
    var keys = function (list) { return list.map(function (n) { return n.dataset.k; }).join('|'); };
    if (force || keys(fresh) !== keys(old)) {
      if (!force && old.some(busy)) return;
      root.replaceChildren(t.content);
      keepList(top);
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
    keepList(top);
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
      showOpen();
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
    // a task's detail modal also closes on its backdrop (the click lands on the dialog itself, outside its content)
    if (ev.target.matches && ev.target.matches('dialog.pp-tdialog')) { ev.target.close(); return; }
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
  window.addEventListener('pagehide', function () {
    var top = listTop();
    try { if (top !== null) sessionStorage.setItem(LIST, JSON.stringify({ top: top, sp: openId() })); } catch (err) { /* private mode */ }
  });
  var left = null;
  try { left = JSON.parse(sessionStorage.getItem(LIST) || 'null'); } catch (err) { /* private mode */ }
  render(root);
  marks();
  function arrive() { if (left && left.sp === openId() && typeof left.top === 'number') keepList(left.top); else showOpen(); }
  arrive();
  window.addEventListener('load', arrive, { once: true });     // the list grows once its fonts arrive
  flowFrames(root);
  setInterval(function () { if (!document.hidden) load(false); }, 4000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) load(false); });
})();
