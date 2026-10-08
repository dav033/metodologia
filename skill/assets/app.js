// Render every <script type="application/json" class="md-src" data-target="id"> block (a JSON string of
// markdown) into its target element. JSON keeps "</script>" inside documents from breaking the page.
document.querySelectorAll('script.md-src').forEach((block) => {
  const target = document.getElementById(block.dataset.target);
  if (!target || !window.marked) return;
  const src = JSON.parse(block.textContent).replace(/^---\n[\s\S]*?\n---\n/, ''); // drop front matter
  target.innerHTML = window.marked.parse(src);
});
