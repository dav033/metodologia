// Owner actions for open Scheduler decisions shown by the selected /flow run.
(function () {
  'use strict';
  var root = document.getElementById('flow'), box = document.getElementById('fl-decisions');
  if (!root || !box) return;
  var token = root.dataset.token || '', selected = '', requestNo = 0, pollTimer = 0;
  var NEEDS_REASON = { retry_with_note: true, review_pass: true, review_fail: true, rework_findings: true };

  function $(selector) { return box.querySelector(selector); }
  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function runKey() {
    var active = root.querySelector('.fl-run[aria-pressed="true"]');
    var run = active ? active.dataset.run : '';
    var match = /^(?:run|task):([^/]+\/REQ-\d+)(?:\/.*)?$/.exec(root.dataset.scope || '');
    return run || (match && match[1]) || '';
  }
  function taskKey() {
    var active = root.querySelector('.fl-task[aria-pressed="true"]');
    return active ? active.dataset.task : '';
  }
  function proposalForm(item, project, req) {
    var data = item.proposalData;
    if (!data) return '<p role="status">No se pudo verificar la propuesta. Recarga la página.</p>';
    function candidate(entry, type) {
      var id = type === 'backings' ? entry.id : entry.tipo;
      var dimensions = type === 'backings' ? entry.medidasCm : entry.partidaCm;
      var size = ['ancho', 'fondo', 'alto'].map(function (key) {
        return key + ': ' + (dimensions[key] == null ? '—' : dimensions[key]) + ' cm';
      }).join(', ');
      var sources = (entry.fuentes || []).map(function (source) {
        var url = source.url || '', label = source.nota || source.rutaFoto || url;
        return /^https?:\/\//i.test(url) ? '<a href="' + esc(url) + '" target="_blank" rel="noopener">' + esc(label) + '</a>' : esc(label);
      }).join('; ');
      var limits = entry.limitesCm ? '<p><b>Rango:</b> ' + ['ancho', 'fondo', 'alto'].map(function (key) {
        var range = entry.limitesCm[key]; return key + ' ' + (range ? range.join('–') + ' cm' : '—');
      }).join(', ') + '</p>' : '';
      var shapes = (entry.geometria || []).filter(function (shape) { return shape.forma === 'nueva'; }).map(function (shape) {
        return '<p><b>Forma nueva:</b> ' + esc(shape.nombreForma) + ' · ' + esc(shape.descripcion) + ' · ' +
          esc(shape.porQueNoBasta) + ' · parámetros: ' + esc((shape.parametros || []).map(function (p) { return p.nombre + ' (' + p.unidad + ')'; }).join(', ')) + ' · ' + esc(shape.estimacionMin) + ' min</p>';
      }).join('');
      var chairs = entry.reglaSillas ? '<p><b>Sillas:</b> ' + esc(entry.reglaSillas.lados.join(', ')) + ' · capacidad inicial ' +
        esc(entry.reglaSillas.capacidadPartida) + '</p>' : '';
      var finishes = entry.acabados ? '<p><b>Acabados:</b> ' + esc(entry.acabados.join(', ')) + ' · <b>Colores:</b> ' +
        esc((entry.coloresHex || []).join(', ')) + ' · <b>Relevancia en fotos:</b> ' + esc(entry.relevanciaFoto) + '</p>' : '';
      var geometry = (entry.geometria || []).filter(function (shape) { return shape.forma !== 'nueva'; }).map(function (shape) {
        return esc(shape.forma + ': ' + shape.proposito);
      }).join('; ');
      var extra = geometry ? '<p><b>Geometría:</b> ' + geometry + '</p>' : '';
      if (entry.reglaSillas) extra += '<p><b>Camino de mesa:</b> ' + (entry.admiteCamino ? 'sí' : 'no') +
        ' · <b>Simétrica:</b> ' + (entry.simetrica ? 'sí' : 'no') + '</p>';
      return '<div class="fl-proposal-item"><label class="fl-proposal-choice"><input type="checkbox" name="' + type + '" value="' + esc(id) + '">' +
        '<span><strong>' + esc(entry.nombre.es) + '</strong><small>' + esc(entry.nombre.en) + ' · ' + esc(id) + ' · ' + esc(entry.estimacionMin) + ' min de trabajo estimado</small></span></label>' +
        '<div class="fl-proposal-details"><p>' + esc((entry.descripcion || {}).es || entry.contorno || '') + '</p>' +
        '<p><b>Medidas' + (entry.partidaCm ? ' iniciales' : '') + ':</b> ' + esc(size) + '</p>' + limits + chairs + finishes + extra + shapes +
        '<p><b>También se conoce como:</b> ' + esc((entry.sinonimos || []).join(', ')) + '</p>' +
        '<p><b>Fuentes:</b> ' + sources + '</p></div></div>';
    }
    return '<form class="fl-proposal" data-flow-proposal><input type="hidden" name="token" value="' + esc(token) + '">' +
      '<input type="hidden" name="project" value="' + esc(project) + '"><input type="hidden" name="req" value="' + esc(req) + '">' +
      '<input type="hidden" name="request" value="' + esc(item.id) + '"><input type="hidden" name="attempt" value="' + esc(data.attempt) + '">' +
      '<input type="hidden" name="sha256" value="' + esc(data.sha256) + '"><input type="hidden" name="option" value="owner_proposal">' +
      '<p>Selecciona hasta seis backings y tres mesas. Deja todo sin marcar para aprobar ninguno.</p>' +
      '<div class="fl-proposal-groups"><fieldset><legend>Backings · <span data-proposal-count="backings">0 de 6</span></legend>' + data.proposal.backings.map(function (e) { return candidate(e, 'backings'); }).join('') + '</fieldset>' +
      '<fieldset><legend>Mesas · <span data-proposal-count="mesas">0 de 3</span></legend>' + data.proposal.mesas.map(function (e) { return candidate(e, 'mesas'); }).join('') + '</fieldset></div>' +
      '<button type="submit" class="primary">Aprobar selección</button></form>';
  }
  function render(requests, project, req, task) {
    var visible = requests.filter(function (item) { return !task || item.task === task; });
    box.hidden = !visible.length;
    if (!visible.length) { box.innerHTML = ''; return; }
    box.innerHTML = '<h2>Decisiones pendientes</h2>' + visible.map(function (item) {
      var evidence = item.diagnosis_html ? '' : (item.evidence || []).slice(0, 8).map(function (line) { return '<li>' + esc(line) + '</li>'; }).join('');
      var review = window.FlowFailureLinks.decisionHref(project, req, item);
      var isProposal = project === 'pictures' && req === 'REQ-021' && item.task === 'T3.2' && item.source === 'review';
      var ordered = (item.options || []).filter(function (option) { return !isProposal || (option.id !== 'review_pass' && option.id !== 'review_fail'); }).sort(function (a, b) {
        return (b.id === item.recommended) - (a.id === item.recommended);
      });
      var options = ordered.map(function (option, index) {
        var recommended = option.id === item.recommended;
        var note = NEEDS_REASON[option.id] ? '<label class="fl-decision-reason">' +
          (option.id === 'retry_with_note' ? 'Indicación para el siguiente intento' : option.id === 'rework_findings' ? 'Hallazgos que deben arreglar (llegan a cada tarea)' : 'Razón de tu decisión') +
          '<textarea name="reason" required maxlength="4000" placeholder="Escribe tu indicación">' +
          (option.id === 'retry_with_note' ? esc(item.note_prefill || '') : '') + '</textarea></label>' : '';
        return '<form class="fl-decision-option" data-flow-decision>' +
          '<input type="hidden" name="token" value="' + esc(token) + '">' +
          '<input type="hidden" name="project" value="' + esc(project) + '">' +
          '<input type="hidden" name="req" value="' + esc(req) + '">' +
          '<input type="hidden" name="request" value="' + esc(item.id) + '">' +
          '<input type="hidden" name="option" value="' + esc(option.id) + '">' + note +
          '<button type="submit"' + (recommended ? ' class="primary"' : '') + '>' + esc(option.label) +
          (recommended ? ' (recomendada)' : '') + '</button><p>' + esc(option.consequence) + '</p></form>' +
          (index === 0 && ordered.length > 1 && recommended ? '<details class="dx-more"><summary>Otras opciones (' + (ordered.length - 1) + ')</summary>' : '') +
          (index === ordered.length - 1 && ordered.length > 1 && ordered[0].id === item.recommended ? '</details>' : '');
      }).join('');
      return '<article class="fl-decision" data-project="' + esc(project) + '" data-req="' + esc(req) + '"><h3>' +
        esc(String(item.title || '').split(':')[0]) + (item.reason ? ' <small class="fl-reason">· ' + esc(item.reason) + '</small>' : '') + '</h3>' +
        (isProposal ? '<p>Elige los candidatos aprobados para continuar la verificación.</p>' : (item.diagnosis_html || '<p>' + esc(item.what) + '</p>')) +
        (evidence ? '<ul>' + evidence + '</ul>' : '') +
        (review ? '<p><a class="fl-failure-link" href="' + esc(review) + '" target="_blank" rel="noopener">Abrir log del último intento</a></p>' : '') +
        (isProposal ? proposalForm(item, project, req) : '') +
        (item.manual ? '<p><a class="fl-manual-link primary" href="/plans/' + encodeURIComponent(project) + '/' +
          encodeURIComponent(req) + '#d-' + esc(item.id) + '">Probar esto: arrancar ' + esc(item.manual.task) +
          ' y responder Funciona / No funciona →</a></p>' : '') + options + '</article>';
    }).join('') + '<p class="fl-decision-status" role="status"></p>';
    clearTimeout(pollTimer);       // while an agent is diagnosing, refresh until its answer is on the card
    if (visible.some(function (item) { return item.agent && item.agent.state === 'running'; })) {
      pollTimer = setTimeout(function () { load(true); }, 5000);
    }
  }
  function load(force) {
    var run = runKey(), key = run + '|' + taskKey();
    if (!force && key === selected) return;
    selected = key;
    var match = /^([^/]+)\/(REQ-\d+)$/.exec(run), current = ++requestNo;
    if (!match || run.indexOf('simulación/') === 0) { box.hidden = true; box.innerHTML = ''; return; }
    fetch('/api/plans/' + encodeURIComponent(match[1]) + '/' + encodeURIComponent(match[2]))
      .then(function (response) { if (!response.ok) throw new Error('No se pudieron cargar las decisiones.'); return response.json(); })
      .then(function (data) {
        var decisions = data.decisions || [];
        var item = decisions.find(function (d) { return match[1] === 'pictures' && match[2] === 'REQ-021' && d.task === 'T3.2' && d.source === 'review'; });
        if (!item) return decisions;
        var query = new URLSearchParams({project: match[1], req: match[2], attempt: item.attempt});
        return fetch('/api/flow/proposal?' + query.toString()).then(function (response) {
          if (!response.ok) return null;
          return response.json();
        }).catch(function () { return null; }).then(function (proposal) { item.proposalData = proposal; return decisions; });
      })
      .then(function (decisions) { if (current === requestNo) render(decisions, match[1], match[2], taskKey()); })
      .catch(function (error) { if (current === requestNo) { box.hidden = false; box.innerHTML = '<p role="status">' + esc(error.message) + '</p>'; } });
  }
  function sync() { load(false); }
  root.addEventListener('click', function (event) {
    if (event.target.closest('[data-run], .fl-task, #flow-feed-list li[data-task]')) setTimeout(sync, 0);
  });
  ['fl-runs', 'fl-tasks'].forEach(function (id) {
    var target = document.getElementById(id);
    if (target && window.MutationObserver) new MutationObserver(sync).observe(target, { childList: true, subtree: true, attributes: true });
  });
  box.addEventListener('click', function (event) {
    var ask = event.target.closest('button[data-diagnose]');
    if (!ask) return;
    var card = ask.closest('.fl-decision'), status = $('.fl-decision-status');
    ask.disabled = true;
    var body = new URLSearchParams({ token: token, project: card.dataset.project, req: card.dataset.req, request: ask.dataset.diagnose });
    fetch('/api/flow/diagnose', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: body.toString() })
      .then(function (response) { return response.json().then(function (data) {
        if (!response.ok) throw new Error(data.error || 'No se pudo pedir el diagnóstico.');
        return data;
      }); })
      .then(function (data) { if (status) status.textContent = data.message; setTimeout(function () { load(true); }, 800); })
      .catch(function (error) { if (status) status.textContent = error.message; ask.disabled = false; });
  });
  function proposalCounts(form) {
    var backings = form.querySelectorAll('input[name="backings"]:checked').length;
    var mesas = form.querySelectorAll('input[name="mesas"]:checked').length;
    form.querySelector('[data-proposal-count="backings"]').textContent = backings + ' de 6';
    form.querySelector('[data-proposal-count="mesas"]').textContent = mesas + ' de 3';
    var excess = [];
    if (backings > 6) excess.push('desmarca ' + (backings - 6) + ' backing' + (backings - 6 === 1 ? '' : 's'));
    if (mesas > 3) excess.push('desmarca ' + (mesas - 3) + ' mesa' + (mesas - 3 === 1 ? '' : 's'));
    return excess;
  }
  box.addEventListener('change', function (event) {
    var form = event.target.closest('form[data-flow-proposal]');
    if (!form) return;
    var excess = proposalCounts(form), status = $('.fl-decision-status');
    if (status) status.textContent = excess.length ? 'Para continuar, ' + excess.join(' y ') + '.' : '';
  });
  box.addEventListener('submit', function (event) {
    var proposal = event.target.closest('form[data-flow-proposal]');
    if (proposal) {
      event.preventDefault();
      var chosen = {backings: [], mesas: []}, body = new URLSearchParams();
      new FormData(proposal).forEach(function (value, key) {
        if (key === 'backings' || key === 'mesas') chosen[key].push(value); else body.append(key, value);
      });
      var proposalStatus = $('.fl-decision-status'), submit = proposal.querySelector('button');
      var excess = proposalCounts(proposal);
      if (excess.length) {
        if (proposalStatus) proposalStatus.textContent = 'Para continuar, ' + excess.join(' y ') + '.';
        return;
      }
      body.set('selection', JSON.stringify(chosen)); submit.disabled = true;
      fetch('/api/flow/decision', {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded'}, body: body.toString()})
        .then(function (response) { return response.json().then(function (data) { if (!response.ok) throw new Error(data.error); return data; }); })
        .then(function (data) { if (proposalStatus) proposalStatus.textContent = data.message; })
        .catch(function (error) { if (proposalStatus) proposalStatus.textContent = error.message; submit.disabled = false; });
      return;
    }
    var form = event.target.closest('form[data-flow-decision]');
    if (!form) return;
    event.preventDefault();
    var button = form.querySelector('button'), status = $('.fl-decision-status');
    button.disabled = true;
    if (status) status.textContent = 'Aplicando decisión…';
    fetch('/api/flow/decision', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(new FormData(form)).toString() })
      .then(function (response) { return response.json().then(function (data) {
        if (!response.ok) throw new Error(data.error || 'No se aplicó la decisión.');
        return data;
      }); })
      .then(function (data) {
        if (status) status.textContent = data.message;
        setTimeout(function () { load(true); }, 1800);
      })
      .catch(function (error) { if (status) status.textContent = error.message; })
      .then(function () { button.disabled = false; });
  });
  load(false);
})();
