// 核心逻辑单元测试 + 生成产物冒烟测试 + 无头启动测试（无框架，仅用 Node 内置模块）。
// 运行：node tests/test_logic.js
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const core = require("../snake_core.js");

let passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log("  ✓ " + name);
}

function noOverlap(state) {
  const keys = new Set();
  for (const s of state.snake) {
    const k = s.x + "," + s.y;
    assert(!keys.has(k), "蛇身自身重叠");
    keys.add(k);
  }
  for (const m of state.mines) {
    const k = m.x + "," + m.y;
    assert(!keys.has(k), "雷与蛇/食物重叠");
    keys.add(k);
  }
  if (state.food) {
    const k = state.food.x + "," + state.food.y;
    assert(!keys.has(k), "食物与蛇/雷重叠");
  }
}

// 极简 DOM/Canvas 桩，用于无头启动冒烟测试。
function makeCtx() {
  return {
    fillStyle: "", strokeStyle: "", lineWidth: 1, globalAlpha: 1, lineCap: "", lineJoin: "",
    fillRect: function () {}, beginPath: function () {}, moveTo: function () {},
    lineTo: function () {}, stroke: function () {}, arc: function () {}, fill: function () {},
    setTransform: function () {}
  };
}
function makeEl() {
  return {
    textContent: "", innerHTML: "", style: {}, width: 0, height: 0, className: "", value: "",
    classList: { add: function () {}, remove: function () {}, contains: function () { return false; } },
    addEventListener: function () {},
    appendChild: function () {},
    getContext: makeCtx
  };
}

console.log("核心逻辑测试：");
test("createState 默认值正确", () => {
  const s = core.createState({ cols: 20, rows: 20 });
  assert.strictEqual(s.cols, 20);
  assert.strictEqual(s.rows, 20);
  assert.strictEqual(s.score, 0);
  assert.strictEqual(s.steps, 0);
  assert.strictEqual(s.lives, 3);
  assert.strictEqual(s.status, "ready");
  assert.strictEqual(s.snake.length, 3);
  assert.strictEqual(s.mines.length, 3);
  assert.ok(s.food, "应有食物");
  noOverlap(s);
});

test("tick 向右移动一格并计步", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  s.food = null;
  const head = { x: s.snake[0].x, y: s.snake[0].y };
  core.tick(s);
  assert.strictEqual(s.steps, 1);
  assert.strictEqual(s.snake[0].x, head.x + 1);
  assert.strictEqual(s.snake[0].y, head.y);
  assert.strictEqual(s.snake.length, 3);
});

test("吃到食物加分并变长", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  s.food = { x: s.snake[0].x + 1, y: s.snake[0].y };
  const len = s.snake.length;
  core.tick(s);
  assert.strictEqual(s.score, 10);
  assert.strictEqual(s.snake.length, len + 1);
  noOverlap(s);
});

test("撞墙判负", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  s.snake = [{ x: 9, y: 5 }, { x: 8, y: 5 }];
  s.direction = "RIGHT";
  core.tick(s);
  assert.strictEqual(s.status, "lost");
  assert.strictEqual(s.deathReason, "wall");
});

test("咬到自己判负", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  s.snake = [{ x: 5, y: 5 }, { x: 5, y: 6 }, { x: 6, y: 6 }, { x: 6, y: 5 }];
  s.direction = "DOWN";
  core.tick(s);
  assert.strictEqual(s.status, "lost");
  assert.strictEqual(s.deathReason, "self");
});

test("踩雷扣命并移除该雷", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  s.mines = [{ x: s.snake[0].x + 1, y: s.snake[0].y }];
  core.tick(s);
  assert.strictEqual(s.lives, 2);
  assert.strictEqual(s.mines.length, 0);
  assert.ok(s.invincible > 0, "应进入无敌帧");
  assert.strictEqual(s.status, "running");
});

test("最后一条命踩雷判负", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  s.lives = 1;
  s.mines = [{ x: s.snake[0].x + 1, y: s.snake[0].y }];
  core.tick(s);
  assert.strictEqual(s.status, "lost");
  assert.strictEqual(s.deathReason, "mine");
});

test("达到目标分通关", () => {
  const s = core.createState({ cols: 10, rows: 10, target: 10 });
  s.food = { x: s.snake[0].x + 1, y: s.snake[0].y };
  core.tick(s);
  assert.strictEqual(s.score, 10);
  assert.strictEqual(s.status, "won");
});

test("吃到食物后雷数恢复到上限（+1）", () => {
  const s = core.createState({ cols: 10, rows: 10, maxMines: 3 });
  s.mines = [];
  s.food = { x: s.snake[0].x + 1, y: s.snake[0].y };
  core.tick(s);
  assert.strictEqual(s.mines.length, 1);
  assert.ok(s.mines.length <= s.maxMines);
  noOverlap(s);
});

test("禁止反向与缓冲上限", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  assert.strictEqual(core.setDirection(s, "LEFT"), false);
  assert.strictEqual(core.setDirection(s, "RIGHT"), false);
  assert.strictEqual(core.setDirection(s, "UP"), true);
  assert.strictEqual(core.setDirection(s, "LEFT"), true);
  assert.strictEqual(core.setDirection(s, "DOWN"), false);
  assert.strictEqual(s.queue.length, 2);
  assert.strictEqual(core.setDirection(s, "UP"), false);
});

test("暂停时不推进", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  s.status = "paused";
  const before = JSON.stringify(s.snake);
  core.tick(s);
  assert.strictEqual(s.steps, 0);
  assert.strictEqual(JSON.stringify(s.snake), before);
});

test("自定义配置生效", () => {
  const s = core.createState({ cols: 30, rows: 25, target: 200, maxMines: 5, maxLives: 4, foodScore: 20 });
  assert.strictEqual(s.cols, 30);
  assert.strictEqual(s.rows, 25);
  assert.strictEqual(s.target, 200);
  assert.strictEqual(s.maxMines, 5);
  assert.strictEqual(s.lives, 4);
  assert.strictEqual(s.foodScore, 20);
  assert.strictEqual(s.mines.length, 5);
});

console.log("难度与可达性测试：");
test("难度表数值正确", () => {
  assert.strictEqual(core.DIFFICULTIES.easy.label, "简单");
  assert.strictEqual(core.DIFFICULTIES.normal.cols, 40);
  assert.strictEqual(core.DIFFICULTIES.normal.rows, 20);
  assert.strictEqual(core.DIFFICULTIES.normal.maxMines, 20);
  assert.strictEqual(core.DIFFICULTIES.normal.target, 250);
  assert.strictEqual(core.DIFFICULTIES.hard.maxMines, 50);
  assert.strictEqual(core.DIFFICULTIES.hard.target, 1000);
  assert.strictEqual(core.DIFFICULTIES.endless.cols, 40);
  assert.strictEqual(core.DIFFICULTIES.endless.rows, 30);
  assert.strictEqual(core.DIFFICULTIES.endless.maxMines, 50);
  assert.strictEqual(core.DIFFICULTIES.endless.target, null);
  assert.strictEqual(core.DIFFICULTIES.endless.reshuffleMines, true);
});

test("各难度初始布局：食物可达、雷不贴脸、不重叠", () => {
  const cfgs = [
    { cols: 20, rows: 20, maxMines: 3, target: 100 },
    { cols: 40, rows: 20, maxMines: 20, target: 250 },
    { cols: 40, rows: 20, maxMines: 50, target: 1000 },
    { cols: 40, rows: 30, maxMines: 50, target: null, reshuffleMines: true }
  ];
  const near = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  cfgs.forEach((c) => {
    const s = core.createState(c);
    assert.strictEqual(s.mines.length, c.maxMines);
    assert.ok(s.food, "应有食物");
    assert.ok(core.reachable(s, s.snake[0], s.food), "食物应可达（雷不能封死食物）");
    noOverlap(s);
    const h = s.snake[0];
    for (const m of s.mines) {
      for (const [dx, dy] of near) {
        assert.ok(!(m.x === h.x + dx && m.y === h.y + dy), "雷不应紧贴蛇头");
      }
    }
  });
});

test("reachable 能识别被雷隔断的不可达", () => {
  const s = core.createState({ cols: 5, rows: 5, maxMines: 0 });
  s.mines = [{ x: 3, y: 0 }, { x: 3, y: 1 }, { x: 3, y: 2 }, { x: 3, y: 3 }, { x: 3, y: 4 }];
  assert.strictEqual(core.reachable(s, s.snake[0], { x: 4, y: 2 }), false, "右侧被雷墙隔断");
  assert.strictEqual(core.reachable(s, s.snake[0], { x: 0, y: 0 }), true, "左侧应可达");
});

test("无尽模式：吃食物后雷重新分布且不胜利", () => {
  const s = core.createState({ cols: 40, rows: 30, maxMines: 50, target: null, reshuffleMines: true, maxLives: 3, foodScore: 10 });
  s.food = { x: s.snake[0].x + 1, y: s.snake[0].y };
  s.status = "running";
  core.tick(s);
  assert.strictEqual(s.status, "running", "无尽模式不因得分胜利");
  assert.strictEqual(s.score, 10);
  assert.strictEqual(s.mines.length, 50, "吃食物后雷重新分布到满");
  assert.ok(core.reachable(s, s.snake[0], s.food), "新食物应可达");
  noOverlap(s);
});

test("steerToward 朝目标转向且绝不反向", () => {
  const s = core.createState({ cols: 10, rows: 10 });
  s.direction = "RIGHT";
  assert.strictEqual(core.steerToward(s, 8, 5), "RIGHT");
  const behind = core.steerToward(s, 2, 5);
  assert.ok(behind === "UP" || behind === "DOWN", "反向目标应给垂直方向");
  assert.notStrictEqual(behind, "LEFT");
  assert.strictEqual(core.steerToward(s, 5, 8), "DOWN");
  assert.strictEqual(core.steerToward(s, 5.3, 8), "DOWN");
});

console.log("生成产物冒烟测试：");
test("snake_core.js 可 require 且导出 API", () => {
  for (const k of ["createState", "setDirection", "tick", "DIR", "DIFFICULTIES", "reachable", "steerToward", "placeMines", "reshuffleMines"]) {
    assert.ok(core[k], "缺少导出 " + k);
  }
});

test("snake.html 内嵌脚本语法合法", () => {
  const html = fs.readFileSync(path.join(__dirname, "..", "snake.html"), "utf8");
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  assert.ok(scripts.length >= 2, "应至少包含主题初始化与主脚本两段内嵌脚本");
  for (const code of scripts) assert.doesNotThrow(() => new Function(code));
});

console.log("无头启动冒烟测试：");
test("UI 启动、难度切换、操控切换、胜负后按键修复", () => {
  const html = fs.readFileSync(path.join(__dirname, "..", "snake.html"), "utf8");
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const main = scripts[1];

  const elements = {};
  const listeners = {};
  const documentStub = {
    documentElement: { getAttribute: function () { return "dark"; }, setAttribute: function () {}, style: {} },
    getElementById: function (id) { if (!elements[id]) elements[id] = makeEl(); return elements[id]; },
    createElement: function () { return makeEl(); },
    addEventListener: function (type, fn) { (listeners[type] = listeners[type] || []).push(fn); }
  };
  const localStorageStub = {
    _s: {},
    getItem: function (k) { return Object.prototype.hasOwnProperty.call(this._s, k) ? this._s[k] : null; },
    setItem: function (k, v) { this._s[k] = String(v); },
    removeItem: function (k) { delete this._s[k]; }
  };

  const sandbox = {
    window: null, self: null,
    document: documentStub,
    localStorage: localStorageStub,
    getComputedStyle: function () { return { getPropertyValue: function () { return "#000000"; } }; },
    requestAnimationFrame: function () { return 1; },
    console: console,
    performance: { now: function () { return 0; } }
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;

  vm.createContext(sandbox);
  assert.doesNotThrow(function () { vm.runInContext(main, sandbox, { filename: "snake-ui.js" }); });
  assert.ok(sandbox.SnakeCore, "核心逻辑应挂载到全局");

  const app = sandbox.SnakeApp;
  assert.ok(app, "应暴露 SnakeApp 调试钩子");

  // 初始 easy
  let st = app.getState();
  assert.strictEqual(st.cols, 20);
  assert.strictEqual(st.mines.length, 3);
  assert.strictEqual(st.target, 100);

  // 切普通/困难
  app.setDifficulty("normal");
  st = app.getState();
  assert.strictEqual(st.cols, 40);
  assert.strictEqual(st.mines.length, 20);
  assert.strictEqual(st.target, 250);

  app.setDifficulty("hard");
  st = app.getState();
  assert.strictEqual(st.mines.length, 50);
  assert.strictEqual(st.target, 1000);

  // 切无尽
  app.setDifficulty("endless");
  st = app.getState();
  assert.strictEqual(st.target, null);
  assert.strictEqual(st.reshuffleMines, true);
  assert.strictEqual(st.mines.length, 50);

  // 操控方式
  assert.strictEqual(app.getControlMode(), "keyboard");
  app.setControlMode("mouse");
  assert.strictEqual(app.getControlMode(), "mouse");

  // 修复：胜负后按方向键/空格不重开，只有 Enter 重开
  app.setControlMode("keyboard");
  app.setDifficulty("easy");
  app.newGame(true);
  app.getState().status = "lost";
  const key = listeners.keydown && listeners.keydown[0];
  assert.ok(key, "应注册 keydown 监听");
  const noop = { preventDefault: function () {} };
  key(Object.assign({ key: "ArrowRight" }, noop));
  assert.strictEqual(app.getState().status, "lost", "方向键不应重开");
  key(Object.assign({ key: " " }, noop));
  assert.strictEqual(app.getState().status, "lost", "空格不应重开");
  key(Object.assign({ key: "Enter" }, noop));
  assert.strictEqual(app.getState().status, "running", "Enter 应重开");
});

console.log("\n共 " + passed + " 项测试全部通过 ✅");
