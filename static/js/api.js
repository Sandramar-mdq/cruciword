(function () {
  "use strict";

  var state = { token: null, user: null, flushing: false };

  function store() {
    return window.CruciStorage;
  }

  function getToken() {
    if (!state.token && store()) {
      state.token = store().getSession();
    }
    return state.token;
  }

  function setToken(token) {
    state.token = token;
    if (store()) {
      store().setSession(token);
    }
  }

  function clearSession() {
    state.token = null;
    state.user = null;
    if (store()) {
      store().clearSession();
    }
  }

  function authStatus(message) {
    var element = document.getElementById("cw-auth-status");
    if (element) {
      element.textContent = message;
    }
  }

  function syncStatus(message) {
    var element = document.getElementById("cw-sync-status");
    if (element) {
      element.textContent = message;
    }
  }

  function updateAuthUI() {
    var logout = document.querySelector("[data-auth-logout]");
    if (logout) {
      logout.hidden = !state.user;
    }
    authStatus(
      state.user
        ? "Sesión iniciada: " + state.user.username + ". Tus partidas se sincronizan solas."
        : "Juega libremente; la cuenta solo sirve para sincronizar."
    );
  }

  function parseBody(response) {
    if (response.status === 204) {
      return Promise.resolve(null);
    }
    return response.json().catch(function () {
      return null;
    });
  }

  function apiError(response, body) {
    var detail = body && body.detail ? body.detail : "No se pudo completar la solicitud.";
    var message = typeof detail === "string" ? detail : "Revisa los datos e inténtalo de nuevo.";
    var error = new Error(message);
    error.status = response.status;
    error.detail = detail;
    return error;
  }

  function request(path, options) {
    var config = options || {};
    var headers = { Accept: "application/json" };
    var body = null;

    if (config.body !== undefined && config.body !== null) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(config.body);
    }

    var token = config.auth === false ? null : getToken();
    if (token) {
      headers.Authorization = "Bearer " + token;
    }

    return fetch(path, {
      method: config.method || "GET",
      headers: headers,
      body: body,
      credentials: "same-origin"
    }).then(function (response) {
      return parseBody(response).then(function (payload) {
        if (!response.ok) {
          throw apiError(response, payload);
        }
        return { status: response.status, data: payload };
      });
    });
  }

  function restoreSession() {
    if (!getToken()) {
      updateAuthUI();
      return Promise.resolve(null);
    }

    return request("/api/users/me")
      .then(function (result) {
        state.user = result.data;
        updateAuthUI();
        return state.user;
      })
      .catch(function (error) {
        if (error.status === 401) {
          clearSession();
        }
        updateAuthUI();
        return null;
      });
  }

  function login(credentials) {
    return request("/api/auth/login", {
      method: "POST",
      body: credentials,
      auth: false
    }).then(function (result) {
      var token = result.data && result.data.access_token;
      if (!token) {
        throw new Error("El servidor no devolvió una sesión válida.");
      }
      setToken(token);
      return restoreSession();
    });
  }

  function register(credentials) {
    return request("/api/auth/register", {
      method: "POST",
      body: credentials,
      auth: false
    }).then(function () {
      return login(credentials);
    });
  }

  function enqueueProgress(puzzleId, payload) {
    if (!store()) {
      return null;
    }
    return store().enqueue({
      url: "/api/puzzles/" + puzzleId + "/progress",
      method: "POST",
      body: payload
    });
  }

  function checkAnswers(puzzleId, answers) {
    var id = parseInt(puzzleId, 10);
    if (!isFinite(id) || id <= 0) {
      return Promise.resolve(null);
    }
    if (!navigator.onLine) {
      return Promise.resolve(null);
    }
    return request("/api/puzzles/" + id + "/check", {
      method: "POST",
      body: { answers: answers || {} },
      auth: false
    }).then(function (result) {
      return result.data;
    });
  }

  function submitProgress(puzzleId, letters, answers) {
    var id = parseInt(puzzleId, 10);
    if (!isFinite(id) || id <= 0) {
      return Promise.resolve({ queued: false, error: "Crucigrama no válido." });
    }

    var word = String(letters || "")
      .toUpperCase()
      .replace(/[^A-Z]/g, "");
    var finalAnswers = answers && typeof answers === "object" ? answers : { "1_across": word };
    var payload = { answers: finalAnswers, power_mode_used: false, hints_used: 0 };

    if (store()) {
      store().saveProgress(String(id), { answers: finalAnswers, synced: false });
    }

    if (!navigator.onLine || !getToken()) {
      enqueueProgress(id, payload);
      syncStatus("Progreso guardado aquí. Se enviará al entrar o al volver la conexión.");
      return Promise.resolve({ queued: true });
    }

    return request("/api/puzzles/" + id + "/progress", {
      method: "POST",
      body: payload
    })
      .then(function (result) {
        if (store()) {
          store().saveProgress(String(id), {
            answers: finalAnswers,
            synced: true,
            result: result.data
          });
        }
        if (window.CruciBoard && typeof window.CruciBoard.applyProgress === "function") {
          window.CruciBoard.applyProgress(result.data);
        }
        syncStatus("Progreso sincronizado. " + (result.data.message || ""));
        return { queued: false, data: result.data };
      })
      .catch(function (error) {
        if (error.status === 401 || !navigator.onLine) {
          enqueueProgress(id, payload);
          syncStatus("Progreso guardado aquí. Se enviará al entrar o al volver la conexión.");
          return { queued: true };
        }
        syncStatus("No se pudo enviar ahora; tus respuestas siguen guardadas aquí.");
        return { queued: true, persisted: true };
      });
  }

  function flushQueue() {
    if (!store() || state.flushing || !navigator.onLine || !getToken()) {
      return Promise.resolve(0);
    }

    var queue = store().getQueue();
    if (!queue.length) {
      return Promise.resolve(0);
    }

    state.flushing = true;
    var sent = 0;

    function finish(message) {
      state.flushing = false;
      syncStatus(message);
      return Promise.resolve(sent);
    }

    function next(index) {
      if (index >= queue.length) {
        return finish(sent ? "Sincronizadas " + sent + " partidas." : "Todo al día.");
      }

      var item = queue[index];
      return request(item.url, {
        method: item.method || "POST",
        body: item.body
      })
        .then(function () {
          store().removeQueued(item.id);
          sent += 1;
          return next(index + 1);
        })
        .catch(function (error) {
          if (error.status === 401) {
            clearSession();
            updateAuthUI();
            return finish("Entra de nuevo para sincronizar tus partidas guardadas.");
          }
          return finish("Quedan partidas guardadas; se enviarán cuando vuelva la conexión.");
        });
    }

    return next(0);
  }

  function loadPuzzles() {
    var select = document.querySelector("[data-puzzle-select]");
    if (!select) {
      return Promise.resolve([]);
    }

    return request("/api/puzzles", { auth: false })
      .then(function (result) {
        var puzzles = Array.isArray(result.data) ? result.data : [];
        if (!puzzles.length) {
          return puzzles;
        }
        select.innerHTML = "";
        puzzles.forEach(function (puzzle) {
          var option = document.createElement("option");
          option.value = puzzle.id;
          option.textContent = puzzle.title + " · " + puzzle.cefr_level;
          select.appendChild(option);
        });
        return puzzles;
      })
      .catch(function () {
        return [];
      });
  }

  function wire() {
    var form = document.querySelector("[data-auth-form]");
    if (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();

        var submitter = event.submitter || document.activeElement;
        var mode =
          submitter && submitter.getAttribute
            ? submitter.getAttribute("data-auth-submit")
            : "login";
        var credentials = {
          username: form.elements.username.value.trim(),
          password: form.elements.password.value,
          role: "student"
        };
        var buttons = form.querySelectorAll("button");

        Array.prototype.forEach.call(buttons, function (button) {
          button.disabled = true;
        });
        authStatus("Un momento...");

        var action = mode === "register" ? register(credentials) : login(credentials);
        action
          .then(function () {
            form.reset();
            authStatus(mode === "register" ? "Cuenta creada y sesión iniciada." : "Sesión iniciada.");
            updateAuthUI();
            return flushQueue();
          })
          .catch(function (error) {
            authStatus(error && error.message ? error.message : "No se pudo completar el acceso.");
          })
          .then(function () {
            Array.prototype.forEach.call(buttons, function (button) {
              button.disabled = false;
            });
          });
      });

      var logout = document.querySelector("[data-auth-logout]");
      if (logout) {
        logout.addEventListener("click", function () {
          clearSession();
          updateAuthUI();
          authStatus("Sesión cerrada. Tu progreso local sigue aquí.");
        });
      }
    }

    var save = document.querySelector("[data-save-progress]");
    if (save) {
      save.addEventListener("click", function () {
        var select = document.querySelector("[data-puzzle-select]");
        var puzzleId = select ? select.value : "1";
        var word = window.CruciKeyboard ? window.CruciKeyboard.getWord() : "";
        var answers = window.CruciBoard
          ? window.CruciBoard.getAnswers()
          : { "1_across": word };
        submitProgress(puzzleId, word, answers);
      });
    }

    restoreSession().then(flushQueue);
    loadPuzzles();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }

  window.CruciApi = {
    request: request,
    login: login,
    register: register,
    restoreSession: restoreSession,
    checkAnswers: checkAnswers,
    submitProgress: submitProgress,
    loadPuzzles: loadPuzzles,
    flushQueue: flushQueue,
    logout: clearSession,
    token: getToken
  };
}());
