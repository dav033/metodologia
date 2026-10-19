// Render every <script type="application/json" class="md-src" data-target="id"> block (a JSON string of
// markdown) into its target element. JSON keeps "</script>" inside documents from breaking the page.
document.querySelectorAll('script.md-src').forEach((block) => {
  const target = document.getElementById(block.dataset.target);
  if (!target || !window.marked) return;
  const src = JSON.parse(block.textContent).replace(/^---\n[\s\S]*?\n---\n/, ''); // drop front matter
  target.innerHTML = window.marked.parse(src);
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
