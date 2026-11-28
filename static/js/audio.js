(function () {
  "use strict";

  var button = document.querySelector("[data-clue-audio]");
  var clue = document.querySelector("[data-clue-text]");
  var synth = window.speechSynthesis;

  if (!button || !clue || !synth || typeof window.SpeechSynthesisUtterance !== "function") {
    if (button) {
      button.disabled = true;
    }
    return;
  }

  function enabled() {
    return !!(window.CruciStorage && window.CruciStorage.getAudio());
  }

  function sync() {
    var active = enabled();
    button.setAttribute("aria-pressed", String(active));
    button.textContent = active ? "DETENER LECTURA" : "ESCUCHAR PISTA";
  }

  function stop() {
    synth.cancel();
    if (window.CruciStorage) {
      window.CruciStorage.setAudio(false);
    }
    sync();
  }

  button.addEventListener("click", function () {
    if (enabled()) {
      stop();
      return;
    }

    var text = clue.getAttribute("data-clue-audio-text") || clue.textContent || "";
    var utterance = new window.SpeechSynthesisUtterance(text.trim());
    utterance.lang = "en-US";
    utterance.rate = 0.85;
    utterance.onend = stop;
    utterance.onerror = stop;

    if (window.CruciStorage) {
      window.CruciStorage.setAudio(true);
    }
    sync();
    synth.cancel();
    synth.speak(utterance);
  });

  sync();
  window.CruciAudio = { isEnabled: enabled, stop: stop };
}());
