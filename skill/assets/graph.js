// Trace graph view: Cytoscape over the JSON embedded in #graph-data.
(function () {
  const raw = document.getElementById('graph-data');
  if (!raw || !window.cytoscape) return;
  const data = JSON.parse(raw.textContent);
  const css = getComputedStyle(document.documentElement);
  const v = (name, fallback) => css.getPropertyValue(name).trim() || fallback;
  const color = (t) => v('--g-' + t, '#888');
  const project = data.project;

  const SHAPE = { REQ: 'hexagon', US: 'round-rectangle', R: 'ellipse', T: 'ellipse', D: 'diamond', P: 'tag',
                  C: 'round-rectangle', F: 'rectangle' };
  const BASE = { REQ: 34, US: 18, R: 16, T: 18, D: 24, P: 20, C: 12, F: 9 };
  const EDGE = { covers: '--g-T', plans: '--g-REQ', defines: '--g-R', supersedes: '--danger', refs: '--g-C',
                 touches: '--g-F', mentions: '--muted' };
  const TYPE_NAME = { REQ: 'Requerimiento', US: 'Historia', R: 'Requisito', T: 'Tarea', D: 'Decisión',
                      P: 'Pendiente', C: 'Commit', F: 'Archivo' };

  // degree → size, so hubs stand out
  const degree = {};
  data.edges.forEach((e) => { degree[e.source] = (degree[e.source] || 0) + 1; degree[e.target] = (degree[e.target] || 0) + 1; });

  // deterministic starting positions (hash of the id, rings by type): the same graph always lands the same way
  const hash = (s) => { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };
  const ring = { REQ: 0, US: 1, R: 1, T: 2, D: 3, P: 3, C: 4, F: 5 };
  const place = (n) => {
    const h = hash(n.id), a = (h % 3600) / 3600 * 2 * Math.PI, r = 80 + (ring[n.type] ?? 3) * 110 + (h % 40);
    return { x: Math.cos(a) * r, y: Math.sin(a) * r };
  };
  const short = (n) => (n.type === 'F' ? n.label.split('/').pop() : n.id.split('/').pop());
  const status = (n) => (n.status || n.section || '').toLowerCase();

  const elements = [
    ...data.nodes.map((n) => ({
      data: { ...n, short: short(n), size: (BASE[n.type] || 14) + Math.min(14, (degree[n.id] || 0) * 1.6),
              // neighbors show "ID + a few words"; only the focused node shows the full title
              mid: (() => { const rest = n.label.replace(n.id, '').replace(short(n), '').replace(/^[\s—–:-]+/, '');
                            return short(n) + (rest && n.type !== 'F' ? ' · ' + (rest.length > 22 ? rest.slice(0, 21) + '…' : rest) : ''); })() },
      position: place(n),
      classes: [n.undefined && 'undefined', n.done && 'done', /superseded/.test(status(n)) && 'superseded',
                /done|merged|closed/.test(status(n)) && 'done'].filter(Boolean).join(' '),
    })),
    ...data.edges.map((e, i) => ({ data: { id: 'e' + i, ...e } })),
  ];

  const text = v('--text', '#eee'), bg = v('--surface', '#1f1f1d'), accent = v('--accent', '#fb923c');
  const cy = cytoscape({
    container: document.getElementById('graph'),
    elements,
    wheelSensitivity: 0.25,
    minZoom: 0.2,
    maxZoom: 3,
    style: [
      { selector: 'node', style: {
        shape: (n) => SHAPE[n.data('type')] || 'ellipse',
        width: 'data(size)', height: 'data(size)',
        'background-color': (n) => color(n.data('type')),
        'background-opacity': 0.92,
        'border-width': 2, 'border-color': bg, 'border-opacity': 0.9,
        label: 'data(short)', 'font-size': 10, 'font-weight': 600, color: text,
        'text-valign': 'bottom', 'text-margin-y': 5,
        'text-outline-color': bg, 'text-outline-width': 3, 'text-outline-opacity': 0.9,
        'min-zoomed-font-size': 7,
        'underlay-color': (n) => color(n.data('type')), 'underlay-padding': 0, 'underlay-opacity': 0,
        'underlay-shape': 'ellipse',
        'transition-property': 'opacity, underlay-opacity, underlay-padding, border-width, width, height',
        'transition-duration': '180ms' } },
      { selector: 'node.done', style: { 'border-color': v('--ok', '#4ade80'), 'border-width': 3 } },
      { selector: 'node.undefined', style: { 'border-color': v('--danger', '#ef4444'), 'border-style': 'dashed',
        'border-width': 3, 'background-opacity': 0.35 } },
      { selector: 'node.superseded', style: { 'background-opacity': 0.35, 'border-style': 'dotted' } },
      { selector: 'edge', style: {
        width: 1.4, 'curve-style': 'bezier', 'line-color': (e) => v(EDGE[e.data('type')] || '--muted', '#777'),
        'line-opacity': 0.35, 'target-arrow-shape': (e) => (e.data('type') === 'mentions' ? 'none' : 'triangle'),
        'target-arrow-color': (e) => v(EDGE[e.data('type')] || '--muted', '#777'), 'arrow-scale': 0.7,
        'line-style': (e) => (e.data('type') === 'mentions' ? 'dotted' : e.data('type') === 'supersedes' ? 'dashed' : 'solid'),
        'transition-property': 'opacity, line-opacity, width', 'transition-duration': '180ms' } },
      // focus states
      { selector: '.faded', style: { opacity: 0.1 } },
      { selector: 'node.hl', style: { 'underlay-opacity': 0.3, 'underlay-padding': 8, label: 'data(mid)',
        'font-size': 10.5, 'text-max-width': 150, 'text-wrap': 'ellipsis', 'z-index': 10 } },
      { selector: 'edge.hl', style: { 'line-opacity': 0.95, width: 2.6, 'z-index': 9 } },
      { selector: 'node.focus', style: { 'underlay-opacity': 0.5, 'underlay-padding': 13, 'border-color': accent,
        'border-width': 4, label: 'data(label)', 'font-size': 12.5, 'text-wrap': 'wrap', 'text-max-width': 230,
        'text-background-color': bg, 'text-background-opacity': 0.85, 'text-background-padding': 4,
        'text-background-shape': 'round-rectangle', 'text-outline-width': 0, 'z-index': 20 } },
    ],
    layout: { name: 'cose', animate: false, randomize: false, nodeRepulsion: 40000, idealEdgeLength: 95,
              nodeOverlap: 24, gravity: 0.6, numIter: 1500 },
  });

  // ---------------------------------------------------------------- filters
  const hidden = new Set(['F', 'C']);
  function applyFilters() {
    cy.batch(() => cy.nodes().forEach((n) => n.style('display', hidden.has(n.data('type')) ? 'none' : 'element')));
  }
  document.querySelectorAll('[data-type-toggle]').forEach((box) => {
    box.checked = !hidden.has(box.dataset.typeToggle);
    box.closest('label').classList.toggle('off', !box.checked);
    box.addEventListener('change', () => {
      box.checked ? hidden.delete(box.dataset.typeToggle) : hidden.add(box.dataset.typeToggle);
      box.closest('label').classList.toggle('off', !box.checked);
      applyFilters();
    });
  });
  applyFilters();

  // ---------------------------------------------------------------- highlight
  let focused = null;
  function highlight(n, keep) {
    cy.batch(() => {
      cy.elements().removeClass('hl').addClass('faded');
      const hood = n.closedNeighborhood();
      hood.removeClass('faded').addClass('hl');
      if (keep) cy.elements('.focus').removeClass('focus');
      n.addClass('focus');
    });
  }
  function clear() {
    cy.batch(() => cy.elements().removeClass('faded hl focus'));
    focused = null;
  }
  cy.on('mouseover', 'node', (ev) => { if (!focused) highlight(ev.target); document.body.style.cursor = 'pointer'; });
  cy.on('mouseout', 'node', (ev) => {
    document.body.style.cursor = '';
    if (!focused) { ev.target.removeClass('focus'); clear(); }
  });
  cy.on('tap', 'node', (ev) => focus(ev.target.id()));
  cy.on('tap', (ev) => { if (ev.target === cy) { clear(); showEmpty(); } });

  // gentle pulse on the focused node
  let pulseUp = true;
  setInterval(() => {
    if (!focused) return;
    const n = cy.getElementById(focused);
    n.style('underlay-padding', pulseUp ? 16 : 10);
    pulseUp = !pulseUp;
  }, 700);

  function focus(id) {
    const n = cy.getElementById(id);
    if (!n.length) return;
    if (hidden.has(n.data('type'))) { hidden.delete(n.data('type')); syncToggles(); applyFilters(); }
    focused = id;
    highlight(n, true);
    cy.animate({ fit: { eles: n.closedNeighborhood(), padding: 70 } }, { duration: 350, easing: 'ease-out-cubic' });
    show(n);
  }
  function syncToggles() {
    document.querySelectorAll('[data-type-toggle]').forEach((b) => {
      b.checked = !hidden.has(b.dataset.typeToggle);
      b.closest('label').classList.toggle('off', !b.checked);
    });
  }

  // ---------------------------------------------------------------- side panel
  function link(d) {
    if (d.type === 'REQ') return `/p/${project}/req/${d.id}`;
    if (['US', 'R', 'T'].includes(d.type)) return `/p/${project}/req/${d.req}?tab=trace`;
    if (d.type === 'D') return `/p/${project}?tab=decisions`;
    if (d.type === 'P') return `/p/${project}?tab=pending`;
    return '';
  }
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function show(n) {
    const d = n.data();
    const panel = document.getElementById('node-info');
    const chips = [d.status, d.section, d.date, d.repo, d.done ? 'hecha' : ''].filter(Boolean)
      .map((s) => `<span class="badge ${esc(String(s).toLowerCase())}">${esc(s)}</span>`).join(' ');
    const conns = n.connectedEdges().map((e) => {
      const other = e.source().id() === d.id ? e.target() : e.source();
      const dir = e.source().id() === d.id ? '→' : '←';
      return `<li><a href="#" data-goto="${esc(other.id())}"><span class="dot" style="background:${color(other.data('type'))}"></span>` +
        `${esc(other.data('short'))}</a> <span class="muted">${dir} ${esc(e.data('type'))}</span></li>`;
    }).join('');
    const where = (d.mentioned_in || []).map((f) => `<li class="muted">${esc(f)}</li>`).join('');
    const href = link(d);
    panel.innerHTML =
      `<div class="node-type" style="--c:${color(d.type)}">${TYPE_NAME[d.type] || d.type}</div>` +
      `<h3>${esc(d.label)}</h3><div class="chips">${chips}</div>` +
      (href ? `<p><a class="open-link" href="${href}">Abrir →</a></p>` : '') +
      `<h4>Conexiones (${n.connectedEdges().length})</h4><ul class="plain conns">${conns || '<li class="muted">Ninguna</li>'}</ul>` +
      (where ? `<h4>Mencionado en</h4><ul class="plain">${where}</ul>` : '');
    panel.querySelectorAll('[data-goto]').forEach((a) => a.addEventListener('click', (ev) => {
      ev.preventDefault(); focus(a.dataset.goto);
    }));
  }
  function showEmpty() {
    document.getElementById('node-info').innerHTML =
      '<p class="muted">Pasa el mouse por un nodo para ver su vecindario; haz clic para fijarlo.</p>';
  }

  // ---------------------------------------------------------------- search & controls
  document.getElementById('graph-search').addEventListener('keydown', (ev) => {
    if (ev.key !== 'Enter') return;
    const q = ev.target.value.trim().toLowerCase();
    if (!q) return clear();
    const hit = cy.nodes().filter((n) => n.id().toLowerCase() === q || n.data('label').toLowerCase().includes(q));
    if (hit.length) focus(hit[0].id());
  });
  document.querySelectorAll('[data-focus]').forEach((a) => a.addEventListener('click', (ev) => {
    ev.preventDefault(); focus(a.dataset.focus);
    document.getElementById('graph').scrollIntoView({ behavior: 'smooth', block: 'center' });
  }));
  const zoomBy = (f) => cy.animate({ zoom: { level: cy.zoom() * f, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } } },
    { duration: 200 });
  document.getElementById('zoom-in').onclick = () => zoomBy(1.3);
  document.getElementById('zoom-out').onclick = () => zoomBy(1 / 1.3);
  document.getElementById('zoom-fit').onclick = () => { clear(); showEmpty(); cy.animate({ fit: { padding: 40 } }, { duration: 300 }); };
  // the canvas can change size after the first layout (fonts, phone rotation): measure again and fit the whole graph
  let fitTimer = null;
  const refit = () => { clearTimeout(fitTimer); fitTimer = setTimeout(() => { cy.resize(); if (!initialFocus) cy.fit(undefined, 40); }, 120); };
  window.addEventListener('resize', refit);
  refit();
  window.addEventListener('load', refit);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(refit);
  if (window.ResizeObserver) new ResizeObserver(refit).observe(document.getElementById('cy') || document.body);
  if (/[?&]probe=1\b/.test(location.search)) setTimeout(() => {
    document.documentElement.dataset.cy = [cy.width(), cy.height(), cy.zoom().toFixed(2), JSON.stringify(cy.pan()), JSON.stringify(cy.extent())].join(' ');
  }, 1500);
  showEmpty();
  // deep link: /p/<project>/graph?focus=REQ-004 opens the graph focused on that node
  const initial = new URLSearchParams(location.search).get('focus');
  const initialFocus = !!initial;
  if (initial) setTimeout(() => focus(initial), 60);
})();
