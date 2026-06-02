/* Lantern PIN prompt.
 *
 * PIN-gated forms carry class "pin-form" and no longer embed a PIN input.
 * When the gate is enabled, submitting one prompts for the PIN once and
 * injects it as a hidden field, then submits. When disabled, forms submit
 * normally. Any inline confirm() (onsubmit) runs before this.
 */
(function () {
  "use strict";
  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!form.classList || !form.classList.contains("pin-form")) return;
    if (!window.LANTERN_PIN_ENABLED) return;
    if (form.dataset.pinDone) return;            // already handled
    e.preventDefault();
    var pin = window.prompt("Enter PIN");
    if (pin === null) return;                     // cancelled
    var hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = "pin";
    hidden.value = pin;
    form.appendChild(hidden);
    form.dataset.pinDone = "1";
    form.submit();
  });

  // After a wrong PIN, the user hits Back to the form. If it's restored from
  // the bfcache it still carries the rejected PIN + the "done" flag, so a
  // re-submit would silently reuse the bad PIN. Clear that on every show so
  // the next submit re-prompts.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll("form.pin-form").forEach(function (form) {
      delete form.dataset.pinDone;
      form.querySelectorAll('input[type="hidden"][name="pin"]').forEach(function (i) { i.remove(); });
    });
  });
})();
