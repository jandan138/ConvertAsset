/*
 * ConvertAsset Learning Guide — 导航单一事实源 (single source of truth)
 *
 * 这是一个 classic script（非 module），直接挂到 window.BOOK，
 * 这样在 file:// 与本地 http server 下都能工作，无需打包构建。
 *
 * 结构：BOOK.parts[].chapters[].sections[]
 *   - section.id   稳定 id，如 "3-4"，用于页面 <body data-section-id>
 *   - section.t    标题（中文叙述 + 英文术语保留）
 *   - section.href 相对 learn/ 根的路径
 *
 * 章节文本以本表为准；概念稿仅用于视觉。
 */
window.BOOK = {
  title: "ConvertAsset Learning Guide",
  subtitle: "From GAMES101 to a Production USD Asset Pipeline",
  // repoUrl 仅用于顶栏 "Repo" 链接占位，可后续指向真实仓库地址
  repoUrl: "https://github.com/jandan138/ConvertAsset",
  parts: [
    {
      n: "00",
      title: "导论 · Orientation",
      chapters: [
        {
          id: "0",
          num: "0",
          title: "从课堂渲染器到 production pipeline",
          sections: [
            { id: "0-1", t: "你的 GAMES101 渲染器到哪为止", href: "chapters/00-orientation/0-1-classroom-renderer.html" },
            { id: "0-2", t: "production asset pipeline 全景：the asset journey", href: "chapters/00-orientation/0-2-asset-journey.html" },
            { id: "0-3", t: "认识 case study：ConvertAsset 与它的论文问题", href: "chapters/00-orientation/0-3-meet-convertasset.html" },
          ],
        },
      ],
    },
    {
      n: "I",
      title: "场景表示 · Scene Representation",
      chapters: [
        {
          id: "1",
          num: "1",
          title: "USD foundations",
          sections: [
            { id: "1-1", t: "为什么需要 interchange format", href: "chapters/01-usd-foundations/1-1-why-interchange.html" },
            { id: "1-2", t: "data model：Stage / Prim / Property", href: "chapters/01-usd-foundations/1-2-data-model.html" },
            { id: "1-3", t: "Layer 与 opinion", href: "chapters/01-usd-foundations/1-3-layers-opinions.html" },
            { id: "1-4", t: "usdview 与 pxr Python 速览", href: "chapters/01-usd-foundations/1-4-usdview-pxr.html" },
          ],
        },
        {
          id: "2",
          num: "2",
          title: "Composition 与 LIVERPS",
          sections: [
            { id: "2-1", t: "composition arcs 总览", href: "chapters/02-usd-composition/2-1-arcs-overview.html" },
            { id: "2-2", t: "LIVERPS strength ordering", href: "chapters/02-usd-composition/2-2-liverps.html" },
            { id: "2-3", t: "references vs payloads（延迟加载）", href: "chapters/02-usd-composition/2-3-references-payloads.html" },
            { id: "2-4", t: "variant sets", href: "chapters/02-usd-composition/2-4-variant-sets.html" },
            { id: "2-5", t: "case：为什么 ConvertAsset 选择 composition-preserving", href: "chapters/02-usd-composition/2-5-case-non-flatten.html" },
          ],
        },
      ],
    },
    {
      n: "II",
      title: "材质与外观 · Materials & Appearance",
      chapters: [
        {
          id: "3",
          num: "3",
          title: "从 Blinn-Phong 到 PBR",
          sections: [
            { id: "3-1", t: "回顾 Blinn-Phong 与它的不足", href: "chapters/03-pbr/3-1-blinn-phong-recap.html" },
            { id: "3-2", t: "rendering equation 与 BRDF 复习", href: "chapters/03-pbr/3-2-rendering-equation-brdf.html" },
            { id: "3-3", t: "microfacet model 与 energy conservation", href: "chapters/03-pbr/3-3-microfacet.html" },
            { id: "3-4", t: "Cook-Torrance：D · F · G", href: "chapters/03-pbr/3-4-cook-torrance.html" },
            { id: "3-5", t: "GGX (Trowbridge-Reitz) 与 roughness", href: "chapters/03-pbr/3-5-ggx-roughness.html" },
          ],
        },
        {
          id: "4",
          num: "4",
          title: "Production material models",
          sections: [
            { id: "4-1", t: "metallic-roughness vs specular workflow", href: "chapters/04-material-models/4-1-workflows.html" },
            { id: "4-2", t: "UsdPreviewSurface 参数详解", href: "chapters/04-material-models/4-2-usdpreviewsurface.html" },
            { id: "4-3", t: "glTF metallic-roughness", href: "chapters/04-material-models/4-3-gltf-pbr.html" },
            { id: "4-4", t: "Disney principled \u201cuber-shader\u201d", href: "chapters/04-material-models/4-4-disney-principled.html" },
            { id: "4-5", t: "三者对照与互转", href: "chapters/04-material-models/4-5-comparison.html" },
          ],
        },
        {
          id: "5",
          num: "5",
          title: "MDL",
          sections: [
            { id: "5-1", t: "MDL 是什么：declarative + procedural", href: "chapters/05-mdl/5-1-what-is-mdl.html" },
            { id: "5-2", t: "distribution functions 与 material struct", href: "chapters/05-mdl/5-2-distribution-functions.html" },
            { id: "5-3", t: "为什么 renderer-bound", href: "chapters/05-mdl/5-3-renderer-bound.html" },
            { id: "5-4", t: "vMaterials 与 MDL SDK 生态", href: "chapters/05-mdl/5-4-ecosystem.html" },
          ],
        },
        {
          id: "6",
          num: "6",
          title: "Case study：no-MDL conversion",
          sections: [
            { id: "6-1", t: "转换动机：portability vs fidelity", href: "chapters/06-no-mdl/6-1-motivation.html" },
            { id: "6-2", t: "算法：MDL 网络 → UsdPreviewSurface", href: "chapters/06-no-mdl/6-2-algorithm.html" },
            { id: "6-3", t: "path / reference 重写", href: "chapters/06-no-mdl/6-3-reference-rewrite.html" },
            { id: "6-4", t: "论文视角：conversion as controlled perturbation", href: "chapters/06-no-mdl/6-4-perturbation.html" },
            { id: "6-5", t: "before / after 实测", href: "chapters/06-no-mdl/6-5-before-after.html" },
          ],
        },
      ],
    },
    {
      n: "III",
      title: "几何与优化 · Geometry & Optimization",
      chapters: [
        {
          id: "7",
          num: "7",
          title: "Production meshes",
          sections: [
            { id: "7-1", t: "mesh 数据：points / faceVertexIndices / counts", href: "chapters/07-meshes/7-1-mesh-data.html" },
            { id: "7-2", t: "primvars 与 interpolation", href: "chapters/07-meshes/7-2-primvars-interpolation.html" },
            { id: "7-3", t: "UV (st) 与 normals", href: "chapters/07-meshes/7-3-uv-normals.html" },
            { id: "7-4", t: "face-varying 的坑", href: "chapters/07-meshes/7-4-face-varying.html" },
          ],
        },
        {
          id: "8",
          num: "8",
          title: "Mesh simplification：QEM",
          sections: [
            { id: "8-1", t: "LOD 是什么，为什么要简化", href: "chapters/08-mesh-qem/8-1-why-lod.html" },
            { id: "8-2", t: "edge collapse / vertex pair contraction", href: "chapters/08-mesh-qem/8-2-edge-collapse.html" },
            { id: "8-3", t: "quadric error metric 推导", href: "chapters/08-mesh-qem/8-3-quadric-derivation.html" },
            { id: "8-4", t: "最优 contraction 位置求解", href: "chapters/08-mesh-qem/8-4-optimal-position.html" },
            { id: "8-5", t: "case：simplify.py 三个 backend 与 UV 保持", href: "chapters/08-mesh-qem/8-5-case-backends.html" },
          ],
        },
      ],
    },
    {
      n: "IV",
      title: "资产交换与交付 · Asset Interchange",
      chapters: [
        {
          id: "9",
          num: "9",
          title: "glTF 2.0 / GLB",
          sections: [
            { id: "9-1", t: "glTF 设计哲学：runtime delivery", href: "chapters/09-gltf-glb/9-1-philosophy.html" },
            { id: "9-2", t: "scene / node / mesh / accessor / bufferView / buffer", href: "chapters/09-gltf-glb/9-2-data-model.html" },
            { id: "9-3", t: "GLB 二进制容器", href: "chapters/09-gltf-glb/9-3-glb-container.html" },
            { id: "9-4", t: "PBR material 在 glTF 里的表达", href: "chapters/09-gltf-glb/9-4-gltf-material.html" },
            { id: "9-5", t: "二进制解剖实操", href: "chapters/09-gltf-glb/9-5-dissection.html" },
          ],
        },
        {
          id: "10",
          num: "10",
          title: "Case study：USD→GLB pipeline",
          sections: [
            { id: "10-1", t: "orchestration 总览", href: "chapters/10-usd-to-glb/10-1-orchestration.html" },
            { id: "10-2", t: "mesh 提取与 face-varying UV flattening", href: "chapters/10-usd-to-glb/10-2-mesh-extraction.html" },
            { id: "10-3", t: "material / texture 提取", href: "chapters/10-usd-to-glb/10-3-material-extraction.html" },
            { id: "10-4", t: "writer：拼出 GLB", href: "chapters/10-usd-to-glb/10-4-writer.html" },
            { id: "10-5", t: "cycle detection / dedup / lazy import 设计", href: "chapters/10-usd-to-glb/10-5-pipeline-design.html" },
          ],
        },
      ],
    },
    {
      n: "V",
      title: "渲染硬件与实时 · Rendering Hardware",
      chapters: [
        {
          id: "11",
          num: "11",
          title: "GPU rendering pipeline",
          sections: [
            { id: "11-1", t: "从 rasterization 回顾到硬件", href: "chapters/11-gpu-pipeline/11-1-raster-to-hardware.html" },
            { id: "11-2", t: "SM / CUDA core / warp / SIMT 执行模型", href: "chapters/11-gpu-pipeline/11-2-sm-warp-simt.html" },
            { id: "11-3", t: "rasterization pipeline 在硬件上", href: "chapters/11-gpu-pipeline/11-3-raster-pipeline.html" },
            { id: "11-4", t: "ray tracing 为什么贵", href: "chapters/11-gpu-pipeline/11-4-why-rt-expensive.html" },
          ],
        },
        {
          id: "12",
          num: "12",
          title: "RTX：real-time ray tracing 硬件",
          sections: [
            { id: "12-1", t: "BVH：加速结构", href: "chapters/12-rtx/12-1-bvh.html" },
            { id: "12-2", t: "RT Core：traversal + ray-triangle intersection", href: "chapters/12-rtx/12-2-rt-core.html" },
            { id: "12-3", t: "rasterization vs RT 混合管线", href: "chapters/12-rtx/12-3-hybrid-pipeline.html" },
            { id: "12-4", t: "Tensor Core 与 denoising / DLSS", href: "chapters/12-rtx/12-4-tensor-denoising.html" },
            { id: "12-5", t: "Turing → Ampere 演进（whitepaper 数据）", href: "chapters/12-rtx/12-5-turing-ampere.html" },
          ],
        },
      ],
    },
    {
      n: "VI",
      title: "仿真与具身智能 · Simulation & Embodied AI",
      chapters: [
        {
          id: "13",
          num: "13",
          title: "Isaac Sim / Omniverse",
          sections: [
            { id: "13-1", t: "Omniverse 平台与 USD backbone", href: "chapters/13-isaac-sim/13-1-omniverse-usd.html" },
            { id: "13-2", t: "PhysX 与 RTX rendering", href: "chapters/13-isaac-sim/13-2-physx-rtx.html" },
            { id: "13-3", t: "SimReady assets 与为什么要转换 / 简化", href: "chapters/13-isaac-sim/13-3-simready.html" },
            { id: "13-4", t: "单资产本地出图（render / camera）", href: "chapters/13-isaac-sim/13-4-local-render.html" },
          ],
        },
        {
          id: "14",
          num: "14",
          title: "Embodied AI downstream",
          sections: [
            { id: "14-1", t: "VLN 任务是什么", href: "chapters/14-embodied-ai/14-1-vln.html" },
            { id: "14-2", t: "VLM grounding 与 GRScenes", href: "chapters/14-embodied-ai/14-2-vlm-grounding.html" },
            { id: "14-3", t: "metrics：PSNR / SSIM / LPIPS / CLIP / DINOv2", href: "chapters/14-embodied-ai/14-3-metrics.html" },
            { id: "14-4", t: "论文的 evidence-gate protocol", href: "chapters/14-embodied-ai/14-4-evidence-gates.html" },
            { id: "14-5", t: "material-effect risk：转换为何可能影响 grounding", href: "chapters/14-embodied-ai/14-5-material-effect-risk.html" },
          ],
        },
      ],
    },
    {
      n: "VII",
      title: "综合 · Capstone",
      chapters: [
        {
          id: "15",
          num: "15",
          title: "端到端 asset journey",
          sections: [
            { id: "15-1", t: "端到端跑一遍 CLI", href: "chapters/15-capstone/15-1-run-cli.html" },
            { id: "15-2", t: "在 viewer 里逐阶段看 asset", href: "chapters/15-capstone/15-2-stage-viewer.html" },
            { id: "15-3", t: "你建立的 mental model 总结", href: "chapters/15-capstone/15-3-mental-model.html" },
          ],
        },
        {
          id: "app",
          num: "App",
          title: "附录 · Appendix",
          sections: [
            { id: "app-glossary", t: "Glossary 中英术语表", href: "chapters/appendix/glossary.html" },
            { id: "app-cli", t: "CLI cheat-sheet", href: "chapters/appendix/cli-cheatsheet.html" },
            { id: "app-bib", t: "Bibliography 参考资料", href: "chapters/appendix/bibliography.html" },
            { id: "app-math", t: "Math refresher", href: "chapters/appendix/math-refresher.html" },
          ],
        },
      ],
    },
  ],
};

// 扁平化所有 section，便于 prev/next 与查找
window.BOOK.flat = (function () {
  const out = [];
  window.BOOK.parts.forEach(function (part) {
    part.chapters.forEach(function (ch) {
      ch.sections.forEach(function (sec) {
        out.push({
          id: sec.id,
          t: sec.t,
          href: sec.href,
          chapter: ch.num,
          chapterTitle: ch.title,
          part: part.n,
          partTitle: part.title,
        });
      });
    });
  });
  return out;
})();
