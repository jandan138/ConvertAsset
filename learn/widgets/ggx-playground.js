/* ============================================================================
   GGX PBR Material Playground  (widget)
   ES module — 通过 import map 解析 "three" / "three/addons/"。
   挂载点：#ggx-mount（见 3-4-cook-torrance.html）。
   实现 concept-03：左 viewport + 右 sliders(roughness/metallic/baseColor/IOR)
   + metallic/specular workflow 切换 + 预设球 + F0 readout。
   ============================================================================ */
import * as THREE from "three";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const mount = document.getElementById("ggx-mount");
if (mount) initGGX(mount);

function initGGX(root) {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- DOM scaffold ----
  root.innerHTML = `
    <div class="ggx">
      <div class="ggx-view"><div class="ggx-presets" role="group" aria-label="材质预设"></div></div>
      <div class="ggx-controls">
        <div class="ctrl">
          <div class="ctrl-row"><label for="ggx-rough">roughness</label><span class="val" id="ggx-rough-v">0.35</span></div>
          <input type="range" id="ggx-rough" min="0" max="1" step="0.01" value="0.35" />
        </div>
        <div class="ctrl">
          <div class="ctrl-row"><label for="ggx-metal">metallic</label><span class="val" id="ggx-metal-v">0.80</span></div>
          <input type="range" id="ggx-metal" min="0" max="1" step="0.01" value="0.80" />
        </div>
        <div class="ctrl">
          <div class="ctrl-row"><label for="ggx-color">base color</label></div>
          <input type="color" id="ggx-color" value="#9aa0ad" style="width:100%;height:34px;border:1px solid var(--panel-border);border-radius:6px;background:var(--surface);cursor:pointer;" />
        </div>
        <div class="ctrl">
          <div class="ctrl-row"><label for="ggx-ior">IOR</label><span class="val" id="ggx-ior-v">1.45</span></div>
          <input type="range" id="ggx-ior" min="1" max="2.5" step="0.01" value="1.45" />
        </div>
        <div class="ctrl">
          <div class="seg" id="ggx-workflow">
            <button data-wf="metallic" class="active">metallic</button>
            <button data-wf="specular">specular workflow</button>
          </div>
        </div>
        <div class="ggx-readout" id="ggx-f0">F0 = 0.04 → albedo</div>
      </div>
    </div>`;

  const view = root.querySelector(".ggx-view");

  // ---- three.js setup ----
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  view.appendChild(renderer.domElement);
  renderer.domElement.style.display = "block";
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  camera.position.set(0, 0, 4.2);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enablePan = false;
  controls.enableZoom = false;
  controls.autoRotate = !reduceMotion;
  controls.autoRotateSpeed = 1.1;
  controls.enableDamping = true;

  const material = new THREE.MeshPhysicalMaterial({
    color: new THREE.Color("#9aa0ad"),
    metalness: 0.8,
    roughness: 0.35,
    ior: 1.45,
    clearcoat: 0.0,
  });
  const sphere = new THREE.Mesh(new THREE.SphereGeometry(1, 96, 96), material);
  scene.add(sphere);

  function resize() {
    const w = view.clientWidth || 480;
    const h = view.clientHeight || 360;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(resize);
  ro.observe(view);
  resize();

  function loop() {
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // ---- controls wiring ----
  const $ = (id) => root.querySelector(id);
  const rough = $("#ggx-rough"), roughV = $("#ggx-rough-v");
  const metal = $("#ggx-metal"), metalV = $("#ggx-metal-v");
  const color = $("#ggx-color");
  const ior = $("#ggx-ior"), iorV = $("#ggx-ior-v");
  const f0Out = $("#ggx-f0");
  let workflow = "metallic";

  function fresnelF0() {
    const n = parseFloat(ior.value);
    const f0 = Math.pow((1 - n) / (1 + n), 2);
    return f0;
  }
  function updateReadout() {
    const m = parseFloat(metal.value);
    if (workflow === "specular" || m < 0.001) {
      f0Out.textContent = "F0 = ((1-ior)/(1+ior))² = " + fresnelF0().toFixed(3) + "  ·  dielectric";
    } else {
      f0Out.textContent = "F0 → albedo (metallic)  ·  metalness = " + m.toFixed(2);
    }
  }
  function apply() {
    material.roughness = parseFloat(rough.value);
    material.color.set(color.value);
    material.ior = parseFloat(ior.value);
    if (workflow === "metallic") {
      material.metalness = parseFloat(metal.value);
    } else {
      // specular workflow 近似：金属度=0，用 ior 驱动 dielectric 反射
      material.metalness = 0.0;
    }
    material.needsUpdate = true;
    roughV.textContent = parseFloat(rough.value).toFixed(2);
    metalV.textContent = parseFloat(metal.value).toFixed(2);
    iorV.textContent = parseFloat(ior.value).toFixed(2);
    updateReadout();
  }
  [rough, metal, ior].forEach((s) => s.addEventListener("input", apply));
  color.addEventListener("input", apply);

  root.querySelectorAll("#ggx-workflow button").forEach((b) => {
    b.addEventListener("click", () => {
      root.querySelectorAll("#ggx-workflow button").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      workflow = b.getAttribute("data-wf");
      metal.disabled = workflow === "specular";
      metal.style.opacity = workflow === "specular" ? 0.4 : 1;
      apply();
    });
  });

  // ---- presets ----
  const PRESETS = [
    { name: "plastic", color: "#d23b3b", metal: 0.0, rough: 0.45, ior: 1.5 },
    { name: "gold", color: "#ffc24d", metal: 1.0, rough: 0.18, ior: 0.47 },
    { name: "brushed metal", color: "#b8bcc4", metal: 1.0, rough: 0.42, ior: 2.0 },
    { name: "ceramic", color: "#eef0f4", metal: 0.0, rough: 0.08, ior: 1.5 },
  ];
  const presetWrap = root.querySelector(".ggx-presets");
  PRESETS.forEach((p, i) => {
    const b = document.createElement("button");
    b.className = "ggx-chip" + (i === 0 ? " active" : "");
    b.innerHTML = `<span class="dot" style="background:${p.color}"></span><span>${p.name}</span>`;
    b.addEventListener("click", () => {
      presetWrap.querySelectorAll(".ggx-chip").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      rough.value = p.rough; metal.value = p.metal; color.value = p.color; ior.value = p.ior;
      // 预设默认 metallic workflow
      root.querySelector('#ggx-workflow button[data-wf="metallic"]').click();
      rough.value = p.rough; metal.value = p.metal; color.value = p.color; ior.value = p.ior;
      apply();
    });
    presetWrap.appendChild(b);
  });

  apply();
}
