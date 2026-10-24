var t = new URLSearchParams(location.search).get('theme');
if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
var d = t === 'dark' || (t !== 'light' && window.matchMedia &&
  matchMedia('(prefers-color-scheme: dark)').matches);
document.documentElement.classList.toggle('sl-theme-dark', d);
