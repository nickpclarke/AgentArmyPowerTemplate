// Brand wordmark in the header title: un (light) · tool (heavy) · .ai (muted).
// Per docs/brand/UNTOOL.md — "the mark performs the idea." CSS can't weight part of a
// text node, so we re-render the title. document$ is Material's instant-nav-safe hook,
// so this re-applies after client-side navigations (navigation.instant), not just first load.
document$.subscribe(function () {
  document.querySelectorAll(".md-header__title .md-ellipsis").forEach(function (el) {
    if (el.dataset.wordmark === "1") return;
    if (el.textContent.trim() !== "untool.ai") return;
    el.innerHTML =
      'un<strong style="font-weight:700">tool</strong>' +
      '<span style="opacity:.55">.ai</span>';
    el.dataset.wordmark = "1";
  });
});
