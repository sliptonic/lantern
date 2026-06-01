/* Lantern editor live preview — offline, no dependencies.
 *
 * A small Markdown subset renderer drives an approximate single-page preview.
 * It is intentionally lightweight: the AUTHORITATIVE render + overflow check is
 * server-side (headless Chromium). This gives the editor instant "will it fit?"
 * feedback while typing.
 */
(function () {
  "use strict";

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function inline(s) {
    return esc(s)
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
  }

  // Minimal block-level Markdown -> HTML (headings, lists, quote, hr, p).
  function mdToHtml(src) {
    var lines = (src || "").split(/\r?\n/);
    var out = [], list = null, para = [];

    function flushPara() {
      if (para.length) { out.push("<p>" + inline(para.join(" ")) + "</p>"); para = []; }
    }
    function flushList() {
      if (list) { out.push("</" + list + ">"); list = null; }
    }

    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i];
      var h = /^(#{1,6})\s+(.*)$/.exec(ln);
      var ul = /^\s*[-*]\s+(.*)$/.exec(ln);
      var ol = /^\s*\d+\.\s+(.*)$/.exec(ln);
      var quote = /^>\s?(.*)$/.exec(ln);

      if (ln.trim() === "") { flushPara(); flushList(); continue; }
      if (/^(---|\*\*\*|___)\s*$/.test(ln)) { flushPara(); flushList(); out.push("<hr>"); continue; }
      if (h) { flushPara(); flushList(); out.push("<h" + h[1].length + ">" + inline(h[2]) + "</h" + h[1].length + ">"); continue; }
      if (ul || ol) {
        flushPara();
        var want = ul ? "ul" : "ol";
        if (list && list !== want) flushList();
        if (!list) { list = want; out.push("<" + list + ">"); }
        out.push("<li>" + inline((ul ? ul[1] : ol[1])) + "</li>");
        continue;
      }
      flushList();
      if (quote) { flushPara(); out.push("<blockquote>" + inline(quote[1]) + "</blockquote>"); continue; }
      para.push(ln);
    }
    flushPara(); flushList();
    return out.join("\n");
  }

  document.addEventListener("DOMContentLoaded", function () {
    var body = document.getElementById("body");
    var preview = document.getElementById("preview-body");
    var title = document.getElementById("preview-title");
    var machine = document.querySelector('input[name="machine"]');
    var warn = document.getElementById("overflow-warn");
    if (!body || !preview) return;

    function update() {
      preview.innerHTML = mdToHtml(body.value);
      if (title && machine) title.textContent = machine.value || "Machine name";
      // Overflow when the rendered body is taller than its page-body area.
      var over = preview.scrollHeight > preview.clientHeight + 1;
      preview.classList.toggle("overflowing", over);
      if (warn) warn.style.display = over ? "block" : "none";
    }

    body.addEventListener("input", update);
    if (machine) machine.addEventListener("input", update);
    update();
  });
})();
