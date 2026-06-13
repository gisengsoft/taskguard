/* TaskGuard — melhorias progressivas de interface.
 * O app funciona sem JavaScript; este script apenas adiciona conveniências.
 * Servido sob CSP estrita (script-src 'self'), sem dependências externas.
 */
(function () {
  "use strict";

  // Confirmação antes de excluir uma tarefa.
  document.querySelectorAll("[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var message = form.getAttribute("data-confirm") || "Confirmar ação?";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  // Dispensa de mensagens flash ao clicar.
  document.querySelectorAll(".flash").forEach(function (flash) {
    flash.addEventListener("click", function () {
      flash.style.display = "none";
    });
  });

  // Foco automático no primeiro campo de formulário visível.
  var firstField = document.querySelector("form input:not([type=hidden])");
  if (firstField) {
    firstField.focus();
  }
})();
