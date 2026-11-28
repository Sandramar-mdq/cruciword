(function () {
  "use strict";

  var status = document.getElementById("cw-connection-status");

  function update(online) {
    if (!status) {
      return;
    }
    status.textContent = online
      ? "Listo para jugar"
      : "Sin conexión: tu progreso se guarda aquí";
    status.setAttribute("data-online", String(online));
  }

  function flush() {
    if (window.CruciApi) {
      window.CruciApi.flushQueue();
    }
  }

  update(navigator.onLine);
  flush();

  window.addEventListener("online", function () {
    update(true);
    flush();
  });

  window.addEventListener("offline", function () {
    update(false);
  });

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker
        .register("/static/sw.js")
        .catch(function () {
          update(navigator.onLine);
        });
    });
  }
}());
