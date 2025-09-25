# 从 Python 调用 C++ 后端：新手教程（以本项目为例）

这篇教程用最通俗的方式讲清楚：Python 是如何调用 C++ 网格减面后端的；你该如何快速运行；以及出现问题时怎么排查。

## 你将学到什么
- 快速三步，从 CLI 发起一次 C++ 后端的网格简化
- Python 与 C++ 之间“怎么对话”（数据怎么传、结果怎么回）
- 最小可运行的 Python 代码片段（核心调用）
- 常见坑与解决办法

## 前置准备
- 已构建原生二进制 `meshqem`：
  ```bash
  mkdir -p native/meshqem/build
  cd native/meshqem/build
  cmake -DCMAKE_BUILD_TYPE=Release ..
  cmake --build . -j
  ```
- Python 侧可用（推荐在 Isaac 环境下运行 CLI）。

> 可执行文件路径通常为：`/opt/my_dev/ConvertAsset/native/meshqem/build/meshqem`

上述四条命令详解：
- `mkdir -p native/meshqem/build`：创建构建目录（-p 确保多级目录存在即不报错）。
- `cd native/meshqem/build`：进入构建目录，避免把中间产物写到源码目录。
- `cmake -DCMAKE_BUILD_TYPE=Release ..`：生成构建系统
  - `..` 表示以上一级（`native/meshqem`）为源码根；
  - `-DCMAKE_BUILD_TYPE=Release` 启用优化（等价于 `-O3`），适合跑减面；如需调试可改为 `Debug`；
  - 可选：指定生成器（如已装 Ninja），使用 `-G Ninja` 提升构建速度。
- `cmake --build . -j`：实际编译
  - `.` 指当前构建目录；
  - `-j` 开启并行编译，CPU 核数越多越快；
  - 成功后会在本目录生成可执行文件 `meshqem`（有时需 `chmod +x meshqem` 才能运行）。

常见构建问题：
- “找不到 C++17 编译器”：请安装 gcc/g++ 9+ 或 clang 10+；
- “生成器不可用”：若未安装 Ninja，请去掉 `-G Ninja`；
- “权限不足”：在容器或共享目录中，确保对 `build` 目录有写权限。

## 快速上手：三步走
1) 运行简化（从 Python CLI 调 C++）：
   ```bash
   PYTHONPATH=/opt/my_dev/ConvertAsset:$PYTHONPATH \
   /isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py \
     mesh-simplify /opt/my_dev/ConvertAsset/asset/test_scene/scenes/MV7J6NIKTKJZ2AABAAAAADA8_usd/start_result_interaction.usd \
     --backend cpp \
     --cpp-exe /opt/my_dev/ConvertAsset/native/meshqem/build/meshqem \
     --ratio 0.8 --apply --out /tmp/scene_simplified.usd \
     --time-limit 30 --progress
   ```
2) 观察输出：
   - `stdout` 两行摘要（Python 会解析这两行，格式固定用于机器读取）：
     ```
     faces: <before> -> <after>
     verts: <before> -> <after>
     ```
     说明：
     - `<before>` 和 `<after>` 分别是本次网格简化前后的“面数/点数”；
     - 只有这两行会出现在 stdout，便于稳定解析；若缺失，通常表示执行失败或未走到简化阶段；
     - Python 侧会按空格分割，取第 2、4 个字段（示例代码见下文）。
   - `stderr` 周期性进度（每 N 次坍塌一条）
     - 用于人工观察，例如“已坍塌多少条边、当前剩余面数、耗时”等；
     - 进度行不保证稳定格式，不建议依赖脚本解析；
     - 若你看不到进度，可能是 `--progress-interval` 太大或网格很小。
   - 退出码：
     - 成功返回 0；非 0 表示 I/O 或参数错误、或内部异常；
     - 失败时 stderr 通常包含出错原因，stdout 可能为空或不完整。
3) 查看结果：输出路径 `--out /tmp/scene_simplified.usd`。

如果你只想“算个建议比率”（不真正跑 C++），可以用规划模式（不传 `--apply`）：
```bash
PYTHONPATH=/opt/my_dev/ConvertAsset:$PYTHONPATH \
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py \
  mesh-simplify /path/to/scene.usd \
  --backend cpp --target-faces 80000 \
  --cpp-exe /opt/my_dev/ConvertAsset/native/meshqem/build/meshqem
```
规划模式会在 Python 侧根据总面数推一个“建议 ratio”，提前返回，不会调用 C++ 可执行文件（更安全、更快）。

## 原理讲解（通俗易懂版）
可以把这条流水线理解成一次“打包-加工-回填”的过程：

1) Python（适配器 `convert_asset/mesh/backend_cpp.py`）从 USD 里取出一个三角网格（点坐标 + 三角索引）。
2) 为了让 C++ 看得懂，Python 把网格“打包”成一个临时 `OBJ` 文件（只含 `v` 和三角 `f`）。
3) Python 启动 C++ 可执行文件 `meshqem`（用 `subprocess.run`），传入参数：
   - `--in` 输入 OBJ
   - `--out` 输出 OBJ
   - `--ratio` 或 `--target-faces`（目标规模）
   - `--time-limit`（超时保护）、`--progress-interval`（进度频率）等
4) C++ 在内部执行 QEM 减面：
   - 读取 `in.obj` → 进行边坍塌（受目标和时间限制） → 写出 `out.obj`；
   - 向 `stdout` 打印两行摘要（前后面/点数），向 `stderr` 打印进度。
5) Python 读取 `stdout` 的两行摘要来知道“前后面数变化”；若本次需要 `apply`：
   - 再读回 `out.obj` 的新点和面，回填到 USD 网格上，写到新的 USD 文件。
6) 清理临时文件；进入下一个网格。

简而言之：
- “Python 负责和 USD 沟通、落盘中间产物、调用与收尾”；
- “C++ 负责高速计算和最小化可解析输出”。

## 最小 Python 核心调用（示意）
以下片段展示 Python 如何调用 C++ 可执行文件并解析摘要（与项目适配器逻辑一致，但省略了大量工程细节）：

```python
import subprocess, shlex

cpp_exe = "/opt/my_dev/ConvertAsset/native/meshqem/build/meshqem"
args = [
    cpp_exe,
    "--in", "/tmp/in.obj",
    "--out", "/tmp/out.obj",
    "--ratio", "0.8",
    "--time-limit", "30",
    "--progress-interval", "20000",
]
res = subprocess.run(
  args,
  capture_output=True,  # 捕获 stdout/stderr 到内存，便于后续解析与打印
  text=True,            # 将字节流解码为字符串（使用系统默认编码，通常是 UTF-8）
  check=False           # 不自动抛异常；我们用 returncode 自己判断并处理错误
  # timeout=60,         # 可选：对子进程加一个“外层超时”（秒），与 C++ 的 --time-limit 互补
  # cwd="/tmp",          # 可选：子进程的工作目录（默认继承父进程）
  # env=os.environ,     # 可选：自定义环境变量（例如 PATH、LD_LIBRARY_PATH）
)

# 解析 stdout 两行摘要
before_faces = after_faces = before_verts = after_verts = None
for line in res.stdout.splitlines():
    line = line.strip()
    if line.startswith("faces:"):
        # faces: M -> N
        parts = line.split()
        before_faces, after_faces = int(parts[1]), int(parts[3])
    elif line.startswith("verts:"):
        parts = line.split()
        before_verts, after_verts = int(parts[1]), int(parts[3])

if res.returncode != 0:
    raise RuntimeError(f"meshqem failed: code={res.returncode}, err={res.stderr}")

print("faces:", before_faces, "->", after_faces)
print("verts:", before_verts, "->", after_verts)

# 若需要应用结果：读取 /tmp/out.obj，写回到 USD（项目里已有现成实现）

# 额外说明：
# - args 以“列表”形式传给 subprocess.run 时，无需额外转义/拼接字符串，空格与特殊字符会被正确处理；
# - 若改用字符串命令，建议配合 shlex.split 做安全分词；
# - capture_output=True 适合少量输出；若输出非常大可改用 stdout/stderr=PIPE 或直接继承父进程；
# - check=True 会在返回码非 0 时抛出 CalledProcessError，适合你想走异常分支的场景；
# - timeout 触发时会抛 TimeoutExpired，可结合 --time-limit 做双重保护（外杀进程、内控制算法）。
```

要点：
- C++ 只保证 stdout 两行摘要稳定可解析；
- 进度等辅助信息都走 stderr；
- 出错时返回码非 0，stderr 含错误原因。

## 常见问题与排查
- 非三角网格怎么办？
  - 适配器会跳过非三角网格（v1 仅支持三角）。如需支持，请在上游做三角化。
- 为什么有时提前结束？
  - 触发了 `--time-limit`；返回的是“部分简化”的合法结果。可增大时间或调高 `--ratio`。
- 我只想估算全局缩减比例，为什么没跑 C++？
  - 这是“规划模式”（不传 `--apply`），在 Python 侧基于总面数估算建议 `ratio`，不会调用 C++，更快更安全。
- 之前遇到规划阶段崩溃（-11）？
  - 已通过“规划提前返回”规避，规划阶段不再调用 C++ 可执行文件。
- 临时文件与磁盘空间？
  - 适配器使用临时 OBJ 做中转；请保证 `/tmp` 或工作目录有足够空间。
- 权限问题？
  - 确认 `meshqem` 有可执行权限：`chmod +x /opt/my_dev/ConvertAsset/native/meshqem/build/meshqem`。

## 使用建议
- 先用较高 `--ratio`（如 `0.95`）做端到端验证，再逐步降低；
- 为大场景设置 `--time-limit`，并打开 `--progress` 观察进度；
- 并行简化多个网格可在 Python 侧做（v1 原生是单线程）。

## 延伸阅读
- `docs/native_meshqem/usage_and_integration.md`：参数速查与集成要点
- `docs/native_meshqem/algorithm_details.md`：QEM 算法细节
- `docs/native_meshqem/README.md`：项目总览与快速导览
