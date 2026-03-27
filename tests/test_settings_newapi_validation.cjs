const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SETTINGS_JS_PATH = path.join(__dirname, '..', 'static', 'js', 'settings.js');

function createClassList() {
  const values = new Set();
  return {
    add(...items) {
      items.forEach((item) => values.add(item));
    },
    remove(...items) {
      items.forEach((item) => values.delete(item));
    },
    contains(item) {
      return values.has(item);
    },
  };
}

function createElementStub(overrides = {}) {
  return {
    value: '',
    checked: false,
    innerHTML: '',
    textContent: '',
    style: {},
    dataset: {},
    classList: createClassList(),
    addEventListener() {},
    removeEventListener() {},
    querySelectorAll() {
      return [];
    },
    querySelector() {
      return null;
    },
    ...overrides,
  };
}

function createSandbox() {
  const elements = new Map();

  function getElement(id) {
    if (!elements.has(id)) {
      elements.set(id, createElementStub({ id }));
    }
    return elements.get(id);
  }

  const sandbox = {
    console,
    setTimeout,
    clearTimeout,
    document: {
      getElementById(id) {
        return getElement(id);
      },
      querySelectorAll() {
        return [];
      },
      addEventListener() {},
    },
    window: null,
    api: {
      get: async () => [],
      post: async () => ({ success: true }),
      patch: async () => ({ success: true }),
      delete: async () => ({ success: true }),
    },
    toast: {
      success() {},
      error() {},
    },
    confirm: async () => true,
    escapeHtml(value) {
      return String(value ?? '');
    },
  };

  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(SETTINGS_JS_PATH, 'utf8'), sandbox, { filename: 'settings.js' });
  return sandbox;
}

test('validateNewapiApiKeyInput rejects non-ascii text', () => {
  const sandbox = createSandbox();
  const message = vm.runInContext(
    "validateNewapiApiKeyInput('系统访问令牌 (System Access Token)', { required: true })",
    sandbox,
  );

  assert.equal(message, 'Root Token / API Key 只能包含 ASCII 字符，请粘贴实际令牌，不要填写中文说明');
});

test('validateNewapiApiKeyInput allows ascii token', () => {
  const sandbox = createSandbox();
  const message = vm.runInContext(
    "validateNewapiApiKeyInput('token-123', { required: true })",
    sandbox,
  );

  assert.equal(message, '');
});
