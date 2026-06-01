/* Evidence-gate 决策流 (classic script, no deps) — 挂载 #gates-mount
   复现论文的 claim-bounded protocol：四道 gate 必须分别报告，才能支撑 downstream 鲁棒性主张。 */
(function () {
  var mount = document.getElementById("gates-mount");
  if (!mount) return;

  var GATES = [
    { n: "1", nm: "Visual similarity", metric: "PSNR 35.52dB · SSIM 0.990 · LPIPS 0.020 · CLIP 0.925 · DINOv2 0.872", pass: true,
      note: "proxy 相似度很高 —— 但论文强调：proxy fidelity 单独不足以支撑 grounding 主张。" },
    { n: "2", nm: "Grounding", metric: "GRScenes VQA：target-category 30/30；point-hit 27/30→29/30 (Gemma)", pass: true,
      note: "另一模型 (Qwen2.5-VL) 在同一 prompt contract 下暴露 raw-coordinate 偏好 —— 模型相关。" },
    { n: "3", nm: "Material-effect risk", metric: "selected NVIDIA-baseline material-effect audit", pass: true,
      note: "材质转换是否引入系统性外观偏移，需单独评估。" },
    { n: "4", nm: "Embodied-stack usability", metric: "99-episode official InternNav sanity run", pass: true,
      note: "转换后的 USD 能否真的在 embodied stack 里跑通。" },
  ];

  mount.innerHTML =
    '<div class="w2">' +
    '<div id="gate-list" class="w2" style="gap:0"></div>' +
    '<div class="glb-explain" id="gate-note">点击任一 gate 查看说明。论文结论：四个维度应作为<strong>独立证据 gate</strong>分别报告，而不是用一个 proxy 指标代表全部。</div>' +
    "</div>";

  var list = mount.querySelector("#gate-list");
  var noteEl = mount.querySelector("#gate-note");
  GATES.forEach(function (g, i) {
    var row = document.createElement("div");
    row.className = "gate";
    row.innerHTML =
      '<span class="n">' + g.n + "</span>" +
      '<span><strong>' + g.nm + "</strong><br><span class=\"w2-readout\">" + g.metric + "</span></span>" +
      '<span class="st ' + (g.pass ? "pass" : "fail") + '">' + (g.pass ? "report ✓" : "fail") + "</span>";
    row.addEventListener("click", function () {
      noteEl.innerHTML = "<strong>Gate " + g.n + " · " + g.nm + "</strong><br>" + g.note;
      list.querySelectorAll(".gate").forEach(function (x) { x.style.borderColor = "var(--panel-border)"; });
      row.style.borderColor = "var(--accent)";
    });
    list.appendChild(row);
    if (i < GATES.length - 1) { var c = document.createElement("div"); c.className = "gate-conn"; list.appendChild(c); }
  });
})();
