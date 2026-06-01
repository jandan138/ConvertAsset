/* QEM edge-collapse (classic script, Canvas2D, no deps) — 挂载 #qem-mount
   2D 版 quadric error metric：每个顶点累加其相邻 edge 所在直线的 quadric，
   edge 代价 = v^T (Qi+Qj) v（在最优位置 v 处），每步 collapse 代价最小的 edge。 */
(function () {
  var mount = document.getElementById("qem-mount");
  if (!mount) return;

  mount.innerHTML =
    '<div class="w2">' +
    '<canvas class="w2-canvas" id="qem-cv" height="360"></canvas>' +
    '<div class="w2-toolbar">' +
    '<button class="w2-btn primary" id="qem-play">▶ 自动 collapse</button>' +
    '<button class="w2-btn" id="qem-step">single step</button>' +
    '<button class="w2-btn" id="qem-reset">reset</button>' +
    '<span class="w2-readout" id="qem-stat"></span>' +
    "</div>" +
    '<div class="w2-readout">每次坍缩 quadric error 最小的 edge —— 平坦区域先被简化，几何特征（边界、拐角）被保留，这正是 QEM 的核心性质。</div>' +
    "</div>";

  var cv = mount.querySelector("#qem-cv");
  var ctx = cv.getContext("2d");
  var statEl = mount.querySelector("#qem-stat");
  var V, T, Q, playing = false, raf = 0;

  function ink(varName, fb) {
    var c = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    return c || fb;
  }

  function build() {
    V = []; T = [];
    // 同心圆环三角化（一个 disk mesh）
    var rings = 7, seg = 22, R = 150;
    V.push({ x: 0, y: 0, alive: true });
    for (var r = 1; r <= rings; r++) {
      for (var s = 0; s < seg; s++) {
        var a = (s / seg) * Math.PI * 2;
        var rad = (r / rings) * R * (0.86 + 0.14 * Math.cos(a * 3)); // 轻微非圆，制造特征
        V.push({ x: Math.cos(a) * rad, y: Math.sin(a) * rad, alive: true });
      }
    }
    function idx(r, s) { return r === 0 ? 0 : 1 + (r - 1) * seg + ((s % seg + seg) % seg); }
    for (var s2 = 0; s2 < seg; s2++) T.push([idx(0, 0), idx(1, s2), idx(1, s2 + 1)]);
    for (var r2 = 1; r2 < rings; r2++)
      for (var s3 = 0; s3 < seg; s3++) {
        T.push([idx(r2, s3), idx(r2 + 1, s3), idx(r2 + 1, s3 + 1)]);
        T.push([idx(r2, s3), idx(r2 + 1, s3 + 1), idx(r2, s3 + 1)]);
      }
    computeQuadrics();
  }

  function edges() {
    var set = {}, out = [];
    T.forEach(function (t) {
      [[t[0], t[1]], [t[1], t[2]], [t[2], t[0]]].forEach(function (e) {
        var a = Math.min(e[0], e[1]), b = Math.max(e[0], e[1]), key = a + "_" + b;
        if (!set[key]) { set[key] = 1; out.push([a, b]); }
      });
    });
    return out;
  }
  function computeQuadrics() {
    Q = V.map(function () { return [0, 0, 0, 0, 0, 0]; }); // a2,ab,ac,b2,bc,c2
    edges().forEach(function (e) {
      var p = V[e[0]], q = V[e[1]];
      var dx = q.x - p.x, dy = q.y - p.y, len = Math.hypot(dx, dy) || 1;
      var a = dy / len, b = -dx / len, c = -(a * p.x + b * p.y); // 归一化直线
      var add = [a * a, a * b, a * c, b * b, b * c, c * c];
      for (var k = 0; k < 6; k++) { Q[e[0]][k] += add[k]; Q[e[1]][k] += add[k]; }
    });
  }
  function qErr(q, x, y) {
    return q[0]*x*x + 2*q[1]*x*y + 2*q[2]*x + q[3]*y*y + 2*q[4]*y + q[5];
  }
  function bestCollapse() {
    var best = null;
    edges().forEach(function (e) {
      var i = e[0], j = e[1];
      if (!V[i].alive || !V[j].alive) return;
      var q = [0,0,0,0,0,0]; for (var k = 0; k < 6; k++) q[k] = Q[i][k] + Q[j][k];
      // 最优位置解 2x2： [q0 q1; q1 q3] v = [-q2; -q4]
      var det = q[0]*q[3] - q[1]*q[1], vx, vy;
      if (Math.abs(det) > 1e-8) { vx = (-q[2]*q[3] + q[4]*q[1]) / det; vy = (-q[0]*q[4] + q[1]*q[2]) / det; }
      else { vx = (V[i].x + V[j].x) / 2; vy = (V[i].y + V[j].y) / 2; }
      var cost = qErr(q, vx, vy);
      if (!best || cost < best.cost) best = { i: i, j: j, vx: vx, vy: vy, q: q, cost: cost };
    });
    return best;
  }
  function collapse() {
    var aliveV = V.filter(function (v) { return v.alive; }).length;
    if (aliveV <= 14) { playing = false; return false; }
    var b = bestCollapse();
    if (!b) return false;
    V[b.i].x = b.vx; V[b.i].y = b.vy; Q[b.i] = b.q;
    V[b.j].alive = false;
    // 把 j 重映射到 i，删除退化三角形
    var nt = [];
    T.forEach(function (t) {
      var u = t.map(function (x) { return x === b.j ? b.i : x; });
      if (u[0] !== u[1] && u[1] !== u[2] && u[2] !== u[0]) nt.push(u);
    });
    T = nt;
    return true;
  }

  function draw() {
    var w = cv.clientWidth || 600; cv.width = w; cv.height = 360;
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.save(); ctx.translate(cv.width / 2, cv.height / 2);
    ctx.strokeStyle = ink("--panel-border", "#e6e6ef"); ctx.lineWidth = 1;
    ctx.fillStyle = "rgba(91,91,214,0.06)";
    T.forEach(function (t) {
      ctx.beginPath();
      ctx.moveTo(V[t[0]].x, V[t[0]].y);
      ctx.lineTo(V[t[1]].x, V[t[1]].y);
      ctx.lineTo(V[t[2]].x, V[t[2]].y);
      ctx.closePath(); ctx.fill(); ctx.stroke();
    });
    ctx.fillStyle = ink("--accent", "#5b5bd6");
    V.forEach(function (v) { if (v.alive) { ctx.beginPath(); ctx.arc(v.x, v.y, 1.8, 0, 7); ctx.fill(); } });
    ctx.restore();
    statEl.textContent = "vertices: " + V.filter(function (v){return v.alive;}).length + "  ·  triangles: " + T.length;
  }
  function loop() {
    if (!playing) return;
    var ok = collapse(); draw();
    if (ok) raf = setTimeout(function () { requestAnimationFrame(loop); }, 90);
  }

  mount.querySelector("#qem-play").addEventListener("click", function () {
    playing = !playing; this.textContent = playing ? "⏸ 暂停" : "▶ 自动 collapse";
    if (playing) loop();
  });
  mount.querySelector("#qem-step").addEventListener("click", function () { collapse(); draw(); });
  mount.querySelector("#qem-reset").addEventListener("click", function () {
    playing = false; clearTimeout(raf); mount.querySelector("#qem-play").textContent = "▶ 自动 collapse";
    build(); draw();
  });
  window.addEventListener("resize", draw);

  build(); draw();
})();
