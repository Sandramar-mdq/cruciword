(function () {
  "use strict";

  var THEME_COLORS = Object.freeze({
    crema: "#F7EFD9",
    domingo: "#F0EBE1",
    pizarra: "#1C1E1B"
  });

  function current() {
    return document.documentElement.getAttribute("data-theme") || "crema";
  }

  function syncControls(theme) {
    var buttons = document.querySelectorAll("[data-theme-choice]");
    Array.prototype.forEach.call(buttons, function (button) {
      button.setAttribute(
        "aria-pressed",
        String(button.getAttribute("data-theme-choice") === theme)
      );
    });

    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", THEME_COLORS[theme] || THEME_COLORS.crema);
    }
  }

  function setTheme(theme) {
    if (!Object.prototype.hasOwnProperty.call(THEME_COLORS, theme)) {
      return;
    }
    document.documentElement.setAttribute("data-theme", theme);
    syncControls(theme);
    if (window.CruciStorage) {
      window.CruciStorage.setTheme(theme);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    syncControls(current());
  });

  document.addEventListener("click", function (event) {
    var target = event.target;
    if (!target || typeof target.closest !== "function") {
      return;
    }
    var button = target.closest("[data-theme-choice]");
    if (button) {
      setTheme(button.getAttribute("data-theme-choice"));
    }
  });

  window.CruciThemes = { current: current, set: setTheme };
}());
