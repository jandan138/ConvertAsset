# Mesh 减面（Python QEM 后端）

这里是 Python 版 QEM（Quadric Error Metrics）三角网格减面的完整文档，代码实现位于 `convert_asset/mesh/simplify.py`，配套的人脸数统计在 `convert_asset/mesh/faces.py`。

你能在这里找到：
- 概览：目标、范围与数据流
- 算法：QEM 的数学与代码要点
- 命令行：如何运行与参数详解
- 性能与限制：如何调优、边界与对比
- 规划与路线：下一步准备做什么
- 面数统计：如何从 USD Mesh 统计总面数

文档索引：
- [概览（Overview）](./overview.md)
- [QEM 算法（Python 参考实现）](./algorithm_qem.md)
- [命令行用法（Python 后端）](./cli_usage.md)
- [性能与限制](./performance_and_limits.md)
- [路线图](./roadmap.md)
- [面数统计](./face_counting.md)

相关：
- 原生 C++ 后端与适配文档见 `../native_meshqem/`。
