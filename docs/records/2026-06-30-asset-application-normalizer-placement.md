# Asset Application Normalizer Placement

Date: 2026-06-30

## 背景

LabUtopia -> EBench 的 Lift2 / DryingBox POC 已证明：一个 USD asset 进入目标
benchmark，不只是文件转换，还需要 dependency、material、physics、articulation、
runtime smoke、task contract 和 evidence manifest 同时闭环。

用户进一步提出更大的方向：先保证 USD rigid body 和 articulated body 可进入 EBench，
同时保留未来扩展到 AutoBio / MuJoCo / MJCF、Genesis-based benchmark、EOS adapter
的空间。

## 关键纠偏

1. Isaac Sim importer / URDF importer 可以用，但 importer 只解决格式入口。
   URDF 本身不是 rich MDL material 的高保真载体，因此材质闭环仍需要 ConvertAsset
   的 MDL -> UsdPreviewSurface、local mirror、explicit waiver 等策略。
2. LabUtopia 和 AutoBio 不应作为同类项目名硬编码。LabUtopia 目前更准确地说是
   Isaac 5.1-oriented USD asset source；EBench 是 Isaac Sim 4.1 target benchmark
   profile；AutoBio 是 MuJoCo / MJCF assets 和 task semantics。

## 多角度审阅结论

External ecosystem reviewer 的结论：

- OpenUSD / `usdchecker`、Omniverse Asset Validator、SimReady、Isaac importers、
  OpenAssetIO、RoboVerse / MetaSim 都有参考价值；
- 但它们分别覆盖 validation、profile、import、asset management、simulator/task
  execution 等局部问题；
- 缺口仍然是 target-contract normalizer：资产进到某个 benchmark 后是否真的能
  load / render / step / evaluate，并留下可审计证据。

Repo boundary reviewer 的结论：

- ConvertAsset 是主实现仓库，因为它已经拥有 USD / MDL / material / render / mesh
  等资产处理能力；
- EOS 只消费 normalizer 输出的 evidence、asset resolution result、EpisodeTrace 和
  benchmark adapter contract；
- LabUtopia / GenManip 只保留 source / target integration evidence，不做通用工具归宿。

## 决策

文档和未来实现先落 ConvertAsset。

主设计文档：

- `docs/design/asset-application-normalizer.md`

未来实现建议：

```text
convert_asset/asset_application_normalizer/
```

EOS 未来对接点：

- `AssetResolutionRequest`
- `AssetResolutionResult`
- `ExternalAssetRef`
- `AssetBundleManifest`
- `EpisodeTrace`

## MVP 范围

第一阶段只承诺：

- USD rigid body；
- USD articulated body；
- target profile 为 EBench Isaac Sim 4.1；
- 资产 dependency / material / physics / articulation / runtime smoke / benchmark
  contract 全链路证据。

第一阶段不承诺：

- 任意 USD；
- deformable / cloth / particle / liquid；
- AutoBio official reproduction；
- EBench official leaderboard comparability；
- policy success；
- rich MDL 无损跨 runtime。

## 后续动作

1. 在 ConvertAsset 内冻结 design contract 和 docs navigation。
2. 抽取当前 DryingBox / Lift2 POC 的 manifest 字段。
3. 做 USD package scanner 和 material closure report。
4. 定义 EBench Isaac 4.1 target profile。
5. 用第二、第三个 rigid/articulated USD asset 验证 pipeline 不是单资产特化。
6. 单独开 MJCF / AutoBio source adapter research lane。
