// /components and /components/kit: theme, motion, width and reduced-motion switches for the sandboxed previews, search and
// filters (source, category, priority, status), copy buttons and frame heights. Frames have an opaque origin, so
// everything crosses by postMessage and every message is matched to its frame window.
(function () {
  var root = document.getElementById('cg');
  if (!root) return;
  var frames = [].slice.call(root.querySelectorAll('.cg-frame'));
  var state = { theme: 'light', motion: 'natural', width: 'full', reduced: false };
  function stored(k) { try { return localStorage.getItem('cg-' + k); } catch (e) { return null; } }
  function store(k, v) { try { localStorage.setItem('cg-' + k, v); } catch (e) { /* private window */ } }
  var page = document.documentElement.dataset.theme ||
    (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  state.theme = stored('theme') || page;
  state.motion = stored('motion') || 'natural';
  state.width = stored('width') || 'full';
  state.reduced = stored('reduced') === '1' || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);

  function tell(frame) {
    if (frame.contentWindow) frame.contentWindow.postMessage({ kit: 'set', theme: state.theme, motion: state.motion, reduced: state.reduced }, '*');
  }
  function src(frame) {
    var base = frame.getAttribute('src').split('?')[0];
    if (frame.classList.contains('cg-frame-ref')) return /\/kitref\//.test(base) ? base + '?theme=' + state.theme : base + (state.reduced ? '?still=1' : '');
    return base + '?theme=' + state.theme + '&motion=' + state.motion + (state.reduced ? '&rm=1' : '');
  }
  function apply(kind) {
    [].forEach.call(root.querySelectorAll('[data-set="' + kind + '"]'), function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-value') === state[kind]));
    });
    if (kind === 'width') {
      [].forEach.call(root.querySelectorAll('.cg-stage'), function (s) { s.setAttribute('data-width', state.width); });
      fitRefs();
    } else {
      frames.forEach(tell);
    }
  }
  // reference screens: render at the device width (desktop 1280) and scale the frame down to the stage
  var DEVICE = { '390': 390, '768': 768, full: 1280 };
  function fitRefs() {
    [].forEach.call(root.querySelectorAll('.cg-stage-ref'), function (stage) {
      var f = stage.querySelector('.cg-frame'), w = DEVICE[state.width] || 1280, avail = stage.clientWidth || w;
      var k = Math.min(1, avail / w), h = 820;
      f.style.width = w + 'px'; f.style.height = h + 'px'; f.style.transform = k < 1 ? 'scale(' + k + ')' : '';
      f.style.marginLeft = k < 1 ? '0' : Math.max(0, (avail - w) / 2) + 'px';
      stage.style.height = Math.ceil(h * k) + 'px';
    });
  }
  window.addEventListener('resize', fitRefs);

  frames.forEach(function (f) {
    f.setAttribute('src', src(f));                 // first load already in the chosen settings (lazy frames load later)
    f.addEventListener('load', function () { tell(f); });
  });
  ['theme', 'motion', 'width'].forEach(apply);
  var rmBtn = root.querySelector('[data-toggle="reduced"]');
  if (rmBtn) rmBtn.setAttribute('aria-pressed', String(state.reduced));

  root.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-set]');
    if (b) {
      var kind = b.getAttribute('data-set');
      state[kind] = b.getAttribute('data-value');
      store(kind, state[kind]);
      apply(kind);
      return;
    }
    var t = ev.target.closest('[data-toggle="reduced"]');
    if (t) {
      state.reduced = !state.reduced;
      store('reduced', state.reduced ? '1' : '0');
      t.setAttribute('aria-pressed', String(state.reduced));
      frames.forEach(function (f) { if (f.classList.contains('cg-frame-ref')) f.setAttribute('src', src(f)); else tell(f); });
      return;
    }
    var chip = ev.target.closest('[data-filter="source"]');
    if (chip) {
      filters.source = chip.getAttribute('data-value');
      [].forEach.call(root.querySelectorAll('[data-filter="source"]'), function (c) { c.setAttribute('aria-pressed', String(c === chip)); });
      filter();
      return;
    }
    var c = ev.target.closest('.cg-copy');
    if (c) copy(c);
  });
  root.addEventListener('change', function (ev) {
    var s = ev.target.closest('select[data-filter]');
    if (s) { filters[s.getAttribute('data-filter')] = s.value; filter(); }
  });

  window.addEventListener('message', function (ev) {
    var d = ev.data;
    if (!d || d.kit !== 'height' || typeof d.h !== 'number') return;
    for (var i = 0; i < frames.length; i++) {
      var f = frames[i];
      if (f.contentWindow === ev.source && !f.classList.contains('cg-frame-ref')) {
        f.style.height = Math.max(120, Math.min(4000, Math.ceil(d.h))) + 'px';
        return;
      }
    }
  });

  function copy(btn) {
    var code = document.getElementById(btn.getAttribute('data-copy'));
    if (!code) return;
    var text = code.textContent;
    function done() {
      btn.textContent = 'Copiado';
      btn.setAttribute('data-done', '');
      setTimeout(function () { btn.textContent = 'Copiar'; btn.removeAttribute('data-done'); }, 1600);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { select(code); });
    } else select(code);
  }
  function select(node) {
    var r = document.createRange(); r.selectNodeContents(node);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
  }

  var input = document.getElementById('cg-q');
  var none = document.getElementById('cg-none');
  var filters = { source: '', category: '', priority: '', status: '' };
  function matches(comp, terms) {
    var hay = comp.getAttribute('data-search') || '';
    if (!terms.every(function (t) { return hay.indexOf(t) >= 0; })) return false;
    if (filters.source && (' ' + (comp.getAttribute('data-source') || '') + ' ').indexOf(' ' + filters.source + ' ') < 0) return false;
    if (filters.category && comp.getAttribute('data-category') !== filters.category) return false;
    if (filters.priority && comp.getAttribute('data-priority') !== filters.priority) return false;
    if (filters.status && comp.getAttribute('data-status') !== filters.status) return false;
    return true;
  }
  function filter() {
    var terms = (input ? input.value : '').trim().toLowerCase().split(/\s+/).filter(Boolean), shown = 0;
    var active = terms.length || filters.source || filters.category || filters.priority || filters.status;
    [].forEach.call(root.querySelectorAll('.cg-cat[data-cat]'), function (cat) {
      var n = 0;
      [].forEach.call(cat.querySelectorAll('.cg-comp'), function (comp) {
        var hit = matches(comp, terms);
        comp.hidden = !hit; if (hit) n++;
        var link = root.querySelector('[data-comp-link="' + comp.id.slice(2) + '"]');
        if (link) link.parentNode.hidden = !hit;
      });
      cat.hidden = n === 0; shown += n;
      var catLink = root.querySelector('[data-cat-link="' + cat.getAttribute('data-cat') + '"]');
      if (catLink) { catLink.parentNode.hidden = n === 0; catLink.querySelector('.cg-count').textContent = n; }
    });
    none.hidden = shown > 0;
    ['referencias', 'brechas'].forEach(function (id) { var el = document.getElementById(id); if (el) el.hidden = !!active; });
  }
  if (input) input.addEventListener('input', filter);

  if ('IntersectionObserver' in window) {                 // index: mark the component in view
    var links = {};
    [].forEach.call(root.querySelectorAll('[data-comp-link]'), function (a) { links[a.getAttribute('data-comp-link')] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = links[en.target.id.slice(2)];
        if (a && en.isIntersecting) {
          [].forEach.call(root.querySelectorAll('.cg-index a[aria-current]'), function (x) { x.removeAttribute('aria-current'); });
          a.setAttribute('aria-current', 'true');
        }
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    [].forEach.call(root.querySelectorAll('.cg-comp'), function (c) { io.observe(c); });
  }
})();
