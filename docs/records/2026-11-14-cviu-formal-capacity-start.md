# CVIU 正式跨场景与容量对照启动

沿用已讨论范围：30正式场景（20家庭、10商业），每场景8对象×2视角，480对；
Qwen3-VL-8B/32B各对两条件独立运行三次，共5760预测。三场景pilot保持独立。

读取冻结inventory、现有pipeline及模型目录：30入口原始SHA均未变化；本地未缓存32B。
通过官方Hugging Face接口核实32B revision `0cfaf48183f594c314753d30a4c4974bc75f3ccb`，
权重66,714,912,872 bytes，开始下载到既有模型cache，下载完还需加载资格检查。

新增实验目录 `paper/shared/evidence/experiments/13_cviu_formal/`，正式数据配置在
`paper/shared/evidence/raw/cviu_formal/v1/`。具体命令、资源与统计约定见
[实验说明](../../paper/shared/evidence/experiments/13_cviu_formal/README.md)。

修改restore_pilot支持显式--splits，默认pilot保持不变；新增恢复后所有USD层均在
独立workspace内的检查，避免转换跟随绝对引用写回源数据。正式准备按场景子进程执行，
失败记录并继续处理其他已冻结场景，不静默换样本。

已启动独立后台进程：model_download PID2475480，scene_preparation PID2475481。
日志分别为/tmp/cviu-formal-model_download.log、/tmp/cviu-formal-scene_preparation.log。
后续必须检查真实进程/回执，不把PID记录本身当作仍在运行的证明。

验证：场景清点与scratch materializer相关16测试通过。当前仅启动资源准备，未产生
正式图像、32B加载资格或5760预测。渲染复用、目标/视角筛选、统计与主线结论仍需实施。

进展核查：约启动4分40秒时，3/30场景已达到ready_for_target_selection，恢复报告中的
unresolved和external_usd_layers均为0，转换后geometry audit通过。准备进程2475481和
下载进程2475480均核实仍存活。32B缓存约1.07GB，尚无下载完成回执，不能称权重齐备。

新增tests/test_cviu_formal_restore_guard.py：真实USD两subcase验证相对闭包成功、绝对
源USD逃逸被拒，并验证原始源文件hash不变；Isaac Python运行1 test通过。

## 批量渲染和目标池

新增render_scene_views.py：每scene/condition只open_stage一次；session-layer相机覆盖，
全部目标唯一语义标签，逐视角输出RGB/mask与参数回执。pilot A/B/A资格检查用于排除
相机/标签串扰。v1 mask全相同但RGB MAE 0.44/2.45/2.30，超过预设1级阈值；未准入。
v2新建render product时遇到4.1 detach参数须path字符串，修正后v3完成；mask仍全相同，
RGB MAE 0.51/1.28/1.59，仍需调研，未放宽阈值。

当前进一步测试FXAA（spatial，anti_aliasing=2），同时运行batch和两个独立fresh基线，
输出formal_renderer_batch_fxaa_v1/fresh_a_fxaa_v1/fresh_b_fxaa_v1。尚未据此改变正式数据设置。
新增extract_target_pool与collect_target_pools：已通过场景即进入几何候选池，优先类别
多样性与低重复类别、再按固定hash排序；每场景8个暂定目标及完整候补/排除记录。
不调用被测模型筛样本；类名歧义、真实可见性与关系描述仍待QA。两个排序测试通过。

## 外部MDL依赖

商业场景发现http:/单斜杠材质URI，涉及Tinted_Glass_R50/R75、Ash_Planks、
Glass_Glazing_Spandrel和Ground_Leaves。归一化HTTPS官方S3地址后均可读。
已下载5个原始MDL文件至独立formal_remote_materials_v1，URL/hash/import记录在
paper/shared/evidence/raw/cviu_formal/v1/remote_mdl_downloads.json。
还需抓取相对import的GlassWithVolume模板及纹理，并验证nvidia::core_definitions等
运行时模块，再只修改独立副本的资源定位路径；目前这些场景仍未通过，不替换场景。
32B下载仍在运行，尚无完成回执或加载结果。
