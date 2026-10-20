// Pure logic of the /flow page: no DOM, no timers. flow.js draws; this decides. Loaded in the browser (window.FlowCore)
// and in node (module.exports) so it can be tested without a browser.
(function (root) {
  'use strict';
  var NODES = ['agent', 'planner', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'owner'];
  var MAX_PARTICLES = 30;   // simultaneous particles on screen
  var FEED_ROWS = 80;       // grouped rows the message list shows

  // message kind -> category (the page maps categories to theme tokens)
  var KIND_CAT = {
    planning: 'plan', run_created: 'plan', route_map: 'plan', assignment: 'plan', reserved: 'plan',
    reservation_released: 'plan', reservation_refused: 'plan', amendment: 'plan', run_rebased: 'plan',
    start_order: 'run', dispatch_ack: 'run', execution_started: 'run', execution_finished: 'run', executor_event: 'run',
    cancel_order: 'run', dispatch_voided: 'run', reconciled: 'run', reconcile_redeliver: 'run', lease_expired: 'run',
    delivery_abandoned: 'run', verify_order: 'verify', verdict: 'verify', recommendation: 'recover', recovery: 'recover',
    manual_resolution: 'recover', state_change: 'state', task_state: 'state', run_paused: 'state', run_resumed: 'state',
    run_cancelled: 'state', housekeeping: 'state', incident: 'warn', incident_detected: 'warn',
    observation_ignored: 'warn', port_error: 'warn', port_invalid: 'warn', unknown: 'bad', dispatch_rejected: 'bad',
    message_rejected: 'bad', stream: 'stream', digest: 'stream'
  };
  var CATEGORIES = [['plan', 'plan y asignación'], ['run', 'ejecución'], ['verify', 'verificación'],
    ['recover', 'recuperación'], ['state', 'estados'], ['warn', 'avisos'], ['bad', 'fallos y bloqueos']];
  // what a person reads instead of the internal kind name
  var KIND_LABEL = {
    planning: 'planea', run_created: 'crea la ejecución', route_map: 'mapa de rutas', assignment: 'asignación',
    reserved: 'reserva', reservation_released: 'libera la reserva', reservation_refused: 'no puede reservar',
    amendment: 'enmienda', run_rebased: 'nueva revisión', start_order: 'orden de inicio', dispatch_ack: 'acepta la orden',
    execution_started: 'empieza a ejecutar', execution_finished: 'termina de ejecutar', executor_event: 'evento del ejecutor',
    cancel_order: 'cancela', dispatch_voided: 'anula la orden', reconciled: 'reconcilia', reconcile_redeliver: 'reenvía',
    lease_expired: 'vence el permiso', delivery_abandoned: 'abandona la entrega', verify_order: 'pide verificar',
    verdict: 'veredicto', recommendation: 'recomendación', recovery: 'recuperación', manual_resolution: 'resolución manual',
    state_change: 'estado del intento', task_state: 'estado de la tarea', run_paused: 'pausa', run_resumed: 'reanuda',
    run_cancelled: 'cancela la ejecución', housekeeping: 'mantenimiento', incident: 'incidente',
    incident_detected: 'detecta incidente', observation_ignored: 'ignora una observación', port_error: 'error de puerto',
    port_invalid: 'respuesta inválida', unknown: 'sin regla', dispatch_rejected: 'rechaza la orden',
    message_rejected: 'rechaza un mensaje', stream: 'flujo del proveedor', digest: 'detalle del proveedor'
  };

  function category(ev) {
    var d = ev.data || {};
    if (ev.kind === 'verdict' && /fail|reject/i.test(d.status || ev.summary || '')) return 'bad';
    if (ev.kind === 'recommendation' && /block/i.test(d.action || '')) return 'bad';
    if (ev.kind === 'state_change' && /^(failed|rejected)$/.test(d.state || '')) return 'bad';
    return KIND_CAT[ev.kind] || 'state';
  }
  function kindClass(ev) { return 'k-' + category(ev); }
  function label(kind) { return KIND_LABEL[kind] || kind; }
  function edgeKey(ev) { return ev.from + '>' + ev.to; }

  // plan-status task state -> what the strip shows
  var TASK_STATE = { completed: 'done', running: 'running', verifying: 'running', rejected: 'retry', blocked: 'blocked',
    cancelled: 'pending', pending: 'pending', ready: 'pending' };
  var TASK_CLASS = { done: 'k-verify', running: 'k-run', retry: 'k-recover', blocked: 'k-bad', pending: 'k-state' };
  function taskState(state) { return TASK_STATE[state] || 'pending'; }

  // filters: {run, task, cats: {plan: true…}, node, edge}; empty means "any"
  function anyCat(f) { return !!f.cats && Object.keys(f.cats).some(function (k) { return f.cats[k]; }); }
  function matches(ev, f, skipCats) {
    f = f || {};
    return (!f.run || ev.run === f.run) && (!f.task || ev.task === f.task) &&
      (skipCats || !anyCat(f) || !!f.cats[category(ev)]) &&
      (!f.node || ev.from === f.node || ev.to === f.node) && (!f.edge || edgeKey(ev) === f.edge);
  }

  // Counts for the map: per edge (with its categories), per node, and messages a module sends itself (loops).
  // `digests` add the folded provider detail when the reader asked to see it.
  function tally(events, digests) {
    var out = { edges: {}, nodes: {}, loops: {}, total: 0 };
    function add(from, to, cat, n, at) {
      out.total += n;
      if (from === to) out.loops[from] = (out.loops[from] || 0) + n;
      else {
        var e = out.edges[from + '>' + to] || (out.edges[from + '>' + to] = { count: 0, cats: {}, last: 0 });
        e.count += n; e.last = Math.max(e.last, at || 0); e.cats[cat] = (e.cats[cat] || 0) + n;
      }
      [from, to].forEach(function (id) {
        var node = out.nodes[id] || (out.nodes[id] = { count: 0, last: 0 });
        node.count += n; node.last = Math.max(node.last, at || 0);
      });
    }
    events.forEach(function (ev) { add(ev.from, ev.to, category(ev), 1, ev.at_epoch); });
    (digests || []).forEach(function (d) {
      if (d.stream) add('M3', 'M4', 'stream', d.stream, d.at_epoch);
      if (d.incidents) add('M4', 'M1', 'stream', d.incidents, d.at_epoch);
    });
    return out;
  }
  function dominant(cats) {
    var best = '', n = -1;
    Object.keys(cats).forEach(function (k) { if (cats[k] > n) { n = cats[k]; best = k; } });
    return best;
  }

  // Message rows, newest first: consecutive identical messages become one row with ×n and a time range.
  function groupRows(events) {
    var rows = [];
    for (var i = events.length - 1; i >= 0 && rows.length <= FEED_ROWS; i--) {
      var ev = events[i], top = rows[rows.length - 1];
      if (top && top.ev.from === ev.from && top.ev.to === ev.to && top.ev.kind === ev.kind && top.ev.summary === ev.summary &&
          top.ev.run === ev.run) {
        top.n += 1; top.first = ev.at_epoch; continue;
      }
      rows.push({ ev: ev, n: 1, first: ev.at_epoch, last: ev.at_epoch });
    }
    return rows.slice(0, FEED_ROWS);
  }

  // A task's attempts, oldest first, each with its own messages. `history` (plan-status, the authority) gives the
  // attempts; messages without an attempt (the assignment that precedes one) join the next attempt to start.
  function attempts(events, task, history) {
    var mine = events.filter(function (e) { return e.task === task; });
    var blocks = (history || []).map(function (a) {
      return { id: a.id, number: a.number, state: a.state, attempt: a, start: Date.parse(a.started_at || '') / 1000 || null, steps: [] };
    });
    if (!blocks.length) {                               // no plan behind it (a simulation): attempts from the messages
      var seen = {};
      mine.forEach(function (e) {
        if (e.attempt && !seen[e.attempt]) { seen[e.attempt] = { id: e.attempt, number: blocks.length + 1, state: '', attempt: null, start: e.at_epoch, steps: [] }; blocks.push(seen[e.attempt]); }
      });
    }
    var byId = {};
    blocks.forEach(function (b) { byId[b.id] = b; });
    var loose = { id: '', number: 0, state: '', attempt: null, start: null, steps: [] };
    mine.forEach(function (e) {
      var home = e.attempt && byId[e.attempt];
      if (!home) {
        home = blocks.filter(function (b) { return b.start === null || b.start >= e.at_epoch - 1; })[0] || blocks[blocks.length - 1] || loose;
      }
      home.steps.push(e);
    });
    if (loose.steps.length) blocks.unshift(loose);
    return blocks;
  }

  // Replay: real gaps (a run idle for an hour) would make a replay unwatchable, so replay time is VIRTUAL: each gap
  // between consecutive events counts at most GAP_CAP seconds. `at_epoch` is never changed.
  var GAP_CAP = 2;
  function virtualize(events) {
    var vt = 0, out = [];
    for (var i = 0; i < events.length; i++) {
      if (i) vt += Math.min(GAP_CAP, Math.max(0, events[i].at_epoch - events[i - 1].at_epoch));
      out.push(vt);
    }
    return out;
  }
  function span(events) {
    var v = virtualize(events);
    return { length: v.length ? v[v.length - 1] : 0, real: events.length ? events[events.length - 1].at_epoch - events[0].at_epoch : 0 };
  }
  function upTo(events, t) {
    var v = virtualize(events), out = [];
    for (var i = 0; i < events.length && v[i] <= t; i++) out.push(events[i]);
    return out;
  }

  // Particle bookkeeping: add one per event, drop the finished, never exceed MAX_PARTICLES (oldest dropped first).
  function spawn(particles, ev, now, duration) {
    particles.push({ key: edgeKey(ev), cls: kindClass(ev), born: now, life: duration || 900 });
    if (particles.length > MAX_PARTICLES) particles.splice(0, particles.length - MAX_PARTICLES);
    return particles;
  }
  function alive(particles, now) {
    return particles.filter(function (p) { return now - p.born < p.life; });
  }

  // Who is working right now in a run, from plan-status (the authority) and the provider's latest sign of life:
  // [{node, verb, task, attempt, since, last, edges, quiet}] — one per live attempt, or the core itself when waiting.
  var STAGE = {
    reserved: ['M1', 'reserva un ejecutor para', [['M1', 'M2']]],
    dispatched: ['M3', 'está arrancando', [['M1', 'M3']]],
    running: ['M3', 'está ejecutando', [['M1', 'M3'], ['M3', 'M4']]],
    uncertain: ['M3', 'se está reconciliando con', [['M1', 'M3'], ['M3', 'M1']]],
    verifying: ['M6', 'está verificando', [['M1', 'M6'], ['M6', 'M1']]]
  };
  var QUIET_AFTER = 300;    // seconds without a sign of life before "working" reads as "no signs"
  function epochOf(iso) { var t = Date.parse(iso || ''); return isNaN(t) ? 0 : t / 1000; }
  function activity(run, digests, now) {
    if (!run || !run.tasks) return [];
    var out = [];
    run.tasks.forEach(function (t) {
      var a = t.attempt;
      if (a && a.live) {
        var st = STAGE[a.state] || ['M3', 'trabaja en', [['M1', 'M3']]], last = epochOf(a.last_activity_at);
        (digests || []).forEach(function (d) { if (d.attempt === a.id) last = Math.max(last, d.at_epoch || 0); });
        out.push({ node: st[0], verb: st[1], task: t.id, attempt: a, since: epochOf(a.started_at), last: last,
          edges: st[2], quiet: !!last && now - last > QUIET_AFTER });
      } else if (t.state === 'rejected') {
        out.push({ node: 'M5', verb: 'decide cómo recuperar', task: t.id, attempt: null, since: 0, last: 0, edges: [['M5', 'M1']], quiet: false });
      }
    });
    if (!out.length && run.active) {
      out.push({ node: 'M1', verb: run.status === 'paused' ? 'tiene la ejecución en pausa' : 'espera para despachar la siguiente tarea',
        task: '', attempt: null, since: 0, last: 0, edges: [], quiet: false });
    }
    return out;
  }

  // Insert one live message into a list kept sorted by `ord`, ignoring one already there (a reconnect replays).
  function insert(list, seen, ev) {
    var id = (ev.run || '') + '|' + ev.seq;
    if (seen[id]) return false;
    seen[id] = true;
    var i = list.length;
    while (i > 0 && list[i - 1].ord > ev.ord) i--;
    list.splice(i, 0, ev);
    return true;
  }

  var api = { NODES: NODES, MAX_PARTICLES: MAX_PARTICLES, FEED_ROWS: FEED_ROWS, CATEGORIES: CATEGORIES,
    category: category, kindClass: kindClass, label: label, edgeKey: edgeKey, taskState: taskState, TASK_CLASS: TASK_CLASS,
    matches: matches, anyCat: anyCat, tally: tally, dominant: dominant, groupRows: groupRows, attempts: attempts,
    span: span, upTo: upTo, virtualize: virtualize, GAP_CAP: GAP_CAP, spawn: spawn, alive: alive, insert: insert,
    activity: activity, QUIET_AFTER: QUIET_AFTER };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.FlowCore = api;
})(typeof window !== 'undefined' ? window : this);
