/* Lantern sheet editor: two-column body grid + live preview.
 *
 * Each body row has a left Markdown textarea and a right side that is None,
 * an Image (uploaded immediately via AJAX, referenced by token), or a QR from
 * a URL. The single `row_value` field per row carries the image token or the
 * URL, so the save form stays text-only.
 *
 * The live preview renders the REAL print template (POST /sheet/preview) into
 * an iframe and scales it to fit the column, so it matches the printed PDF
 * exactly and the overflow check measures the true page, not the device
 * viewport (issue #14).
 */
(function () {
  "use strict";

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
        schedulePreview();
      })
      .catch(function () { alert("Image upload failed."); });
  }

  function wireRow(row) {
    syncRow(row);
    row.querySelector(".row-kind").addEventListener("change", function () { syncRow(row); schedulePreview(); });
    var file = row.querySelector(".row-image-file");
    if (file) file.addEventListener("change", function () {
      if (file.files && file.files[0]) uploadImage(row, file.files[0]);
    });
    var rm = row.querySelector(".remove-row");
    if (rm) rm.addEventListener("click", function () {
      var grid = document.getElementById("body-grid");
      if (grid.querySelectorAll(".body-row").length > 1) row.remove();
      else { row.querySelector("textarea").value = ""; row.querySelector(".row-kind").value = "none"; syncRow(row); }
      schedulePreview();
    });
  }

  // ---- Live preview (real print template, rendered server-side) ----
  var form, frame, scaleWrap, warn, timer;

  // Scale the rendered page to fit its column and flag overflow. The iframe
  // body lays out at true page size (fixed inches), so these measurements are
  // device-independent and track the actual printed page.
  function fitAndCheck() {
    if (!frame || !scaleWrap) return;
    var doc = frame.contentDocument;
    if (!doc || !doc.body) return;
    var pw = doc.body.offsetWidth, ph = doc.body.offsetHeight;
    if (!pw || !ph) return;
    frame.style.width = pw + "px";
    frame.style.height = ph + "px";
    var scale = scaleWrap.clientWidth / pw;
    frame.style.transform = "scale(" + scale + ")";
    scaleWrap.style.height = (ph * scale) + "px";
    // .body is flex:1; overflow:hidden inside a fixed-height page — when its
    // content is taller than the slot, the sheet spills onto a second page.
    var body = doc.querySelector(".body");
    var over = !!body && body.scrollHeight > body.clientHeight + 1;
    if (warn) warn.style.display = over ? "block" : "none";
    frame.classList.toggle("overflowing", over);
  }

  function refreshPreview() {
    if (!form || !frame) return;
    fetch("/sheet/preview", { method: "POST", body: new FormData(form) })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (html) {
        if (html == null) return;     // keep the last good preview on error
        frame.onload = fitAndCheck;
        frame.srcdoc = html;
      })
      .catch(function () { /* network error — keep last good preview */ });
  }

  function schedulePreview() {
    clearTimeout(timer);
    timer = setTimeout(refreshPreview, 350);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var grid = document.getElementById("body-grid");
    if (!grid) return;
    form = document.querySelector("form.editor");
    frame = document.getElementById("preview-frame");
    scaleWrap = document.querySelector(".pp-scale");
    warn = document.getElementById("overflow-warn");

    grid.querySelectorAll(".body-row").forEach(wireRow);

    var add = document.getElementById("add-row");
    if (add) add.addEventListener("click", function () {
      var tpl = document.getElementById("row-tpl");
      var node = tpl.content.firstElementChild.cloneNode(true);
      grid.appendChild(node);
      wireRow(node);
      schedulePreview();
    });

    if (form) form.addEventListener("input", schedulePreview);
    window.addEventListener("resize", fitAndCheck);
    refreshPreview();   // initial render
  });
})();
