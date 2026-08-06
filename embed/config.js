/**
 * AiCV Chat Widget — developer configuration
 *
 * Load this file BEFORE aicvchat-widget.js, or set window.AiCVChatConfig
 * inline in your page. Values here are defaults; page-level config wins.
 *
 * apiBaseUrl:
 *   Leave empty ("") to auto-detect from the widget script's origin
 *   (recommended when the script is served from the API host at /embed/).
 *   Otherwise set an absolute API origin, e.g. "https://api.example.com"
 */
(function (global) {
  "use strict";

  var defaults = {
    /** API origin only — no trailing slash. Empty = auto from script src. */
    apiBaseUrl: "",

    /**
     * Site key from POST /api/admin/embed-sites (required when EMBED_AUTH_REQUIRED).
     * Prefer baking via /embed/loader.js?key=...
     */
    siteKey: "",

    /** Chat endpoint path (appended to apiBaseUrl). Secured embed route. */
    chatPath: "/api/embed/chat",

    /** Session endpoint path */
    sessionPath: "/api/embed/session",

    /** Launcher / header labels */
    title: "eMasters Talent Assistant",
    subtitle: "IIT Kanpur · AI & ML cohort",
    welcomeMessage:
      "Hi! Ask about AI & ML talent from the eMasters programme — skills, experience, roles, or domains.",
    placeholder: "Ask about skills, roles, experience…",
    launcherLabel: "Chat with talent assistant",

    /** Position: "right" | "left" */
    position: "right",

    /** Open panel on load */
    openOnLoad: false,

    /** Max messages kept in client history sent to the API */
    historyLimit: 12,

    /** Show candidate match cards under assistant replies */
    showMatches: true,

    /** Request timeout (ms) — Ollama can be slow on CPU */
    requestTimeoutMs: 120000,

    /** Z-index for the floating widget */
    zIndex: 2147483000
  };

  global.AiCVChatConfig = Object.assign(
    {},
    defaults,
    global.AiCVChatConfig || {}
  );
})(typeof window !== "undefined" ? window : globalThis);
