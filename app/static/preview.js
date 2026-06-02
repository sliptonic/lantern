/* Lantern Markdown subset renderer (offline, no dependencies).
 *
 * Exposes window.lanternMarkdown(src) -> HTML. Used by the editor's live
 * preview. The AUTHORITATIVE render is server-side (headless Chromium); this is
 * a lightweight approximation for instant feedback.
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
  function mdToHtml(src) {
    var lines = (src || "").split(/\r?\n/);
    var out = [], list = null, para = [];
    function flushPara() { if (para.length) { out.push("<p>" + inline(para.join(" ")) + "</p>"); para = []; } }
    function flushList() { if (list) { out.push("</" + list + ">"); list = null; } }
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
        out.push("<li>" + inline(ul ? ul[1] : ol[1]) + "</li>");
        continue;
      }
      flushList();
      if (quote) { flushPara(); out.push("<blockquote>" + inline(quote[1]) + "</blockquote>"); continue; }
      para.push(ln);
    }
    flushPara(); flushList();
    return out.join("\n");
  }

  window.lanternMarkdown = mdToHtml;
})();
