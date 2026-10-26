// Plan tab while planning: poll the fragment and swap only the blocks ([data-k]) whose HTML changed, so the
// conversation's edits to the plan, the Designer's drafts and the translation appear without a reload. A block
// holding a comment being typed (focused or non-empty textarea) waits; open <details> stay open.
(function () {
  var root = document.getElementById('planning');
  if (!root || !window.fetch) return;
  var live = function () { return document.getElementById('pl-live'); };
  function blocks(n) { return Array.prototype.slice.call(n.querySelectorAll('[data-k]')); }
  function busy(n) {
    return Array.prototype.some.call(n.querySelectorAll('textarea'), function (t) {
      return t === document.activeElement || t.value.trim() !== '';
    });
  }
  function opened(n) {
    var keep = {};
    Array.prototype.forEach.call(n.querySelectorAll('details'), function (d, i) { keep[i] = d.open; });
    return keep;
  }
  function flash(n) {
    n.classList.add('flash-new');
    setTimeout(function () { n.classList.remove('flash-new'); }, 1700);
  }
  function apply(html) {
    var t = document.createElement('template');
    t.innerHTML = html;
    var old = {}, seen = {}, prev = null;
    blocks(root).forEach(function (n) { old[n.dataset.k] = n; });
    blocks(t.content).forEach(function (n) {
      var k = n.dataset.k, o = old[k];
      seen[k] = true;
      if (o && o.dataset.h === n.dataset.h) { o.classList.remove('pl-waiting'); prev = o; return; }
      if (o && busy(o)) { o.classList.add('pl-waiting'); prev = o; return; }
      if (o) {
        var keep = opened(o);
        o.replaceWith(n);
        Array.prototype.forEach.call(n.querySelectorAll('details'), function (d, i) { if (keep[i]) d.open = true; });
      } else if (prev) prev.after(n); else root.prepend(n);
      if (window.renderMarkdown) window.renderMarkdown(n);
      if (k !== 'bar') flash(n);
      prev = n;
    });
    Object.keys(old).forEach(function (k) { if (!seen[k] && !busy(old[k])) old[k].remove(); });
  }
  function tick() {
    if (document.hidden) return;
    fetch(root.dataset.api, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { if (d.html) apply(d.html); var l = live(); if (l) l.classList.remove('off'); })
      .catch(function () { var l = live(); if (l) { l.classList.add('off'); l.textContent = '● sin conexión'; } });
  }
  setInterval(tick, 4000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) tick(); });
})();
