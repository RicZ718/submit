
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

  // 食物 3×3 邻域也排除，避免雷紧贴食物形成「赢不了」的死局。
  function blockNearFood(state, occupied) {
    if (!state.food) return;
    var f = state.food;
    for (var dy = -1; dy <= 1; dy++) {
      for (var dx = -1; dx <= 1; dx++) {
        var x = f.x + dx, y = f.y + dy;
        if (inBounds(state, x, y)) occupied.add(x + "," + y);
      }
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

  // 某格 3×3 邻域内是否有雷。
  function mineNear(state, cell) {
    for (var dy = -1; dy <= 1; dy++) {
      for (var dx = -1; dx <= 1; dx++) {
        var nx = cell.x + dx, ny = cell.y + dy;
        for (var i = 0; i < state.mines.length; i++) {
          if (state.mines[i].x === nx && state.mines[i].y === ny) return true;
        }
      }
    }
    return false;
  }

  // 放置食物：优先取「不贴墙 + 周围 1 格无雷 + 从蛇头可达」的空格，
  // 避免食物落入角落/雷包而变成赢不了的死局。
  function placeFood(state) {
    for (var t = 0; t < 200; t++) {
      var occupied = new Set();
      state.snake.forEach(function (s) { occupied.add(key(s)); });
      (state.mines || []).forEach(function (m) { occupied.add(key(m)); });
      var cell = randomCell(state, occupied);
      if (!cell) return null;
      if (cell.x < 1 || cell.x > state.cols - 2 || cell.y < 1 || cell.y > state.rows - 2) continue; // 不贴墙
      if (mineNear(state, cell)) continue; // 周围 1 格无雷
      if (reachable(state, state.snake[0], cell)) return cell;
    }
    // 兜底：仅要求可达（小棋盘/极端情况）
    for (var t2 = 0; t2 < 60; t2++) {
      var occupied2 = new Set();
      state.snake.forEach(function (s) { occupied2.add(key(s)); });
      (state.mines || []).forEach(function (m) { occupied2.add(key(m)); });
      var cell2 = randomCell(state, occupied2);
      if (!cell2) return null;
      if (reachable(state, state.snake[0], cell2)) return cell2;
    }
    return null;
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
      blockNearFood(state, occupied);
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
    blockNearFood(state, occ);
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

  // 返回从 from 出发、走第一步的方向即可达 to 的方向（BFS，不返回完整路径）。
  function bfsFirstStep(state, from, to, blocked) {
    var dirs = [[1, 0, "RIGHT"], [-1, 0, "LEFT"], [0, 1, "DOWN"], [0, -1, "UP"]];
    var queue = [];
    var seen = new Set();
    seen.add(key(from));
    for (var i = 0; i < dirs.length; i++) {
      var nx = from.x + dirs[i][0], ny = from.y + dirs[i][1];
      var k = nx + "," + ny;
      if (!inBounds(state, nx, ny) || blocked.has(k)) continue;
      if (nx === to.x && ny === to.y) return dirs[i][2];
      seen.add(k);
      queue.push({ x: nx, y: ny, first: dirs[i][2] });
    }
    while (queue.length) {
      var cur = queue.shift();
      for (var j = 0; j < dirs.length; j++) {
        var nx2 = cur.x + dirs[j][0], ny2 = cur.y + dirs[j][1];
        var k2 = nx2 + "," + ny2;
        if (!inBounds(state, nx2, ny2) || blocked.has(k2) || seen.has(k2)) continue;
        if (nx2 === to.x && ny2 === to.y) return cur.first;
        seen.add(k2);
        queue.push({ x: nx2, y: ny2, first: cur.first });
      }
    }
    return null;
  }

  // 从 (x, y) 出发能走到的空格数量（BFS 洪泛）。
  function floodArea(state, x, y, blocked) {
    var queue = [{ x: x, y: y }];
    var seen = new Set();
    seen.add(x + "," + y);
    var area = 0;
    var dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
    while (queue.length) {
      var cur = queue.shift();
      area++;
      for (var i = 0; i < dirs.length; i++) {
        var nx = cur.x + dirs[i][0], ny = cur.y + dirs[i][1];
        var k = nx + "," + ny;
        if (!inBounds(state, nx, ny) || blocked.has(k) || seen.has(k)) continue;
        seen.add(k);
        queue.push({ x: nx, y: ny });
      }
    }
    return area;
  }

  // 从 from 到 to 是否有通路（blocked 为显式障碍集合；to 不在 blocked 中）。
  function canReach(state, from, to, blocked) {
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

  // 判断某方向是否「安全」：不撞墙/雷/自身，且走完后蛇头仍能回到尾巴（不会被逼死）。
  function isSafeMove(state, dir) {
    var d = DIR[dir];
    var head = state.snake[0];
    var nx = head.x + d.x, ny = head.y + d.y;
    if (!inBounds(state, nx, ny)) return false;
    var willEat = !!state.food && nx === state.food.x && ny === state.food.y;
    var newSnake = [{ x: nx, y: ny }].concat(state.snake);
    if (!willEat) newSnake.pop();
    for (var i = 1; i < newSnake.length; i++) {
      if (newSnake[i].x === nx && newSnake[i].y === ny) return false; // 自身碰撞
    }
    for (var j = 0; j < state.mines.length; j++) {
      if (state.mines[j].x === nx && state.mines[j].y === ny) return false; // 踩雷
    }
    var tail = newSnake[newSnake.length - 1];
    var blocked = new Set();
    for (var k = 0; k < newSnake.length - 1; k++) blocked.add(key(newSnake[k]));
    for (var m = 0; m < state.mines.length; m++) blocked.add(key(state.mines[m]));
    return canReach(state, { x: nx, y: ny }, tail, blocked); // 蛇头仍可达尾巴
  }

  // AI 自动控制：最短安全路径去食物；不可达/不安全时向「可活动空间最大」处绕行。
  function autoMove(state) {
    if (!state.food) return null;
    var head = state.snake[0];
    var blocked = new Set();
    for (var i = 0; i < state.snake.length - 1; i++) blocked.add(key(state.snake[i]));
    for (var j = 0; j < state.mines.length; j++) blocked.add(key(state.mines[j]));
    var curDir = state.queue.length ? state.queue[state.queue.length - 1] : state.direction;
    var rev = OPPOSITE[curDir];
    if (rev) {
      var rd = DIR[rev];
      var rx = head.x + rd.x, ry = head.y + rd.y;
      if (inBounds(state, rx, ry)) blocked.add(rx + "," + ry);
    }

    var dirs = [[1, 0, "RIGHT"], [-1, 0, "LEFT"], [0, 1, "DOWN"], [0, -1, "UP"]];

    // 1) 最短安全路径去食物
    var dir = bfsFirstStep(state, head, state.food, blocked);
    if (dir && isSafeMove(state, dir)) return dir;

    // 2) 安全方向里，选「可活动空间最大」者（远离死角，绕行等待机会）
    var best = null, bestArea = -1;
    for (var k = 0; k < dirs.length; k++) {
      if (dirs[k][2] === rev) continue;
      if (!isSafeMove(state, dirs[k][2])) continue;
      var nx = head.x + dirs[k][0], ny = head.y + dirs[k][1];
      var area = floodArea(state, nx, ny, blocked);
      if (area > bestArea) { bestArea = area; best = dirs[k][2]; }
    }
    if (best) return best;

    // 3) 兜底：不做安全校验，最大活动空间
    bestArea = -1;
    for (var k2 = 0; k2 < dirs.length; k2++) {
      var nx2 = head.x + dirs[k2][0], ny2 = head.y + dirs[k2][1];
      var kk2 = nx2 + "," + ny2;
      if (!inBounds(state, nx2, ny2) || blocked.has(kk2)) continue;
      var area2 = floodArea(state, nx2, ny2, blocked);
      if (area2 > bestArea) { bestArea = area2; best = dirs[k2][2]; }
    }
    return best;
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
    reshuffleMines: reshuffleMines,
    autoMove: autoMove
  };
});
