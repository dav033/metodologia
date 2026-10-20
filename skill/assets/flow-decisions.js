// Owner actions for open Scheduler decisions shown by the selected /flow run.
(function () {
  'use strict';
  var root = document.getElementById('flow'), box = document.getElementById('fl-decisions');
  if (!root || !box) return;
  var token = root.dataset.token || '', selected = '', requestNo = 0;
  var NEEDS_REASON = { retry_with_note: true, review_pass: true, review_fail: true };

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
      var evidence = (item.evidence || []).slice(0, 8).map(function (line) { return '<li>' + esc(line) + '</li>'; }).join('');
      var review = window.FlowFailureLinks.decisionHref(project, req, item);
      var options = (item.options || []).map(function (option) {
        var recommended = option.id === item.recommended;
        var note = NEEDS_REASON[option.id] ? '<label class="fl-decision-reason">' +
          (option.id === 'retry_with_note' ? 'Indicación para el siguiente intento' : 'Razón de tu decisión') +
          '<textarea name="reason" required maxlength="4000" placeholder="Escribe tu indicación"></textarea></label>' : '';
        return '<form class="fl-decision-option" data-flow-decision>' +
          '<input type="hidden" name="token" value="' + esc(token) + '">' +
          '<input type="hidden" name="project" value="' + esc(project) + '">' +
          '<input type="hidden" name="req" value="' + esc(req) + '">' +
          '<input type="hidden" name="request" value="' + esc(item.id) + '">' +
          '<input type="hidden" name="option" value="' + esc(option.id) + '">' + note +
          '<button type="submit"' + (recommended ? ' class="primary"' : '') + '>' + esc(option.label) +
          (recommended ? ' (recomendada)' : '') + '</button><p>' + esc(option.consequence) + '</p></form>';
      }).join('');
      return '<article class="fl-decision"><h3>' + esc(item.title) + '</h3><p>' + esc(item.what) + '</p>' +
        (evidence ? '<ul>' + evidence + '</ul>' : '') +
        (review ? '<p><a class="fl-failure-link" href="' + esc(review) + '" target="_blank" rel="noopener">Abrir log del último intento</a></p>' : '') +
        options + '</article>';
    }).join('') + '<p class="fl-decision-status" role="status"></p>';
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
