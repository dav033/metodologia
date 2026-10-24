(function () {
  var live = document.getElementById('live');
  if (!live) return;
  var sel = '[data-k]';
  function leaves(n) { return Array.prototype.slice.call(n.querySelectorAll(sel)); }
  function sigOf(n) {
    var c = n.cloneNode(true);
    Array.prototype.forEach.call(c.querySelectorAll('[data-v]'), function (x) { x.textContent = ''; });
    return c.outerHTML;
  }
  function mark(n) { n._full = n.outerHTML; n._sig = sigOf(n); }
  leaves(live).forEach(mark);
  function openIdx(n) { return Array.prototype.map.call(n.querySelectorAll('details'), function (d) { return d.open; }); }
  function apply(html) {
    var t = document.createElement('template'); t.innerHTML = html;
    var nw = leaves(t.content), old = leaves(live);
    var same = nw.length === old.length && nw.every(function (n, i) { return n.dataset.k === old[i].dataset.k; });
    if (!same) { live.replaceChildren(t.content); leaves(live).forEach(mark); return; }
    nw.forEach(function (n, i) {
      var o = old[i], full = n.outerHTML, sig = sigOf(n); if (o._full === full) return;
      if (o._sig === sig) {
        var ov = o.querySelectorAll('[data-v]'), nv = n.querySelectorAll('[data-v]');
        for (var j = 0; j < ov.length && j < nv.length; j++) if (ov[j].innerHTML !== nv[j].innerHTML) ov[j].innerHTML = nv[j].innerHTML;
        o._full = full; return;
      }
      var opened = openIdx(o); o.replaceWith(n); mark(n);
      Array.prototype.forEach.call(n.querySelectorAll('details'), function (d, j) { if (opened[j]) d.open = true; });
      n.classList.add('flash-new'); setTimeout(function () { n.classList.remove('flash-new'); }, 1700);
    });
  }
  function reveal() {
    var id = decodeURIComponent(location.hash.slice(1)), n = id && document.getElementById(id); if (!n) return;
    for (var p = n.parentElement; p; p = p.parentElement) if (p.tagName === 'DETAILS') p.open = true;
    if (n.classList.contains('task')) Array.prototype.forEach.call(n.querySelectorAll('details.tdet'), function (d) { d.open = true; });
    n.scrollIntoView({ block: 'center' }); n.classList.add('flash-new');
    setTimeout(function () { n.classList.remove('flash-new'); }, 1700);
  }
  reveal(); window.addEventListener('hashchange', reveal);
  var dot = document.getElementById('live-dot');
  function state(t) { if (dot) dot.textContent = t; }
  function refresh() { fetch(live.dataset.api, { cache: 'no-store' }).then(function (r) { return r.json(); })
    .then(function (d) { if (d.html) apply(d.html); }).catch(function () {}); }
  var poll = null;
  function startPoll() { if (!poll) { poll = setInterval(refresh, 3000); state('● sondeo cada 3 s'); } }
  function stopPoll() { if (poll) { clearInterval(poll); poll = null; } }
  if (!/[?&]live=0(&|$)/.test(location.search) && window.EventSource) {
    var es = new EventSource(live.dataset.events);
    es.onopen = function () { stopPoll(); state('● en vivo'); refresh(); };
    es.onerror = function () { startPoll(); };
    es.addEventListener(live.dataset.event, function (ev) { try { apply(JSON.parse(ev.data).html); } catch (x) {} });
  } else if (!/[?&]live=0(&|$)/.test(location.search)) startPoll();
})();
