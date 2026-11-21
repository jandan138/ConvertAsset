# paper-experiment-runner Memory

只记录稳定的、项目级的、跨会话仍有价值的论文实验经验。

- 记录可用环境、结果 schema、已验证脚本模式
- 不记录当前批次实验的临时状态

- Isaac4.1 SimulationApp不消费4.5的extra_args配置键；Kit参数应在构造前经sys.argv传入。并行渲染必须实读omni_global_cache token和纹理cache路径回执，不能只凭配置字符串认定隔离。
- 恢复后的GRScenes实验副本Materials常链接至源库；修复KooPbr导入前先复制MDL到独立库，纹理保持只读链接，禁止通过Materials目录链接执行原地修复。静态USD/MDL依赖闭包不能替代RTX运行日志检查；MDL1.5的无前缀`import GlassUtils::symbol;`也需要递归解析。
- 绿色mask轮廓同时描绘外轮廓和遮挡孔洞；不能仅凭围绕前景物的绿线判断它被计入目标mask。需要用实际二值mask像素/区域检查确认成员关系，再记录排除理由。
