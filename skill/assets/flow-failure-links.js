// Shared URL construction for opening a failed attempt's local M6 review.
(function () {
  'use strict';
  function href(project, req, task, attempt, reference) {
    if (!/^[A-Za-z0-9_-]+$/.test(project || '') || !/^REQ-\d+$/.test(req || '') || !task || !attempt ||
        !/^m6:\/\/result\/[0-9a-f]{64}$/.test(reference || '')) return '';
    return '/flow/review?' + new URLSearchParams({ project: project, req: req, task: task, attempt: attempt, ref: reference }).toString();
  }
  function attemptHref(run, task, attempt) {
    var match = /^([^/]+)\/(REQ-\d+)$/.exec(run || ''), failure = attempt && attempt.failure;
    return match ? href(match[1], match[2], task, attempt.id, failure) : '';
  }
  function attemptLink(run, task, attempt) {
    var target = attemptHref(run, task, attempt);
    return target ? '<a class="fl-failure-link" href="' + target.replace(/&/g, '&amp;').replace(/"/g, '&quot;') +
      '" target="_blank" rel="noopener">Abrir log de verificación</a>' : '';
  }
  function decisionHref(project, req, item) {
    var reference = (item.evidence || []).map(function (line) {
      var found = /m6:\/\/result\/[0-9a-f]{64}/.exec(line);
      return found ? found[0] : '';
    }).filter(Boolean)[0];
    return href(project, req, item.task, item.attempt, reference);
  }
  window.FlowFailureLinks = { href: attemptHref, link: attemptLink, decisionHref: decisionHref };
})();
