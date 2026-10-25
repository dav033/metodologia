// Page-wide progressive enhancements, applied to the initial page and to fragments that live updates insert:
// the current section in the main navigation, tables that scroll instead of squeezing, and keyboard-reachable
// scroll regions. Without JavaScript every page still renders; tables then fall back to the page's own overflow.
(function () {
  // Main navigation: mark the section the page belongs to.
  var path = location.pathname;
  document.querySelectorAll('header.top nav.mainnav a').forEach(function (a) {
    var href = a.getAttribute('href');
    if (href && href !== '/' && (path === href || path.indexOf(href + '/') === 0)) a.setAttribute('aria-current', 'page');
  });

  function scrolls(el) {
    for (var a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      var o = getComputedStyle(a).overflowX;
      if (o === 'auto' || o === 'scroll') return true;
    }
    return false;
  }

  function label(el) {
    var prev = el.previousElementSibling;
    if (prev && /^H[1-6]$/.test(prev.tagName)) return prev.textContent.trim();
    var cap = el.querySelector && el.querySelector('caption, h2, h3, summary');
    return cap ? cap.textContent.trim() : 'Tabla';
  }

  function wrapTable(table) {
    if (table.closest('.table-scroll') || scrolls(table)) return;
    var wrap = document.createElement('div');
    var cols = table.rows[0] ? table.rows[0].cells.length : 0;
    wrap.className = 'table-scroll' + (cols >= 5 ? ' wide' : '');
    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
    wrap.setAttribute('aria-label', label(wrap));
    if (table.closest('.md')) {
      table.querySelectorAll('td').forEach(function (cell) {
        if (cell.textContent.trim().length <= 14) cell.classList.add('nw');
      });
    }
  }

  // A region that actually scrolls must be reachable and named for keyboard and screen-reader users.
  function focusable(el) {
    if (el.scrollWidth <= el.clientWidth + 1 || el.hasAttribute('tabindex')) return;
    el.tabIndex = 0;
    if (!el.hasAttribute('role')) el.setAttribute('role', 'region');
    if (!el.hasAttribute('aria-label')) el.setAttribute('aria-label', label(el.querySelector('table') || el));
  }

  function enhance(root) {
    root.querySelectorAll('table').forEach(wrapTable);
    root.querySelectorAll('.table-scroll, .tscroll, .panel, .fl-mapwrap, [style*="overflow-x:auto"], [style*="overflow-x: auto"]')
      .forEach(focusable);
  }

  enhance(document);
  // On a phone the section tabs scroll sideways: keep the selected one in view.
  var on = document.querySelector('.tabs a.on');
  if (on && on.parentElement.scrollWidth > on.parentElement.clientWidth) {
    var r = on.getBoundingClientRect(), pr = on.parentElement.getBoundingClientRect();
    on.parentElement.scrollLeft += r.left - pr.left - (pr.width - r.width) / 2;
  }
  addEventListener('resize', function () { enhance(document); });
  new MutationObserver(function (records) {
    records.forEach(function (r) {
      r.addedNodes.forEach(function (n) { if (n.nodeType === 1) enhance(n.parentElement || n); });
    });
  }).observe(document.body, { childList: true, subtree: true });
})();
