/* USD→GLB pipeline stepper (classic script, no deps) — 挂载 #pipeline-mount
   点击各阶段查看做了什么 + 对应 repo 模块。 */
(function () {
  var mount = document.getElementById("pipeline-mount");
  if (!mount) return;

  var STEPS = [
    { nm: "USD scene", mod: "*.usd", ic: "M20 4 L34 12 V28 L20 36 L6 28 V12 Z",
      body: "输入：带 MDL 材质的 Isaac Sim USD 资产。可能由 sublayer / reference / payload / variant 组合而成。" },
    { nm: "no-MDL", mod: "no_mdl/", ic: "M8 20 H32 M20 8 V32",
      body: "递归把 MDL shader network 换成 <span class='term'>UsdPreviewSurface</span>，重写 asset path 为 <code>*_noMDL.usd</code>。<strong>不 flatten</strong>，保留 composition。模块：<code>processor.py</code> / <code>materials.py</code> / <code>references.py</code>。" },
    { nm: "simplify", mod: "mesh/", ic: "M20 6 L32 14 V26 L20 34 L8 26 V14 Z M8 14 L20 22 L32 14",
      body: "QEM mesh simplification，按 <code>--ratio</code> 减面，保持 <span class='term'>face-varying</span> UV。后端：<code>py</code> / <code>cpp</code> / <code>cpp-uv</code>。模块：<code>mesh/simplify.py</code>。" },
    { nm: "export GLB", mod: "glb/", ic: "M9 9 H31 V31 H9 Z",
      body: "提取 mesh 与 UsdPreviewSurface 材质，<span class='term'>face-varying UV flattening</span>（拆点以符合 glTF 逐顶点 UV），写出二进制 <code>.glb</code>。模块：<code>glb/converter.py</code> / <code>usd_mesh.py</code> / <code>writer.py</code>。" },
    { nm: "render", mod: "render/ camera/", ic: "M20 13 a6 6 0 1 1 0 0 M11 34 V27 a9 9 0 0 1 18 0 V34",
      body: "用 orbit camera framing 给单资产出缩略图 / 本地 Isaac 渲染。模块：<code>render/single.py</code> / <code>camera/orbit.py</code> / <code>camera/fit.py</code>。" },
  ];

  mount.innerHTML =
    '<div class="w2">' +
    '<div class="pipe" id="pipe-row"></div>' +
    '<div class="pipe-detail" id="pipe-detail"></div>' +
    "</div>";

  var row = mount.querySelector("#pipe-row");
  var detail = mount.querySelector("#pipe-detail");
  function select(i) {
    row.querySelectorAll(".pipe-step").forEach(function (s, j) { s.classList.toggle("active", i === j); });
    detail.innerHTML = "<strong>" + STEPS[i].nm + "</strong> · <code>" + STEPS[i].mod + "</code><br>" + STEPS[i].body;
  }
  STEPS.forEach(function (s, i) {
    var d = document.createElement("div");
    d.className = "pipe-step";
    d.innerHTML =
      '<div class="ic"><svg width="34" height="34" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.4">' +
      '<path d="' + s.ic + '"/></svg></div>' +
      '<div class="nm">' + s.nm + "</div><div class=\"mod\">" + s.mod + "</div>";
    d.addEventListener("click", function () { select(i); });
    row.appendChild(d);
  });
  select(0);
})();
