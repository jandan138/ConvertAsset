# references.py 深入浅出

本文面向对 USD 组合关系（references/payloads/sublayers/variants/clips）不熟悉的同学，解释本项目中 `convert_asset/no_mdl/references.py` 的职责、数据流与边界情况，并说明它与 `processor.py`、`materials.py` 的关系。

---

## 1. 它在整个流程中的位置

- 顶层调度在 `processor.py`：
  1) 打开源 USD；
  2) 调用 `_collect_asset_paths(stage)` 收集当前文件里“指向其它 USD”的所有位置；
  3) 先递归处理所有子 USD，得到“源→目标(_noMDL)”映射；
  4) 导出当前 root layer 为兄弟的 `*_noMDL.usd`；
  5) 打开新文件，调用 `_rewrite_assets_in_stage(dst_stage, mapping)` 把所有指向改成 `_noMDL` 版本；
  6) 再调用材质转换（`convert_and_strip_mdl_in_this_file_only`），把 MDL 切换为 `UsdPreviewSurface`；
  7) 保存并验证。

- `references.py` 负责的就是 2) 和 5)：
  - 收集依赖（在哪些地方引用了其它资产文件）；
  - 在新文件中将这些引用改写为 `_noMDL` 对应路径。

- `materials.py` 则负责材质网络改写（切换 MDL→Preview、接线、清理 MDL）。两者互不重叠：一个改结构的“指向”，一个改材质的“内容”。

---

## 2. 为什么要分别“收集”和“改写”？

- “收集”是为了先知道所有子文件，递归地优先把子文件处理成 `_noMDL`，这样我们在“改写当前文件”的时候，才能把指向替换为已经存在的新路径。
- “改写”只发生在当前正在导出的那个目标文件上（兄弟 `*_noMDL`），不会修改原始源文件；并且保持 references/payloads/sublayers/variants/clips 的结构与语义不变，只改 assetPath 字符串。

---

## 3. 收集是怎么做的（_collect_asset_paths）

- 遍历 Root Layer 的 `subLayerPaths`（记录分层文件）。
- 遍历每个 Prim：
  - 从 `metadata` 读取 `references` 的 ListOp；
  - 从 `metadata` 读取 `payloads` 的 ListOp（有时字段名可能是 `payload`）；
  - 读取 `clips`（如果存在）：
    - `clipAssetPaths` 为列表；
    - `manifestAssetPath` 为单值。
  - 遍历每个 VariantSet，进入每个变体（`with vs.GetVariantEditContext(vname):`）：
    - 在变体上下文内，同样从 `metadata` 读取 `references`/`payloads`。
  - 结束后可选恢复原来的 `variant selection`，以免影响作者设定。

- 为了兼容不同 USD 版本，我们在收集阶段使用 `GetMetadata("references")` 返回 ListOp，然后通过 `_listop_items` 展开为普通列表；这样不依赖较新的 API。

- 返回的数据结构为六元组：
  - `(kind, holder, layer_dir, assetPath, prim_path, extra)`
  - `kind`：如 `sublayer`、`reference`、`payload`、`variant_ref`、`variant_payload`、`clip_asset`、`clip_manifest`；
  - `holder`：定位信息，便于日志或后续调试（例如 `("prim", "/World/Geom")` 或 `("/Prim", setName, varName)`）；
  - `layer_dir`：发现该条目时所处 layer 的目录；
  - `assetPath`：引用到的资产路径字符串（可能相对）；
  - `prim_path`：关联的 Prim 路径（如有）；
  - `extra`：对于 references/payloads 是 ListOp item，本身包含 `primPath` 与 `layerOffset` 等；对于 clips 是字段名字符串（如 `"clipAssetPaths"`）。

---

## 4. 改写是怎么做的（_rewrite_assets_in_stage）

- 输入：打开的目标 Stage，与一个“源绝对路径 → 目标绝对路径”的字典映射（来自 `Processor.process` 的递归结果）。
- 解析锚点：以 root layer 的目录作为相对路径基准。
- 对每一类组合关系进行替换：
  1) `sublayers`：遍历 `layer.subLayerPaths`，遇到匹配的源绝对路径，就替换为映射的相对路径；最后写回整个列表。
  2) `references`：
     - 收集旧条目（metadata → ListOp）；
     - 对每个条目尝试将 `assetPath` 绝对化并查映射，命中则新建 `Sdf.Reference`（保留 `primPath` 与 `layerOffset`），放入新列表；
     - 如果有变动，优先用 API：`ClearReferences()` 后逐个 `AddReference()`；如 API 不可用或异常则回退 `SetMetadata("references", new_items)`。
  3) `payloads`：与 `references` 同理，使用 `Sdf.Payload`、`ClearPayloads()`/`AddPayload()`。
  4) `clips`：如果 prim 有 `clips` 字典：
     - 遍历 `clipAssetPaths` 列表逐项替换；
     - 替换 `manifestAssetPath`；
     - 有改动则整体写回 `clips` 元数据。
  5) `variants`：进入每个变体的上下文，重复对 `references`/`payloads` 的改写，并可选恢复原选择。

- 写回相对路径：我们用 `_relpath(layer_dir, target_abs)` 把绝对目标路径转回相对于当前 layer 目录的相对路径，保持项目工程的相对引用习惯。

---

## 5. 为什么既用 API 又写 metadata？

- 在一些 USD 版本或特定场景下，References/Payloads 的 API 写入可能不可用或行为不一致。
- 为了稳健性，我们采用“API 优先、失败回退 metadata”的策略：
  - 成功则保持结构语义最清晰；
  - 失败时 metadata 写回也能达到改写效果，保证不因版本差异而中断流程。

---

## 6. 边界与注意事项

- 文件路径锚点：收集时记录了发现条目时的 layer 目录；改写时以目标 stage 的 root layer 目录为基准重新计算相对路径，避免层混淆。
- usdz 打包：若指向 `.usdz`，本模块只改写路径，不解包也不重新打包（符合“不打平”的策略）。
- 变体还原：启用 `RESTORE_VARIANT_SELECTION` 时，会在进入变体扫描/改写之后恢复选择，避免意外改变作者设定。
- Clips 结构：仅在 `clips` 为 dict 且键符合 `clipAssetPaths`/`manifestAssetPath` 预期时进行改写；异常或不支持的结构会被安全跳过。

---

## 7. 与 materials.py 的分工界面

- references.py：
  - 只改“指向关系”（paths），保证组合结构不变；
  - 不处理具体材质节点与连接。
- materials.py：
  - 只改“材质网络”（nodes/inputs/outputs），把 MDL 切换成 Preview 并剥离残留；
  - 不改任何 references/payloads/sublayers/variants/clips。

这样的分工使逻辑清晰、可测试性强，也方便独立调试结构问题与材质问题。

---

## 8. 快速检查清单（Debug Guide）

- 如果发现子文件没有被改写为 `_noMDL`：
  - 检查 `Processor` 是否先递归处理子文件并建立了映射；
  - 用 `_collect_asset_paths` 打印收集到的条目，确认对应路径是否被枚举到。
- 如果 references/payloads 没有生效：
  - 观察是否走到了回退写 metadata 的分支；
  - 用 USDView 打开目标文件，检查属性是否在正确的层被著述。
- 如果变体内的改写缺失：
  - 检查是否进入了正确的 `VariantEditContext`，以及是否恢复了原选择。
- 如果 clips 未改写：
  - 确认 `clips` 结构为字典，键名与预期一致；
  - 列表中的每一项路径是否存在于映射中。

---

## 9. 进一步阅读

- 本仓库：`docs/processor.md`（流程与 Root Layer 教程）、`docs/usd_knowledge/roots_refs_prims.md`（根层与组合关系基础）
- Pixar USD 文档：Sdf（ListOp, Layer）, Usd（Prim, Stage）, UsdShade（材质 API）
