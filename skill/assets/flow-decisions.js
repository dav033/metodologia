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
  function render(requests, project, req, task) {
    var visible = requests.filter(function (item) { return !task || item.task === task; });
    box.hidden = !visible.length;
    if (!visible.length) { box.innerHTML = ''; return; }
    box.innerHTML = '<h2>Decisiones pendientes</h2>' + visible.map(function (item) {
      var evidence = item.diagnosis_html ? '' : (item.evidence || []).slice(0, 8).map(function (line) { return '<li>' + esc(line) + '</li>'; }).join('');
      var review = window.FlowFailureLinks.decisionHref(project, req, item);
      var ordered = (item.options || []).slice().sort(function (a, b) {
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
        (item.diagnosis_html || '<p>' + esc(item.what) + '</p>') +
        (evidence ? '<ul>' + evidence + '</ul>' : '') +
        (review ? '<p><a class="fl-failure-link" href="' + esc(review) + '" target="_blank" rel="noopener">Abrir log del último intento</a></p>' : '') +
        options + '</article>';
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
      .then(function (data) { if (current === requestNo) render(data.decisions || [], match[1], match[2], taskKey()); })
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
  box.addEventListener('submit', function (event) {
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
