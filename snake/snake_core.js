
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.SnakeCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var DIR = {
    UP: { x: 0, y: -1 },
    DOWN: { x: 0, y: 1 },
    LEFT: { x: -1, y: 0 },
    RIGHT: { x: 1, y: 0 }
  };
  var OPPOSITE = { UP: "DOWN", DOWN: "UP", LEFT: "RIGHT", RIGHT: "LEFT" };

  // 四档难度。easy 的尺寸/雷/目标取生成器注入的基线（cols/rows/target/maxMines）。
  var DIFFICULTIES = {
    easy:    { label: "简单", cols: null, rows: null, maxMines: null, target: undefined, reshuffleMines: false },
    normal:  { label: "普通", cols: 40, rows: 20, maxMines: 20, target: 250,  reshuffleMines: false },
    hard:    { label: "困难", cols: 40, rows: 20, maxMines: 50, target: 1000, reshuffleMines: false },
    endless: { label: "无尽", cols: 40, rows: 30, maxMines: 50, target: null, reshuffleMines: true }
  };

  function key(p) { return p.x + "," + p.y; }

  function inBounds(state, x, y) { return x >= 0 && x < state.cols && y >= 0 && y < state.rows; }

  // 在给定 occupied 集合之外随机取一个空格。
  function randomCell(state, occupied) {
    var free = [];
    for (var y = 0; y < state.rows; y++) {
      for (var x = 0; x < state.cols; x++) {
        if (!occupied.has(x + "," + y)) free.push({ x: x, y: y });
      }
    }
    if (free.length === 0) return null;
    return free[Math.floor(Math.random() * free.length)];
  }

  // 蛇头四邻也排除，避免开局/刷新时贴脸刷雷导致不公平。
  function blockNearHead(state, occupied) {
    var h = state.snake[0];
    var n = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    for (var i = 0; i < n.length; i++) {
      var x = h.x + n[i][0], y = h.y + n[i][1];
      if (inBounds(state, x, y)) occupied.add(x + "," + y);
    }
  }

  function randomFreeCell(state) {
    var occupied = new Set();
    state.snake.forEach(function (s) { occupied.add(key(s)); });
    if (state.food) occupied.add(key(state.food));
    (state.mines || []).forEach(function (m) { occupied.add(key(m)); });
    return randomCell(state, occupied);
  }

  // 从 from 到 to 是否可通（BFS；蛇身与雷视为障碍，to 视为可达目标）。
  function reachable(state, from, to, extraMines) {
    var blocked = new Set();
    state.snake.forEach(function (s) { blocked.add(key(s)); });
    var mines = extraMines || state.mines || [];
    mines.forEach(function (m) { blocked.add(key(m)); });
    if (to) blocked.delete(key(to));
    var queue = [from];
    var seen = new Set();
    seen.add(key(from));
    while (queue.length) {
      var cur = queue.shift();
      if (cur.x === to.x && cur.y === to.y) return true;
      var dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
      for (var i = 0; i < dirs.length; i++) {
        var nx = cur.x + dirs[i][0], ny = cur.y + dirs[i][1];
        var k = nx + "," + ny;
        if (!inBounds(state, nx, ny) || blocked.has(k) || seen.has(k)) continue;
        seen.add(k);
        queue.push({ x: nx, y: ny });
      }
    }
    return false;
  }

  // 放置食物：优先取「从蛇头可达」的空格，保证食物不会因雷/蛇身被隔死。
  function placeFood(state) {
    for (var t = 0; t < 60; t++) {
      var occupied = new Set();
      state.snake.forEach(function (s) { occupied.add(key(s)); });
      (state.mines || []).forEach(function (m) { occupied.add(key(m)); });
      var cell = randomCell(state, occupied);
      if (!cell) return null;
      if (reachable(state, state.snake[0], cell)) return cell;
    }
    return null; // 找不到可达空格（棋盘几乎被占满/蛇身封死），按通关处理
  }

  // 放置雷：不贴蛇身/食物/蛇头四邻，并保证食物仍从蛇头可达（否则重试）。
  // fresh=false 在现有雷基础上补到 count；fresh=true 丢弃现有雷全新分布 count 颗。
  function placeMinesImpl(state, count, fresh) {
    var t, i;
    for (t = 0; t < 60; t++) {
      var occupied = new Set();
      state.snake.forEach(function (s) { occupied.add(key(s)); });
      if (state.food) occupied.add(key(state.food));
      if (!fresh) (state.mines || []).forEach(function (m) { occupied.add(key(m)); });
      blockNearHead(state, occupied);
      var mines = fresh ? [] : (state.mines || []).slice();
      while (mines.length < count) {
        var cell = randomCell(state, occupied);
        if (!cell) break;
        occupied.add(key(cell));
        mines.push(cell);
      }
      if (state.food && !reachable(state, state.snake[0], state.food, mines)) continue;
      return mines;
    }
    // 兜底：尽量放满但不再验证（极端满盘才会走到这里）
    var occ = new Set();
    state.snake.forEach(function (s) { occ.add(key(s)); });
    if (state.food) occ.add(key(state.food));
    if (!fresh) (state.mines || []).forEach(function (m) { occ.add(key(m)); });
    blockNearHead(state, occ);
    var out = fresh ? [] : (state.mines || []).slice();
    for (i = 0; i < count; i++) {
      var c = randomCell(state, occ);
      if (!c) break;
      occ.add(key(c));
      out.push(c);
    }
    return out;
  }

  function placeMines(state, count) { return placeMinesImpl(state, count, false); }
  function reshuffleMines(state, count) { return placeMinesImpl(state, count, true); }

  function createState(opts) {
    opts = opts || {};
    var cols = opts.cols || 20;
    var rows = opts.rows || 20;
    var hx = Math.floor(cols / 2);
    var hy = Math.floor(rows / 2);
    var snake = [
      { x: hx, y: hy },
      { x: hx - 1, y: hy },
      { x: hx - 2, y: hy }
    ];
    var state = {
      cols: cols,
      rows: rows,
      target: (opts.target === undefined) ? 100 : opts.target, // null = 无尽，无胜利
      maxMines: opts.maxMines || 3,
      maxLives: opts.maxLives || 3,
      foodScore: opts.foodScore || 10,
      reshuffleMines: !!opts.reshuffleMines,
      snake: snake,
      direction: "RIGHT",
      queue: [],
      food: null,
      mines: [],
      score: 0,
      steps: 0,
      lives: opts.maxLives || 3,
      status: "ready",        // ready | running | paused | won | lost
      invincible: 0,
      deathReason: null       // wall | self | mine
    };
    state.food = placeFood(state);
    state.mines = placeMines(state, state.maxMines);
    return state;
  }

  // 缓冲转向：禁止反向、最多缓存 2 次，保证手感顺滑。
  function setDirection(state, dir) {
    if (state.status === "won" || state.status === "lost") return false;
    var last = state.queue.length ? state.queue[state.queue.length - 1] : state.direction;
    if (dir === last || dir === OPPOSITE[last]) return false;
    if (state.queue.length >= 2) return false;
    state.queue.push(dir);
    return true;
  }

  // 鼠标操控：根据目标点（网格浮点坐标）返回推荐方向，绝不返回当前方向的反向。
  function steerToward(state, tx, ty) {
    var head = state.snake[0];
    var dx = tx - (head.x + 0.5);
    var dy = ty - (head.y + 0.5);
    if (Math.abs(dx) < 0.4 && Math.abs(dy) < 0.4) return null; // 已在目标附近
    var cur = state.queue.length ? state.queue[state.queue.length - 1] : state.direction;
    var primary, secondary;
    if (Math.abs(dx) >= Math.abs(dy)) {
      primary = dx > 0 ? "RIGHT" : "LEFT";
      secondary = dy > 0 ? "DOWN" : "UP";
    } else {
      primary = dy > 0 ? "DOWN" : "UP";
      secondary = dx > 0 ? "RIGHT" : "LEFT";
    }
    if (primary !== OPPOSITE[cur]) return primary;
    if (secondary !== OPPOSITE[cur]) return secondary;
    return null;
  }

  // 前进一格。纯状态迁移，便于单测。
  function tick(state) {
    if (state.status === "won" || state.status === "lost" || state.status === "paused") {
      return state;
    }
    if (state.queue.length) state.direction = state.queue.shift();

    var d = DIR[state.direction];
    var head = state.snake[0];
    var next = { x: head.x + d.x, y: head.y + d.y };

    if (!inBounds(state, next.x, next.y)) {
      state.status = "lost";
      state.deathReason = "wall";
      return state;
    }

    var willEat = !!state.food && next.x === state.food.x && next.y === state.food.y;
    var body = willEat ? state.snake : state.snake.slice(0, state.snake.length - 1);
    for (var i = 0; i < body.length; i++) {
      if (body[i].x === next.x && body[i].y === next.y) {
        state.status = "lost";
        state.deathReason = "self";
        return state;
      }
    }

    state.steps += 1;

    // 踩雷：移除该雷；非无敌状态扣 1 条命并进入短暂无敌。
    var mi = -1;
    for (var j = 0; j < state.mines.length; j++) {
      if (state.mines[j].x === next.x && state.mines[j].y === next.y) { mi = j; break; }
    }
    if (mi >= 0) {
      state.mines.splice(mi, 1);
      if (state.invincible <= 0) {
        state.lives -= 1;
        state.invincible = 15;
        if (state.lives <= 0) state.deathReason = "mine";
      }
    }

    state.snake.unshift(next);
    if (willEat) {
      state.score += state.foodScore;
      state.food = placeFood(state);
      if (state.food === null) {
        state.status = "won"; // 棋盘被占满，视为通关
      } else if (state.reshuffleMines) {
        state.mines = reshuffleMines(state, state.maxMines); // 无尽：雷全部重新分布
      } else if (state.mines.length < state.maxMines) {
        state.mines = placeMines(state, state.mines.length + 1); // 补一颗雷
      }
      if (state.target !== null && state.score >= state.target) state.status = "won";
    } else {
      state.snake.pop();
    }

    if (state.invincible > 0) state.invincible -= 1;
    if (state.lives <= 0 && state.status !== "won") {
      state.status = "lost";
      if (!state.deathReason) state.deathReason = "mine";
    }
    if (state.status === "ready") state.status = "running";

    return state;
  }

  return {
    DIR: DIR,
    OPPOSITE: OPPOSITE,
    DIFFICULTIES: DIFFICULTIES,
    createState: createState,
    setDirection: setDirection,
    steerToward: steerToward,
    tick: tick,
    reachable: reachable,
    randomFreeCell: randomFreeCell,
    placeFood: placeFood,
    placeMines: placeMines,
    reshuffleMines: reshuffleMines
  };
});
