(function () {
  "use strict";

  var VALID_THEMES = ["crema", "domingo", "pizarra"];

  try {
    var stored = JSON.parse(window.localStorage.getItem("cruciword:theme"));
    if (VALID_THEMES.indexOf(stored) !== -1) {
      document.documentElement.setAttribute("data-theme", stored);
    }
  } catch (error) {
    return;
  }
}());
