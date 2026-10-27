// Plan tab: a workspace around a Designer mockup. The mockup (sandboxed iframe) reports its selectors through postMessage
// (assets/mockup-bridge.js, injected by the server); this script
//  - puts a compact toolbar above the frame: previous/next view, the view's name, a state menu (with status dots), a dialog menu
//    and a theme switch;
//  - on the review screen, a left rail with a live thumbnail of every view, to see them all at once and jump to one;
//  - remembers the choice per contract, so a live refresh of the block (which reloads the iframe) puts the mockup back.
(function () {
  var root = document.getElementById('planning');
  if (!root) return;
  var remembered = {};
  var restored = new WeakSet();
  var thumbSet = new WeakSet();
  var hidden = new WeakSet();
  var THUMB_W = 1200, THUMB_H = 800;

  function allFrames() { return document.querySelectorAll('.pp-frame iframe, .pp-full iframe.pp-full-frame'); }
  function mainFrame(win) {
    var all = allFrames();
    for (var i = 0; i < all.length; i++) if (all[i].contentWindow === win) return all[i];
    return null;
  }
  function thumbFrame(win) {
    var all = root.querySelectorAll('iframe.pp-thumb-frame');
    for (var i = 0; i < all.length; i++) if (all[i].contentWindow === win) return all[i];
    return null;
  }
  function key(iframe) {
    try { var u = new URL(iframe.src, location.href); return (u.searchParams.get('contract') || '') + '#' + (u.searchParams.get('rev') || '') + '#' + (u.searchParams.get('direction') || ''); }
    catch (e) { return iframe.src; }
  }
  function send(iframe, patch) {
    var msg = { pp: 'set' };
    Object.keys(patch).forEach(function (k) { msg[k] = patch[k]; });
    iframe.contentWindow.postMessage(msg, '*');
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function clean(label) { return String(label).replace(/^\s*\d+\s*[·.:\-–]\s*/, ''); }
  function tone(o) {
    var t = (o.value + ' ' + o.label).toLowerCase();
    if (/error|fall|denied|permiso|bloque/.test(t)) return 'bad';
    if (/offline|conexi|stale|parcial|desactual|empty|vac|sin datos|sin resultados|no_results/.test(t)) return 'warn';
    if (/load|carg/.test(t)) return 'info';
    return 'ok';
  }
  function current(list, value) {
    for (var i = 0; i < list.length; i++) if (list[i].value === value) return list[i];
    return list[0] || { value: '', label: '' };
  }

  // ---------------------------------------------------------------- toolbar
  function navFor(iframe) {
    if (iframe.classList.contains('pp-full-frame')) return iframe.closest('.pp-full').querySelector('.pp-mocknav');
    var frame = iframe.closest('.pp-frame');
    var prev = frame.previousElementSibling;
    if (prev && prev.classList.contains('pp-mocknav')) return prev;
    var nav = el('div', 'pp-mocknav');
    nav.setAttribute('aria-label', 'Vistas del mockup');
    frame.parentNode.insertBefore(nav, frame);
    return nav;
  }
  function menu(iframe, kind, label, list, value, withDots) {
    var cur = current(list, value);
    var d = el('details', 'pp-mdrop ' + kind);
    var s = el('summary');
    if (withDots) s.appendChild(el('i', 'pp-mdot ' + tone(cur)));
    s.appendChild(el('span', 'pp-mkey', label));
    s.appendChild(el('strong', '', cur.label));
    d.appendChild(s);
    var body = el('div', 'pp-mmenu');
    list.forEach(function (o) {
      var b = el('button', 'pp-mopt' + (o.value === cur.value ? ' on' : ''));
      b.type = 'button';
      b.disabled = !!o.disabled;
      if (withDots) b.appendChild(el('i', 'pp-mdot ' + tone(o)));
      b.appendChild(el('span', '', o.label));
      b.addEventListener('click', function () { var p = {}; p[kind] = o.value; send(iframe, p); d.open = false; });
      body.appendChild(b);
    });
    d.appendChild(body);
    return d;
  }
  function renderToolbar(iframe, d) {
    var nav = navFor(iframe);
    nav.replaceChildren();
    var views = d.views || [];
    var idx = Math.max(0, views.findIndex(function (v) { return v.value === d.current.view; }));
    var bar = el('div', 'pp-mtool');
    var prev = el('button', 'pp-mstep', '‹');
    prev.type = 'button'; prev.title = 'Vista anterior'; prev.disabled = idx <= 0;
    prev.addEventListener('click', function () { send(iframe, { view: views[idx - 1].value }); });
    var next = el('button', 'pp-mstep', '›');
    next.type = 'button'; next.title = 'Vista siguiente'; next.disabled = idx >= views.length - 1;
    next.addEventListener('click', function () { send(iframe, { view: views[idx + 1].value }); });
    var title = el('div', 'pp-mtitle');
    title.appendChild(el('span', 'pp-mnum', (idx + 1) + ' / ' + views.length));
    title.appendChild(el('strong', '', views[idx] ? clean(views[idx].label) : ''));
    if (views.length > 1) {
      var vm = menu(iframe, 'view', 'Ir a', views, d.current.view, false);
      vm.classList.add('pp-mviews');
      vm.querySelector('summary').replaceChildren(el('span', 'pp-mkey', 'Vistas'), el('strong', '', views.length));
      [].forEach.call(vm.querySelectorAll('.pp-mopt span'), function (s) { s.textContent = clean(s.textContent); });
      bar.appendChild(vm);
    }
    bar.appendChild(prev); bar.appendChild(title); bar.appendChild(next);
    var right = el('div', 'pp-mright');
    if ((d.states || []).length > 1) right.appendChild(menu(iframe, 'state', 'Estado', d.states, d.current.state, true));
    if ((d.scenes || []).length > 1) right.appendChild(menu(iframe, 'scene', 'Diálogo', d.scenes, d.current.scene, false));
    if ((d.themes || []).length > 1) {
      var themes = d.themes, ti = themes.findIndex(function (t) { return t.value === d.current.theme; });
      var tb = el('button', 'pp-mtheme', themes[ti >= 0 ? ti : 0].label);
      tb.type = 'button'; tb.title = 'Cambiar de tema';
      tb.addEventListener('click', function () { send(iframe, { theme: themes[(ti + 1) % themes.length].value }); });
      right.appendChild(tb);
    }
    if (!iframe.classList.contains('pp-full-frame')) {
      var fs = el('button', 'pp-mfull', '⛶ Pantalla completa');
      fs.type = 'button'; fs.title = 'Ver el mockup a pantalla completa, como lo vería un usuario';
      fs.addEventListener('click', function () { openFull(iframe); });
      right.appendChild(fs);
    }
    bar.appendChild(right);
    nav.appendChild(bar);
  }

  // ---------------------------------------------------------------- full screen, as a user would see it
  var full = null;
  function openFull(main) {
    if (full) return;
    var overlay = el('div', 'pp-full');
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-label', 'Mockup a pantalla completa');
    var stage = el('div', 'pp-fullstage');
    var f = document.createElement('iframe');
    f.className = 'pp-full-frame';
    f.setAttribute('sandbox', 'allow-scripts');
    f.title = 'Mockup a pantalla completa';
    f.src = main.src + (main.src.indexOf('?') < 0 ? '?' : '&') + 'preview=1';
    stage.appendChild(f);
    var pill = el('button', 'pp-fullpill', '☰ Controles');
    pill.type = 'button';
    var bar = el('div', 'pp-fullbar');
    var nav = el('div', 'pp-mocknav');
    var widths = el('div', 'pp-fullwidths');
    [['Móvil', '390px'], ['Tableta', '768px'], ['Escritorio', '100%']].forEach(function (w, i) {
      var b = el('button', 'pp-mchip' + (i === 2 ? ' on' : ''), w[0]);
      b.type = 'button';
      b.addEventListener('click', function () {
        f.style.width = w[1];
        f.classList.toggle('narrow', w[1] !== '100%');
        [].forEach.call(widths.children, function (x) { x.classList.toggle('on', x === b); });
      });
      widths.appendChild(b);
    });
    var close = el('button', 'pp-fullclose', '✕ Salir');
    close.type = 'button'; close.title = 'Salir (Esc)';
    var pinned = false, timer = 0;
    function show() { clearTimeout(timer); overlay.classList.add('open'); }
    function hideSoon() { if (pinned) return; clearTimeout(timer); timer = setTimeout(function () { overlay.classList.remove('open'); [].forEach.call(bar.querySelectorAll('.pp-mdrop[open]'), function (m) { m.open = false; }); }, 1400); }
    var pin = el('button', 'pp-fullpin', 'Fijar'); pin.type = 'button'; pin.title = 'Mantener los controles a la vista';
    pin.addEventListener('click', function () { pinned = !pinned; pin.classList.toggle('on', pinned); pin.textContent = pinned ? 'Fijado' : 'Fijar'; if (pinned) show(); else hideSoon(); });
    [pill, bar].forEach(function (n) { n.addEventListener('mouseenter', show); n.addEventListener('mouseleave', hideSoon); n.addEventListener('focusin', show); });
    pill.addEventListener('click', show);
    bar.appendChild(nav); bar.appendChild(widths); bar.appendChild(pin); bar.appendChild(close);
    overlay.appendChild(stage); overlay.appendChild(pill); overlay.appendChild(bar);
    document.body.appendChild(overlay);
    full = { overlay: overlay, main: main, frame: f };
    overlay.classList.add('open'); setTimeout(hideSoon, 2600);                 // shown at first so the owner knows where the controls are
    function exit() {
      if (!full) return;
      var k = key(main), want = remembered[k];
      full.overlay.remove();
      full = null;
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('fullscreenchange', onFs);
      if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
      if (want && main.contentWindow) send(main, want);                       // the page's own frame follows what was chosen there
    }
    function onKey(ev) { if (ev.key === 'Escape') exit(); }
    function onFs() { if (!document.fullscreenElement) exit(); }
    close.addEventListener('click', exit);
    document.addEventListener('keydown', onKey, true);
    document.addEventListener('fullscreenchange', onFs);
    if (overlay.requestFullscreen) overlay.requestFullscreen().catch(function () {});
  }

  // ---------------------------------------------------------------- rail of thumbnails (review screen)
  function railFor(iframe) {
    var main = iframe.closest('.pp-rmain');
    if (!main) return null;
    var rail = main.querySelector(':scope > .pp-vrail');
    if (!rail) {
      rail = el('aside', 'pp-vrail');
      rail.setAttribute('aria-label', 'Todas las vistas');
      main.classList.add('has-rail');
      main.insertBefore(rail, main.firstChild);
    }
    return rail;
  }
  function renderRail(iframe, d) {
    var rail = railFor(iframe);
    if (!rail || !(d.views || []).length) return;
    var sig = d.views.map(function (v) { return v.value; }).join('|') + '@' + iframe.src;
    if (rail.dataset.sig === sig) {                               // same mockup: only move the highlight
      [].forEach.call(rail.querySelectorAll('.pp-vcard'), function (c) { c.classList.toggle('on', c.dataset.view === d.current.view); });
      var on = rail.querySelector('.pp-vcard.on');
      if (on) { var top = on.offsetTop - rail.offsetTop; if (top < rail.scrollTop || top + on.offsetHeight > rail.scrollTop + rail.clientHeight) rail.scrollTop = Math.max(0, top - 40); }
      return;
    }
    rail.dataset.sig = sig;
    rail.replaceChildren(el('p', 'pp-vhead', 'Vistas · ' + d.views.length));
    d.views.forEach(function (v, i) {
      var card = el('button', 'pp-vcard' + (v.value === d.current.view ? ' on' : ''));
      card.type = 'button';
      card.dataset.view = v.value;
      var thumb = el('span', 'pp-vthumb');
      var f = document.createElement('iframe');
      f.className = 'pp-thumb-frame';
      f.setAttribute('sandbox', 'allow-scripts');
      f.setAttribute('tabindex', '-1');
      f.setAttribute('aria-hidden', 'true');
      f.loading = 'lazy';
      f.dataset.view = v.value;
      f.src = iframe.src + (iframe.src.indexOf('?') < 0 ? '?' : '&') + 'thumb=1';
      thumb.appendChild(f);
      var meta = el('span', 'pp-vmeta');
      meta.appendChild(el('span', 'pp-vnum', String(i + 1).padStart(2, '0')));
      meta.appendChild(el('span', 'pp-vname', clean(v.label)));
      card.appendChild(thumb); card.appendChild(meta);
      card.addEventListener('click', function () { send(iframe, { view: v.value }); });
      rail.appendChild(card);
    });
  }

  // ---------------------------------------------------------------- messages
  window.addEventListener('message', function (ev) {
    var d = ev.data;
    if (!d || d.pp !== 'mockup' || !d.current) return;
    var thumb = thumbFrame(ev.source);
    if (thumb) {                                                 // a thumbnail loaded: show its own view, once, in the neutral state
      if (!thumbSet.has(thumb)) {
        thumbSet.add(thumb);
        var first = (d.states || [])[0];
        send(thumb, { view: thumb.dataset.view, state: first ? first.value : undefined });
      }
      return;
    }
    var iframe = mainFrame(ev.source);
    if (!iframe) return;
    var k = key(iframe);
    if (!restored.has(iframe)) {                                  // a freshly loaded frame: put it back where the owner was
      restored.add(iframe);
      var want = remembered[k];
      if (want && ['view', 'state', 'scene', 'theme'].some(function (x) { return want[x] && want[x] !== d.current[x]; })) {
        send(iframe, want);
        return;
      }
    }
    remembered[k] = d.current;
    if (!hidden.has(iframe)) { hidden.add(iframe); send(iframe, { hideOwn: true }); }
    renderToolbar(iframe, d);
    renderRail(iframe, d);
  });

  // header shortcut: the same full screen as the toolbar button, for the first mockup on the page
  document.addEventListener('click', function (ev) {
    if (!(ev.target.closest && ev.target.closest('[data-pp-full]'))) return;
    var frame = root.querySelector('.pp-frame iframe');
    if (frame) openFull(frame);
  });

  // menus close on an outside click or Escape; arrows step through the views
  document.addEventListener('click', function (ev) {
    [].forEach.call(document.querySelectorAll('.pp-mdrop[open]'), function (m) { if (!m.contains(ev.target)) m.open = false; });
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') [].forEach.call(document.querySelectorAll('.pp-mdrop[open]'), function (m) { m.open = false; });
    var tag = ev.target && ev.target.tagName;
    if ((ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') || /INPUT|TEXTAREA|SELECT/.test(tag || '')) return;
    var nav = root.querySelector('.pp-mocknav');
    if (!nav || !root.contains(ev.target)) return;
    var btn = nav.querySelector(ev.key === 'ArrowRight' ? '.pp-mstep:last-of-type' : '.pp-mstep');
    if (btn && !btn.disabled) { ev.preventDefault(); btn.click(); }
  });
})();
