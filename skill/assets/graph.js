// Trace graph view: Cytoscape over the JSON embedded in #graph-data.
(function () {
  const raw = document.getElementById('graph-data');
  if (!raw || !window.cytoscape) return;
  const data = JSON.parse(raw.textContent);
  const css = getComputedStyle(document.documentElement);
  const color = (t) => css.getPropertyValue('--g-' + t).trim() || '#888';
  const project = data.project;

  const elements = [
    ...data.nodes.map((n) => ({ data: { ...n, short: n.type === 'F' ? n.label.split('/').pop() : n.id.split('/').pop() } })),
    ...data.edges.map((e, i) => ({ data: { id: 'e' + i, ...e } })),
  ];
  const cy = cytoscape({
    container: document.getElementById('graph'),
    elements,
    wheelSensitivity: 0.2,
    style: [
      { selector: 'node', style: {
        'background-color': (n) => color(n.data('type')), label: 'data(short)', 'font-size': 9,
        color: css.getPropertyValue('--text').trim(), 'text-valign': 'bottom', 'text-margin-y': 3,
        width: (n) => ({ REQ: 26, D: 18, P: 16, T: 14, R: 12, US: 12, C: 10, F: 8 }[n.data('type')] || 12),
        height: (n) => ({ REQ: 26, D: 18, P: 16, T: 14, R: 12, US: 12, C: 10, F: 8 }[n.data('type')] || 12),
        'border-width': (n) => (n.data('undefined') ? 2 : 0), 'border-color': '#d33' } },
      { selector: 'edge', style: {
        width: 1, 'line-color': css.getPropertyValue('--border').trim(), 'curve-style': 'bezier',
        'target-arrow-shape': 'triangle', 'arrow-scale': 0.6,
        'target-arrow-color': css.getPropertyValue('--border').trim(),
        'line-style': (e) => (e.data('type') === 'mentions' ? 'dashed' : 'solid') } },
      { selector: '.faded', style: { opacity: 0.12 } },
      { selector: 'node:selected', style: { 'border-width': 3, 'border-color': css.getPropertyValue('--accent').trim() } },
    ],
    layout: { name: 'cose', animate: false, nodeRepulsion: 9000, idealEdgeLength: 60 },
  });

  const hidden = new Set(['F', 'C']);
  function applyFilters() {
    cy.batch(() => cy.nodes().forEach((n) => n.style('display', hidden.has(n.data('type')) ? 'none' : 'element')));
  }
  document.querySelectorAll('[data-type-toggle]').forEach((box) => {
    box.checked = !hidden.has(box.dataset.typeToggle);
    box.addEventListener('change', () => {
      box.checked ? hidden.delete(box.dataset.typeToggle) : hidden.add(box.dataset.typeToggle);
      applyFilters();
    });
  });
  applyFilters();

  function focus(id) {
    const n = cy.getElementById(id);
    if (!n.length) return;
    const hood = n.closedNeighborhood().closedNeighborhood();
    cy.elements().addClass('faded');
    hood.removeClass('faded');
    cy.animate({ fit: { eles: hood, padding: 40 } }, { duration: 300 });
    n.select();
    show(n.data());
  }
  function link(d) {
    if (d.type === 'REQ') return `/p/${project}/req/${d.id}`;
    if (['US', 'R', 'T'].includes(d.type)) return `/p/${project}/req/${d.req}?tab=trace`;
    if (d.type === 'D') return `/p/${project}?tab=decisions`;
    if (d.type === 'P') return `/p/${project}?tab=pending`;
    return '';
  }
  function show(d) {
    const panel = document.getElementById('node-info');
    const skip = new Set(['id', 'label', 'short', 'type']);
    const rows = Object.entries(d).filter(([k]) => !skip.has(k))
      .map(([k, v]) => `<tr><th>${k}</th><td>${Array.isArray(v) ? v.join('<br>') : v}</td></tr>`).join('');
    const href = link(d);
    panel.innerHTML = `<h3>${d.label}</h3><p class="muted">${d.type}${href ? ` · <a href="${href}">abrir</a>` : ''}</p>` +
      `<table>${rows}</table>`;
  }
  cy.on('tap', 'node', (ev) => focus(ev.target.id()));
  cy.on('tap', (ev) => { if (ev.target === cy) cy.elements().removeClass('faded'); });

  document.getElementById('graph-search').addEventListener('change', (ev) => {
    const q = ev.target.value.trim().toLowerCase();
    if (!q) return cy.elements().removeClass('faded');
    const hit = cy.nodes().filter((n) => n.id().toLowerCase() === q || n.data('label').toLowerCase().includes(q));
    if (hit.length) {
      if (hidden.has(hit[0].data('type'))) { hidden.delete(hit[0].data('type')); applyFilters(); }
      focus(hit[0].id());
    }
  });
  document.querySelectorAll('[data-focus]').forEach((a) => a.addEventListener('click', (ev) => {
    ev.preventDefault(); focus(a.dataset.focus);
  }));
})();
