/* BVH traversal 可视化 (classic script, Canvas2D, no deps) — 挂载 #bvh-mount
   演示 RT Core 的工作：对一条 ray 自顶向下做 box test（命中才下探），
   叶子里再做 ray-triangle intersection。计数 box tests / triangle tests。 */
(function () {
  var mount = document.getElementById("bvh-mount");
  if (!mount) return;

  mount.innerHTML =
    '<div class="w2">' +
    '<canvas class="w2-canvas" id="bvh-cv" height="340"></canvas>' +
    '<div class="w2-toolbar">' +
    '<button class="w2-btn primary" id="bvh-step">▶ 单步 traverse</button>' +
    '<button class="w2-btn" id="bvh-auto">自动</button>' +
    '<button class="w2-btn" id="bvh-new">换一条 ray</button>' +
    '<span class="w2-readout" id="bvh-stat"></span>' +
    "</div>" +
    '<div class="w2-readout">蓝框 = AABB 节点。命中(实线)才下探，未命中(虚线灰)整棵子树被 prune。叶子里才做 ray-triangle 测试。这两类测试正是 Turing/Ampere 上 <span class="term">RT Core</span> 硬件加速、从 <span class="term">SM</span> 卸载的工作。</div>' +
    "</div>";

  var cv = mount.querySelector("#bvh-cv");
  var ctx = cv.getContext("2d");
  var statEl = mount.querySelector("#bvh-stat");
  var tris, root, ray, queue, visited, boxTests, triTests, hit, autoT = 0;

  function ink(v, fb) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim() || fb; }
  function rnd(a, b) { return a + Math.random() * (b - a); }

  function makeTris(W, H) {
    var arr = [];
    for (var i = 0; i < 10; i++) {
      var cx = rnd(60, W - 60), cy = rnd(50, H - 50), s = rnd(16, 30);
      arr.push([{ x: cx, y: cy - s }, { x: cx - s, y: cy + s }, { x: cx + s, y: cy + s }]);
    }
    return arr;
  }
  function aabb(items) {
    var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    items.forEach(function (t) { t.forEach(function (p) { x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y); }); });
    return { x0: x0 - 4, y0: y0 - 4, x1: x1 + 4, y1: y1 + 4 };
  }
  function buildBVH(items, depth) {
    var node = { box: aabb(items), items: items, leaf: items.length <= 2 || depth >= 3 };
    if (!node.leaf) {
      var b = node.box, splitX = (b.x1 - b.x0) >= (b.y1 - b.y0);
      var sorted = items.slice().sort(function (p, q) {
        var pc = splitX ? (p[0].x + p[1].x + p[2].x) : (p[0].y + p[1].y + p[2].y);
        var qc = splitX ? (q[0].x + q[1].x + q[2].x) : (q[0].y + q[1].y + q[2].y);
        return pc - qc;
      });
      var mid = Math.ceil(sorted.length / 2);
      node.l = buildBVH(sorted.slice(0, mid), depth + 1);
      node.r = buildBVH(sorted.slice(mid), depth + 1);
    }
    return node;
  }
  function rayBox(r, b) {
    var tmin = -1e9, tmax = 1e9, ax = [["x0","x1","ox","dx"],["y0","y1","oy","dy"]];
    for (var k = 0; k < 2; k++) {
      var lo = b[ax[k][0]], hi = b[ax[k][1]], o = r[ax[k][2]], d = r[ax[k][3]];
      if (Math.abs(d) < 1e-9) { if (o < lo || o > hi) return false; }
      else { var t1 = (lo - o) / d, t2 = (hi - o) / d; if (t1 > t2) { var tt = t1; t1 = t2; t2 = tt; } tmin = Math.max(tmin, t1); tmax = Math.min(tmax, t2); if (tmin > tmax) return false; }
    }
    return tmax >= 0;
  }
  function rayTri(r, t) {
    // 2D：测试 ray 段是否与三角形任一边相交（够用于演示命中）
    function seg(p1, p2) {
      var ox = r.ox, oy = r.oy, dx = r.dx * 1000, dy = r.dy * 1000;
      var x3 = p1.x, y3 = p1.y, x4 = p2.x, y4 = p2.y;
      var den = (dx) * (y3 - y4) - (dy) * (x3 - x4);
      if (Math.abs(den) < 1e-9) return false;
      var tt = ((ox - x3) * (y3 - y4) - (oy - y3) * (x3 - x4)) / den;
      var uu = ((ox - x3) * (dy) - (oy - y3) * (dx)) / den;
      return tt >= 0 && tt <= 1 && uu >= 0 && uu <= 1;
    }
    return seg(t[0], t[1]) || seg(t[1], t[2]) || seg(t[2], t[0]);
  }

  function reset(newRay) {
    var W = cv.clientWidth || 600; cv.width = W; cv.height = 340;
    if (newRay || !tris) { tris = makeTris(W, cv.height); root = buildBVH(tris, 0); }
    var oy = rnd(60, cv.height - 60);
    ray = { ox: 6, oy: oy, dx: 1, dy: rnd(-0.25, 0.25) };
    var n = Math.hypot(ray.dx, ray.dy); ray.dx /= n; ray.dy /= n;
    queue = [root]; visited = []; boxTests = 0; triTests = 0; hit = null;
    draw();
  }
  function step() {
    if (!queue.length) return false;
    var node = queue.shift();
    boxTests++;
    var inBox = rayBox(ray, node.box);
    visited.push({ box: node.box, hit: inBox, leaf: node.leaf });
    if (inBox) {
      if (node.leaf) {
        node.items.forEach(function (t) { triTests++; if (rayTri(ray, t)) hit = hit || t; });
      } else { queue.push(node.l, node.r); }
    }
    draw();
    return queue.length > 0;
  }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    // 三角形
    ctx.lineWidth = 1.2;
    tris.forEach(function (t) {
      ctx.beginPath(); ctx.moveTo(t[0].x, t[0].y); ctx.lineTo(t[1].x, t[1].y); ctx.lineTo(t[2].x, t[2].y); ctx.closePath();
      var isHit = hit === t;
      ctx.fillStyle = isHit ? "rgba(15,181,166,0.35)" : "rgba(120,120,140,0.10)";
      ctx.strokeStyle = isHit ? ink("--interactive", "#0fb5a6") : ink("--ink-muted", "#8a8a99");
      ctx.fill(); ctx.stroke();
    });
    // 已访问的盒子
    visited.forEach(function (v) {
      ctx.lineWidth = v.hit ? 2 : 1;
      ctx.setLineDash(v.hit ? [] : [4, 3]);
      ctx.strokeStyle = v.hit ? ink("--accent", "#5b5bd6") : ink("--ink-muted", "#8a8a99");
      ctx.strokeRect(v.box.x0, v.box.y0, v.box.x1 - v.box.x0, v.box.y1 - v.box.y0);
    });
    ctx.setLineDash([]);
    // ray
    ctx.strokeStyle = ink("--interactive", "#0fb5a6"); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(ray.ox, ray.oy); ctx.lineTo(ray.ox + ray.dx * 1000, ray.oy + ray.dy * 1000); ctx.stroke();
    ctx.fillStyle = ink("--interactive", "#0fb5a6"); ctx.beginPath(); ctx.arc(ray.ox, ray.oy, 4, 0, 7); ctx.fill();
    statEl.textContent = "box tests: " + boxTests + "  ·  triangle tests: " + triTests + (hit ? "  ·  HIT ✓" : (queue && queue.length ? "" : "  ·  miss"));
  }

  mount.querySelector("#bvh-step").addEventListener("click", function () { step(); });
  mount.querySelector("#bvh-auto").addEventListener("click", function () {
    clearInterval(autoT); autoT = setInterval(function () { if (!step()) clearInterval(autoT); }, 320);
  });
  mount.querySelector("#bvh-new").addEventListener("click", function () { clearInterval(autoT); reset(true); });
  window.addEventListener("resize", function () { draw(); });

  reset(true);
})();
