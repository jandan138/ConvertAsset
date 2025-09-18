# USD 新手教程：ListOp 与组合关系的几种“条目类型”

适合读者：第一次接触 USD 里 references/payloads/sublayers/variants/clips 的同学。

目标：搞清楚两个层面。
- ListOp 是什么、为什么 references/payloads 读出来是“一个操作栈”而不是简单数组？
- 我们在代码与文档里经常提到的“条目类型”：`sublayer`、`reference`、`payload`、`variant_ref`、`variant_payload`、`clip_asset`、`clip_manifest`，各自表示什么、在哪出现、如何改写？

---

## 1. 什么是 ListOp？

- 在 USD 里，像 `references`、`payloads` 这样的字段不是简单的“列表”，而是“列表操作（ListOp）”。
- ListOp 支持多种来源分层叠加（不同 Layer 都可以往里加/删/覆盖），因此它有“操作型”的概念，比如：
  - 显式设置（Explicit）
  - 添加项（Added）
  - 前置添加（Prepended）
  - 后置添加（Appended）
  - 移除项（Deleted）
- 当我们读取 `prim.GetMetadata("references")` 时，拿到的是一个 ListOp 对象，而不是普通数组。
- 在代码中，我们通常把它“展开”为一个普通列表来遍历，这就是 `_listop_items(listop)` 在做的事：
  - 依次取 `GetExplicitItems / GetAddedItems / GetPrependedItems / GetAppendedItems` 并合并。

直觉理解：ListOp 像是“合成出来的列表的做法”，而不是“最后的拍扁结果”。我们为了遍历，就临时当它是列表用；但真正写回时最好用 API（Clear/Add）去表达更清晰的意图，写失败再回退 metadata。

---

## 2. 条目类型总览（我们文档里的 kind 字段）

我们把收集到的每一条“指向其它资产”的记录抽象成一个六元组 `(kind, holder, layer_dir, assetPath, prim_path, extra)`，其中最关键的就是 `kind`，它表示这条记录是什么类型的“组合关系”。

下表是几个常见 kind 的含义与出现位置：

- `sublayer`
  - 出现位置：Root Layer 的 `subLayerPaths` 列表。
  - 意义：当前文件由哪些 Layer “分层组合”起来；像“图层堆叠”。
  - 改写方式：直接替换 `layer.subLayerPaths` 中的字符串（通常写相对路径）。

- `reference`
  - 出现位置：某个 Prim 上的 `references`（ListOp）。
  - 意义：把另一个 USD 的内容“引用/拼装”到当前 Prim 下，可进一步通过 `primPath` 指向子树；类似“乐高积木拼装”。
  - 改写方式：把 `Sdf.Reference(assetPath, primPath, layerOffset)` 的 `assetPath` 替换为目标路径（保持 `primPath` 和 `layerOffset` 不变）。

- `payload`
  - 出现位置：某个 Prim 上的 `payloads`（ListOp）。
  - 意义：也是“拼装”，但它通常是惰性加载的（需要时才加载），适合大资产；
    可以理解为“引用的一种，强调按需加载”。
  - 改写方式：同 `reference`，用 `Sdf.Payload` 替换 assetPath，保持其它字段。

- `variant_ref`
  - 出现位置：某个 Prim 的 VariantSet 中（进入变体编辑上下文后）读到的 `references`。
  - 意义：跟 `reference` 一样，但它只在“某个变体被激活时才生效”。
  - 改写方式：进入 `with vs.GetVariantEditContext(vname):` 的上下文后，按 `reference` 的方式改写。

- `variant_payload`
  - 出现位置：某个 Prim 的 VariantSet 中（进入变体编辑上下文后）读到的 `payloads`。
  - 意义：同 `payload`，但受变体选择控制。
  - 改写方式：在变体上下文里按 `payload` 的方式改写。

- `clip_asset`
  - 出现位置：Prim 的 `clips` 元数据中的 `clipAssetPaths`（列表）。
  - 意义：USD 的时间切片（value clips）机制，可以让一个 Prim 在不同时间段读不同的 USD 片段。
  - 改写方式：对列表中每一项检查并替换为目标路径。

- `clip_manifest`
  - 出现位置：Prim 的 `clips` 元数据中的 `manifestAssetPath`。
  - 意义：为 clips 提供“目录册”（manifest），描述各时间段的布局。
  - 改写方式：如果路径命中映射则替换为目标路径。

---

## 3. 我应该在什么“目录基准”下解析/写回路径？

- 解析（读）：先把 `assetPath` 结合“当前 root layer 的目录”转成绝对路径，这样才能在“全局”层面查到“源→目标”的映射。
- 写回：把目标的绝对路径再转回“相对于当前 layer 目录”的相对路径，保持工程习惯，避免把路径写死成绝对路径。

小贴士：Root Layer 的目录可以用 `os.path.dirname(layer.realPath or layer.identifier)` 获取。

---

## 4. 为什么优先用 API 写回，失败再回退 metadata？

- `references`/`payloads` 是 ListOp，推荐的写法是：
  - `ref_api.ClearReferences()` → 循环 `ref_api.AddReference(Sdf.Reference(...))`
  - `pay_api.ClearPayloads()` → 循环 `pay_api.AddPayload(Sdf.Payload(...))`
- 这样更符合 USD 的意图、也能减少歧义。
- 但在一些版本或特定场景，API 写入可能失败或行为与预期不一致，所以我们保底用 `prim.SetMetadata("references", new_items)`/`SetMetadata("payloads", new_items)` 来写回。

---

## 5. 和 MDL→Preview 转换有什么关系？

- 这些“条目类型”的改写，解决的是“结构层面”的问题：让当前文件的组合关系都指向对应的 `_noMDL` 子文件。
- 然后在“当前文件内”，`materials.py` 再做“内容层面”的转换：搭 Preview 网络、接线、断开并删除 MDL 输出、删除 MDL Shader。
- 两者配合：
  1) 先把图纸上所有零件（references/payloads/sublayers/variants/clips）都换成 `_noMDL` 版本；
  2) 再把当前文件里自己的材质改成 Preview；
  这样每个文件都能“独立打开即是 Preview”，而顶层文件仍保持原有的拼装关系。

---

## 6. 小结 + 实用建议

- 看到 `ListOp` 不要慌：把它当作“合成出来的列表的做法”，遍历时展开就好；写回时优先 API，失败回 metadata。
- 分清条目类型：
  - sublayer 是“图层堆叠”；
  - reference/payload 是“拼装子文件”（payload 更偏向按需加载）；
  - variant_* 是“只在某个变体下生效的拼装”；
  - clip_* 是“按时间切片的拼装”。
- 路径处理：读时绝对化（root 目录为锚），写时相对化（各 layer 的目录为锚）。

这份指南适合作为你阅读 `convert_asset/no_mdl/references.py` 的快速预备知识。更多关于 Root Layer/Prim/Reference 的基础，请参阅本仓库的 `docs/usd_knowledge/roots_refs_prims.md`。
