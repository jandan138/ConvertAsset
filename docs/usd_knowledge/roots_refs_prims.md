# USD 组合关系速成：Root Layer、defaultPrim、sublayer、reference 与 prim

> 面向实战的直觉解释与例子，帮助快速建立“组合图”心智模型。

## 一、全局图景（类比）
- Stage = 最终搭好的积木模型（运行时合成视图）。
- Layer = 积木说明书（USD 文件，多个叠加）。
- Root Layer = 主说明书第一页（组合入口、相对路径锚点）。
- defaultPrim = 默认入口页（打开或被引用时的默认起点）。
- reference = 在某个位置吊装来自别的说明书的一棵子树（Prim 级拼装）。
- sublayer = 把另一份说明书的内容合并到当前说明书（文件级叠加）。
- prim = 具体零件（节点，有父子层级）。

## 二、Stage / Layer / Root Layer 是什么
- Stage：`Usd.Stage`，打开后得到的场景实例，是所有层合成结果。
- Layer：`Sdf.Layer`，USD 文件本体，含 prim 定义与元数据。
- Root Layer：`stage.GetRootLayer()`，当前这次组合的根文件：
  - 决定文件身份（`identifier/realPath`）
  - 决定相对路径的解析目录（贴图、子层、引用等）
  - 承载 `subLayerPaths`，是 LayerStack 的起点

## 三、defaultPrim 有啥用
- 定义“默认入口 Prim 是谁”。
- 影响：
  1) 打开文件时默认显示哪个 Prim（工具友好）。
  2) 作为引用目标的兜底：`@File.usd@` 未写 prim 路径时，会引用该文件的 `defaultPrim`。
- 没设 `defaultPrim` 的文件：打开可能“看不到东西”；被别人只写文件名引用时也可能失败。

## 四、sublayer vs reference（两类组合）
- sublayer（子层）：文件级叠加，把其它 Layer 并入当前 Layer，形成强弱覆盖关系。
- reference（引用）：Prim 级拼装，把另一个文件的某个 prim 子树挂到当前 prim 之下。
- 常搭配使用：
  - 用 sublayer 做“全局/文件级”合并与覆盖；
  - 用 reference 做“局部/树级”拼装与复用。

## 五、reference 的工作流程
假设：
- 当前文件的 prim `/World/CarRef` 上添加 `references = @Car.usd@`
- `Car.usd` 的 `defaultPrim = /Car`
- 结果：`Car.usd` 里 `/Car` 这棵树出现在 `/World/CarRef` 下。

树形对照：
- 当前文件：
  - `/World`（通常作为 `defaultPrim`）
    - `/World/CarRef`（此处挂 reference → `@Car.usd@`）
- Car.usd：
  - `defaultPrim = /Car`
  - `/Car`
    - `/Car/Body`
    - `/Car/Wheel`
- 合成后：
  - `/World/CarRef/Body`
  - `/World/CarRef/Wheel`

提示：这不是“复制粘贴”，而是“组合视图”。数据仍在 Car.usd，你可在当前层做局部覆盖（不改原文件）。

## 六、prim 层级与路径解析锚点
- prim 是树形：如 `/World` → `/World/Env`、`/World/CarRef`。
- 引用/载荷（payloads）挂在具体 prim 上。
- 相对路径解析锚点＝“声明该路径的那个 Layer 的目录”（常以 Root Layer 目录最稳）。

## 七、典型小场景串联
- 打开 `Scene.usd` → `Stage`，其 `Root Layer = Scene.usd`。
- `Scene.usd` 设 `defaultPrim = /World`，打开即可看到主场景。
- 在 `/World/CarRef` 写 `@Car.usd@`（不写 prim 路径）→ 使用 Car.usd 的 `defaultPrim` `/Car`。
- 还可通过 `subLayerPaths` 叠加全局覆盖文件 `CommonOverrides.usd`。

## 八、易混点速记
- `defaultPrim` ≠ `Root Layer`：前者是“默认入口 Prim”，后者是“这次组合的根文件”。
- 只写 `@File.usd@` 时，一定确保被引文件设置了 `defaultPrim`；否则改为 `@File.usd@ </PrimPath>`。
- 相对路径的锚点以“声明路径的 Layer 目录”为准，不是当前工作目录。
- `.usd/.usda/.usdc` 为同类不同编码，`.usdz` 为打包容器（入口可作为 Root Layer）。

## 九、我们项目里的落地做法
- 不 flatten：保留 `sublayers/references/payloads/variants/clips` 等组合关系，仅把目标指向对应的 `_noMDL` 文件。
- 每个源文件都“骨架导出”成自己的 `_noMDL`（复制其 Root Layer），并在该文件内改写组合弧目标。
- 确保/设置 `defaultPrim`，让单独打开 `_noMDL` 文件也能直达主场景。

## 十、记忆法（比喻）
- Root Layer：总施工图（这次工程的主图纸）。
- defaultPrim：进门第一眼看到的主展厅（默认带你看的房间）。
- sublayer：把其它楼层图纸并入（文件级）。
- reference：把隔壁工厂整套模块吊装进来（节点级）。
- prim：每个房间/家具（节点）。
