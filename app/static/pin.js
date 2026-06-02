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
})();
