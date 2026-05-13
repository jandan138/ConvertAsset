# 为什么需要 `scripts/isaac_python.sh`：给初学者的完整说明书

面向读者：刚接触 Omniverse Isaac Sim 与 Python/USD（pxr）的同学。

本页详细解释：
- 这个脚本存在的背景和目的；
- 它解决了哪些常见“环境坑”；
- 它如何自动找到 Isaac Sim 并准备好 USD 运行环境；
- 如何在各种场景下正确使用；
- 常见问题与排错清单；
- 脚本关键逻辑的逐段解读。

> 结论先行：要运行本仓库里的 USD 工具（比如无 MDL 转换、材质检查、缩略图渲染），请优先用仓库内的包装脚本：
>
> ```bash
> ./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py <子命令...>
> ```
>
> 它会自动定位并调用 Isaac Sim 自带的 Python 与 USD 库，避免“本机 Python 找不到 pxr”的各种报错。

---

## 一、背景：为什么直接用系统 Python 会失败？

- Omniverse/Isaac Sim 使用的是 NVIDIA 打包的 USD（pxr）生态，包含大量 C++ 动态库（例如 `libtf.so`）与扩展插件（`kit/plugins`）。
- 普通的系统 Python/虚拟环境（venv、conda）默认没有这些库与插件，因此：
  - `import pxr` 会失败（ModuleNotFoundError: No module named 'pxr'）；
  - 或者导入成功但运行时报找不到动态库（比如找不到 `libtf.so`）。
- Isaac Sim 官方提供的 `python.sh` 会把一整套 USD/Kit 运行时装好再启动 Python，所以“在 Isaac 的 python 里跑”是最省心的方式。

本仓库的工具依赖 USD/pxr，因此必须在“带 USD 的 Python 环境”里运行。`scripts/isaac_python.sh` 就是为了：
- 自动找 Isaac Sim 的安装位置；
- 必要时补齐 PYTHONPATH / LD_LIBRARY_PATH；
- 最终调用 Isaac 自带的 `python.sh` 执行你的命令。

---

## 二、它具体解决了什么问题？

1) 找不到 Isaac Sim 安装路径
- 不同机器/安装方式路径不一样（Docker 是 `/isaac-sim`，本地安装在 `~/.local/share/ov/pkg/isaac_sim-*`，也可能在 `/opt/...`）。
- 脚本实现“多路径自动探测 + 环境变量覆盖”的策略，不用你每次手动填绝对路径。

2) `pxr` 导入失败或找不到动态库
- 脚本会在执行前，按需把包含 `pxr` 的目录加入 `PYTHONPATH`，把包含 `libtf.so`（`omni.usd.libs/bin/`）与 `kit/lib`、`kit/plugins` 加入 `LD_LIBRARY_PATH`。

3) 与已有 conda/venv 冲突
- Isaac 官方脚本常提示“Running in conda env, please deactivate…”。
- 我们保留提醒，但不强行退出；多数情况下仍可运行。如果你遇到奇怪崩溃，建议暂时停用外部 conda/venv 后再试。

---

## 三、脚本如何找到 Isaac Sim？（自动定位算法）

优先级从高到低：
1. 环境变量 `ISAAC_SIM_ROOT` 指向包含 `python.sh` 的目录（最可靠）；
2. Docker/容器内的固定路径：`/isaac-sim/python.sh`；
3. 用户本地安装：`~/.local/share/ov/pkg/isaac_sim-*`（选择最高版本号）；
4. 常见系统目录：`/opt/nvidia/isaac-sim`、`/opt/NVIDIA/isaac-sim`、`/opt/omniverse/isaac-sim`。

若以上都找不到，会报错并给出提示，建议你设置：

```bash
export ISAAC_SIM_ROOT="/abs/path/to/isaac_sim-<version>"
```

---

## 四、环境准备的两件事（自动完成）

为了对齐官方 `/isaac-sim/isaac_python.sh` 的行为，本脚本在调用 `python.sh` 前会：

1) 处理 `PYTHONPATH`
- 在 Isaac 安装目录的 `extscache` 下查找所有包含 `pxr` 的父目录，并依次加入 `PYTHONPATH`。
- 作用：让 Python 能 import 到 USD 的 Python 模块（`pxr`）。

2) 处理 `LD_LIBRARY_PATH`
- 在 `extscache` 下查找 `omni.usd.libs` 包里的 `bin/libtf.so` 所在目录，加入 `LD_LIBRARY_PATH`。
- 同时加入 `${ISAAC_ROOT}/kit/lib` 与 `${ISAAC_ROOT}/kit/plugins`。
- 作用：让运行时能成功链接 USD/Kit 的动态库与插件。

> 注：这些路径准备是“按需”的。如果 `python.sh` 自身已经处理好了，这些环境变量也不会造成负面影响；它们更多是“兜底”。

---

## 五、如何使用

最通用的调用方式：

```bash
# 在仓库根目录执行
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py <子命令> [参数...]
```

常用示例：

- 无 MDL 转换（最小输出，只保留新 USD）
```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py no-mdl \
  "/path/to/instance_or_top.usd" --only-new-usd
```

- 材质检查（只读）
```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py inspect \
  "/path/to/scene.usd" mdl /Looks/Mat01
```

- 导出 MDL 材质为独立 USD
```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py export-mdl-materials \
  "/path/to/scene.usd" --out-dir-name mdl_materials --placement authoring
```

- 多视角缩略图（需要 Isaac 渲染）
```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py thumbnails \
  "/path/to/scene.usd" --views 6 --width 600 --height 450
```

> 如果你的 Isaac 安装在非标准路径，先设置环境变量：
>
> ```bash
> export ISAAC_SIM_ROOT="/abs/path/to/isaac_sim-<version>"
> ./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py no-mdl "/path/to.x.usd"
> ```

---

## 六、与官方 `/isaac-sim/isaac_python.sh` 的关系

- 官方脚本是“在容器或标准安装目录里”直接可用的入口；
- 本仓库的包装器是“更通用的入口”，支持自动定位不同安装位置，并在必要时补齐环境变量；
- 两者可互换使用，但为了统一团队操作与文档，本仓库推荐始终使用 `./scripts/isaac_python.sh`。

---

## 七、常见问题与排错

1) 提示“running in conda env, please deactivate …”
- 说明当前 shell 激活了外部 conda 环境。多数情况下仍能运行；
- 若出现奇怪崩溃/段错误，尝试 `conda deactivate` 或在一个干净的 shell 中运行脚本。

2) ModuleNotFoundError: No module named 'pxr'
- 通常代表没有通过包装脚本启动，或 Isaac 安装路径未被正确检测到；
- 先用本脚本；若仍失败，设置 `ISAAC_SIM_ROOT` 指向包含 `python.sh` 的目录。

3) 找不到 libtf.so / Kit 插件
- 升级脚本后会自动处理 `LD_LIBRARY_PATH`；
- 若你的安装结构有差异，检查 `${ISAAC_SIM_ROOT}/extscache` 中是否存在 `omni.usd.libs`；
- 也可临时手动：
  ```bash
  export LD_LIBRARY_PATH="/path/to/omni.usd.libs/bin:${LD_LIBRARY_PATH}"
  ```

4) 找不到 Isaac Sim
- 按前述优先级自动搜索；若失败，请显式设置：
  ```bash
  export ISAAC_SIM_ROOT="/abs/path/to/isaac_sim-<version>"
  ```

5) 权限问题（脚本无法执行）
- 确保脚本有可执行位：
  ```bash
  chmod +x ./scripts/isaac_python.sh
  ```

---

## 八、源码逐段解读（简版）

1) 解析参数、检查输入：确保你传入了要执行的脚本与参数。
2) `resolve_isaac_root()`：按“环境变量 → 容器固定路径 → 用户包路径（最高版本） → 常见系统路径”的顺序查找 `python.sh`。
3) 预处理环境变量：
   - `PYTHONPATH`：把 `extscache` 下所有含 `pxr` 的父目录加入，确保 `import pxr` 可用；
   - `LD_LIBRARY_PATH`：加入 `omni.usd.libs/bin`、`kit/lib`、`kit/plugins`，确保动态库和插件能被加载。
4) `exec "${ISAAC_ROOT}/python.sh" "$@"`：用 Isaac 自带 Python 启动你的命令（`exec` 会替换当前进程，环境已就绪）。

> 你无需修改脚本，只要调用它即可。

---

## 九、术语表（速查）

- USD（Universal Scene Description）：皮克斯开源场景描述技术，Python 包为 `pxr`。
- Isaac Sim：NVIDIA 的仿真/渲染平台，内置特定版本的 USD 与丰富插件。
- `python.sh`：Isaac 提供的入口脚本，确保启动时库与插件路径都已配置好。
- `extscache`：Isaac 的扩展缓存目录，含 `omni.usd.libs` 等包。
- `kit/lib`、`kit/plugins`：Kit 引擎的动态库与插件目录。

---

## 十、我该记住的最少两条

1) 运行任何需要 USD/pxr 的工具时，优先用：
```bash
./scripts/isaac_python.sh /opt/my_dev/ConvertAsset/main.py <子命令...>
```

2) 如果找不到 Isaac 安装：
```bash
export ISAAC_SIM_ROOT="/abs/path/to/isaac_sim-<version>"
```

以上即可应对 90% 的环境问题。
