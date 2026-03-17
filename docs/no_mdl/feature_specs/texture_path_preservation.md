# Feature Spec: 纹理路径类型保持（Preserve Texture Path Type）

**文档状态**: Draft
**日期**: 2026-03-02
**版本**: 1.0

---

## 1. 问题陈述与现状

### 1.1 问题

`convert_asset/no_mdl/materials.py` 中的 `copy_textures()` / `_set_tex()` 函数，通过 `_resolve_abs_path(anchor_dir, path)` 将所有纹理路径强制转为绝对路径，再写入输出的 `*_noMDL.usd`。

**影响**：
- 输出 USD 不可移植：依赖绝对路径，换机器或换目录即失效。
- 与 `references.py` 的处理逻辑不一致：后者将 sublayer / reference / payload 路径转为相对路径以保持可移植性。

### 1.2 当前行为（现状）

```
_set_tex(tag, path, anchor_dir=anchor_dir)
  └─ ap = _resolve_abs_path(anchor_dir, path)   # 相对 → 绝对，绝对 → 不变
       └─ fin.Set(ap)                             # 写入绝对路径字符串
```

无论源 USD 中纹理路径是相对还是绝对，输出 USD 中纹理路径均为绝对路径。

### 1.3 期望行为（新行为）

| 源路径类型 | 默认输出路径类型 | `--resolve-textures-to-absolute` 开启时 |
|---|---|---|
| 相对路径 | 相对路径（相对于输出文件目录重算） | 绝对路径（旧行为） |
| 绝对路径 | 绝对路径 | 绝对路径 |

---

## 2. 详细修改方案

### 2.1 修改文件总览

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `convert_asset/no_mdl/path_utils.py` | 新增函数 | 添加 `_rebase_tex_path()` 工具函数 |
| `convert_asset/no_mdl/materials.py` | 核心修改 | `_set_tex()` 新增 `dst_layer_dir` 参数，判断并重算相对路径 |
| `convert_asset/no_mdl/materials.py` | 签名修改 | `copy_textures()` 新增 `dst_layer_dir` / `resolve_to_absolute` 参数 |
| `convert_asset/no_mdl/convert.py` | 传参修改 | `_convert_active_materials()` 从 stage 提取 dst_layer_dir 并传下去 |
| `convert_asset/no_mdl/config.py` | 新增配置项 | `RESOLVE_TEXTURES_TO_ABSOLUTE = False`（可覆盖默认行为） |
| `convert_asset/cli.py` | 新增 CLI flag | `--resolve-textures-to-absolute` 加到 `no-mdl` 子命令 |

### 2.2 `path_utils.py` 新增函数

**新增函数 `_rebase_tex_path()`**

```python
def _rebase_tex_path(
    src_path: str | None,
    src_anchor_dir: str | None,
    dst_layer_dir: str | None,
    resolve_to_absolute: bool = False,
) -> str | None:
    """根据"保持路径类型"策略，重算纹理路径。

    规则：
    - 若 src_path 为 None 或空字符串，返回 None。
    - 若 resolve_to_absolute=True（旧行为/CLI 强制），则总是返回绝对路径。
    - 否则：
        - 若原始路径是绝对路径 → 保持绝对。
        - 若原始路径是相对路径 → 先解析为绝对（用 src_anchor_dir），
          再计算相对于 dst_layer_dir 的相对路径写回。

    参数：
    - src_path: 原始路径字符串（可为相对或绝对）。
    - src_anchor_dir: 原始路径的锚点目录（MDL 属性所在 layer 的目录）。
    - dst_layer_dir: 输出 *_noMDL.usd 文件所在目录。
    - resolve_to_absolute: True → 总是绝对化（向后兼容/强制模式）。

    返回：
    - 处理后的路径字符串（POSIX 风格）；None 表示输入无效。
    """
    if not src_path:
        return None
    is_abs = os.path.isabs(src_path)
    if resolve_to_absolute:
        # 旧行为：绝对化
        return _resolve_abs_path(src_anchor_dir, src_path)
    if is_abs:
        # 源路径已是绝对 → 保持绝对
        return _to_posix(os.path.normpath(src_path))
    # 源路径是相对 → 先解析为绝对，再转为相对于 dst
    abs_path = _resolve_abs_path(src_anchor_dir, src_path)
    if not abs_path:
        return _to_posix(src_path)  # 无法解析则原样返回
    if not dst_layer_dir:
        return abs_path  # 无目标目录信息则退回绝对
    return _to_posix(os.path.relpath(abs_path, start=dst_layer_dir))
```

**注意**：不使用 `Sdf.ComputeAssetPathRelativeToLayer`，因为：
1. 该 API 依赖 Layer 对象而非目录字符串，在 `_set_tex()` 内部无法直接访问 dst Layer（只有 `stage`）。
2. 用 `os.path.relpath()` 足以正确处理相对路径重算，且无额外 USD 依赖。
3. 如需要，可作为备选：`Sdf.ComputeAssetPathRelativeToLayer(layer, abs_path)` 等价于 `os.path.relpath(abs_path, dst_layer_dir)`。

### 2.3 `materials.py` 修改：`_set_tex()` 内部签名

当前 `_set_tex()` 位于 `copy_textures()` 的闭包内（闭包函数），需要能访问两个新的外部上下文变量：
- `dst_layer_dir`：输出文件目录（从 `copy_textures()` 参数传入）。
- `resolve_to_absolute`：行为开关。

**修改方案**：通过 `copy_textures()` 的参数将 `dst_layer_dir` 和 `resolve_to_absolute` 传入，`_set_tex()` 闭包通过 `nonlocal` 或直接引用外层变量捕获它们。

#### `_set_tex()` 修改后逻辑（伪代码）

```
def _set_tex(tag, path, colorspace="raw", invert_r_to_rough=False, anchor_dir=None):
    if not path:
        return False

    # 【核心变化】根据路径类型保持策略重算最终写入路径
    ap = _rebase_tex_path(
        src_path=path,
        src_anchor_dir=anchor_dir,
        dst_layer_dir=dst_layer_dir,    # 来自 copy_textures() 参数
        resolve_to_absolute=resolve_to_absolute,  # 来自 copy_textures() 参数
    )
    if not ap:
        return False

    # 以下逻辑不变：找 Tex_{tag} prim，设置 inputs:file、sourceColorSpace、scale/bias
    tex_prim = stage.GetPrimAtPath(f"{mpath}/{GROUP}/Tex_{tag}")
    ...
    fin.Set(ap)   # 写入重算后的路径
    if tag == "BaseColor":
        bc_tex = ap  # 注意：bc_tex 现在可能是相对路径，需调整"白图"判断
    ...
```

**`bc_tex` 的白图判断兼容性**：`_is_white_tex(path)` 仅检查 `os.path.basename(path)`（文件名），对相对路径和绝对路径均有效，无需额外修改。

#### `copy_textures()` 签名修改

```python
def copy_textures(
    stage: Usd.Stage,
    mdl_shader,
    mat: UsdShade.Material,
    dst_layer_dir: str | None = None,    # 新增：输出文件目录
    resolve_to_absolute: bool = False,   # 新增：强制绝对化开关
):
```

当 `dst_layer_dir=None` 时：
- 相对路径走 `_resolve_abs_path(anchor_dir, path)`，即退化为旧行为（保守兜底）。
- 绝对路径保持绝对。

### 2.4 `convert.py` 修改：传递 dst_layer_dir

`copy_textures()` 被 `_convert_active_materials()` 调用（第 63 行）：

```python
filled, has_c, c_rgb, bc_tex = copy_textures(stage, mdl, mat)
```

需改为：

```python
dst_layer_dir = os.path.dirname(
    stage.GetRootLayer().realPath or stage.GetRootLayer().identifier
)
filled, has_c, c_rgb, bc_tex = copy_textures(
    stage, mdl, mat,
    dst_layer_dir=dst_layer_dir,
    resolve_to_absolute=resolve_to_absolute,  # 来自函数参数或模块级配置
)
```

`_convert_active_materials()` 需新增 `resolve_to_absolute=False` 参数，并向上传至 `convert_and_strip_mdl_in_this_file_only()`。

在 `convert.py` 中，外部材质 override 流程（第 107 行）同样调用了 `copy_textures()`，也需同步传参。

### 2.5 `config.py` 新增配置项

在 `config.py` 末尾添加：

```python
# ================= Texture Path Mode =================
# 默认行为（False）：保持源路径类型（相对保持相对、绝对保持绝对）。
# 设为 True 时：总是将纹理路径解析为绝对路径（旧行为，向后兼容）。
# 可被 CLI --resolve-textures-to-absolute 覆盖。
RESOLVE_TEXTURES_TO_ABSOLUTE = False
```

### 2.6 `cli.py` 修改：新增 CLI flag

在 `no-mdl` 子命令的参数定义区（当前第 22-24 行附近）添加：

```python
p_nomdl.add_argument(
    "--resolve-textures-to-absolute",
    action="store_true",
    default=False,
    help=(
        "Force all texture paths in *_noMDL.usd to be written as absolute paths. "
        "By default (without this flag), relative paths in source MDL are preserved "
        "as relative paths (re-computed relative to the output file directory)."
    ),
)
```

在 `cli.py` 的 `no-mdl` 处理逻辑中（当前第 90-111 行），在 `Processor()` 初始化前，写入配置或传递给 Processor：

```python
if getattr(args_ns, "resolve_textures_to_absolute", False):
    try:
        from .no_mdl import config as _cfg
        _cfg.RESOLVE_TEXTURES_TO_ABSOLUTE = True
    except Exception:
        pass
```

---

## 3. Logic Flow（新行为流程图）

### 3.1 `_set_tex()` 新逻辑流

```
_set_tex(tag, path, colorspace, invert_r_to_rough, anchor_dir)
    │
    ├─ path 为空? → return False
    │
    ├─ 调用 _rebase_tex_path(
    │       src_path=path,
    │       src_anchor_dir=anchor_dir,
    │       dst_layer_dir=dst_layer_dir,   ← 从 copy_textures() 捕获
    │       resolve_to_absolute=resolve_to_absolute  ← 从 copy_textures() 捕获
    │  )
    │     │
    │     ├─ resolve_to_absolute=True?
    │     │    └─ _resolve_abs_path(anchor_dir, path) → 绝对路径  [旧行为]
    │     │
    │     ├─ os.path.isabs(path)?
    │     │    └─ normpath(path) → 绝对路径  [绝对保持绝对]
    │     │
    │     └─ 相对路径处理:
    │          abs = _resolve_abs_path(anchor_dir, path)  ← 先解析为绝对
    │          │
    │          ├─ abs 无效? → return src_path (原样)
    │          ├─ dst_layer_dir 无效? → return abs  [退回绝对]
    │          └─ os.path.relpath(abs, dst_layer_dir) → 相对路径  [新行为]
    │
    ├─ ap 无效? → return False
    │
    ├─ 找 Tex_{tag} prim
    ├─ fin.Set(ap)   ← 写入最终路径
    ├─ 设置 sourceColorSpace
    ├─ 设置 scale/bias (Roughness invert)
    ├─ 更新 bc_tex (BaseColor 专用)
    └─ filled[tag] = True; return True
```

### 3.2 `copy_textures()` 参数传递流

```
copy_textures(stage, mdl_shader, mat, dst_layer_dir=None, resolve_to_absolute=False)
    │
    ├─ 若 dst_layer_dir 未提供:
    │    可从 stage.GetRootLayer().realPath 推导（可选，作为兜底）
    │
    ├─ 构造闭包 _set_tex，捕获 dst_layer_dir 和 resolve_to_absolute
    │
    ├─ 步骤 1: 读取 MDL pin → 调用 _set_tex(tag, path, ...)
    ├─ 步骤 2: 解析 .mdl 文本 → 调用 _set_tex(tag, path, anchor_dir=anchor_dir, ...)
    └─ 步骤 3: 读取 BaseColor 常量 (不涉及路径，无变化)
```

### 3.3 调用链全貌（新行为）

```
cli.py: parse --resolve-textures-to-absolute
    └─ config.RESOLVE_TEXTURES_TO_ABSOLUTE = True (若开启)

processor.process(src_usd_abs)
    └─ convert_and_strip_mdl_in_this_file_only(dst_stage)
         └─ _convert_active_materials(stage, stats, processed, resolve_to_absolute)
              ├─ dst_layer_dir = os.path.dirname(stage.GetRootLayer().realPath)
              └─ copy_textures(stage, mdl, mat,
                               dst_layer_dir=dst_layer_dir,
                               resolve_to_absolute=resolve_to_absolute)
                   └─ _set_tex(tag, path, anchor_dir=anchor_dir)
                        └─ _rebase_tex_path(path, anchor_dir, dst_layer_dir, resolve_to_absolute)
                             └─ fin.Set(final_path)  ← 写入正确类型的路径
```

---

## 4. CLI 参数设计

### 4.1 参数规格

| 属性 | 值 |
|---|---|
| 参数名 | `--resolve-textures-to-absolute` |
| 子命令 | `no-mdl` |
| 类型 | `store_true`（布尔 flag） |
| 默认值 | `False`（即默认保持路径类型，新行为） |
| 向后兼容 | 旧用户未指定此 flag，默认行为改变（见兼容策略） |

### 4.2 使用示例

```bash
# 新默认行为：保持源路径类型（相对保持相对）
./scripts/isaac_python.sh ./main.py no-mdl /path/to/scene.usd

# 旧行为：强制绝对化（明确要求时）
./scripts/isaac_python.sh ./main.py no-mdl /path/to/scene.usd --resolve-textures-to-absolute
```

### 4.3 `usd-to-glb` 子命令的处理

`usd-to-glb` 内部调用 `no-mdl` 流程（通过 `Processor()`），但当前不传递配置参数。建议：
- 阶段一：`usd-to-glb` 不暴露此 flag（`no-mdl` 已有），GLB 导出时绝对路径更可靠（读磁盘文件），故不影响 GLB 产出质量。
- 阶段二（可选）：给 `usd-to-glb` 也加上此 flag，确保中间 `*_noMDL.usd` 的可移植性。

---

## 5. Config 层设计

### 5.1 `config.py` 新增项

```python
# ================= Texture Path Mode =================
# False（默认）：保持源路径类型。相对路径在输出中保持相对（相对于输出文件目录重算）。
# True：总是将纹理路径解析为绝对路径（旧行为）。
# 可被运行时覆盖（CLI --resolve-textures-to-absolute 或直接修改此值）。
RESOLVE_TEXTURES_TO_ABSOLUTE = False
```

### 5.2 运行时覆盖机制

与现有的 `RUNTIME_ONLY_NEW_USD` 模式一致：在 `cli.py` 中直接修改模块级变量：

```python
# cli.py (no-mdl 处理块)
if getattr(args_ns, "resolve_textures_to_absolute", False):
    try:
        from .no_mdl import config as _cfg
        _cfg.RESOLVE_TEXTURES_TO_ABSOLUTE = True
    except Exception:
        pass
```

随后在 `convert.py` 中导入此配置：

```python
from .config import RESOLVE_TEXTURES_TO_ABSOLUTE
```

并传递给 `convert_and_strip_mdl_in_this_file_only()`，再层层传至 `copy_textures()`。

---

## 6. 边缘情况处理

### 6.1 `anchor_dir` 为 None

当 `_anchor_dir_for_attr()` 返回 `None`（层栈不可用或全为匿名层），`_rebase_tex_path()` 中：
- 若路径是相对路径且 `anchor_dir=None`：无法解析为绝对路径，`_resolve_abs_path(None, path)` 返回原始相对路径字符串。
- 策略：退回原始路径字符串，写入输出。这等同于"无锚点时原样保留路径"，与旧行为一致。

### 6.2 `dst_layer_dir` 为 None 或无效

当 `dst_layer_dir` 未传入或 `stage.GetRootLayer().realPath` 为空（匿名 stage）：
- `_rebase_tex_path()` 在最后的 `if not dst_layer_dir` 分支中返回绝对路径（退回绝对）。
- 写入绝对路径比写入可能失效的相对路径更安全（保守策略）。

### 6.3 路径不存在于磁盘

纹理路径的重算是纯字符串/路径运算，不检查文件是否实际存在。
- 若源路径已是相对路径但文件不在对应位置，`_rebase_tex_path()` 仍会进行数学重算，写入相对路径。
- 下游使用（如 GLB 导出）在实际读取文件时才会发现路径失效。
- 与当前行为一致（旧代码也不校验纹理文件是否存在）。

### 6.4 源路径来自 `resolvedPath`（已是绝对）

在 `copy_textures()` 步骤 1（直接读取 MDL pin），代码读取的是：
```python
path = getattr(v, "resolvedPath", getattr(v, "path", None)) if v is not None else None
```

`resolvedPath` 通常已是绝对路径（USD 解析后的结果）。此时：
- `_rebase_tex_path()` 检测到 `os.path.isabs(path)=True`，保持绝对，与新规则吻合。
- 若需要"用户希望相对保存"，此处的行为可能与期望不符（因为 pin 上 `resolvedPath` 覆盖了相对信息）。

**处理策略**：优先读取 `v.path`（原始路径，可能是相对）而非 `v.resolvedPath`（已解析绝对路径）：

```python
# 修改前
path = getattr(v, "resolvedPath", getattr(v, "path", None)) if v is not None else None

# 修改后：优先读取原始路径以保留相对信息；若原始路径为空则回退到 resolvedPath
raw_path = getattr(v, "path", None) if v is not None else None
resolved_path = getattr(v, "resolvedPath", None) if v is not None else None
path = (raw_path or resolved_path) if v is not None else None
```

当 `raw_path` 非空时，传入 `_set_tex()` 的是原始相对/绝对路径，后续由 `_rebase_tex_path()` 根据类型处理。当 `raw_path` 为空（如 pin 中路径仅以 resolvedPath 形式存在）时，回退绝对路径，保守兜底。

### 6.5 Windows 路径

`_to_posix()` 负责统一转换反斜杠，`os.path.relpath()` 在 Linux 上运行不存在 Windows 路径问题。如需跨平台，`pathlib.PurePosixPath` 可替代，但当前项目全程运行在 Linux（Isaac Sim）下，无需额外处理。

### 6.6 `bc_tex` 变量在相对路径下的白图判断

`_is_white_tex(path)` 使用 `os.path.basename(path)` 提取文件名，对相对路径（如 `../../textures/white.png`）同样有效，无需修改。

---

## 7. 向后兼容策略

### 7.1 行为变化说明

| 场景 | 旧行为 | 新行为 |
|---|---|---|
| 源 MDL 纹理路径是相对路径 | 转为绝对路径写入输出 | 转为相对路径（相对输出文件目录）写入输出 |
| 源 MDL 纹理路径是绝对路径 | 保持绝对路径 | 保持绝对路径（不变） |
| 使用 `--resolve-textures-to-absolute` | N/A（新 flag） | 强制旧行为（全部绝对） |
| `config.py` 中 `RESOLVE_TEXTURES_TO_ABSOLUTE=True` | N/A | 强制旧行为（无需 CLI） |

### 7.2 影响评估

**需要注意的场景**（新行为可能导致行为变化）：
1. 后续 GLB 导出（`export-glb` / `usd-to-glb`）：GLB converter 读取 `*_noMDL.usd` 时，其纹理路径将变为相对路径。实际实现中，`glb/usd_material.py` 读到 `inputs:file` 后，如果路径是相对的，会以 `stage.GetRootLayer().realPath` 所在目录为基准拼接绝对路径，并不会调用 `SdfComputeAssetPathRelativeToLayer` 或 `resolvedPath`；这在某些材质存在多层 authoring 的场景里可能无法按照最初的 authoring layer 解析出正确的相对路径。
2. 已有的 `*_noMDL.usd` 文件：不受影响（本功能只影响新生成的文件）。
3. 依赖绝对路径行为的脚本/工具：可通过 `--resolve-textures-to-absolute` 恢复旧行为。

### 7.3 `config.py` 作为安全阀

如果团队级别需要统一使用旧行为（生产稳定性优先），只需在 `config.py` 中将默认值改为：

```python
RESOLVE_TEXTURES_TO_ABSOLUTE = True  # 强制旧行为
```

这不需要修改任何调用代码。

---

## 8. 实现阶段（建议实施顺序）

### Phase 1 - 核心路径逻辑（必须）

1. `path_utils.py`：新增 `_rebase_tex_path()` 函数。
2. `config.py`：新增 `RESOLVE_TEXTURES_TO_ABSOLUTE = False`。
3. `materials.py`：
   - 修改 `copy_textures()` 签名（新增 `dst_layer_dir`、`resolve_to_absolute` 参数）。
   - 修改闭包 `_set_tex()` 内调用 `_rebase_tex_path()` 替换原 `_resolve_abs_path()`。
   - 修改步骤 1 读取 pin 路径时优先取 `v.path` 而非 `v.resolvedPath`。

### Phase 2 - 上游传参（必须）

4. `convert.py`：
   - `_convert_active_materials()` 新增 `resolve_to_absolute` 参数。
   - 提取 `dst_layer_dir` 并传入 `copy_textures()`。
   - `convert_and_strip_mdl_in_this_file_only()` 新增参数，从 `config.RESOLVE_TEXTURES_TO_ABSOLUTE` 读取默认值。
   - 外部材质 override 路径同步传参（第 107 行 `copy_textures()` 调用）。

### Phase 3 - CLI 暴露（必须）

5. `cli.py`：
   - `no-mdl` 子命令新增 `--resolve-textures-to-absolute` 参数。
   - 在处理逻辑中，检测 flag 并设置 `config.RESOLVE_TEXTURES_TO_ABSOLUTE = True`。

### Phase 4 - 测试（强烈建议）

6. 编写 `tests/reproduce_texture_path.py` 验证脚本（见 Agent 协作指令部分）。

---

## 9. 关于 USD API 路径计算的备注

需求中提到了 `Sdf.ComputeAssetPathRelativeToLayer`。调查结果：

- **该 API 存在**（USD 文档：`Sdf.ComputeAssetPathRelativeToLayer(layer, assetPath)`）。
- **适用场景**：输入是一个 `Sdf.Layer` 对象 + 绝对路径字符串，输出是相对于该 layer 的相对路径。
- **等价性**：对于文件 layer，其结果等同于 `os.path.relpath(abs_path, os.path.dirname(layer.realPath))`。
- **本实现选择**：使用 `os.path.relpath()` + 已有的 `_to_posix()`，无需额外 layer 对象传递，逻辑更清晰，且与 `references.py` 中 `_relpath()` 的实现风格一致。
- **若需要 USD API 精确性**：可在 `_set_tex()` 内访问 `stage.GetRootLayer()`，调用 `Sdf.ComputeAssetPathRelativeToLayer(dst_layer, abs_tex_path)` 来替代 `os.path.relpath()`，两者在正常文件场景下结果相同。

---

## 附录 A：受影响函数的完整签名对比

### `copy_textures()`

```python
# 旧签名
def copy_textures(stage: Usd.Stage, mdl_shader, mat: UsdShade.Material):

# 新签名
def copy_textures(
    stage: Usd.Stage,
    mdl_shader,
    mat: UsdShade.Material,
    dst_layer_dir: str | None = None,
    resolve_to_absolute: bool = False,
):
```

### `_convert_active_materials()`

```python
# 旧签名
def _convert_active_materials(stage: Usd.Stage, stats: dict, processed_paths: set):

# 新签名
def _convert_active_materials(
    stage: Usd.Stage,
    stats: dict,
    processed_paths: set,
    resolve_to_absolute: bool = False,
):
```

### `convert_and_strip_mdl_in_this_file_only()`

```python
# 旧签名
def convert_and_strip_mdl_in_this_file_only(stage: Usd.Stage):

# 新签名
def convert_and_strip_mdl_in_this_file_only(
    stage: Usd.Stage,
    resolve_to_absolute: bool | None = None,  # None 表示从 config 读取
):
```

---

## 附录 B：关联文档

- `docs/no_mdl/texture_path_handling.md`：现有行为的完整分析（本功能的问题来源文档）
- `docs/no_mdl/materials_details.md`：`materials.py` 的详细说明
- `docs/architecture/flow.md`：整体处理流程
- `convert_asset/no_mdl/path_utils.py`：路径工具函数集合
- `convert_asset/no_mdl/references.py`：相对路径处理的参考实现（`_relpath`）
