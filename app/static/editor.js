/* Lantern sheet editor: two-column body grid + live preview.
 *
 * Each body row has a left Markdown textarea and a right side that is None,
 * an Image (uploaded immediately via AJAX, referenced by token), or a QR from
 * a URL. The single `row_value` field per row carries the image token or the
 * URL, so the save form stays text-only.
 */
(function () {
  "use strict";

  function md(s) { return window.lanternMarkdown ? window.lanternMarkdown(s) : ""; }

  // Configure a row's right-side controls from its current kind/value.
  function syncRow(row) {
    var kind = row.querySelector(".row-kind").value;
    var value = row.querySelector(".row-value");
    var imgCtl = row.querySelector(".row-image-ctl");
    var thumb = row.querySelector(".row-image-thumb");
    if (kind === "qr") {
      value.type = "text"; value.hidden = false; value.placeholder = "https://video-url…";
      imgCtl.hidden = true;
    } else if (kind === "image") {
      value.type = "hidden"; value.hidden = true;
      imgCtl.hidden = false;
      if (value.value) { thumb.src = "/image/" + value.value; thumb.hidden = false; }
      else { thumb.hidden = true; }
    } else { // none
      value.type = "hidden"; value.hidden = true; value.value = "";
      imgCtl.hidden = true; thumb.hidden = true;
    }
  }

  function uploadImage(row, file) {
    var fd = new FormData();
    fd.append("image", file);
    fetch("/image/upload", { method: "POST", body: fd })
      .then(function (r) { if (!r.ok) throw new Error("upload failed"); return r.json(); })
      .then(function (j) {
        var value = row.querySelector(".row-value");
        var thumb = row.querySelector(".row-image-thumb");
        value.value = j.token;
        thumb.src = j.url; thumb.hidden = false;
        renderPreview();
      })
      .catch(function () { alert("Image upload failed."); });
  }

  function wireRow(row) {
    syncRow(row);
    row.querySelector(".row-kind").addEventListener("change", function () { syncRow(row); renderPreview(); });
    var file = row.querySelector(".row-image-file");
    if (file) file.addEventListener("change", function () {
      if (file.files && file.files[0]) uploadImage(row, file.files[0]);
    });
    var rm = row.querySelector(".remove-row");
    if (rm) rm.addEventListener("click", function () {
      var grid = document.getElementById("body-grid");
      if (grid.querySelectorAll(".body-row").length > 1) row.remove();
      else { row.querySelector("textarea").value = ""; row.querySelector(".row-kind").value = "none"; syncRow(row); }
      renderPreview();
    });
  }

  var preview, warn;
  function renderPreview() {
    if (!preview) return;
    var rows = document.querySelectorAll("#body-grid .body-row");
    preview.innerHTML = "";
    rows.forEach(function (row) {
      var left = row.querySelector("textarea[name=row_left]").value;
      var kind = row.querySelector(".row-kind").value;
      var value = row.querySelector(".row-value").value;
      var hasRight = (kind === "image" || kind === "qr") && value;
      var pr = document.createElement("div");
      pr.className = "pp-row" + (hasRight ? "" : " full");
      var l = document.createElement("div"); l.className = "pp-left"; l.innerHTML = md(left);
      pr.appendChild(l);
      if (kind === "image" && value) {
        var r = document.createElement("div"); r.className = "pp-right";
        var im = document.createElement("img"); im.src = "/image/" + value; r.appendChild(im);
        pr.appendChild(r);
      } else if (kind === "qr" && value) {
        var q = document.createElement("div"); q.className = "pp-right pp-qr";
        q.textContent = "▢ QR → " + value; pr.appendChild(q);
      }
      preview.appendChild(pr);
    });
    var over = preview.scrollHeight > preview.clientHeight + 1;
    preview.classList.toggle("overflowing", over);
    if (warn) warn.style.display = over ? "block" : "none";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var grid = document.getElementById("body-grid");
    if (!grid) return;
    preview = document.getElementById("preview-body");
    warn = document.getElementById("overflow-warn");
    var title = document.getElementById("preview-title");
    var titleInput = document.querySelector('input[name="title"]');

    grid.querySelectorAll(".body-row").forEach(wireRow);

    var add = document.getElementById("add-row");
    if (add) add.addEventListener("click", function () {
      var tpl = document.getElementById("row-tpl");
      var node = tpl.content.firstElementChild.cloneNode(true);
      grid.appendChild(node);
      wireRow(node);
      renderPreview();
    });

    grid.addEventListener("input", renderPreview);
    if (titleInput && title) titleInput.addEventListener("input", function () {
      title.textContent = titleInput.value || "Title";
    });
    renderPreview();
  });
})();
