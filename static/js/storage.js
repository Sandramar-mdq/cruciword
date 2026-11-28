(function () {
  "use strict";

  var KEYS = Object.freeze({
    theme: "cruciword:theme",
    progress: "cruciword:progress",
    queue: "cruciword:sync-queue",
    session: "cruciword:session",
    audio: "cruciword:clues-audio"
  });

  function read(key, fallback) {
    try {
      var raw = window.localStorage.getItem(key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch (error) {
      return fallback;
    }
  }

  function write(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      return false;
    }
  }

  function objectOrEmpty(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value)
      ? value
      : {};
  }

  function arrayOrEmpty(value) {
    return Array.isArray(value) ? value : [];
  }

  function newId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
  }

  var api = {
    keys: KEYS,

    getTheme: function () {
      return read(KEYS.theme, null);
    },

    setTheme: function (themeId) {
      return write(KEYS.theme, themeId);
    },

    getSession: function () {
      return read(KEYS.session, null);
    },

    setSession: function (token) {
      return write(KEYS.session, token);
    },

    clearSession: function () {
      return write(KEYS.session, null);
    },

    getAudio: function () {
      return read(KEYS.audio, false) === true;
    },

    setAudio: function (enabled) {
      return write(KEYS.audio, enabled === true);
    },

    getProgress: function () {
      return objectOrEmpty(read(KEYS.progress, {}));
    },

    getPuzzleProgress: function (puzzleId) {
      return objectOrEmpty(api.getProgress()[puzzleId]);
    },

    saveProgress: function (puzzleId, patch) {
      var all = api.getProgress();
      var previous = objectOrEmpty(all[puzzleId]);
      var updated = Object.assign({}, previous, objectOrEmpty(patch), {
        updatedAt: new Date().toISOString()
      });
      all[puzzleId] = updated;
      write(KEYS.progress, all);
      return updated;
    },

    clearProgress: function () {
      return write(KEYS.progress, {});
    },

    getQueue: function () {
      return arrayOrEmpty(read(KEYS.queue, []));
    },

    enqueue: function (payload) {
      var request = objectOrEmpty(payload);
      var item = {
        id: newId(),
        url: String(request.url || ""),
        method: String(request.method || "POST").toUpperCase(),
        body: request.body === undefined ? null : request.body,
        createdAt: new Date().toISOString()
      };
      var queue = api.getQueue();
      queue.push(item);
      write(KEYS.queue, queue);
      return item;
    },

    removeQueued: function (id) {
      var queue = api.getQueue().filter(function (item) {
        return item.id !== id;
      });
      return write(KEYS.queue, queue);
    },

    clearQueue: function () {
      return write(KEYS.queue, []);
    }
  };

  window.CruciStorage = api;
}());
