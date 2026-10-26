// Render every <script type="application/json" class="md-src" data-target="id"> block (a JSON string of
// markdown) into its target element. JSON keeps "</script>" inside documents from breaking the page.
// Wrapping tables in scroll regions is done page-wide by enhance.js.
const NOT_AN_EMAIL = /@(v?\d|[^@]*\.(md|json|ya?ml|tsx?|jsx?|py|css|html)$)/i; // `contract@v1.md`, `jest@30.5.2`

// Exposed as window.renderMarkdown(root) so live regions (planning-live.js) can render the blocks they swap in.
function renderMarkdown(root) {
root.querySelectorAll('script.md-src').forEach((block) => {
  const target = document.getElementById(block.dataset.target);
  if (!target || !window.marked) return;
  const src = JSON.parse(block.textContent)
    .replace(/^---\n[\s\S]*?\n---\n/, '') // drop front matter
    .replace(/<!--[\s\S]*?-->/g, ''); // author notes in HTML comments are not content (raw HTML is shown escaped)
  const renderer = new window.marked.Renderer();
  renderer.html = (html) => html.replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  window.marked.setOptions({ renderer });
  target.innerHTML = window.marked.parse(src);
  // GFM autolinks versioned names and package pins as e-mail addresses: show them as plain text.
  target.querySelectorAll('a[href^="mailto:"]').forEach((a) => {
    if (NOT_AN_EMAIL.test(a.textContent.trim())) a.replaceWith(document.createTextNode(a.textContent));
  });
  // Task-list checkboxes are read-only marks: give them a name instead of an unlabelled control.
  target.querySelectorAll('input[type="checkbox"][disabled]').forEach((box) => {
    box.setAttribute('aria-label', box.checked ? 'Hecho' : 'Pendiente');
  });
});
}
window.renderMarkdown = renderMarkdown;
renderMarkdown(document);

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
