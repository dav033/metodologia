// Live layer shared by every page: the "Ahora" bar and the /now cards come from one SSE stream (/live?scope=global);
// durations and "hace N s" are ticked locally from their data-since / data-ago timestamps.
(function () {
  function fmt(s) {
    s = Math.max(0, Math.floor(s));
    if (s < 60) return s + ' s';
    if (s < 3600) return Math.floor(s / 60) + ' min ' + String(s % 60).padStart(2, '0') + ' s';
    return Math.floor(s / 3600) + ' h ' + String(Math.floor((s % 3600) / 60)).padStart(2, '0') + ' min';
  }
  function tick() {
    var now = Date.now();
    document.querySelectorAll('[data-since]').forEach(function (el) {
      var t = Date.parse(el.dataset.since);
      if (!isNaN(t)) el.textContent = fmt((now - t) / 1000);
    });
    document.querySelectorAll('[data-ago]').forEach(function (el) {
      var t = Date.parse(el.dataset.ago);
      if (!isNaN(t)) el.textContent = 'hace ' + fmt((now - t) / 1000);
    });
  }
  tick();
  setInterval(tick, 1000);
  // ?probe=1 (used by scripts/tools/visual_tour.py): report horizontal overflow on <html data-overflow> for --dump-dom
  if (/[?&]probe=1\b/.test(location.search)) {
    window.addEventListener('load', function () {
      setTimeout(function () {
        var root = document.documentElement;
        root.dataset.overflow = String(root.scrollWidth - root.clientWidth);
        root.dataset.viewport = window.innerWidth + 'x' + window.innerHeight;
        root.dataset.probe = 'done';
      }, 800);
    });
  }
  var bar = document.getElementById('nowbar');
  // ?live=0 keeps the page static (screenshots, tests): an open event stream keeps a headless browser from finishing
  if (!window.EventSource || !bar || /[?&]live=0\b/.test(location.search)) return;
  function onNow(ev) {
    var html;
    try { html = JSON.parse(ev.data).html || {}; } catch (e) { return; }
    bar.innerHTML = html.bar || '';
    bar.hidden = !html.bar;
    var cards = document.getElementById('now-cards');
    if (cards && typeof html.cards === 'string') cards.innerHTML = html.cards;
    var agents = document.getElementById('now-agents');
    if (agents && typeof html.agents === 'string') agents.innerHTML = html.agents;
    document.dispatchEvent(new CustomEvent('now-frame', { detail: JSON.parse(ev.data) }));
    tick();
  }
  window.liveNow = onNow;
  if (window.flowOwnsLive) return;     // /flow's stream already delivers the "now" frames (see flow.js)
  new EventSource('/live?scope=global').addEventListener('now', onNow);
})();
