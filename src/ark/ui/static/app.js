"use strict";

(() => {
  const byId = (id) => document.getElementById(id);
  const input = byId("message-input");
  const send = byId("send");
  const reset = byId("reset");
  const suggestions = [...document.querySelectorAll("[data-prompt]")];
  const messages = byId("messages");
  const scrollArea = byId("scroll-area");
  let state = null;
  let connected = false;
  let actionPending = false;
  let composing = false;
  let transportError = "";
  let connectionError = "";
  let lastSubmission = "";
  let submittedRevision = -1;
  let displaySignature = "";
  let refreshing = null;

  function notice(id, text) {
    byId(id).textContent = text || "";
    byId(id).hidden = !text;
  }

  function controls() {
    const ready = connected && state?.state === "ready" && !actionPending;
    input.disabled = !ready;
    send.disabled = !ready || !input.value.trim();
    reset.disabled = !ready;
    suggestions.forEach((button) => { button.disabled = !ready; });
  }

  function messageElement(role, text, pending = false) {
    const article = document.createElement("article");
    article.className = `message ${role}${pending ? " pending" : ""}`;
    const label = document.createElement("div");
    label.className = "message-label";
    if (role === "assistant") {
      const icon = document.createElement("img");
      icon.src = "/mark.svg";
      icon.alt = "";
      label.append(icon);
    }
    label.append(document.createTextNode(role === "user" ? "YOU" : "ARK"));
    const body = document.createElement("div");
    body.className = "message-content";
    // Treat model and user output as text, including HTML/script-looking answers.
    body.textContent = text;
    if (pending) {
      const dots = document.createElement("span");
      dots.className = "generating-dots";
      dots.setAttribute("aria-hidden", "true");
      for (let i = 0; i < 3; i += 1) dots.append(document.createElement("span"));
      body.append(dots);
    }
    article.append(label, body);
    return article;
  }

  function render() {
    if (!state) { controls(); return; }
    const model = state.model;
    const phase = state.state;
    const labels = { loading: "Loading model", ready: "Ready", generating: "Generating…", error: "Needs attention" };
    byId("state-label").textContent = connected ? labels[phase] : "Disconnected";
    byId("model-name").textContent = model?.name || (phase === "error" ? "モデル未接続" : "モデルを読み込み中…");
    byId("model-detail").textContent = model?.name || "—";
    byId("quantization").textContent = model?.quantization || "—";
    byId("logging").textContent = state.logging ? "Local JSONL" : "Off";
    byId("local-label").textContent = model ? (model.local_model ? "LOCAL MODEL" : "MOCK · NO MODEL") : "LOCAL UI";
    byId("local-badge").classList.toggle("mock", !!model && !model.local_model);
    byId("composer-state").textContent = !connected ? "サーバーとの接続を確認してください" : {
      loading: "モデルを準備しています",
      ready: model?.local_model ? "ローカルモデルで応答" : "Mock demo · Echo応答",
      generating: "回答を生成しています…",
      error: "エラーを確認してサーバーを再起動してください",
    }[phase];
    notice("error", connectionError || transportError || state.error);
    notice("warning", state.warning);
    byId("context-note").hidden = !state.dropped_turns;
    const signature = JSON.stringify([state.messages, state.pending_message]);
    if (signature !== displaySignature) {
      const follow = scrollArea.scrollHeight - scrollArea.scrollTop - scrollArea.clientHeight < 100;
      const previousTop = scrollArea.scrollTop;
      const fragment = document.createDocumentFragment();
      state.messages.forEach((message) => fragment.append(messageElement(message.role, message.content)));
      if (state.pending_message) {
        fragment.append(messageElement("user", state.pending_message));
        fragment.append(messageElement("assistant", "Generating", true));
      }
      messages.replaceChildren(fragment);
      byId("welcome").hidden = !!(state.messages.length || state.pending_message);
      displaySignature = signature;
      scrollArea.scrollTop = follow || lastSubmission ? scrollArea.scrollHeight : previousTop;
    }
    if (state.revision > submittedRevision && phase !== "generating" && lastSubmission) {
      if (state.error && !input.value) input.value = lastSubmission;
      lastSubmission = "";
    }
    controls();
  }

  async function api(path, payload) {
    const options = { cache: "no-store", signal: AbortSignal.timeout(15000) };
    if (payload) {
      options.method = "POST";
      options.headers = { "Content-Type": "application/json", "X-ARK-Token": state.token };
      options.body = JSON.stringify(payload);
    }
    const response = await fetch(path, options);
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
    return body;
  }

  function refresh() {
    if (refreshing) return refreshing;
    refreshing = (async () => {
      try {
        const incoming = await api("/api/status");
        if (!state || incoming.token !== state.token || incoming.revision >= state.revision) state = incoming;
        connected = true;
        connectionError = "";
      } catch {
        connected = false;
        connectionError = "ARKに接続できません。ターミナルでサーバーが動作しているか確認してください。送信は自動再試行されません。";
      }
      render();
      notice("error", connectionError || transportError || state?.error);
    })().finally(() => { refreshing = null; });
    return refreshing;
  }

  async function act(path, payload) {
    actionPending = true;
    transportError = "";
    controls();
    try {
      submittedRevision = state.revision + 1;
      await api(path, { ...payload, revision: state.revision });
      if (path === "/api/chat") {
        lastSubmission = input.value;
        input.value = "";
      }
    } catch (error) {
      transportError = `${error.message} 状態を確認してから再操作してください。`;
    } finally {
      // Drain an older poll before reading the post-action state.
      if (refreshing) await refreshing;
      await refresh();
      actionPending = false;
      controls();
      if (!input.disabled) input.focus();
    }
  }

  byId("chat-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (send.disabled || composing) return;
    void act("/api/chat", { message: input.value });
  });
  input.addEventListener("compositionstart", () => { composing = true; });
  input.addEventListener("compositionend", () => { composing = false; });
  input.addEventListener("keydown", (event) => {
    // keyCode 229 also covers Windows IME's Enter/composition ordering.
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing && !composing && event.keyCode !== 229) {
      event.preventDefault();
      byId("chat-form").requestSubmit();
    }
  });
  input.addEventListener("input", controls);
  reset.addEventListener("click", () => { if (!reset.disabled) void act("/api/reset", {}); });
  suggestions.forEach((button) => button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    controls();
    input.focus();
  }));
  async function poll() {
    await refresh();
    window.setTimeout(poll, state?.state === "generating" ? 700 : 1400);
  }
  void poll();
})();
