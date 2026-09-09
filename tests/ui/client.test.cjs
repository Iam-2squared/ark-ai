// Unit tests of the shipped script with a minimal DOM/fetch double, not a browser render.
// Native Windows IME, layout and real/offline inference remain target-PC gates.
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const { test } = require("node:test");
const { runInNewContext } = require("node:vm");

const staticRoot = resolve(__dirname, "../../src/ark/ui/static");
const html = readFileSync(resolve(staticRoot, "index.html"), "utf8");
const script = readFileSync(resolve(staticRoot, "app.js"), "utf8");

class Element {
  constructor() {
    this.value = "";
    this.disabled = false;
    this.hidden = false;
    this.children = [];
    this.listeners = new Map();
    this.dataset = {};
    this.classList = { toggle() {} };
    this.scrollTop = 0;
    this.scrollHeight = 100;
    this.clientHeight = 100;
    this.content = "";
  }
  set textContent(value) { this.content = value; this.children = []; }
  get textContent() { return this.content + this.children.map((c) => c.textContent).join(""); }
  set innerHTML(_) { throw new Error("Untrusted HTML rendering is forbidden"); }
  setAttribute() {}
  append(...children) { this.children.push(...children); }
  replaceChildren(fragment) { this.children = [...fragment.children]; }
  focus() {}
  addEventListener(type, fn) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(fn);
    this.listeners.set(type, listeners);
  }
  dispatch(type, details = {}) {
    let prevented = false;
    const event = { preventDefault() { prevented = true; }, ...details };
    (this.listeners.get(type) || []).forEach((fn) => fn(event));
    return prevented;
  }
  requestSubmit() { this.dispatch("submit"); }
}

async function settle() {
  for (let i = 0; i < 6; i += 1) await new Promise(setImmediate);
}

async function app() {
  const elements = new Map([...html.matchAll(/\bid="([^"]+)"/g)].map((m) => [m[1], new Element()]));
  const suggestions = [...html.matchAll(/\bdata-prompt="([^"]+)"/g)].map((m) => {
    const element = new Element();
    element.dataset.prompt = m[1];
    return element;
  });
  const server = {
    state: "ready", revision: 1, token: "process-one", intelligence: "V2",
    model: { name: "test.gguf", local_model: true, quantization: "Q4_K_M" },
    logging: true, messages: [], pending_message: null, error: null, dropped_turns: 0,
  };
  let online = true;
  const writes = [];
  const polls = [];
  runInNewContext(script, {
    document: {
      getElementById: (id) => { assert.ok(elements.has(id), `missing HTML element: ${id}`); return elements.get(id); },
      querySelectorAll: () => suggestions,
      createElement: () => new Element(),
      createDocumentFragment: () => new Element(),
      createTextNode: (value) => { const node = new Element(); node.textContent = value; return node; },
    },
    window: { setTimeout: (callback) => polls.push(callback) },
    AbortSignal,
    fetch: async (url, options) => {
      assert.ok(["/api/status", "/api/chat", "/api/reset"].includes(url));
      if (!online) throw new Error("connection lost");
      if (options.method === "POST") {
        const payload = JSON.parse(options.body);
        assert.equal(options.headers["X-ARK-Token"], server.token);
        writes.push({ url, payload });
        if (payload.revision !== server.revision) return { ok: false, json: async () => ({ error: "stale revision" }) };
        server.revision += 1;
        if (url === "/api/chat") {
          server.state = "generating";
          server.pending_message = payload.message;
          server.error = null;
        } else {
          server.messages = [];
          server.error = null;
        }
      }
      const snapshot = structuredClone(server);
      return { ok: true, json: async () => snapshot };
    },
  });
  await settle();
  return {
    server, writes, get: (id) => elements.get(id), suggestions,
    setOnline: (value) => { online = value; },
    tick: async () => { assert.ok(polls.length); polls.shift()(); await settle(); },
    type: (value) => { const input = elements.get("message-input"); input.value = value; input.dispatch("input"); },
    complete: (answer, error = null) => {
      if (!error) server.messages.push({ role: "user", content: server.pending_message }, { role: "assistant", content: answer });
      server.state = "ready";
      server.pending_message = null;
      server.error = error;
      server.revision += 1;
    },
  };
}

test("Enter sends once; duplicate submission and reset stay disabled during generation", async () => {
  const ui = await app();
  assert.equal(ui.get("local-label").textContent, "LOCAL MODEL");
  assert.equal(ui.get("model-detail").textContent, "test.gguf");
  ui.type("こんにちは");
  assert.equal(ui.get("message-input").dispatch("keydown", { key: "Enter" }), true);
  ui.get("chat-form").requestSubmit();
  ui.get("reset").dispatch("click");
  await settle();
  assert.equal(ui.writes.length, 1);
  assert.equal(ui.writes[0].payload.message, "こんにちは");
  assert.equal(ui.get("send").disabled, true);
  assert.equal(ui.get("reset").disabled, true);
  assert.match(ui.get("messages").textContent, /Generating/);
  ui.complete("こんにちは。");
  await ui.tick();
  assert.equal(ui.get("message-input").disabled, false);
  assert.match(ui.get("messages").textContent, /こんにちは。/);
  ui.get("reset").dispatch("click");
  await settle();
  assert.equal(ui.writes.at(-1).url, "/api/reset");
  assert.equal(ui.get("messages").children.length, 0);
  assert.equal(ui.get("welcome").hidden, false);
});

test("Shift+Enter and Japanese composition Enter do not submit", async () => {
  const ui = await app();
  const input = ui.get("message-input");
  ui.type("日本語");
  assert.equal(input.dispatch("keydown", { key: "Enter", shiftKey: true }), false);
  assert.equal(input.dispatch("keydown", { key: "Enter", isComposing: true }), false);
  input.dispatch("compositionstart");
  assert.equal(input.dispatch("keydown", { key: "Enter" }), false);
  input.dispatch("compositionend");
  assert.equal(input.dispatch("keydown", { key: "Enter", keyCode: 229 }), false);
  assert.equal(ui.writes.length, 0);
  input.dispatch("keydown", { key: "Enter" });
  await settle();
  assert.equal(ui.writes.length, 1);
});

test("generation error restores draft and displays literal, untrusted output safely", async () => {
  const ui = await app();
  ui.type("<script>not executable</script>");
  ui.get("chat-form").requestSubmit();
  await settle();
  ui.complete(null, "generation failed");
  await ui.tick();
  assert.equal(ui.get("error").textContent, "generation failed");
  assert.equal(ui.get("message-input").value, "<script>not executable</script>");
  ui.get("chat-form").requestSubmit();
  await settle();
  ui.complete('<img src=x onerror="malicious()">');
  await ui.tick();
  assert.match(ui.get("messages").textContent, /<img src=x/);
});

test("connection failure is visible, is not retried as a write, and recovers", async () => {
  const ui = await app();
  ui.type("keep this draft");
  ui.setOnline(false);
  ui.get("chat-form").requestSubmit();
  await settle();
  assert.equal(ui.get("message-input").value, "keep this draft");
  assert.equal(ui.get("send").disabled, true);
  assert.equal(ui.get("error").hidden, false);
  ui.setOnline(true);
  await ui.tick();
  assert.equal(ui.get("send").disabled, false);
  assert.equal(ui.writes.length, 0);
});

test("mock, loading and load error states cannot claim a ready real model", async () => {
  const ui = await app();
  ui.server.model.local_model = false;
  await ui.tick();
  assert.equal(ui.get("local-label").textContent, "MOCK · NO MODEL");
  ui.server.state = "loading";
  ui.server.model = null;
  await ui.tick();
  assert.equal(ui.get("message-input").disabled, true);
  assert.equal(ui.get("local-label").textContent, "LOCAL UI");
  ui.server.state = "error";
  ui.server.error = "missing model";
  await ui.tick();
  assert.equal(ui.get("error").textContent, "missing model");
  assert.equal(ui.get("send").disabled, true);
});

test("bundled resources have no CDN, remote fonts, inline scripts or external URLs", () => {
  for (const match of html.matchAll(/\b(?:src|href)="([^"]+)"/g)) {
    assert.ok(["/", "/mark.svg", "/app.css", "/app.js"].includes(match[1]));
  }
  assert.doesNotMatch(html, /\son\w+=|<style>|<script>/i);
  assert.doesNotMatch(readFileSync(resolve(staticRoot, "app.css"), "utf8"), /@import|url\s*\(/i);
  assert.doesNotMatch(script, /https?:\/\//i);
});
