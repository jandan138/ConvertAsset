/* LIVERPS strength-ordering resolver (classic script, no deps)
   挂载到 #liverps-mount。演示：当多个 composition arc 对同一 property 给出 opinion 时，
   USD 自上而下按 LIVERPS 顺序取第一个有 opinion 的 arc。 */
(function () {
  var mount = document.getElementById("liverps-mount");
  if (!mount) return;

  var ARCS = [
    { k: "L", name: "Local", desc: "当前 layer 上的直接 opinion", color: "#e23b3b" },
    { k: "I", name: "Inherits", desc: "class 继承", color: "#e2873b" },
    { k: "V", name: "VariantSets", desc: "条件变体", color: "#d8b400" },
    { k: "R", name: "References", desc: "引用外部 asset", color: "#2fa84f" },
    { k: "P", name: "Payloads", desc: "可延迟加载的引用", color: "#2f7fe2" },
    { k: "S", name: "Specializes", desc: "基类特化（最弱）", color: "#7b5be0" },
  ];
  // 默认开关：模拟 References 与 Payloads 都给了 opinion，但 References 更强
  var state = [false, false, false, true, true, false];

  mount.innerHTML =
    '<div class="w2">' +
    '<div class="liverps-result"><span>resolved <code>color</code>:</span><span class="big" id="lv-big"></span><strong id="lv-win"></strong></div>' +
    '<div id="lv-rows" class="w2" style="gap:8px"></div>' +
    '<div class="w2-toolbar">' +
    '<button class="w2-btn primary" id="lv-scan">▶ 扫描 resolve</button>' +
    '<button class="w2-btn" data-preset="0">preset: 只有 Reference</button>' +
    '<button class="w2-btn" data-preset="1">preset: Local 覆盖一切</button>' +
    '<button class="w2-btn" data-preset="2">preset: Variant 胜出</button>' +
    '</div>' +
    '<div class="w2-readout">规则：自上而下找到第一个「有 opinion」的 arc 即胜出，停止下探（recursive，对 reference/payload 内部再做一次 LIVERPS）。注：现代 USD 在 V 与 R 之间还有 <strong>rElocates</strong>（LIVE<strong>R</strong>PS→LIVERPS 的 E），是命名空间重定位修饰符。</div>' +
    "</div>";

  var rowsEl = mount.querySelector("#lv-rows");
  var bigEl = mount.querySelector("#lv-big");
  var winEl = mount.querySelector("#lv-win");

  function render() {
    rowsEl.innerHTML = "";
    ARCS.forEach(function (a, i) {
      var row = document.createElement("div");
      row.className = "liverps-arc" + (state[i] ? "" : " off");
      row.innerHTML =
        '<span class="k">' + a.k + "</span>" +
        '<span class="nm">' + a.name + "<small>" + a.desc + "</small></span>" +
        '<span class="sw" style="background:' + a.color + '"></span>' +
        '<span class="w2-readout">' + (state[i] ? "has opinion" : "no opinion") + "</span>";
      row.addEventListener("click", function () { state[i] = !state[i]; render(); resolve(false); });
      row.dataset.idx = i;
      rowsEl.appendChild(row);
    });
  }
  function winnerIndex() { for (var i = 0; i < ARCS.length; i++) if (state[i]) return i; return -1; }
  function resolve(animate) {
    var win = winnerIndex();
    rowsEl.querySelectorAll(".liverps-arc").forEach(function (r) { r.classList.remove("winner", "scanning"); });
    if (win < 0) { bigEl.style.background = "transparent"; bigEl.style.borderStyle = "dashed"; winEl.textContent = "→ fallback default"; return; }
    bigEl.style.borderStyle = "solid";
    function mark() {
      bigEl.style.background = ARCS[win].color;
      winEl.textContent = "→ " + ARCS[win].name + " 胜出";
      var rows = rowsEl.querySelectorAll(".liverps-arc");
      if (rows[win]) rows[win].classList.add("winner");
    }
    if (!animate) { mark(); return; }
    var rows = rowsEl.querySelectorAll(".liverps-arc");
    var i = 0;
    (function step() {
      rows.forEach(function (r) { r.classList.remove("scanning"); });
      if (i > win) { mark(); return; }
      if (rows[i]) rows[i].classList.add("scanning");
      if (i === win) { setTimeout(mark, 280); return; }
      i++; setTimeout(step, 280);
    })();
  }

  mount.querySelector("#lv-scan").addEventListener("click", function () { resolve(true); });
  mount.querySelectorAll("[data-preset]").forEach(function (b) {
    b.addEventListener("click", function () {
      var p = b.getAttribute("data-preset");
      if (p === "0") state = [false, false, false, true, false, false];
      if (p === "1") state = [true, false, true, true, true, false];
      if (p === "2") state = [false, false, true, true, true, false];
      render(); resolve(true);
    });
  });

  render();
  resolve(false);
})();
