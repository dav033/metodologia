// /flow: one run at a time — its state in a sentence, its tasks, the module map and the messages, live or replayed.
// Data: GET /api/flow (messages, digests of provider detail, runs from plan-status) + EventSource /live (new ones).
// Decisions live in flow-core.js; this file only draws.
(function () {
  'use strict';
  var C = window.FlowCore;
  var root = document.getElementById('flow');
  if (!root || !C) return;
  var NS = 'http://www.w3.org/2000/svg';
  var scope = root.dataset.scope || 'global';
  var q = new URLSearchParams(location.search);
  var staticPage = q.get('live') === '0';
  // this page's own stream also carries the "now" frames, so live.js does not open a second one: a browser allows only
  // 6 HTTP/1.1 connections per host, and two streams per tab hang the panel after three tabs (worse through an SSH tunnel)
  window.flowOwnsLive = !staticPage && !!window.EventSource;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // fixed layout (viewBox 880x540): where each module sits, what it is called, what it does
  var N = {
    owner: { x: 110, y: 80, w: 150, h: 64, label: 'Dueño', sub: 'crea y pausa' },
    planner: { x: 110, y: 270, w: 176, h: 70, label: 'Planeación', sub: 'SPEC · PLAN' },
    agent: { x: 110, y: 460, w: 160, h: 64, label: 'Agente', sub: 'sesión que planea' },
    M2: { x: 450, y: 80, w: 184, h: 70, label: 'M2 · decisión', sub: 'rutas y modelos' },
    M1: { x: 450, y: 270, w: 200, h: 78, label: 'M1 · núcleo', sub: 'estado y despacho' },
    M4: { x: 770, y: 80, w: 164, h: 70, label: 'M4 · monitor', sub: 'flujo y tokens' },
    M3: { x: 770, y: 270, w: 164, h: 70, label: 'M3 · ejecutor', sub: 'agentes' },
    M6: { x: 360, y: 460, w: 172, h: 70, label: 'M6 · calidad', sub: 'verificación' },
    M5: { x: 580, y: 460, w: 184, h: 70, label: 'M5 · recuperación', sub: 'reintentos y bloqueos' }
  };
  // soft bands behind the nodes: what each part of the map is for
  var ZONES = [{ x: 14, y: 6, w: 214, h: 528, label: 'ENTRADA' }, { x: 300, y: 6, w: 566, h: 182, label: 'DECIDIR Y VIGILAR' },
    { x: 300, y: 196, w: 566, h: 186, label: 'DESPACHAR Y EJECUTAR' }, { x: 300, y: 392, w: 500, h: 142, label: 'VERIFICAR Y RECUPERAR' }];
  var HOT_FOR = 60;   // seconds an edge keeps its dot after its last message
  var BASE_EDGES = [['agent', 'planner'], ['planner', 'M1'], ['owner', 'M1'], ['M2', 'M1'], ['M1', 'M2'], ['M1', 'M3'],
    ['M3', 'M1'], ['M3', 'M4'], ['M4', 'M1'], ['M1', 'M6'], ['M6', 'M1'], ['M5', 'M1']];

  var all = [], seen = {}, feedSeen = null, digests = {}, runs = [], extraRuns = {}, doing = {};   // doing: attempt -> what its agent does now
  var S = { run: '', task: '', cats: {}, node: '', edge: '', detail: false, tab: 'feed', mode: 'live', t: 0, playing: false,
    speed: 5, paused: false };
  var svg, gE, gN, gP, edgeEls = {}, nodeEls = {}, particles = [], partEls = [], shown = 0, last = 0, pending = false;

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function el(name, attrs, parent) {
    var n = document.createElementNS(NS, name);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(n);
    return n;
  }
  function short(id) { return N[id] ? N[id].label.split(' ·')[0] : id; }
  function fmt(n) { return Number(n || 0).toLocaleString('es-CO'); }
  function hhmm(t, sec) { return t ? new Date(t * 1000).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: sec ? '2-digit' : undefined, hour12: false }) : ''; }
  function ago(t) {
    if (!t) return '';
    var s = Math.max(0, Date.now() / 1000 - t);
    if (s < 60) return 'hace ' + Math.round(s) + ' s';
    if (s < 3600) return 'hace ' + Math.round(s / 60) + ' min';
    if (s < 86400) return 'hace ' + (s / 3600).toFixed(1).replace('.', ',') + ' h';
    return 'hace ' + Math.round(s / 86400) + ' d';
  }
  function dur(s) { s = Math.round(s || 0); return s < 60 ? s + ' s' : Math.floor(s / 60) + ' min' + (s % 60 ? ' ' + (s % 60) + ' s' : ''); }
  // links: every task, attempt and run id leads to the plan page where it lives (new tab, so the map stays as it is)
  function planHref(run) {
    var m = /^([^/]+)\/(REQ-\d+)$/.exec(run || '');
    return m ? '/plans/' + encodeURIComponent(m[1]) + '/' + encodeURIComponent(m[2]) : '';
  }
  function link(href, text) { return href ? '<a class="fl-link" href="' + href + '" target="_blank" rel="noopener">' + text + '</a>' : text; }
  function taskLink(run, id) { return id ? link(planHref(run) && planHref(run) + '#t-' + encodeURIComponent(id), esc(id)) : ''; }
  function attLink(run, id) { return id ? link(planHref(run) && planHref(run) + '#a-' + encodeURIComponent(id), esc(id)) : ''; }
  function linkIds(run, text) {                           // escape, then turn the ids inside a summary into links
    return esc(text).replace(/\b(att-\d+)\b|\b(T\d+)\b/g, function (m, att, task) { return att ? attLink(run, att) : taskLink(run, task); });
  }
  function epoch(iso) { var t = Date.parse(iso || ''); return isNaN(t) ? 0 : t / 1000; }
  function route(a) { return a ? [a.provider && a.model ? a.provider + '/' + a.model : a.provider || a.model, a.account, a.effort].filter(Boolean).join(' · ') : ''; }

  // ---- what the selected run has
  function runInfo(id) { return runs.filter(function (r) { return r.run === id; })[0] || extraRuns[id] || null; }
  function runEvents() { return all.filter(function (e) { return e.run === S.run; }); }
  function inView() {
    var list = runEvents();
    if (S.mode !== 'replay') return list;
    return C.upTo(list, S.t);
  }
  function runDigests(list) {
    var lastAt = list.length ? list[list.length - 1].at_epoch : 0;
    return Object.keys(digests).map(function (k) { return digests[k]; }).filter(function (d) {
      return d.run === S.run && (!S.task || d.task === S.task) && (S.mode !== 'replay' || d.first_epoch <= lastAt);
    });
  }
  function allRunIds() {
    var ids = runs.map(function (r) { return r.run; });
    Object.keys(extraRuns).forEach(function (k) { if (ids.indexOf(k) < 0) ids.push(k); });
    all.forEach(function (e) { if (ids.indexOf(e.run) < 0) ids.push(e.run); });
    return ids;
  }
  function lastOf(id) {
    for (var i = all.length - 1; i >= 0; i--) if (all[i].run === id) return all[i].at_epoch;
    return 0;
  }

  // ---- runs and the sentence
  function renderRuns() {
    var ids = allRunIds();
    $('fl-runs').innerHTML = ids.length ? ids.map(function (id) {
      var r = runInfo(id), cls, pill, desc;
      if (r && r.tasks) {
        var live = r.tasks.filter(function (t) { return C.taskState(t.state) === 'running'; }).map(function (t) { return t.id; });
        cls = r.active ? (live.length ? 'k-run' : 'k-warn') : r.status === 'completed' ? 'k-verify' : r.status === 'blocked' ? 'k-bad' : 'k-state';
        pill = live.length ? 'ejecutando ' + live.join(', ') : statusText(r.status);
        desc = r.summary.tasks_done + ' de ' + r.summary.tasks_total + ' tareas aceptadas' + (lastOf(id) ? ' · último mensaje ' + ago(lastOf(id)) : '');
      } else if (r && r.simulated) {
        cls = 'k-plan'; pill = 'simulación'; desc = 'plan corrido con dobles, sin proveedores';
      } else {
        var n = all.filter(function (e) { return e.run === id; }).length;
        cls = 'k-plan'; pill = 'planeando'; desc = n + ' señales del agente · última ' + ago(lastOf(id));
      }
      return '<button type="button" class="fl-run ' + cls + '" data-run="' + esc(id) + '" aria-pressed="' + (id === S.run) + '">' +
        '<i class="fl-st"></i><span class="fl-nm">' + esc(id) + '</span><span class="fl-pill">' + esc(pill) + '</span>' +
        (r && r.title ? '<span class="fl-ti" title="' + esc(r.title) + '">' + esc(r.title) + '</span>' : '') +
        '<span class="fl-ds">' + esc(desc) + '</span>' + progress(r) + '</button>';
    }).join('') : '<p class="muted">Ninguna ejecución del Scheduler en este alcance todavía.</p>';
  }
  function progress(r) {
    if (!r || !r.summary || !r.summary.tasks_total) return '';
    var staged = r.stage && r.stage.length && r.tasks ? r.tasks.filter(function (x) { return r.stage.indexOf(x.subplan_id) >= 0; }) : null;
    var pct = staged && staged.length ? Math.round(100 * staged.filter(function (x) { return C.taskState(x.state) === 'done'; }).length / staged.length)
      : Math.round(100 * r.summary.tasks_done / r.summary.tasks_total);   // a staged run: progress of the approved stage
    return '<span class="fl-prog" role="progressbar" aria-label="Avance" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + pct +
      '"><i style="width:' + pct + '%"></i></span>';
  }
  function statusText(s) {
    return { running: 'en marcha', waiting: 'esperando', paused: 'en pausa', completed: 'terminada', blocked: 'bloqueada',
      cancelled: 'cancelada', pending: 'sin empezar' }[s] || s || '—';
  }
  function renderNow(list) {
    var r = runInfo(S.run), box = $('fl-now');
    $('fl-eyebrow').innerHTML = 'flujo · ' + (S.run ? link(planHref(S.run), esc(S.run)) : 'sin ejecuciones') + (S.mode === 'replay' ? ' · repetición' : '');
    if (!S.run) { box.innerHTML = ''; return; }
    if (!r || !r.tasks) {
      box.innerHTML = r && r.simulated ? 'Simulación del plan <b>' + esc(S.run) + '</b>: ' + list.length + ' mensajes, sin proveedores ni escritura.' :
        'Un agente está escribiendo el plan de <b>' + esc(S.run) + '</b>. Todavía no hay ejecución: solo se ven sus ' + list.length +
        ' señales hacia Planeación' + (list.length ? ', la última ' + ago(list[list.length - 1].at_epoch) : '') + '.';
      return;
    }
    var t = r.tasks, live = t.filter(function (x) { return C.taskState(x.state) === 'running'; });
    var rejected = [], failed = [], blocked = t.filter(function (x) { return x.state === 'blocked'; });
    t.forEach(function (x) {
      (x.history || []).forEach(function (a) {
        if (a.state === 'rejected' && rejected.indexOf(x.id) < 0) rejected.push(x.id);
        if (a.state === 'failed' && failed.indexOf(x.id) < 0) failed.push(x.id);
      });
    });
    var nRejected = t.reduce(function (n, x) { return n + (x.history || []).filter(function (a) { return a.state === 'rejected'; }).length; }, 0);
    var nFailed = t.reduce(function (n, x) { return n + (x.history || []).filter(function (a) { return a.state === 'failed'; }).length; }, 0);
    var h = '';
    if (live.length) h += live.map(function (x) {
      var a = x.attempt || {};
      return '<b>' + taskLink(S.run, x.id) + '</b> ' + (x.state === 'verifying' ? 'se está verificando' : 'está en curso') + (route(a) ? ' con <code>' + esc(route(a)) + '</code>' : '') +
        (a.started_at ? ', empezó ' + ago(epoch(a.started_at)) : '');
    }).join('; ') + '. ';
    else h += r.active ? 'Nada se ejecuta en este momento (' + esc(statusText(r.status)) + '). ' : 'La ejecución está ' + esc(statusText(r.status)) + '. ';
    var staged = r.stage && r.stage.length ? t.filter(function (x) { return r.stage.indexOf(x.subplan_id) >= 0; }) : null;
    if (staged) h += '<b>' + staged.filter(function (x) { return C.taskState(x.state) === 'done'; }).length + ' de ' + staged.length +
      '</b> ' + link(planHref(S.run), 'tareas aceptadas') + ' en la etapa aprobada (' + esc(r.stage.join(', ')) + '; el plan tiene ' +
      r.summary.tasks_total + ')';
    else h += '<b>' + r.summary.tasks_done + ' de ' + r.summary.tasks_total + '</b> ' + link(planHref(S.run), 'tareas aceptadas');
    var ids = function (list) { return list.map(function (id) { return taskLink(S.run, id); }).join(', '); };
    if (nRejected) h += '; M6 rechazó ' + nRejected + ' intento' + (nRejected > 1 ? 's' : '') + ' (' + ids(rejected) + ')';
    if (nFailed) h += '; ' + nFailed + ' intento' + (nFailed > 1 ? 's' : '') + ' fallaron al ejecutar (' + ids(failed) + ')';
    h += blocked.length ? '; bloqueada' + (blocked.length > 1 ? 's' : '') + ': ' + ids(blocked.map(function (x) { return x.id; })) + '.' : '.';
    box.innerHTML = h;
  }

  // ---- task strip
  function renderTasks() {
    var r = runInfo(S.run), box = $('fl-tasks-box');
    box.hidden = !(r && r.tasks && r.tasks.length);
    if (box.hidden) return;
    var chip = function (t) {
      var st = C.taskState(t.state), tries = t.attempts > 1 ? t.attempts + ' intentos' : t.attempts ? '1 intento' : '—';
      return '<button type="button" class="fl-task s-' + st + ' ' + C.TASK_CLASS[st] + '" data-task="' + esc(t.id) + '" aria-pressed="' + (S.task === t.id) +
        '" title="' + esc(t.id + ' · ' + t.title + (route(t.attempt) ? ' · ' + route(t.attempt) : '')) + '"><span>' + esc(t.id) + '</span><span class="fl-bar"></span>' +
        '<span class="fl-tr">' + tries + '</span></button>';
    };
    if (!r.subplans || !r.subplans.length) { $('fl-tasks').innerHTML = r.tasks.map(chip).join(''); return; }
    // one group per subplan in plan order (then the composition checks); the one working now stands out, the ones
    // outside the approved stage step back
    var groups = r.subplans.map(function (sp) { return { sp: sp, tasks: [] }; }), rest = { sp: null, tasks: [] };
    r.tasks.forEach(function (t) {
      var g = groups.filter(function (x) { return x.sp.id === t.subplan_id; })[0] || rest;
      g.tasks.push(t);
    });
    if (rest.tasks.length) groups.push(rest);
    $('fl-tasks').innerHTML = groups.filter(function (g) { return g.tasks.length; }).map(function (g) {
      var states = g.tasks.map(function (t) { return C.taskState(t.state); });
      var done = states.filter(function (x) { return x === 'done'; }).length;
      var live = states.some(function (x) { return x === 'running' || x === 'retry'; });
      var out = g.sp ? !g.sp.in_stage : !r.subplans.every(function (x) { return x.in_stage; });
      var cls = live ? ' on' : out ? ' out' : '';
      var badge = live ? '<span class="fl-sp-badge on">activo</span>' : out ? '<span class="fl-sp-badge">fuera de la etapa</span>' :
        done === g.tasks.length ? '<span class="fl-sp-badge ok">terminado</span>' : '<span class="fl-sp-badge">en la etapa</span>';
      var head = g.sp ? '<b>' + esc(g.sp.id) + '</b> ' + esc(g.sp.title) : '<b>Comprobaciones de integración</b>';
      return '<section class="fl-sp' + cls + '"><header>' + head + badge + '<span class="fl-sp-n">' + done + ' / ' + g.tasks.length +
        '</span></header><div class="fl-sp-chips">' + g.tasks.map(chip).join('') + '</div></section>';
    }).join('');
  }

  // ---- the map
  function anchor(a, b) {
    var dx = b.x - a.x, dy = b.y - a.y;
    var s = Math.min((a.w / 2 + 4) / Math.abs(dx || 1e-9), (a.h / 2 + 4) / Math.abs(dy || 1e-9));
    return { x: a.x + dx * s, y: a.y + dy * s };
  }
  function geometry(from, to) {
    var a = N[from], b = N[to];
    if (!a || !b || from === to) return null;
    var rev = BASE_EDGES.some(function (x) { return x[0] === to && x[1] === from; }) || !!edgeEls[to + '>' + from];
    var p = anchor(a, b), qq = anchor(b, a), dx = qq.x - p.x, dy = qq.y - p.y, len = Math.hypot(dx, dy) || 1;
    var nx = -dy / len, ny = dx / len, off = rev ? 9 : 0, bend = rev ? 22 : 0;
    p = { x: p.x + nx * off, y: p.y + ny * off }; qq = { x: qq.x + nx * off, y: qq.y + ny * off };
    var c = { x: (p.x + qq.x) / 2 + nx * bend, y: (p.y + qq.y) / 2 + ny * bend };
    var tx = qq.x - c.x, ty = qq.y - c.y, tl = Math.hypot(tx, ty) || 1;
    tx /= tl; ty /= tl;
    return { p: p, c: c, q: qq, tx: tx, ty: ty, m: { x: 0.25 * p.x + 0.5 * c.x + 0.25 * qq.x, y: 0.25 * p.y + 0.5 * c.y + 0.25 * qq.y } };
  }
  function ensureEdge(from, to) {
    var key = from + '>' + to;
    if (edgeEls[key]) return edgeEls[key];
    var g = geometry(from, to);
    if (!g) return null;
    var grp = el('g', { class: 'fl-edge idle', 'data-edge': key, tabindex: 0, role: 'button', 'aria-label': N[from].label + ' a ' + N[to].label }, gE);
    var d = 'M' + g.p.x + ',' + g.p.y + ' Q' + g.c.x + ',' + g.c.y + ' ' + (g.q.x - g.tx * 9) + ',' + (g.q.y - g.ty * 9);
    el('path', { d: d, class: 'fl-hit' }, grp);
    var ln = el('path', { d: d, class: 'fl-ln' }, grp);
    el('path', { d: d, class: 'fl-run-path' }, grp);
    var px = -g.ty, py = g.tx;
    el('path', { class: 'fl-hd', d: 'M' + g.q.x + ',' + g.q.y + ' L' + (g.q.x - g.tx * 11 + px * 5.5) + ',' + (g.q.y - g.ty * 11 + py * 5.5) +
      ' L' + (g.q.x - g.tx * 11 - px * 5.5) + ',' + (g.q.y - g.ty * 11 - py * 5.5) + 'z' }, grp);
    var dot = el('circle', { class: 'fl-dotm', r: 4.5 }, grp);
    var mo = el('animateMotion', { path: d, dur: Math.max(1.6, Math.hypot(g.q.x - g.p.x, g.q.y - g.p.y) / 110).toFixed(1) + 's', repeatCount: 'indefinite' }, dot);
    var pb = el('rect', { class: 'fl-pb', rx: 9, height: 18, y: g.m.y - 9 }, grp);
    var pt = el('text', { class: 'fl-pt', x: g.m.x, y: g.m.y + 4, 'text-anchor': 'middle' }, grp);
    edgeEls[key] = { g: grp, ln: ln, pb: pb, pt: pt, geo: g };
    return edgeEls[key];
  }
  function drawMap() {
    svg = el('svg', { viewBox: '0 0 880 540', role: 'group', 'aria-label': 'Mapa de módulos y mensajes entre ellos' }, $('flow-map'));
    var gZ = el('g', { class: 'fl-zones', 'aria-hidden': 'true' }, svg);
    ZONES.forEach(function (z) {
      el('rect', { class: 'fl-zone', x: z.x, y: z.y, width: z.w, height: z.h, rx: 22 }, gZ);
      el('text', { class: 'fl-zl', x: z.x + 18, y: z.y + 20 }, gZ).textContent = z.label;
    });
    gE = el('g', {}, svg); gN = el('g', {}, svg); gP = el('g', {}, svg);
    BASE_EDGES.forEach(function (e) { ensureEdge(e[0], e[1]); });
    Object.keys(N).forEach(function (id) {
      var n = N[id], g = el('g', { class: 'fl-node' + (id === 'M1' ? ' core' : ''), 'data-node': id, tabindex: 0, role: 'button', 'aria-label': n.label }, gN);
      el('rect', { class: 'fl-halo', x: n.x - n.w / 2 - 5, y: n.y - n.h / 2 - 5, width: n.w + 10, height: n.h + 10, rx: 18 }, g);
      el('rect', { class: 'fl-box', x: n.x - n.w / 2, y: n.y - n.h / 2, width: n.w, height: n.h, rx: 14 }, g);
      el('rect', { class: 'fl-acc', x: n.x - n.w / 2 + 12, y: n.y - n.h / 2 + 10, width: 4, height: n.h - 20, rx: 2 }, g);
      el('text', { class: 'fl-nl', x: n.x, y: n.y - 10, 'text-anchor': 'middle' }, g).textContent = n.label;
      el('text', { class: 'fl-ns', x: n.x, y: n.y + 7, 'text-anchor': 'middle' }, g).textContent = n.sub;
      var meta = el('text', { class: 'fl-nm', x: n.x, y: n.y + 24, 'text-anchor': 'middle' }, g);
      var loop = el('g', { class: 'fl-loop', style: 'display:none', transform: 'translate(' + (n.x + n.w / 2 - 4) + ',' + (n.y - n.h / 2 + 2) + ')' }, g);
      el('circle', { r: 12 }, loop);
      var lt = el('text', { 'text-anchor': 'middle', y: 3.5 }, loop);
      el('title', {}, loop).textContent = 'Mensajes que el módulo se envía a sí mismo';
      var badge = id === 'planner' || id === 'agent' ? el('text', { class: 'fl-badge', x: n.x, y: n.y - n.h / 2 - 8, 'text-anchor': 'middle' }, g) : null;
      var tag = el('g', { class: 'fl-tag', style: 'display:none' }, g);
      var tagBox = el('rect', { rx: 10, height: 20, y: n.y - n.h / 2 - 27 }, tag);
      var tagText = el('text', { x: n.x, y: n.y - n.h / 2 - 13, 'text-anchor': 'middle' }, tag);
      nodeEls[id] = { g: g, meta: meta, loop: loop, lt: lt, badge: badge, tag: tag, tagBox: tagBox, tagText: tagText, n: n };
    });
  }
  // agent sessions from the shared live stream (live.js): who is planning right now, on the Planeación node
  document.addEventListener('now-frame', function (ev) {
    var working = ((ev.detail && ev.detail.sessions) || []).filter(function (x) { return x.state === 'working' && !x.quiet; });
    var planning = working.filter(function (x) { return x.activity === 'planning'; }).length;
    if (nodeEls.planner) nodeEls.planner.badge.textContent = planning ? '● ' + planning + (planning > 1 ? ' agentes planeando' : ' agente planeando') : '';
    if (nodeEls.agent) nodeEls.agent.badge.textContent = working.length ? '● ' + working.length + ' en sesión' : '';
  });
  function renderMap(list) {
    var vis = list.filter(function (e) { return C.matches(e, S); });
    var showDigests = S.detail && !C.anyCat(S) && !S.node && !S.edge;
    var tal = C.tally(vis, showDigests ? runDigests(list) : []), max = 1;
    vis.forEach(function (e) { ensureEdge(e.from, e.to); });
    Object.keys(tal.edges).forEach(function (k) { max = Math.max(max, tal.edges[k].count); });
    var focus = S.task || S.node || S.edge;
    Object.keys(edgeEls).forEach(function (k) {
      var E = edgeEls[k], e = tal.edges[k];
      E.g.setAttribute('class', 'fl-edge ' + (e ? 'k-' + C.dominant(e.cats) : 'idle') + (S.edge === k ? ' sel' : '') + (focus && !e ? ' fade' : ''));
      E.ln.setAttribute('stroke-width', e ? (1.6 + 4.4 * Math.log(1 + e.count) / Math.log(1 + max)).toFixed(2) : 1.4);
      if (e) {
        var txt = fmt(e.count), w = txt.length * 7 + 14;
        E.pt.textContent = txt; E.pb.setAttribute('x', E.geo.m.x - w / 2); E.pb.setAttribute('width', w);
      }
    });
    var acts = liveActs(), actNode = {}, actEdge = {};
    acts.forEach(function (a) {
      (actNode[a.node] = actNode[a.node] || []).push(a);
      a.edges.forEach(function (e) { var E = ensureEdge(e[0], e[1]); if (E && !a.quiet) actEdge[e[0] + '>' + e[1]] = true; });   // a silent agent moves nothing
    });
    var nowS = Date.now() / 1000;
    Object.keys(edgeEls).forEach(function (k) {
      var e = tal.edges[k];
      if (actEdge[k]) edgeEls[k].g.classList.add('live');
      // the travelling dot means «talking right now»: a live attempt or a message in the last minute (live mode only)
      if (actEdge[k] || (S.mode === 'live' && e && nowS - e.last < HOT_FOR)) edgeEls[k].g.classList.add('hot');
    });
    Object.keys(nodeEls).forEach(function (id) {
      var X = nodeEls[id], o = tal.nodes[id], loops = tal.loops[id] || 0, act = actNode[id];
      X.meta.textContent = o ? fmt(o.count) + ' msj · ' + ago(o.last) : 'sin mensajes';
      X.loop.style.display = loops ? '' : 'none';
      X.lt.textContent = loops > 999 ? Math.round(loops / 1000) + 'k' : loops || '';
      X.tag.style.display = act ? '' : 'none';
      if (act) {
        var txt = act.map(function (a) { return a.task || (a.verb.indexOf('pausa') >= 0 ? 'en pausa' : 'esperando'); }).join(' · ');
        txt = (act.some(function (a) { return a.quiet; }) ? '◌ ' : '▶ ') + txt;
        X.tagText.textContent = txt;
        var w = txt.length * 7 + 18, left = X.n.x - X.n.w / 2 + 4;      // top-left corner: edges leave from the middle
        X.tagBox.setAttribute('x', left); X.tagBox.setAttribute('width', w); X.tagText.setAttribute('x', left + w / 2);
      }
      var quiet = act && act.every(function (a) { return a.quiet; });
      X.g.setAttribute('class', 'fl-node' + (id === 'M1' ? ' core' : '') + (act ? ' active' : '') + (quiet ? ' quiet' : '') +
        (S.node === id ? ' sel' : '') + (focus && !o && !act ? ' fade' : ''));
    });
  }
  // what is working now in the selected run (live mode only: a replay shows the past)
  function liveActs() {
    if (S.mode !== 'live') return [];
    var r = runInfo(S.run);
    return C.activity(r, Object.keys(digests).map(function (k) { return digests[k]; }), Date.now() / 1000)
      .filter(function (a) { return !S.task || a.task === S.task || !a.task; });
  }
  function renderLive() {
    var box = $('fl-live'), acts = liveActs();
    box.hidden = !acts.length;
    if (!acts.length) return;
    box.className = 'fl-live' + (acts.every(function (a) { return a.quiet; }) ? ' quiet' : '');
    box.innerHTML = '<span class="fl-live-dot"></span><span>' + acts.map(function (a) {
      var task = a.task && ((runInfo(S.run) || {}).tasks || []).filter(function (t) { return t.id === a.task; })[0];
      var who = '<b>' + esc(N[a.node].label) + '</b> ' + esc(a.verb) + (a.task ? ' <b>' + taskLink(S.run, a.task) + '</b>' + (task ? ' · ' + esc(task.title) : '') : '');
      var how = a.attempt ? [attLink(S.run, a.attempt.id), esc(route(a.attempt))].filter(Boolean).join(' · ') : '';
      var when = [a.since ? 'empezó ' + ago(a.since) : '',
        a.last ? (a.quiet ? 'sin señales ' : 'última señal ') + ago(a.last) : ''].filter(Boolean).join(' · ');
      return '<div>' + who + (how ? ' <span class="fl-live-how">(' + how + ')</span>' : '') + (when ? ' · ' + esc(when) : '') + '</div>' +
        (a.attempt ? doingHtml(doing[a.attempt.id]) : '');
    }).join('') + '</span>';
  }
  // the agent's own account of this moment: the action in progress, its last sentence, its last finished steps
  var TOOL = { exec: 'comando', 'apply patch': 'edita', Bash: 'comando', Edit: 'edita', Write: 'escribe', MultiEdit: 'edita',
    Read: 'lee', Grep: 'busca', Glob: 'busca archivos', WebFetch: 'consulta', WebSearch: 'busca en la web', Task: 'delega',
    TodoWrite: 'actualiza su lista' };
  function toolName(t) { return TOOL[t] || t; }
  function doingHtml(d) {
    if (!d || !(d.current || d.said || (d.steps && d.steps.length))) return '';
    var h = '<div class="fl-doing">';
    if (d.current) h += '<div><span class="fl-doing-k">ahora</span><span class="fl-doing-t">' + esc(toolName(d.current.tool)) + '</span><code title="' + esc(d.current.what || '') + '">' +
      esc(d.current.what || '') + '</code></div>';
    if (d.said) h += '<div><span class="fl-doing-k">dice</span>«' + esc(d.said) + '»</div>';
    if (d.steps && d.steps.length) h += '<div><span class="fl-doing-k">antes</span><ol>' + d.steps.slice().reverse().map(function (st) {
      return '<li class="' + (st.ok === false ? 'bad' : '') + '"><span class="fl-doing-t">' + (st.ok === false ? '✗ ' : st.ok ? '✓ ' : '') +
        esc(toolName(st.tool)) + '</span><code title="' + esc(st.what || '') + '">' + esc(st.what || '') + '</code></li>';
    }).join('') + '</ol></div>';
    if (d.updated_at) h += '<div class="fl-doing-m">registro del agente actualizado ' + esc(ago(d.updated_at)) + '</div>';
    return h + '</div>';
  }
  var doingBusy = false;
  function refreshDoing() {
    var acts = liveActs().filter(function (a) { return a.attempt; });
    if (!acts.length || doingBusy || !planHref(S.run)) { if (!acts.length) doing = {}; return; }
    doingBusy = true;
    fetch('/api/flow/agent?run=' + encodeURIComponent(S.run)).then(function (r) { return r.json(); })
      .then(function (d) { doing = d.attempts || {}; renderLive(); }).catch(function () {})
      .then(function () { doingBusy = false; });
  }

  // ---- messages
  function renderCats(list) {
    var n = {};
    list.filter(function (e) { return C.matches(e, S, true); }).forEach(function (e) { var c = C.category(e); n[c] = (n[c] || 0) + 1; });
    $('fl-cats').innerHTML = C.CATEGORIES.map(function (c) {
      return '<button type="button" class="fl-cat k-' + c[0] + (n[c[0]] ? '' : ' zero') + '" data-cat="' + c[0] + '" aria-pressed="' + !!S.cats[c[0]] + '"><i></i>' +
        esc(c[1]) + ' <b>' + fmt(n[c[0]] || 0) + '</b></button>';
    }).join('');
  }
  function digestRow(d) {
    var types = Object.keys(d.types || {}).sort(function (a, b) { return d.types[b] - d.types[a]; }).slice(0, 3)
      .map(function (k) { return k + ' ' + fmt(d.types[k]); }).join(', ');
    return '<li class="fl-agg k-stream" data-task="' + esc(d.task || '') + '"><div class="fl-hd"><span>M3 → M4 · detalle del proveedor</span><span class="fl-x">×' + fmt(d.count) + '</span></div>' +
      fmt(d.stream) + ' eventos de flujo' + (types ? ' (' + esc(types) + ')' : '') + (d.incidents ? ' y ' + fmt(d.incidents) + ' avisos informativos' : '') +
      '<div class="fl-mt">' + hhmm(d.first_epoch, true) + '–' + hhmm(d.at_epoch, true) + (d.task ? ' · ' + taskLink(d.run, d.task) : '') + (d.attempt ? ' · ' + attLink(d.run, d.attempt) : '') + '</div></li>';
  }
  function renderFeed(list) {
    var vis = list.filter(function (e) { return C.matches(e, S); }), rows = C.groupRows(vis), html = [];
    var dg = S.detail && !C.anyCat(S) && !S.node && !S.edge ? runDigests(list).sort(function (a, b) { return b.at_epoch - a.at_epoch; }) : [];
    var di = 0, fresh = {};
    var firstLoad = !feedSeen && all.length > 0;       // the first batch is history, not news: only later rows animate
    if (all.length) feedSeen = feedSeen || {};
    all.forEach(function (e) { var k = e.run + '#' + e.seq; if (!firstLoad && !feedSeen[k]) fresh[k] = 1; feedSeen[k] = 1; });
    rows.forEach(function (r) {
      while (di < dg.length && dg[di].at_epoch >= r.last) html.push(digestRow(dg[di++]));
      var e = r.ev;
      html.push('<li class="' + C.kindClass(e) + (fresh[e.run + '#' + e.seq] ? ' fl-new' : '') + '" data-task="' + esc(e.task || '') + '"><div class="fl-hd"><span>' + esc(short(e.from)) + ' → ' + esc(short(e.to)) +
        ' · ' + esc(C.label(e.kind)) + '</span>' + (r.n > 1 ? '<span class="fl-x">×' + r.n + '</span>' : '') + '</div>' + linkIds(e.run, e.summary) +
        '<div class="fl-mt">' + hhmm(r.first, true) + (r.n > 1 ? '–' + hhmm(r.last, true) : '') + (e.task ? ' · ' + taskLink(e.run, e.task) : '') + (e.attempt ? ' · ' + attLink(e.run, e.attempt) : '') + '</div></li>');
    });
    while (di < dg.length) html.push(digestRow(dg[di++]));
    $('flow-feed-list').innerHTML = html.join('') || '<li class="fl-empty">' + (S.run ? 'Ningún mensaje con estos filtros.' : 'Sin mensajes todavía.') + '</li>';
    $('fl-feed-n').textContent = fmt(vis.length);
    var hidden = runDigests(list).reduce(function (n, d) { return n + d.count; }, 0);
    $('fl-detail-n').textContent = hidden ? '(' + fmt(hidden) + ')' : '';
    $('fl-detail').checked = S.detail;
  }

  // ---- one task's path, attempt by attempt
  var RESULT = { accepted: ['aceptado', 'k-verify'], rejected: ['rechazado', 'k-bad'], failed: ['falló', 'k-bad'], cancelled: ['cancelado', 'k-state'],
    running: ['en curso', 'k-run'], verifying: ['verificando', 'k-run'], dispatched: ['despachado', 'k-run'], reserved: ['reservado', 'k-plan'] };
  function renderTrace(list) {
    var box = $('fl-trace');
    if (!S.task) { box.innerHTML = '<p class="fl-lead">Elige una tarea en la franja o en un mensaje para ver su recorrido, intento por intento.</p>'; $('fl-trace-n').textContent = ''; return; }
    var r = runInfo(S.run), task = r && r.tasks ? r.tasks.filter(function (t) { return t.id === S.task; })[0] : null;
    var blocks = C.attempts(list, S.task, task && task.history);
    var real = blocks.filter(function (b) { return b.id; });
    $('fl-trace-n').textContent = real.length || '';
    var dg = {};
    runDigests(list).forEach(function (d) { dg[d.attempt] = d; });
    box.innerHTML = '<p class="fl-lead"><b>' + taskLink(S.run, S.task) + '</b>' + (task ? ' · ' + esc(task.title) : '') + ' · ' + real.length + ' intento' + (real.length === 1 ? '' : 's') +
      ', del más reciente al primero.</p>' + (task && task.objective ? '<p class="fl-obj">' + esc(task.objective) + '</p>' : '') + blocks.slice().reverse().map(function (b) {
        var a = b.attempt, res = RESULT[b.state] || (b.id ? [b.state || '—', 'k-state'] : ['tarea', 'k-state']);
        var when = a ? (a.live || !a.ended_at ? (a.started_at ? 'empezó ' + ago(epoch(a.started_at)) : '') : dur(a.duration_s)) : '';
        var d = dg[b.id];
        return '<div class="fl-att"><div class="fl-ah"><span class="fl-an">' + (b.id ? 'Intento ' + (b.number || '') + ' · ' + attLink(S.run, b.id) : 'Antes del primer intento') + '</span>' +
          '<span class="fl-res ' + res[1] + '">' + esc(res[0]) + '</span></div>' +
          (a ? '<div class="fl-who">' + esc([route(a), when].filter(Boolean).join(' · ')) + (a.failure ? ' · ' + esc(typeof a.failure === 'string' ? a.failure : (a.failure.cause || a.failure.reason || '')) : '') + '</div>' : '') +
          (a ? '<p>' + window.FlowFailureLinks.link(S.run, S.task, a) + '</p>' : '') +
          '<ul class="fl-steps">' + b.steps.map(function (e) {
            return '<li class="' + C.kindClass(e) + '"><span class="fl-tm">' + hhmm(e.at_epoch, true) + '</span><span class="fl-md">' + esc(short(e.from)) + '</span>' + linkIds(e.run, e.summary) + '</li>';
          }).join('') + (d ? '<li class="k-stream fl-quiet"><span class="fl-tm">' + hhmm(d.at_epoch, true) + '</span>' + fmt(d.count) + ' eventos de detalle del proveedor (ocultos)</li>' : '') +
          (b.steps.length || d ? '' : '<li class="k-state fl-quiet">Sin mensajes de este intento.</li>') + '</ul></div>';
      }).join('');
  }

  function renderCrumbs() {
    var c = [];
    if (S.task) c.push(['task', 'tarea ' + S.task]);
    if (S.node) c.push(['node', 'módulo ' + N[S.node].label]);
    if (S.edge) { var p = S.edge.split('>'); c.push(['edge', short(p[0]) + ' → ' + short(p[1])]); }
    $('fl-crumbs').innerHTML = c.length ? 'Mostrando ' + c.map(function (x) {
      return '<span class="fl-crumb">' + esc(x[1]) + '<button type="button" data-clear="' + x[0] + '" aria-label="Quitar filtro">×</button></span>';
    }).join('') : 'Mostrando todo · clic en un módulo o una flecha para filtrar';
  }

  function render() {
    pending = false;
    var ids = allRunIds();
    if (!S.run || ids.indexOf(S.run) < 0) S.run = ids[0] || '';     // before reading the run's messages
    var list = inView();
    renderRuns(); renderNow(list); renderTasks(); renderLive(); renderCrumbs(); renderMap(list); renderCats(list); renderFeed(list); renderTrace(list);
    $('fl-tab-feed').classList.toggle('on', S.tab === 'feed');
    $('fl-tab-trace').classList.toggle('on', S.tab === 'trace');
    $('fl-pane-feed').hidden = S.tab !== 'feed';
    $('fl-trace').hidden = S.tab !== 'trace';
  }
  function soon() { if (!pending) { pending = true; requestAnimationFrame(render); } }

  // ---- particles and replay
  function flash(ev) {
    if (ev.run !== S.run || !C.matches(ev, S)) return;
    var E = edgeEls[C.edgeKey(ev)];
    if (E && !S.paused && !reduced) C.spawn(particles, ev, performance.now(), 1100 / Math.max(1, S.speed / 5));
    var X = nodeEls[ev.to];
    if (X) { X.g.classList.add('flash'); setTimeout(function () { X.g.classList.remove('flash'); }, 450); }
  }
  function spanLen() { return C.span(runEvents()).length; }
  function clock() {
    var len = spanLen();
    $('flow-clock').textContent = S.t.toFixed(1).replace('.', ',') + ' / ' + len.toFixed(1).replace('.', ',') + ' s';
    $('flow-seek').value = len ? Math.round(1000 * S.t / len) : 0;
  }
  function frame(now) {
    var dt = last ? (now - last) / 1000 : 0;
    last = now;
    if (S.mode === 'replay' && S.playing) {
      S.t = Math.min(spanLen(), S.t + dt * S.speed);
      var upto = inView();
      if (upto.length !== shown) { upto.slice(shown).slice(-C.MAX_PARTICLES).forEach(flash); shown = upto.length; soon(); }
      clock();
      if (S.t >= spanLen()) { S.playing = false; $('flow-play').textContent = '▶ Reproducir'; }
    }
    particles = C.alive(particles, now);
    while (partEls.length > particles.length) gP.removeChild(partEls.pop());
    while (partEls.length < particles.length) partEls.push(el('circle', { r: 6 }, gP));
    particles.forEach(function (p, i) {
      var E = edgeEls[p.key], c = partEls[i];
      if (!E) return;
      var k = (now - p.born) / p.life, u = 1 - k, g = E.geo;
      c.setAttribute('cx', u * u * g.p.x + 2 * u * k * g.c.x + k * k * g.q.x);
      c.setAttribute('cy', u * u * g.p.y + 2 * u * k * g.c.y + k * k * g.q.y);
      c.setAttribute('class', 'fl-fp ' + p.cls);
    });
    requestAnimationFrame(frame);
  }
  function setMode(m) {
    S.mode = m; S.playing = false; S.t = 0; shown = 0;
    $('flow-live').classList.toggle('on', m === 'live');
    $('flow-replay').classList.toggle('on', m === 'replay');
    $('flow-replaybar').hidden = m !== 'replay';
    $('flow-play').textContent = '▶ Reproducir';
    clock(); render();
  }
  function setSpeed(v) {
    S.speed = v;
    Array.prototype.forEach.call(document.querySelectorAll('[data-speed]'), function (o) { o.classList.toggle('on', +o.dataset.speed === v); });
  }

  // ---- controls
  function wire() {
    root.parentNode.addEventListener('click', function (ev) {
      var t = ev.target, b;
      if (t.closest('a[href]')) return;                     // a link opens its page; it does not select anything
      if ((b = t.closest('[data-run]'))) { S.run = b.dataset.run; S.task = S.node = S.edge = ''; S.cats = {}; doing = {}; setMode(S.mode); refreshDoing(); return; }
      if ((b = t.closest('.fl-task'))) { S.task = S.task === b.dataset.task ? '' : b.dataset.task; S.tab = S.task ? 'trace' : 'feed'; render(); return; }
      if ((b = t.closest('[data-cat]'))) { S.cats[b.dataset.cat] = !S.cats[b.dataset.cat]; render(); return; }
      if ((b = t.closest('[data-clear]'))) { S[b.dataset.clear] = ''; render(); return; }
      if ((b = t.closest('.fl-node'))) { S.node = S.node === b.dataset.node ? '' : b.dataset.node; S.edge = ''; S.tab = 'feed'; render(); return; }
      if ((b = t.closest('.fl-edge'))) { S.edge = S.edge === b.dataset.edge ? '' : b.dataset.edge; S.node = ''; S.tab = 'feed'; render(); return; }
      if ((b = t.closest('#flow-feed-list li[data-task]')) && b.dataset.task) { S.task = b.dataset.task; S.tab = 'trace'; render(); }
    });
    root.addEventListener('keydown', function (ev) {
      if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.closest && ev.target.closest('.fl-node, .fl-edge')) {
        ev.preventDefault(); ev.target.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      }
    });
    $('fl-tab-feed').addEventListener('click', function () { S.tab = 'feed'; render(); });
    $('fl-tab-trace').addEventListener('click', function () { S.tab = 'trace'; render(); });
    $('fl-detail').addEventListener('change', function (e) { S.detail = e.target.checked; render(); });
    $('flow-live').addEventListener('click', function () { setMode('live'); });
    $('flow-replay').addEventListener('click', function () { setMode('replay'); });
    $('flow-play').addEventListener('click', function (e) {
      if (S.t >= spanLen()) { S.t = 0; shown = 0; render(); }
      S.playing = !S.playing; e.target.textContent = S.playing ? '❚❚ Pausa' : '▶ Reproducir';
    });
    $('flow-seek').addEventListener('input', function (e) { S.t = spanLen() * e.target.value / 1000; shown = inView().length; clock(); render(); });
    Array.prototype.forEach.call(document.querySelectorAll('[data-speed]'), function (b) {
      b.addEventListener('click', function () { setSpeed(+b.dataset.speed); });
    });
    $('flow-pause').addEventListener('click', function (e) {
      S.paused = !S.paused;
      if (svg && svg.pauseAnimations) S.paused ? svg.pauseAnimations() : svg.unpauseAnimations();
      $('flow').classList.toggle('fl-paused', S.paused);
      e.currentTarget.firstChild.textContent = S.paused ? 'Reanudar animación' : 'Pausar animación';
    });
    $('flow-sim').addEventListener('click', function (e) {
      var btn = e.currentTarget, target = (btn.dataset.sim || '').split('/');
      btn.disabled = true;
      document.querySelector('.fl-more').open = false;
      fetch('/api/simulate?project=' + encodeURIComponent(target[0]) + '&req=' + encodeURIComponent(target[1]))
        .then(function (r) { if (!r.ok) throw new Error('No se pudo simular ' + btn.dataset.sim + '.'); return r.json(); })
        .then(function (d) {
          var evs = d.events || [];
          if (!evs.length) throw new Error('La simulación no produjo mensajes.');
          evs.forEach(function (ev) { C.insert(all, seen, ev); });
          extraRuns[evs[0].run] = { run: evs[0].run, simulated: true };
          S.run = evs[0].run; S.task = S.node = S.edge = ''; S.cats = {};
          setMode('replay'); setSpeed(20); $('flow-play').click();
        })
        .catch(function (err) { $('fl-now').textContent = err.message; })
        .then(function () { btn.disabled = false; });
    });
  }

  // ---- data
  function absorb(d) {
    (d.events || []).forEach(function (ev) { C.insert(all, seen, ev); });
    (d.digests || []).forEach(function (g) { digests[g.seq] = g; });
    if (d.runs) runs = d.runs;
  }
  var runsTimer = null;
  function refreshRuns(delay) {
    clearTimeout(runsTimer);
    runsTimer = setTimeout(function () {
      fetch('/api/flow/runs?scope=' + encodeURIComponent(scope)).then(function (r) { return r.json(); })
        .then(function (d) { runs = d.runs || runs; soon(); }).catch(function () {});
    }, delay);
  }
  var TASK_KINDS = { task_state: 1, state_change: 1, verdict: 1, assignment: 1, recommendation: 1, run_paused: 1, run_resumed: 1, run_created: 1 };
  function follow() {
    if (!window.EventSource || staticPage) return;
    var lastOrd = all.length ? all[all.length - 1].ord : '0';    // '0': nothing yet, so whatever arrived since the fetch
    var es = new EventSource('/live?scope=' + encodeURIComponent(scope) + '&last=' + encodeURIComponent(lastOrd));
    es.addEventListener('now', function (m) { if (window.liveNow) window.liveNow(m); });
    es.addEventListener('flow', function (m) {
      var ev = JSON.parse(m.data);
      if (!C.insert(all, seen, ev)) return;
      if (S.mode === 'live') { flash(ev); soon(); }
      if (TASK_KINDS[ev.kind]) refreshRuns(1500);
    });
    es.addEventListener('digest', function (m) {
      var g = JSON.parse(m.data), before = digests[g.seq];
      digests[g.seq] = g;
      if (S.mode !== 'live' || g.run !== S.run) return;
      // the provider's raw stream is folded away unless «Mostrar detalle» is on, so it must not animate the map either
      if (S.detail && before && g.stream > before.stream) flash({ run: g.run, task: g.task, attempt: g.attempt, from: 'M3', to: 'M4', kind: 'digest', data: {} });
      soon();                                           // the sign of life moves the "última señal" clock
    });
  }
  function start() {
    drawMap(); wire();
    if (reduced) S.paused = true;
    var pick = scope.match(/^(run|task|subplan):([^/]+\/[^/]+)(?:\/(.+))?$/);
    fetch('/api/flow?scope=' + encodeURIComponent(scope) + '&limit=5000').then(function (r) { return r.json(); })
      .then(function (d) {
        absorb(d);
        if (pick) { S.run = pick[2]; S.task = pick[1] === 'task' ? pick[3] || '' : ''; if (S.task) S.tab = 'trace'; }
        setMode('live');
        refreshDoing();
        if (q.get('simulate') === '1') $('flow-sim').click();
        if (q.get('replay') === '1') {
          setMode('replay');
          if (+q.get('speed')) setSpeed(+q.get('speed'));
          if (q.get('autoplay') === '1') $('flow-play').click();
        }
        follow();
      })
      .catch(function () { $('fl-runs').innerHTML = '<p class="muted">No se pudo leer el flujo. Recarga la página.</p>'; });
    setInterval(function () { if (S.mode === 'live') refreshRuns(0); }, 15000);
    setInterval(function () { if (S.mode === 'live') soon(); }, 5000);   // "hace N s" keeps counting
    setInterval(function () { if (S.mode === 'live') refreshDoing(); }, 3000);
    requestAnimationFrame(frame);
  }
  start();
})();
