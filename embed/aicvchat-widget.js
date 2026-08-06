/**
 * AiCV Chat — embeddable widget (vanilla JS, Shadow DOM)
 * Does not depend on the Next.js frontend. Calls POST /api/chat.
 */
(function (global) {
  "use strict";

  if (global.__AiCVChatLoaded) return;
  global.__AiCVChatLoaded = true;

  function ensureFonts() {
    if (document.getElementById("aicvchat-fonts")) return;
    var pre1 = document.createElement("link");
    pre1.rel = "preconnect";
    pre1.href = "https://fonts.googleapis.com";
    var pre2 = document.createElement("link");
    pre2.rel = "preconnect";
    pre2.href = "https://fonts.gstatic.com";
    pre2.crossOrigin = "anonymous";
    var link = document.createElement("link");
    link.id = "aicvchat-fonts";
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&family=Lora:wght@500;600&display=swap";
    document.head.appendChild(pre1);
    document.head.appendChild(pre2);
    document.head.appendChild(link);
  }

  var STYLE = [
    ":host, * { box-sizing: border-box; }",
    ":host {",
    "  all: initial;",
    "  font-family: 'Lato', 'Segoe UI', Helvetica, Arial, sans-serif;",
    "  color: #0f2a55;",
    "  line-height: 1.45;",
    "  -webkit-font-smoothing: antialiased;",
    "}",
    ":host {",
    "  --blue-900: #0a1e42;",
    "  --blue-800: #0f2a55;",
    "  --blue-700: #143a6a;",
    "  --blue-600: #1c4e8b;",
    "  --blue-500: #2b6fbf;",
    "  --blue-400: #4a8dd0;",
    "  --blue-100: #cfe0f2;",
    "  --blue-50: #eaf2fb;",
    "  --maroon-600: #8a2438;",
    "  --gold-500: #e0ad2e;",
    "  --gold-400: #f2c14e;",
    "  --ink: #0f2a55;",
    "  --body: #2a3350;",
    "  --muted: #5b6478;",
    "  --line: #e2e8f2;",
    "  --white: #ffffff;",
    "  --offwhite: #f7f9fc;",
    "  --shadow-lg: 0 18px 40px rgba(15,42,85,.16), 0 6px 14px rgba(15,42,85,.08);",
    "  --radius: 18px;",
    "  --ease: cubic-bezier(.22,.61,.36,1);",
    "}",
    ".root { position: fixed; inset: auto 20px 20px auto; z-index: var(--aicv-z, 2147483000); font-family: 'Lato', sans-serif; }",
    ".root.left { inset: auto auto 20px 20px; }",
    ".launcher {",
    "  width: 60px; height: 60px; border: 0; border-radius: 50%;",
    "  background: linear-gradient(145deg, var(--blue-700), var(--blue-900));",
    "  color: var(--white); cursor: pointer; display: grid; place-items: center;",
    "  box-shadow: var(--shadow-lg), 0 0 0 4px rgba(232,173,46,.25);",
    "  transition: transform .25s var(--ease), box-shadow .25s var(--ease);",
    "}",
    ".launcher:hover { transform: translateY(-2px) scale(1.03); }",
    ".launcher:focus-visible { outline: 3px solid var(--gold-400); outline-offset: 3px; }",
    ".launcher svg { width: 28px; height: 28px; }",
    ".launcher[aria-expanded='true'] { display: none; }",
    ".panel {",
    "  position: absolute; bottom: 0; right: 0; width: min(400px, calc(100vw - 24px));",
    "  height: min(640px, calc(100vh - 32px));",
    "  background: var(--white); border-radius: var(--radius);",
    "  box-shadow: var(--shadow-lg); display: flex; flex-direction: column;",
    "  overflow: hidden; border: 1px solid var(--line);",
    "  opacity: 0; transform: translateY(12px) scale(.98); pointer-events: none;",
    "  transition: opacity .28s var(--ease), transform .28s var(--ease);",
    "}",
    ".root.left .panel { right: auto; left: 0; }",
    ".panel.open { opacity: 1; transform: none; pointer-events: auto; }",
    ".header {",
    "  flex: 0 0 auto; padding: 14px 16px; color: var(--white);",
    "  background: linear-gradient(135deg, var(--blue-800) 0%, var(--blue-600) 55%, #245a9e 100%);",
    "  display: flex; align-items: center; gap: 12px;",
    "}",
    ".avatar {",
    "  width: 40px; height: 40px; border-radius: 12px; flex: 0 0 auto;",
    "  background: rgba(255,255,255,.12); display: grid; place-items: center;",
    "  border: 1px solid rgba(242,193,78,.55);",
    "}",
    ".avatar svg { width: 22px; height: 22px; }",
    ".header-text { min-width: 0; flex: 1; }",
    ".header-title {",
    "  margin: 0; font-family: 'Lora', Georgia, serif; font-weight: 600;",
    "  font-size: 15px; letter-spacing: .01em; white-space: nowrap;",
    "  overflow: hidden; text-overflow: ellipsis;",
    "}",
    ".header-sub { margin: 2px 0 0; font-size: 12px; color: rgba(255,255,255,.78); }",
    ".status-dot {",
    "  display: inline-block; width: 7px; height: 7px; border-radius: 50%;",
    "  background: #3dcf8e; margin-right: 6px; box-shadow: 0 0 0 3px rgba(61,207,142,.25);",
    "  vertical-align: middle;",
    "}",
    ".icon-btn {",
    "  border: 0; background: rgba(255,255,255,.1); color: var(--white);",
    "  width: 34px; height: 34px; border-radius: 10px; cursor: pointer;",
    "  display: grid; place-items: center; flex: 0 0 auto;",
    "}",
    ".icon-btn:hover { background: rgba(255,255,255,.2); }",
    ".icon-btn:focus-visible { outline: 2px solid var(--gold-400); }",
    ".messages {",
    "  flex: 1 1 auto; overflow-y: auto; padding: 16px 14px;",
    "  background:",
    "    radial-gradient(1200px 400px at 10% -10%, rgba(207,224,242,.55), transparent 55%),",
    "    linear-gradient(180deg, var(--offwhite), #eef3f9);",
    "  scroll-behavior: smooth;",
    "}",
    ".day-sep {",
    "  text-align: center; font-size: 11px; color: var(--muted);",
    "  margin: 6px 0 14px; letter-spacing: .04em; text-transform: uppercase;",
    "}",
    ".row { display: flex; margin-bottom: 12px; gap: 8px; align-items: flex-end; }",
    ".row.user { justify-content: flex-end; }",
    ".row.assistant { justify-content: flex-start; }",
    ".bubble {",
    "  max-width: min(86%, 310px); padding: 10px 12px;",
    "  border-radius: 14px; font-size: 14px; color: var(--body);",
    "  word-wrap: break-word; overflow-wrap: anywhere; white-space: pre-wrap;",
    "}",
    ".row.user .bubble {",
    "  background: linear-gradient(160deg, var(--blue-700), var(--blue-800));",
    "  color: #f5f8fc; border-bottom-right-radius: 4px;",
    "}",
    ".row.assistant .bubble {",
    "  background: var(--white); border: 1px solid var(--line);",
    "  border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(15,42,85,.04);",
    "  color: var(--ink);",
    "}",
    ".meta {",
    "  display: flex; align-items: center; gap: 6px; margin-top: 6px;",
    "  font-size: 11px; line-height: 1; user-select: none;",
    "}",
    ".row.user .meta { justify-content: flex-end; color: rgba(255,255,255,.72); }",
    ".row.assistant .meta { color: var(--muted); }",
    ".ticks { display: inline-flex; align-items: center; gap: 0; }",
    ".ticks svg { width: 14px; height: 14px; display: block; }",
    ".ticks.sent { opacity: .75; }",
    ".ticks.delivered { opacity: .9; }",
    ".ticks.read { color: var(--gold-400); filter: drop-shadow(0 0 1px rgba(224,173,46,.35)); }",
    ".row.user .ticks.read { color: #ffd88f; }",
    ".typing {",
    "  display: inline-flex; align-items: center; gap: 5px; padding: 4px 2px; min-height: 18px;",
    "}",
    ".typing span {",
    "  width: 7px; height: 7px; border-radius: 50%; background: var(--blue-500);",
    "  animation: aicv-bounce 1.2s infinite ease-in-out;",
    "}",
    ".typing span:nth-child(2) { animation-delay: .15s; }",
    ".typing span:nth-child(3) { animation-delay: .3s; }",
    "@keyframes aicv-bounce {",
    "  0%, 80%, 100% { transform: translateY(0); opacity: .45; }",
    "  40% { transform: translateY(-4px); opacity: 1; }",
    "}",
    ".loader-card {",
    "  display: flex; align-items: center; gap: 10px; padding: 4px 0 2px;",
    "  color: var(--muted); font-size: 12.5px;",
    "}",
    ".spinner {",
    "  width: 16px; height: 16px; border-radius: 50%;",
    "  border: 2px solid var(--blue-100); border-top-color: var(--blue-600);",
    "  animation: aicv-spin .7s linear infinite; flex: 0 0 auto;",
    "}",
    "@keyframes aicv-spin { to { transform: rotate(360deg); } }",
    ".matches { margin-top: 10px; display: grid; gap: 8px; }",
    ".match {",
    "  border: 1px solid var(--line); border-radius: 12px; padding: 8px 10px;",
    "  background: var(--blue-50);",
    "}",
    ".match-name { margin: 0; font-size: 13px; font-weight: 700; color: var(--blue-800); }",
    ".match-role { margin: 2px 0 0; font-size: 12px; color: var(--body); }",
    ".match-reason { margin: 4px 0 0; font-size: 11.5px; color: var(--muted); }",
    ".skills { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }",
    ".skill {",
    "  font-size: 10.5px; padding: 2px 7px; border-radius: 999px;",
    "  background: var(--white); color: var(--blue-700); border: 1px solid var(--blue-100);",
    "}",
    ".composer {",
    "  flex: 0 0 auto; border-top: 1px solid var(--line); background: var(--white);",
    "  padding: 10px 12px 12px; display: grid; grid-template-columns: 1fr auto; gap: 8px;",
    "  align-items: end;",
    "}",
    ".composer textarea {",
    "  width: 100%; min-height: 44px; max-height: 120px; resize: none;",
    "  border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px;",
    "  font: inherit; font-size: 14px; color: var(--ink); background: var(--offwhite);",
    "  outline: none;",
    "}",
    ".composer textarea:focus { border-color: var(--blue-400); box-shadow: 0 0 0 3px rgba(43,111,191,.15); }",
    ".composer textarea::placeholder { color: #8a93a8; }",
    ".send {",
    "  width: 44px; height: 44px; border: 0; border-radius: 12px; cursor: pointer;",
    "  background: linear-gradient(145deg, var(--blue-600), var(--blue-800));",
    "  color: var(--white); display: grid; place-items: center;",
    "  box-shadow: 0 8px 18px rgba(28,78,139,.28);",
    "}",
    ".send:disabled { opacity: .45; cursor: not-allowed; box-shadow: none; }",
    ".send:focus-visible { outline: 2px solid var(--gold-400); outline-offset: 2px; }",
    ".send svg { width: 18px; height: 18px; }",
    ".footer-note {",
    "  grid-column: 1 / -1; font-size: 10.5px; color: var(--muted); text-align: center;",
    "}",
    ".error-text { color: var(--maroon-600); }",
    "@media (max-width: 480px) {",
    "  .root, .root.left { inset: 0; width: 100%; height: 100%; }",
    "  .panel {",
    "    position: fixed; inset: 0; width: 100%; height: 100%;",
    "    max-height: none; border-radius: 0; border: 0;",
    "  }",
    "  .launcher { position: fixed; right: 16px; bottom: 16px; }",
    "  .root.left .launcher { right: auto; left: 16px; }",
    "  .bubble { max-width: 92%; }",
    "}"
  ].join("\n");

  var ICONS = {
    chat:
      '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 5.5A2.5 2.5 0 0 1 7.5 3h9A2.5 2.5 0 0 1 19 5.5v7A2.5 2.5 0 0 1 16.5 15H13l-3.2 3.2c-.5.5-1.3.1-1.3-.6V15H7.5A2.5 2.5 0 0 1 5 12.5v-7Z" stroke="currentColor" stroke-width="1.7"/><circle cx="9" cy="9" r="1" fill="currentColor"/><circle cx="12" cy="9" r="1" fill="currentColor"/><circle cx="15" cy="9" r="1" fill="currentColor"/></svg>',
    close:
      '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M7 7l10 10M17 7 7 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    send:
      '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4.5 11.2 19 4.8l-5.2 14.4-2.3-5.2-5-2.8Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="m11.5 13.2 7.5-8.4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>',
    bot:
      '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="4" y="7" width="16" height="11" rx="3" stroke="currentColor" stroke-width="1.6"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7" stroke="currentColor" stroke-width="1.6"/><circle cx="9.5" cy="12.5" r="1.1" fill="currentColor"/><circle cx="14.5" cy="12.5" r="1.1" fill="currentColor"/><path d="M9 16h6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    check:
      '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3.5 8.2 6.2 11l6.3-7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    checks:
      '<svg viewBox="0 0 18 16" fill="none" aria-hidden="true"><path d="M1.5 8.2 4.2 11 10.5 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.2 8.2 8.9 11 15.2 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };

  function mergeConfig() {
    var page = global.AiCVChatConfig || {};
    var base = {
      apiBaseUrl: "",
      siteKey: "",
      chatPath: "/api/chat",
      sessionPath: "/api/embed/session",
      title: "eMasters Talent Assistant",
      subtitle: "IIT Kanpur · AI & ML cohort",
      welcomeMessage:
        "Hi! Ask about AI & ML talent from the eMasters programme — skills, experience, roles, or domains.",
      placeholder: "Ask about skills, roles, experience…",
      launcherLabel: "Chat with talent assistant",
      position: "right",
      openOnLoad: false,
      historyLimit: 12,
      showMatches: true,
      requestTimeoutMs: 120000,
      zIndex: 2147483000
    };
    return Object.assign({}, base, page);
  }

  function resolveApiBase(cfg, scriptEl) {
    if (cfg.apiBaseUrl && String(cfg.apiBaseUrl).trim()) {
      return String(cfg.apiBaseUrl).replace(/\/$/, "");
    }
    try {
      if (scriptEl && scriptEl.src) {
        return new URL(scriptEl.src, global.location.href).origin;
      }
    } catch (e) { /* ignore */ }
    if (global.location && /^https?:$/i.test(global.location.protocol)) {
      return global.location.origin;
    }
    return "http://localhost:8000";
  }

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function formatTime(date) {
    var d = date instanceof Date ? date : new Date(date);
    var h = d.getHours();
    var m = d.getMinutes();
    var ampm = h >= 12 ? "PM" : "AM";
    var h12 = h % 12 || 12;
    return h12 + ":" + pad(m) + " " + ampm;
  }

  function formatDay(date) {
    var d = date instanceof Date ? date : new Date(date);
    var today = new Date();
    var yday = new Date();
    yday.setDate(today.getDate() - 1);
    if (d.toDateString() === today.toDateString()) return "Today";
    if (d.toDateString() === yday.toDateString()) return "Yesterday";
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: d.getFullYear() !== today.getFullYear() ? "numeric" : undefined
    });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function createHost(cfg) {
    ensureFonts();
    var host = document.createElement("div");
    host.id = "aicvchat-widget-host";
    host.style.zIndex = String(cfg.zIndex);
    var shadow = host.attachShadow({ mode: "open" });

    var style = document.createElement("style");
    style.textContent = STYLE;
    shadow.appendChild(style);

    var root = document.createElement("div");
    root.className = "root" + (cfg.position === "left" ? " left" : "");
    root.style.setProperty("--aicv-z", String(cfg.zIndex));
    root.innerHTML =
      '<button type="button" class="launcher" aria-expanded="false" aria-controls="aicv-panel" title="' +
      escapeHtml(cfg.launcherLabel) +
      '">' +
      ICONS.chat +
      '</button>' +
      '<section class="panel" id="aicv-panel" role="dialog" aria-modal="false" aria-label="' +
      escapeHtml(cfg.title) +
      '" hidden>' +
      '  <header class="header">' +
      '    <div class="avatar" aria-hidden="true">' +
      ICONS.bot +
      "</div>" +
      '    <div class="header-text">' +
      '      <h2 class="header-title">' +
      escapeHtml(cfg.title) +
      "</h2>" +
      '      <p class="header-sub"><span class="status-dot"></span>' +
      escapeHtml(cfg.subtitle) +
      "</p>" +
      "    </div>" +
      '    <button type="button" class="icon-btn close-btn" aria-label="Close chat">' +
      ICONS.close +
      "</button>" +
      "  </header>" +
      '  <div class="messages" role="log" aria-live="polite" aria-relevant="additions"></div>' +
      '  <form class="composer">' +
      '    <textarea rows="1" maxlength="2000" placeholder="' +
      escapeHtml(cfg.placeholder) +
      '" aria-label="Message"></textarea>' +
      '    <button type="submit" class="send" aria-label="Send message" disabled>' +
      ICONS.send +
      "</button>" +
      '    <div class="footer-note">Responses may take 15–20s on CPU · powered by local AI</div>' +
      "  </form>" +
      "</section>";

    shadow.appendChild(root);
    document.body.appendChild(host);
    return { host: host, shadow: shadow, root: root };
  }

  function AiCVChat(cfg, scriptEl) {
    this.cfg = cfg;
    this.apiBase = resolveApiBase(cfg, scriptEl);
    this.history = [];
    this.messages = [];
    this.busy = false;
    this.open = false;
    this.accessToken = null;
    this.tokenExpiresAt = 0;
    this.authError = null;
    this.ui = createHost(cfg);
    this.els = {
      launcher: this.ui.root.querySelector(".launcher"),
      panel: this.ui.root.querySelector(".panel"),
      close: this.ui.root.querySelector(".close-btn"),
      messages: this.ui.root.querySelector(".messages"),
      form: this.ui.root.querySelector(".composer"),
      input: this.ui.root.querySelector("textarea"),
      send: this.ui.root.querySelector(".send")
    };
    this._bind();
    this._seedWelcome();
    if (cfg.openOnLoad) this.setOpen(true);
    // Prefetch session when site key present
    if (cfg.siteKey) {
      this.ensureSession().catch(function () { /* surfaced on send */ });
    }
  }

  AiCVChat.prototype.ensureSession = function (force) {
    var self = this;
    var key = (this.cfg.siteKey || "").trim();
    if (!key) {
      return Promise.resolve(null);
    }
    var now = Date.now();
    // Refresh 60s before expiry
    if (
      !force &&
      this.accessToken &&
      this.tokenExpiresAt &&
      now < this.tokenExpiresAt - 60000
    ) {
      return Promise.resolve(this.accessToken);
    }
    var url = this.apiBase + (this.cfg.sessionPath || "/api/embed/session");
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ site_key: key })
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          var detail =
            (data && (data.detail || data.message)) ||
            "Unauthorized embed domain or site key";
          if (typeof detail !== "string") detail = JSON.stringify(detail);
          self.authError = detail;
          self.accessToken = null;
          throw new Error(detail);
        }
        self.accessToken = data.access_token;
        self.tokenExpiresAt = Date.now() + (Number(data.expires_in) || 600) * 1000;
        self.authError = null;
        if (data.api_base_url) self.apiBase = String(data.api_base_url).replace(/\/$/, "");
        return self.accessToken;
      });
    });
  };

  AiCVChat.prototype._bind = function () {
    var self = this;
    this.els.launcher.addEventListener("click", function () {
      self.setOpen(true);
    });
    this.els.close.addEventListener("click", function () {
      self.setOpen(false);
    });
    this.els.form.addEventListener("submit", function (e) {
      e.preventDefault();
      self.send();
    });
    this.els.input.addEventListener("input", function () {
      self._autosize();
      self.els.send.disabled = self.busy || !self.els.input.value.trim();
    });
    this.els.input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        self.send();
      }
    });
    global.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && self.open) self.setOpen(false);
    });
  };

  AiCVChat.prototype.setOpen = function (open) {
    this.open = !!open;
    this.els.launcher.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      this.els.panel.hidden = false;
      // force reflow for transition
      void this.els.panel.offsetWidth;
      this.els.panel.classList.add("open");
      this.els.input.focus();
      this._scrollBottom();
    } else {
      this.els.panel.classList.remove("open");
      var panel = this.els.panel;
      setTimeout(function () {
        if (!panel.classList.contains("open")) panel.hidden = true;
      }, 280);
      this.els.launcher.focus();
    }
  };

  AiCVChat.prototype._autosize = function () {
    var el = this.els.input;
    el.style.height = "auto";
    el.style.height = Math.min(120, Math.max(44, el.scrollHeight)) + "px";
  };

  AiCVChat.prototype._scrollBottom = function () {
    var box = this.els.messages;
    box.scrollTop = box.scrollHeight;
  };

  AiCVChat.prototype._seedWelcome = function () {
    this._pushMessage({
      id: "welcome",
      role: "assistant",
      content: this.cfg.welcomeMessage,
      at: new Date(),
      status: "read"
    });
    this._render();
  };

  AiCVChat.prototype._pushMessage = function (msg) {
    this.messages.push(msg);
    return msg;
  };

  AiCVChat.prototype._markUserMessagesRead = function () {
    for (var i = 0; i < this.messages.length; i++) {
      var m = this.messages[i];
      if (m.role === "user" && m.status !== "read") m.status = "read";
    }
  };

  AiCVChat.prototype._ticksHtml = function (status) {
    if (status === "read") {
      return '<span class="ticks read" title="Read">' + ICONS.checks + "</span>";
    }
    if (status === "delivered") {
      return '<span class="ticks delivered" title="Delivered">' + ICONS.checks + "</span>";
    }
    return '<span class="ticks sent" title="Sent">' + ICONS.check + "</span>";
  };

  AiCVChat.prototype._matchHtml = function (matches) {
    if (!this.cfg.showMatches || !matches || !matches.length) return "";
    var html = '<div class="matches">';
    for (var i = 0; i < matches.length; i++) {
      var m = matches[i];
      var skills = (m.top_skills || []).slice(0, 5);
      var skillHtml = skills
        .map(function (s) {
          return '<span class="skill">' + escapeHtml(s) + "</span>";
        })
        .join("");
      var roleBits = [];
      if (m.current_title) roleBits.push(m.current_title);
      if (m.years_experience != null) roleBits.push(m.years_experience + " yrs");
      html +=
        '<article class="match">' +
        '<p class="match-name">' +
        escapeHtml(m.full_name || "Candidate") +
        "</p>" +
        (roleBits.length
          ? '<p class="match-role">' + escapeHtml(roleBits.join(" · ")) + "</p>"
          : "") +
        (m.short_match_reason
          ? '<p class="match-reason">' + escapeHtml(m.short_match_reason) + "</p>"
          : "") +
        (skillHtml ? '<div class="skills">' + skillHtml + "</div>" : "") +
        "</article>";
    }
    return html + "</div>";
  };

  AiCVChat.prototype._render = function () {
    var box = this.els.messages;
    var html = "";
    var lastDay = "";
    for (var i = 0; i < this.messages.length; i++) {
      var m = this.messages[i];
      var day = formatDay(m.at);
      if (day !== lastDay) {
        html += '<div class="day-sep">' + escapeHtml(day) + "</div>";
        lastDay = day;
      }
      if (m.kind === "typing") {
        html +=
          '<div class="row assistant" data-id="' +
          escapeHtml(m.id) +
          '"><div class="bubble" aria-label="Assistant is typing">' +
          '<div class="typing" aria-hidden="true"><span></span><span></span><span></span></div>' +
          '<div class="loader-card"><span class="spinner" aria-hidden="true"></span>' +
          "<span>" +
          escapeHtml(m.content || "Thinking… searching resumes") +
          "</span></div>" +
          "</div></div>";
        continue;
      }
      var body =
        '<div class="bubble">' +
        (m.isError
          ? '<span class="error-text">' + escapeHtml(m.content) + "</span>"
          : escapeHtml(m.content)) +
        this._matchHtml(m.matches) +
        '<div class="meta"><span class="time">' +
        escapeHtml(formatTime(m.at)) +
        "</span>" +
        (m.role === "user" ? this._ticksHtml(m.status || "sent") : "") +
        "</div></div>";
      html +=
        '<div class="row ' +
        m.role +
        '" data-id="' +
        escapeHtml(m.id) +
        '">' +
        body +
        "</div>";
    }
    box.innerHTML = html;
    this._scrollBottom();
  };

  AiCVChat.prototype._setBusy = function (busy) {
    this.busy = busy;
    this.els.send.disabled = busy || !this.els.input.value.trim();
    this.els.input.disabled = busy;
  };

  AiCVChat.prototype._showTyping = function (label) {
    this._removeTyping();
    this._pushMessage({
      id: "typing",
      kind: "typing",
      role: "assistant",
      content: label || "Thinking… searching resumes",
      at: new Date()
    });
    this._render();
  };

  AiCVChat.prototype._removeTyping = function () {
    this.messages = this.messages.filter(function (m) {
      return m.kind !== "typing" && m.id !== "typing";
    });
  };

  AiCVChat.prototype._historyPayload = function () {
    var limit = this.cfg.historyLimit || 12;
    var items = [];
    for (var i = 0; i < this.history.length; i++) {
      items.push({
        role: this.history[i].role,
        content: this.history[i].content
      });
    }
    if (items.length > limit) items = items.slice(items.length - limit);
    return items;
  };

  AiCVChat.prototype.send = function () {
    var text = (this.els.input.value || "").trim();
    if (!text || this.busy) return;

    var self = this;
    var userMsg = this._pushMessage({
      id: "u-" + Date.now(),
      role: "user",
      content: text,
      at: new Date(),
      status: "sent"
    });
    this.history.push({ role: "user", content: text });
    this.els.input.value = "";
    this._autosize();
    this._render();
    this._setBusy(true);
    this._showTyping("Securing session…");

    var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = null;
    if (controller) {
      timer = setTimeout(function () {
        controller.abort();
      }, this.cfg.requestTimeoutMs || 120000);
    }

    var url = this.apiBase + (this.cfg.chatPath || "/api/chat");

    this.ensureSession()
      .then(function (token) {
        self._showTyping("Thinking… this can take up to 20s");
        var headers = {
          "Content-Type": "application/json",
          Accept: "application/json"
        };
        if (token) headers.Authorization = "Bearer " + token;
        return fetch(url, {
          method: "POST",
          headers: headers,
          body: JSON.stringify({
            message: text,
            history: self._historyPayload(),
            filters: null
          }),
          signal: controller ? controller.signal : undefined
        });
      })
      .then(function (res) {
        userMsg.status = "delivered";
        self._render();
        if (!res.ok) {
          if (res.status === 401 || res.status === 403) {
            self.accessToken = null;
            throw new Error(
              "This website is not authorized to use the assistant (domain/site key)."
            );
          }
          if (res.status === 429) {
            throw new Error("Too many requests. Please wait a moment and try again.");
          }
          throw new Error("Request failed (" + res.status + ")");
        }
        return res.json();
      })
      .then(function (data) {
        self._removeTyping();
        self._markUserMessagesRead();
        var answer = (data && data.answer) || "I could not generate an answer right now.";
        var matches = (data && data.matches) || [];
        self._pushMessage({
          id: "a-" + Date.now(),
          role: "assistant",
          content: answer,
          matches: matches,
          at: new Date(),
          status: "read"
        });
        self.history.push({ role: "assistant", content: answer });
        self._render();
      })
      .catch(function (err) {
        self._removeTyping();
        userMsg.status = "delivered";
        var msg;
        if (err && err.name === "AbortError") {
          msg = "The request timed out. Please try again.";
        } else if (err && err.message) {
          msg = err.message;
        } else {
          msg =
            "Something went wrong reaching the assistant. Check the API URL and site key.";
        }
        self._pushMessage({
          id: "e-" + Date.now(),
          role: "assistant",
          content: msg,
          at: new Date(),
          isError: true,
          status: "read"
        });
        self._render();
      })
      .finally(function () {
        if (timer) clearTimeout(timer);
        self._setBusy(false);
        self.els.input.focus();
      });
  };

  AiCVChat.prototype.destroy = function () {
    if (this.ui && this.ui.host && this.ui.host.parentNode) {
      this.ui.host.parentNode.removeChild(this.ui.host);
    }
    global.__AiCVChatLoaded = false;
    global.AiCVChatInstance = null;
  };

  function boot() {
    var cfg = mergeConfig();
    var scriptEl =
      document.currentScript ||
      (function () {
        var nodes = document.getElementsByTagName("script");
        for (var i = nodes.length - 1; i >= 0; i--) {
          if ((nodes[i].src || "").indexOf("aicvchat-widget") !== -1) return nodes[i];
        }
        return null;
      })();

    function start() {
      if (global.AiCVChatInstance) return global.AiCVChatInstance;
      global.AiCVChatInstance = new AiCVChat(cfg, scriptEl);
      return global.AiCVChatInstance;
    }

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", start);
    } else {
      start();
    }
  }

  global.AiCVChat = {
    init: function (overrides) {
      if (overrides) {
        global.AiCVChatConfig = Object.assign({}, global.AiCVChatConfig || {}, overrides);
      }
      if (global.AiCVChatInstance) return global.AiCVChatInstance;
      boot();
      return global.AiCVChatInstance;
    },
    destroy: function () {
      if (global.AiCVChatInstance) global.AiCVChatInstance.destroy();
    },
    open: function () {
      if (global.AiCVChatInstance) global.AiCVChatInstance.setOpen(true);
    },
    close: function () {
      if (global.AiCVChatInstance) global.AiCVChatInstance.setOpen(false);
    }
  };

  boot();
})(typeof window !== "undefined" ? window : globalThis);
