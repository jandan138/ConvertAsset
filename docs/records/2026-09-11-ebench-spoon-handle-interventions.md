# 2026-09-11 EBench 勺柄几何干预资产

本次服务于 EEOS 的 EBench 自主进化研究：Astra 从 dish 的结果与原始观测提出
勺子获取几何与任务进度两种竞争解释，要求制作同流程原尺寸对照和加宽勺柄。
本记录只报告资产生成与运行检查，不报告模型效果。

## 调查与决定

源资产来自 EBench `long_horizon/scene_dish/scene.usd:/root/obj_spoon`，包含单个
1511 顶点网格及其源材质、纹理和物理属性。原任务对该物体应用均匀 0.2 缩放。
勺子沿局部 Z 轴延伸，正 Z 段为勺头，负 Z 段为勺柄。

新增 `scripts/build_ebench_spoon_intervention.py`：Blender 4.4.3 读取相同原始网格，
在 `z<=-0.1` 对 X/Y 横截面作 1×或 2×缩放，在 `[-0.1,0.1]` 平滑衔接，
`z>=0.1` 的勺头顶点完全不动；所有 Z 坐标保持不变。
两版均经过 Blender 建模与法线重算，保留同一拓扑、源材质和 UV。

源质量 `0.10000000149011612` 保留于两版。源惯量配置保持，运行时求解后的惯量还未匹配；
源 collision approximation 为 convexDecomposition，contactOffset 为约 0.02 stage units。
这些来源设置不是已测得的真实勺子参数；后续抓取实验应核对实际碰撞响应，不能仅凭几何加宽
宣布抓取更容易。

## 版本与打包

r1 保留了对整间房源文件的引用，AAN 依赖扫描因此遇到 8 个不属于勺子子树的房间缺失纹理。
没有补造或忽略这些依赖。r2 改为导出组合后的勺子子树，再交现有 AAN 正常处理纹理与 MDL 闭包。
这是 ConvertAsset 生产者范围内的作用域提取，未修改原始场景，也未要求 scenario-forge 修复资产。

当前输出：`outputs/ebench_spoon_intervention_20260911_r2/`。

- `spoon_variants.blend`：包含两个原点重合的可编辑网格，查看单版时需隐藏另一版。
- `handle_1p0.usda` / `handle_2p0.usda`：生成源，仍含外部材质依赖。
- `control_package` / `wide_package`：通过静态检查的 AAN 包。
- `control_runtime_package` / `wide_runtime_package`：通过静态与运行检查的 AAN 包。
- `generation_report.json`：源指纹、变形误差、质量处理、Blender 版本与生成资产哈希。
- `*_geometry_preview.png`：相同相机的 Blender 几何预览，仅用于检查轮廓，不是策略输入。

## 实际验证

两版均保留 1511 顶点及原拓扑。对照版变形误差为 0，加宽版最大误差约 `1.82e-9`
源坐标单位；勺头顶点逐点相同。两版的材质绑定路径及继承质量一致。

| 资产 | 独立运行 ID | 实际 Kit 版本 | 冷加载 | 渲染读回 | 物理步 | 重置 |
| --- | --- | --- | --- | --- | --- | --- |
| 原尺寸对照 | `f130fa1dc1874296a37223ad7ed77df4` | `4.1.0-rc.7+4.1.14801.71533b68.gl` | pass | pass | 120 | pass |
| 加宽勺柄 | `b4281560a41e493db92726868f132c09` | 同上 | pass | pass | 120 | pass |

报告位于各运行包的 `evidence/runtime_smoke/report.json`，图像位于同目录 `render.png`
和 `material_views/`。当前智能体实际查看了两版 Blender 几何预览和 Isaac 主图：
勺子可辨认，几何预览可看出柄部加宽。Isaac 诊断场景中的加宽版主图有明显白色区域，
这些独立自适应取景图不作为材质不变或 VLA 输入公平性的配对证据；需最终任务中的固定相机图确认。
本次不是独立盲审。

测试：`tests/test_ebench_spoon_intervention.py` 的 2 项测试通过，新增脚本及测试 ruff 通过。
未修改既有转换实现；未运行 ConvertAsset 全量测试，未合并。

## 复现命令

```bash
EEOS_PYTHON=/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-py310/bin/python
"$EEOS_PYTHON" scripts/build_ebench_spoon_intervention.py \
  --source /cpfs/shared/simulation/zhuzihou/dev/GenManip/saved/assets/scene_usds/ebench/long_horizon/scene_dish/scene.usd \
  --blender /cpfs/shared/simulation/zhuzihou/tools/blender-4.4.3-linux-x64/blender \
  --out outputs/NEW-ebench-spoon-interventions
```

两版分别调用现有 `main.py normalize-asset`，参数为 `--asset-role dynamic`、
`--source-runtime generic_usd`、`--target-runtime isaac41`、`--target-benchmark ebench-lift2`、
`--asset-scope-prim /World/Spoon`、`--required-prim /World/Spoon`、`--gates static,runtime`，
并显式传入项目 IsaacSim41 Python。原始实际命令与配置保留在包 manifest 中。
`generic_usd` 表示源 USD 由原生资产与 Blender 几何编辑共同组成，Blender 版本另记在生成报告中。

## 给消费者的交接

后续增加 `--overlay-asset` 入口，把 AAN 资产映射回 `/root/obj_spoon`，恢复原场景的
完整 source Xform，重映射材质连接。输出 `native_control_overlay.usda` 与
`native_wide_overlay.usda`，供 Scenario Forge 组合。实际组合检查未出现重复 0.2 缩放；
新增测试验证姿态与材质绑定。当前共 3 项测试通过。overlay 的最终任务运行仍需另验。

目标：将两个候选放入相同 dish 任务条件，检验获取几何与任务进度的解释。
范围：资产交付；没有证明 Lift2 可抓持、完整任务可解或 VLA 成功。

资产入口 `/World/Spoon` 已含 0.2 的源物体缩放。消费者必须核实实际组合后的尺寸，
不能再盲目乘一次原任务的 0.2。场景姿态需从原任务元数据恢复，避免由 standalone 预览原点
直接推断桌面放置。

后续仍需适用的交互／质量绑定、最终场景固定相机检查、抓取与任务运行；当前包的
目标为 ebench-lift2，不能伪称已满足 scenario-forge 额外的 rigid_object 交互资格合同。

本次遵循 scenario-forge 的 ASSET-001（生产者拥有资产修复）、ASSET-002（来源绑定）
及 VAL-002/003（验证匹配改动与最终内容）。没有改变通用规则，因此不修改其规范库。
