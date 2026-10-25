// Render every <script type="application/json" class="md-src" data-target="id"> block (a JSON string of
// markdown) into its target element. JSON keeps "</script>" inside documents from breaking the page.
document.querySelectorAll('script.md-src').forEach((block) => {
  const target = document.getElementById(block.dataset.target);
  if (!target || !window.marked) return;
  const src = JSON.parse(block.textContent).replace(/^---\n[\s\S]*?\n---\n/, ''); // drop front matter
  const renderer = new window.marked.Renderer();
  renderer.html = (html) => html.replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  window.marked.setOptions({ renderer });
  target.innerHTML = window.marked.parse(src);
  // Tables scroll inside a focusable region instead of squeezing cells letter by letter; short cells stay on one line.
  target.querySelectorAll('table').forEach((table) => {
    const wrap = document.createElement('div');
    wrap.className = 'table-scroll' + (table.rows[0] && table.rows[0].cells.length >= 5 ? ' wide' : '');
    wrap.tabIndex = 0;
    wrap.setAttribute('role', 'region');
    const prev = table.previousElementSibling;
    wrap.setAttribute('aria-label', prev && /^H[1-6]$/.test(prev.tagName) ? prev.textContent.trim() : 'Tabla');
    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
    table.querySelectorAll('td').forEach((cell) => {
      if (cell.textContent.trim().length <= 14) cell.classList.add('nw');
    });
  });
});

// Ids in rendered markdown headings (## D-045 — ...) become anchors, so /go/D-045 lands on the exact section.
(function () {
  var ID = /^(REQ|P|D|LG)-\d+/i;
  document.querySelectorAll('.md h1, .md h2, .md h3, .md h4').forEach(function (h) {
    var m = ID.exec(h.textContent.trim());
    if (m && !h.id) h.id = m[0].toUpperCase();
  });
  if (location.hash) {
    var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (el) el.scrollIntoView();
  }
})();
