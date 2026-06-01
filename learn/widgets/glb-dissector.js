/* GLB 二进制容器解剖 (classic script, no deps) — 挂载 #glb-mount
   展示 GLB = 12B header + JSON chunk + BIN chunk，点击各段查看字段含义。 */
(function () {
  var mount = document.getElementById("glb-mount");
  if (!mount) return;

  var SEGS = [
    { cls: "hdr", label: "magic  0x46546C67  ('glTF')", title: "Header · magic",
      body: "GLB 文件头共 12 字节。前 4 字节是 magic <code>0x46546C67</code>，ASCII 即 \"glTF\"，用于快速识别二进制 glTF。" },
    { cls: "hdr", label: "version  2", title: "Header · version",
      body: "接着 4 字节小端 <code>uint32</code> = 版本号，glTF 2.0 这里是 <code>2</code>。" },
    { cls: "hdr", label: "length  (total)", title: "Header · length",
      body: "最后 4 字节 <code>uint32</code> = 整个 GLB 文件的总字节数（含 header 与所有 chunk）。" },
    { cls: "json", label: "chunk0  type=JSON  'JSON'", title: "Chunk 0 · JSON",
      body: "第一个 chunk 必须是 JSON：<code>chunkLength</code>(4B) + <code>chunkType</code>=0x4E4F534A('JSON')(4B) + 数据。它就是 .gltf 的场景描述：scenes / nodes / meshes / accessors / bufferViews / materials。用空格 <code>0x20</code> 填充到 4 字节对齐。" },
    { cls: "bin", label: "chunk1  type=BIN  '\\0BIN'", title: "Chunk 1 · BIN",
      body: "第二个 chunk 是二进制 buffer：<code>chunkLength</code>(4B) + <code>chunkType</code>=0x004E4942('BIN')(4B) + 几何/动画原始字节。JSON 里的 <code>buffer[0]</code> 不带 uri，即指向这段内嵌 BIN。用 <code>0x00</code> 填充对齐。" },
  ];

  mount.innerHTML =
    '<div class="w2">' +
    '<div class="glb-bytes" id="glb-bytes"></div>' +
    '<div class="glb-explain" id="glb-explain">点击上方任意分段查看其字段含义。</div>' +
    '<div class="w2-readout">每个 chunk 结构：<code>uint32 chunkLength</code> · <code>uint32 chunkType</code> · <code>ubyte[] chunkData</code>。Internet Media Type：<code>model/gltf-binary</code>。</div>' +
    "</div>";

  var bytesEl = mount.querySelector("#glb-bytes");
  var explainEl = mount.querySelector("#glb-explain");
  SEGS.forEach(function (s, i) {
    var d = document.createElement("div");
    d.className = "glb-seg " + s.cls;
    d.textContent = s.label;
    d.addEventListener("click", function () {
      bytesEl.querySelectorAll(".glb-seg").forEach(function (x) { x.classList.remove("active"); });
      d.classList.add("active");
      explainEl.innerHTML = "<strong>" + s.title + "</strong><br>" + s.body;
    });
    bytesEl.appendChild(d);
  });
})();
