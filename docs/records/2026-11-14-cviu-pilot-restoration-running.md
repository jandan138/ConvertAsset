# CVIU 三场景恢复与渲染启动定位

最新状态：三场景12对输入与72预测已完成，详见[结果与最终审计](2026-11-14-cviu-three-scene-pilot-results.md)。下文为保留的历史过程，不代表当前仍有任务在运行。

目标仍为三场景 12 对输入、72 次 Qwen3-VL-8B 推理及统计，未完成。
新增 restore_pilot.py：在独立目录复制原始 USD 层闭包，恢复 models/Materials 链接，
共享材质只读，不改源数据和历史产物。目标输出：
`/cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_sources_20261114_v1`。
恢复进程 session 77644，日志 /tmp/cviu-restore-pilot.log；首场景已记录 955 层、
22434 prims、0 unresolved，剩余场景继续处理。以 restore_report.json 为最终事实。

新增 render_probe.py：直接使用远端 /isaac-sim/python.sh，独立 portable/纹理缓存，
关闭 sync_loads，指定 GPU 0，使用 render product RGB annotator。90 秒周期 stack dump，
240 秒超时及 15 秒终止宽限。首个柜子 probe session 29717；日志
/tmp/cviu-render-product-probe.log；输出 recovery_20261114/render_product_probe_v1。
目前只记录 before SimulationApp，尚未返回构造函数，不是场景载入/图像捕获成功。

下次继续须先轮询这些活跃句柄或核对进程，不重启重复任务。恢复结果完成后在独立副本
重新转换；任何恢复过程残留指向源 USD 的 models 链接必须移除后才能转换。
正式几何一致性、可见性、图像和推理均待完成。

恢复进程已退出 0；三场景结果：[('MVUCSQAKTKJ5EAABAAAAAAA8_usd', 955, 22434, 0), ('MVUHLWYKTKJ5EAABAAAAADI8_usd', 659, 15268, 0), ('MVSYCXYKTKJ66AABAAAAADA8_usd', 412, 6047, 0)]。小型报告已归档 recovery_20261114/pilot_restore_report.json。

三场景重新转换已启动，session 68260，日志 /tmp/cviu-pilot-conversion.log；进度以独立工作区 conversion_report.json 为准。转换前检查 models 解析目标在新工作区内。渲染 session 29717 本轮再次轮询仍在运行。

## 渲染启动根因与下一批验证

render_product_probe_v1 的 faulthandler 显示阻塞于 Isaac 4.5 SimulationApp._wait_for_viewport
第 520 行；headless 下 viewport_handle 为 None 的循环没有上限。
render_probe.py 改为 create_new_stage=False，随后显式 open_stage 和创建 render product。
v2 已输出 after SimulationApp 和 stage opened，进入 rep.orchestrator.step；图像仍未验收。
v2 session 94490，日志 /tmp/cviu-render-product-probe-v2.log，GPU 1，独立输出 render_product_probe_v2。
旧 v1 session 29717 仍需检查最终退出，不因新探针启动而假定已结束。

三场景 target_candidates.json 已存入独立 workspace：380、234、374 个对象参考 prim，
包含类别、世界包围盒、up-axis 和单位；候选尚未按可见性验收，不是最终 6 个目标。
第一场景转换返回 0；总体转换 session 68260 仍运行。
新增 audit_pairs.py 对实例代理也进行遍历，比对 mesh 点、拓扑与世界变换，检查两条件依赖。
首批审计 session 53500，输出 pilot_pair_audit_partial_v1.json，仅覆盖当时已完成转换的场景，
不得当作三场景审计；日志 /tmp/cviu-audit-pairs.log。

## 完整转换审计与 Hydra 根因

三场景转换均完成；full audit 输出为 recovery_20261114/pilot_pair_audit_full_v1.json。
原始/转换 mesh 分别 8738、4080、1278，均几何/世界变换一致且未解析依赖为零。
prepare_pilot_views.py 已生成 24 个自然场景相机（12 对候选），每场景两对象两视角，
输出 workspace 同级 pilot_views_20261114_v1/jobs.json。投影框只为候选，不代表可见 mask。

render v3 绕过 rep.step 后 app updates 正常但 RGB 空；fast_shutdown 曾掩盖失败，
v4 改为 fast_shutdown=False 并保存 failure.json。v4 明确打印 hydra engines []，
于是 v5 显式 omni.usd.add_hydra_engine('rtx',context) 再打开场景。
v5 句柄见会话工具返回，日志 /tmp/cviu-render-product-probe-v5.log；
v4 session 39823 仍需确认结束。结果必须检查 rgb.png 和 receipt.json，不只看退出码。

v5 session 85673 已退出 1，add_hydra_engine 后 open_stage 引发 GUI menu hotkey 回调段错误，日志含 Fatal Python error。没有 RGB，不算通过。需要处理 headless GUI/显示依赖；不能继续单纯加长超时。

## 扩展隔离与备用已装运行环境

v4 已确认超时退出 124。v6（session 57169，GPU1）禁用 isaacsim.gui.menu 后不再在
菜单回调处崩溃，但仍无 Hydra 引擎；v7（session 85604，GPU2）调整为 stage open 后
add_hydra_engine + attach_all_hydra_engines，目前出现 GPU cmdlist semaphore 错误，仍需检查终态。
两者日志 /tmp/cviu-render-product-probe-v6.log、v7.log。

远端旧模型环境导入实测：torch 2.10.0+cu128、transformers 5.2.0、CUDA True，
Qwen3VLForConditionalGeneration 可导入。未加载权重，不计为模型推理完成。

为隔离容器 Isaac4.5 GUI/runtime 问题，使用主机现成的
embodied-eval-os-isaacsim41-py310 环境启动相同柜子探针；不安装或覆盖环境。
GPU3，CUDA_VISIBLE_DEVICES=3、physics_gpu=0，独立缓存与输出 render_product_probe_41_v1。
session 21290；日志 /tmp/cviu-render-product-probe-41-v1.log，240s上限。若通过，整批原始/
转换图像统一在该版本生成，记录版本差异，不混用不同渲染版本作为实验配对。

## 首张输出验收失败与自然场景捕获

4.1 cabinet probe 生成 rgb.png/receipt.json，但进程关闭时退出 255；本地实际查看图片
为纯灰背景，视觉验收 FAIL。追溯 original_camera.usda 发现先前诊断柜子的包围盒为空
导致相机平移约 1e39、clip 为 inf。该探针不属于有效实验图像。正式三场景相机投影有限。
render_probe.py 新增有限相机/clip 检查和近常量 RGB 拒收；仅在 context 未挂引擎时添加，
避免 4.1 已有 RTX 被重复附加。GUI menu 禁用仅限进程，不修改安装环境。

4.5 v6/v7 均确认退出 124。现正使用4.1捕获正式第一家庭场景 couch v0 original，
session 66356，GPU0，日志 /tmp/cviu-natural-couch.log；输出 natural_couch_original_v1。
使用 GPU1 启动 Qwen3-VL-8B 的实际权重和 processor 加载资格检查，session 37802，
日志 /tmp/cviu-qwen8b-load.log。检查完会释放模型，不把权重加载算作72条预测。

Qwen3-VL-8B 实际权重+processor 加载资格通过：退出0，BF16，耗时约60s，GPU分配
17,534,319,104 bytes。回执已存 recovery_20261114/qwen8b_load_qualification.json。
模型进程已退出释放显存。natural couch session 66356 仍在 app.update 中，90s堆栈已采集；
不能据此判为死锁，完整场景首次材质/着色器加载也可能耗时，等待当前240s进程终态。

## 固定时间捕获对照

natural original updates 模式仍在 app.update 原生调用内，观察到 CPU 持续活动，不能
从 Python 堆栈推断为死锁。新增 step 模式使用 delta_time=0、pause_timeline=True，
避免推进物理时间；原始 probe session 20140、GPU1、日志 /tmp/cviu-natural-couch-step.log；
转换 probe 日志 /tmp/cviu-natural-couch-converted-step.log、GPU2。均480秒上限、独立缓存，
用于区分原始MDL加载和通用整场景渲染问题；不是更换场景或改变几何。
需核对当前工具句柄/远端进程，未见 PNG 前不能宣告成功。

original updates session 66356 已终止，工具退出码255，无 rgb/receipt，未通过；最后堆栈仍是 app.update。转换固定时间探针 session 80581。

## 自然视图产物与验收

converted step session 80581 退出0，约47秒得到1024x768 RGB。但实际本地视觉检查 FAIL：
画面几乎全被浅色表面覆盖，无法辨认沙发。小型 QA 回执 natural_couch_converted_visual_qa.json。
这是捕获流程成功，不是数据验收通过。候选相机必须增加遮挡检查；尚无有效12对图像。
原始 MDL step session 20140 仍在运行，等待当前进程终态，不重复启动相同任务。

新增 pilot_inference.py：输入必须为已视觉验收、哈希匹配的 image/mask，完整三场景
每场景至少两对象两视角、至少12对；每次单独模型加载，支持repeat0/1/2；固定贪心解码，
逐行保存 prompt/raw_response/point/hit/runtime_error。运行异常 hit=null。
8项解析和输入规模测试通过（tests/test_cviu_pilot_inference.py + test_cviu_inventory.py）。
尚无合格manifest，因此没有执行正式预测；评分统计与配对案例报告仍待完成。

## 几何遮挡筛选 v2

prepare_pilot_views.py 复用现有 AABB 视线分类器，检查模型参考 prim 的世界包围盒，
排除目标及其祖先/后代，枚举不同距离、方位和仰角；先排除相机在障碍物内，再检查
到目标前表面的视线，按固定顺序选择相隔至少30度的两视角。保留完整筛选记录，
不使用模型输出选视角。相机 stage 显式继承 upAxis 和 metersPerUnit。
六目标1080候选：759 centerline_clear、205 blocked_centerline、116 camera_inside。
新输出 pilot_views_20261114_v2，24 camera stages（12对），仍为视觉未验收候选。

render_probe.py 增加 instance_id_segmentation annotator，写 instance_ids.npy 与映射info；
只有 actual render 后才能据此形成可见目标 mask。首个 v2 couch converted 捕获
session 14897，GPU2，日志 /tmp/cviu-natural-couch-visible-v2.log。
原始 MDL step session20140尚需持续核对。
解析/输入测试复跑8 passed；未声称几何筛选取代视觉验收或已完成72条推理。

original step session20140 已退出0并生成1024x768 RGB，实际视觉检查为室外城市背景与大面积白墙，无法看到沙发，FAIL。两种材质全场景捕获均已通，但v1相机不合格。新QA记录 natural_couch_original_visual_qa.json；继续验证v2遮挡筛选视角。

v2 converted couch capture session14897退出0；实际查看RGB可见橙色沙发、茶几和窗帘，局部视觉PASS。实例ID文件已输出。QA记录 natural_couch_v2_visual_qa.json。随后启动24幅候选四卡队列，入口 render_pilot_batch.py；进度 pilot_renders_20261114_v1/progress.json，日志 /tmp/cviu-pilot-batch.log。每幅仍需视觉检查，不自动通过。

## 可见mask标注更正

已有 instance_id_segmentation 的 idToLabels 全部167项为INVALID，不能用于目标mask。
render_probe.py 增加从相机目录 jobs.json 查目标prim，在 session layer 施加
SemanticsAPI class=cviu_target，semantic_segmentation 导出 target_mask.npy及semantic_info。
未修改源USD，不绘制任何输入标记。已启动的前四任务仍执行旧版本，后续任务读取新脚本；
缺mask的产物必须补渲染/标注后才可纳入manifest。新增每个捕获进程启动时脚本SHA256。
本轮没有将无效实例ID映射用于评分。

新增 analyze_pilot.py：读取三次独立推理，严格拒绝缺失/重复矩阵和未解决runtime_error，
报告每次O/F命中、loss/gain/flip、同条件三组重复对分歧、按scene及逐pair案例。
不把重复视作独立场景，不把翻转自动归因给材料。输出 results.json/report.md，尚未运行真实输入。
测试解析/规模/均值抵消/重复噪声/运行错误合计11 passed。
当前批次session96472仍运行，无全量视觉验收；必须补有效semantic mask后才能执行正式推理。

## 并行缓存隔离纠正

核对已运行process环境未设XDG_CACHE_HOME，旧参数 /omni/global/cachePath 不是真正Kit token。
修复为 /app/tokens/omni_global_cache，新增 carb.tokens 解析回执及路径属于输出目录的检查。
原batch v1 因未证实缓存隔离及首四任务缺semantic标注，主动取消自身调度PID2105121及
四个timeout父进程2746147–2746150，保留 cancelled.json 和所有日志，排除科学结果使用。
这不是观测超时重启；是确认配置缺陷后的版本变更。
render_pilot_batch.py 改为启动前冻结renderer脚本副本与SHA256，全批统一版本。
下批使用pilot_renders_20261114_v2，仍为同一24幅相机，不改场景/目标/几何。

旧batch session96472退出143，远端四个worker成为终止后的defunct；GPU0显存尚未完全回收。修正版batch session59655使用GPU1/2/3，同24jobs，日志 /tmp/cviu-pilot-batch-v2.log。脚本支持--gpus选择空闲卡并冻结renderer版本。必须等待并检查cache_receipt.json再认定隔离生效。

## Isaac4.1 命令行缓存参数资格通过

读取4.1 SimulationApp源码发现extra_args配置键不被使用，必须将Kit参数放入sys.argv。
修复后isolated_semantic_probe_v1实际token与纹理cache均在独立输出路径，退出0。
RGB实际可见沙发，target_mask为768×1024 bool、44973 pixels，查看mask轮廓与RGB对应，
排除靠垫和前景遮挡；QA及hash记录 isolated_semantic_probe_qa.json，单张PASS非整对PASS。
批次v2因cache检查失败主动终止调度及所属timeout。v3使用已验证冻结脚本，GPU0–3，
输出pilot_renders_20261114_v3，日志 /tmp/cviu-pilot-batch-v3.log。

新增freeze_inputs.py：要求逐图RGB与mask的PASS及对应hash、目标prim和stage回执，
验证三场景×每场景两对象×每对象两视角完整矩阵后才输出推理manifest。未自动批准任何新图。

## v3实际运行检查

session87241持续运行。首四任务cache_receipt确认global/texture路径均落在各自目录；
所有任务已打开场景并挂载RTX。约4分钟时四worker PID2760877–2760880仍活跃，CPU与内存
有使用，尚未见RGB；继续等待当前900秒任务，不凭观测超时重启。
缓存检查快照 batch_v3_initial_cache_check.json，不代表图像已验收。
输入验证增加同pair的query/target/view/scene一致性检查，测试12 passed。

## v3首批视觉验收与mesh遮挡修正

01转换沙发v0本地视觉PASS；mask44973 pixels，形状与先前已查看轮廓相符。
03转换沙发v1为近处暗表面遮挡，目标不可见且无target_mask，FAIL。
QA记录 batch_v3_visual_qa.json，失败不进入推理，不按模型结果挑选样本。
prepare_pilot_views.py 遮挡物改为遍历实际Mesh（包括instance proxies），不再只看有reference
的prim，以覆盖直接authored墙体。新候选输出pilot_views_20261114_v3，旧批次继续不修改。
新候选生成session见工具返回，日志 /tmp/cviu-pilot-views-v3.log。

mesh AABB版v3候选生成因所有沙发候选被包围盒判挡而退出1；这是保守AABB把复杂墙体/房间
整体包围的问题，未输出可用jobs。改为AABB预筛＋实际mesh三角形射线相交，按世界变换
展开网格，跳过不可见mesh，检查射线在目标包围盒前的真实交点。v4候选生成正在运行，
session71708，日志 /tmp/cviu-pilot-views-v4.log；仍需视觉验证，不能据几何测试自动接受。
当前batch v3继续生成未完成图像；已完成01 PASS、03 FAIL、05/07待查看。

本轮新增实际RGB与mask检查：05/07 laptop两视角PASS（07前景书本遮挡但可定位可见屏幕背面）；
09/11第二家庭场景couch两视角PASS（09侧视部分遮挡，11完整）。QA文件累计5 PASS、1 FAIL，
仅转换侧，尚不构成完整配对验收。原始MDL首两任务约10分钟仍有CPU活动，不擅自重启。
三角形射线v4候选生成退出0，24相机已产出，待用于失败视角的替换验证。

调度恢复：session87241退出143，本地controller消失，但远端00/02/13/15进程仍存活。
新增--resume：读取已有progress、逐输出目录检查远端实际render进程，等待存活任务结束，
不重启它们；未执行任务才新开。使用nohup持续controller，日志
/tmp/cviu-pilot-batch-v3-resume.log，远端新任务将退出码写入NN.exit。
旧任务由孤立进程回收时退出码未知，保留null，不伪造0。仍以实际图像和QA验收。

## 失败任务恢复队列

原接管中00/02/13/15确认终态无图，退出码不明保留null；主controller2236879继续剩余任务。
新增recover_render_batch.py等待primary progress全部终态，再收集capture失败、QA FAIL及
目标mask缺失/空的pair。视觉失败按v4新候选同时替换O/F，单纯捕获失败保持原相机。
恢复任务另存pilot_renders_20261114_repairs_v1，原始所有失败数据不覆盖；单任务上限3600秒。
恢复controller以独立session后台等待，日志/tmp/cviu-render-recovery-queue.log。
不按模型输出调整输入，不在原任务仍存活时启动同任务。恢复结束仍需逐图人工式视觉验收。

17/19商业场景stool转换两视角RGB与mask本地视觉PASS；暗光仍可识别背靠缺失的木凳，
mask正确排除腿间空隙及两侧有靠背椅。当前已检查转换侧7PASS/1FAIL。
推理记录增加visible_bbox_hit作为辅助指标，主指标仍为可见mask命中，用于识别空洞型目标
（如凳子）中bbox中心与实际可见表面评分的区别；尚未进行推理，不依据结果改指标。

商业21 toy-v0实际为猫蜷卧宠物窝；RGB与mask检查PASS，mask正确仅覆盖猫不含窝。
23 toy-v1被墙完全遮挡，无mask，FAIL。源toy类别不符合视觉指令，预先统一query为
Point to the cat in the image.，源category及prim保留；两条件同一query，尚无模型输出。
freeze_inputs支持QA中明确记录的pair级query_override并拒绝冲突。当前转换侧8PASS/2FAIL，
微波炉两视角中断未出图，原始侧仍等待；不宣告12对或72预测完成。

## 首批完整配对与空闲卡补渲染

04/06原始laptop两视角已完成；RGB本地视觉PASS，与05/07转换视角一致，mask逐像素相同。
当前已有laptop两对完整视觉输入，仍未覆盖每场景两目标。QA更新记录原始图hash。
检测GPU1/3空闲后启动early repair controller2289469，输出pilot_renders_20261114_early_repairs_v1，
日志/tmp/cviu-early-repairs.log。7个任务：失败couch-v1与cat-v1的转换图、两张中断微波炉转换图、
cat-v1原始新视角、couch-v0原始缺失、couch-v1原始新视角；单任务3600秒，独立缓存。
未打断主队列GPU0/2的第二场景原始任务。
原等待恢复controller2252194在尚未派发任务时终止，改为2290875，等待主/early两批终态，
按pair/condition/实际stage复用成功且有非空mask的补渲染，避免重复执行。日志保持同名。

恢复等待器载入非空mask复用检查的新进程PID2295073（替代尚未派发任务的2290875）。12组v2相机参数实读比对均相同，报告pilot_camera_pair_audit.json。

early repairs 00新couch-v1转换RGB与mask视觉PASS；01新cat-v1转换RGB/mask视觉PASS，
暗光与椅腿局部遮挡保留记录，猫身体耳部可辨。QA为early_repairs_visual_qa.json；
只覆盖这两个新转换产物，原始侧尚未验收。统计输出明确新增命中率、翻转率、输出覆盖率
与可见框辅助命中率；缺失字段保留null而非0，12测试通过。

early微波炉02空白检查拒收、03柜体背面遮挡，均FAIL；加入early_repairs_visual_qa。
全部尝试的QA合并all_attempt_review_decisions供恢复队列选择，仍保留原始独立QA文件。
等待恢复controller更换为2325337，尚未派发任务，原渲染不受影响。
primary12/14原始微波炉旧相机若尚无输出目录则预建cancelled记录，明确因匹配转换视角
已确认遮挡而跳过，无渲染/无任务分数；新v4视角两条件进入后续补渲染。

08/10第二家庭场景couch原始两视角RGB视觉PASS，mask分别93832/134412 pixels，与09/11转换
对应mask逐像素一致；原始反射和背景透明可见性差异仅作视觉观察，尚无模型效应结论。
完整可用配对增至4（laptop两对＋第二场景couch两对）。v4替换相机参数实读12组也一致，
报告pilot_v4_camera_pair_audit.json。其余原始与微波炉新视角继续队列。

early04原始cat-v1 RGB本地视觉PASS，暗光/遮挡特征明确，23542像素mask与early01转换逐像素一致。
完整可用配对增至5。primary22旧cat-v1视角尚无目录时标记跳过，因两条件替代相机均已验收，
不重复已知失败视角。新增冻结输入的中心点基线与均匀像素随机命中概率（mask面积比例），
用于解释目标视角带来的定位难度。最终试验为双条件可见性合格子集；排除记录保留，
不将结果外推为全部转换场景的失败比例。

新增assemble_pilot_inputs.py，将实际capture progress与绑定hash的视觉QA按输出目录/配对键
合并；复核图像/mask哈希及O/F相机文本参数。当前只读汇总实测15张PASS、5个完整pair；
没有--out时不冻结部分数据。仅完整12pair才生成selected progress/QA并调用freeze_inputs。
保留来源progress/QA的hash与被排除review记录，避免补渲染合并丢失失败历史。

16/18商业stool原始两图实际视觉PASS，对应17/19转换mask逐像素相同；原始木饰面/反射与
转换有可见差异，仅记录输入变化，未声称模型效应。完整pair增至7。全部原始geometry
一致性已有full audit，最终selected输入仍须逐pair核对camera与image/mask哈希。

primary20 cat-v0、early05 couch-v0、early06 couch-v1原始RGB均实看PASS，mask与对应转换图
逐像素相同；完整输入增至10pair。main与early均终态；自动恢复已派发仅微波炉4张v4新图。
检测到自动恢复输出已存在时，手动加速重复启动被前置检查阻止，未产生重复任务。
恢复仍由2325337监督，日志/tmp/cviu-render-recovery-queue.log，输出pilot_renders_20261114_repairs_v1。

微波炉v4补渲染01转换v0、02原始v1、03转换v1已实看RGB/mask PASS；源microwave实际为
带下拉门、温度显示的嵌入式烤箱，推理前统一query为Point to the built-in oven in the image.，
保留源category/prim，避免语义标签错误混淆材质效应。v1原始/转换mask228729 pixels逐像素相同。
QA在final_repairs_visual_qa.json；待00原始v0，其他图不重渲染。完整pair目前11。
推理将保存引擎/runner快照及checkpoint配置文件hash，12项基础测试通过，尚无正式预测。

## 12对输入冻结与正式推理启动

最后微波炉00原始v0实看PASS，mask与01转换逐像素一致。全24图通过本地视觉验收，
包含3场景、6目标、每目标2视角，共12对；全部实际输入相机参数已在assembler复核。
冻结目录 paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1，含manifest、
selected progress/QA与来源hash/排除记录。query在推理前修正toy→cat、microwave→built-in oven。

run_pilot_repeats.py已启动三次独立Qwen3-VL-8B进程，GPU0/1/2，每次24条，贪心BF16，
输出冻结目录inference/repeat0–2；配置、脚本快照、原始响应和输入hash逐条保存。
日志/tmp/cviu-pilot-inference.log；只启动不代表已完成，需检查72条及runtime_error状态。
