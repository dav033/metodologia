if (document.currentScript && document.currentScript.dataset.enabled === '1') {
  setTimeout(function () {
    var active = document.activeElement;
    if (!active || active.tagName !== 'TEXTAREA') location.reload();
  }, 8000);
}
