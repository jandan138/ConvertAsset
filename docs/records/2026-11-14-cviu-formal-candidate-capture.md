# CVIU 正式候选视角与原始条件采集

## 已完成资格

独立同序batch A/B/A对照通过：mask逐像素相同，RGB MAE为0.419、0.352、0.575，均低于
预设阈值1。证据：[匹配批次重复资格](../../paper/shared/evidence/raw/cviu_formal/v1/matched_batch_repeat_qualification.json)。
这不是与旧单张流程像素等价的证明；旧对照差异保留。正式O/C使用相同最终视角顺序、
Isaac4.1/RayTracedLighting/DLSS、sync_loads=False，独立缓存；另有3场景完整重渲染控制。

完整数值buffer几何审计补强：30场景均通过，直接hash时间0的顶点、拓扑与世界变换
二进制数组，不依赖格式化字符串。证据：[汇总](../../paper/shared/evidence/raw/cviu_formal/v1/binary_geometry_audit/summary.json)。

## 视角与标签资格

初版相机写文件因释放Stage后Layer弱句柄失效而失败；已用保存后重新打开Sdf.Layer修复。
真实USD回归通过。第二版30场景均生成16对几何候选，但首场景预览表明中心线可通行
不等于目标类别可辨：TV边缘视角、冰箱侧视和一个空白视角需改进。

现在每目标保留最多4个原始几何候选，仍只选择2个最终有效视角；30场景共有902个原始
候选视图，最终要求仍为480对。候选与后续模型结果无关。固定hash候补顺序、所有排除
与标签更正保留，不通过替换正式场景凑数。

首场景预览发现hearth实际为燃气灶，sofa_chair为曲线休闲椅；上层小烤箱需要与下层
电器区分。已记录[初步视觉检查](../../paper/shared/evidence/raw/cviu_formal/v1/first_scene_preliminary_qa.json)，
不是正式输入验收；后续还需mask核对和确定每个目标的清晰指代表达。不可全局假定
hearth一定是壁炉、microwave一定是微波炉。

## 当前运行

- 全30场景原始候选捕获controller PID3086078，日志/tmp/cviu-formal-original-candidates.log。
- 输出：assets/convertasset_research/experiments/cviu/formal_original_candidates_20261114_v1。
- 相机输入：formal_views_20261114_v3；仅原始条件用于初筛，之后冻结最终视角并同序捕获O/C。
- 每GPU空闲后派发，不中断其他任务。每场景冻结renderer快照，一次加载后捕获多个视角。
- 空白RGB保存并标记待检查，不自动当基础设施失败，也不再中断后续视角；无效buffer仍报错。
- 32B增加8线程协作下载PID3085473，与原PID2475480共享同一revision的Hub缓存及文件锁，
  不另存权重副本；不同回执文件区分两次下载调用。截至核对缓存约27.35GB，未完成加载资格。

正式图像资格、480对冻结数据、两模型5760预测及CVIU主张判定均尚未完成。pilot结论不变。

## 原始图像逐目标检查（本地视觉审阅）

刷新生成136份目标检查图，每份最多4个候选视角，绿色轮廓只用于检查，不修改模型RGB输入。
实际打开首场景MVUHL5YKTKJ5EAABAAAAAAI8_usd的8份检查图（29张候选RGB），保存
[逐图判定与哈希](../../paper/shared/evidence/raw/cviu_formal/v1/original_visual_reviews/MVUHL5YKTKJ5EAABAAAAAAI8_usd.json)。
该审阅由主会话完成，不是独立人工复核；尚不等于正式输入冻结。

- 提议每目标2视角，共16视角；最终还需相机间隔验证及同序O/C重新捕获。
- 排除电视v0的极端侧视，以及靠垫v0/v2的黑色RGB。黑图的非空mask不能证明图像可用。
- 标签更正为gas cooktop、curved lounge chair、washbasin；上层小烤箱和沙发花纹靠垫使用明确指代表达。
- 冰箱v0保留WARN：前景墙与倾斜视角存在，但双门及控制面板可辨；不是遮挡消失。
- 电视下方搁板的USD实例mask包含其上装饰物，需保留实例层级指标定义，不能描述为严格部件分割。
- 对29张RGB及mask重新计算SHA256，均与捕获回执一致。所有选择均在正式模型推理前完成。

本轮核对时采集controller和两个权重下载进程均仍存在；采集17/30场景终止并等待QA。

## 运行时MDL导入错误：先前候选资格撤回

第二场景逐图审阅发现多物体统一鲜红色。日志确认`C120 could not find module
'::KooPbr'`及`KooPbr_maps`，不是材质干预结果。扫描25份当前日志，12个场景有
材质编译错误，其中包括前述首场景；首场景16个提议视角仅保留为历史，不具备正式资格。
[运行日志审计](../../paper/shared/evidence/raw/cviu_formal/v1/runtime_material_log_audit_01.json)
记录逐行错误和日志hash；无匹配错误也不等同于视觉通过。

根因是home Materials中的生成MDL用绝对模块导入，同目录模块实际存在。
复用既有`scripts/fix_mdl_absolute_imports.py`的纯文本修复函数，在新独立库中复制
1677份MDL，1566份修复为相对导入；纹理目录仍为只读源链接。逐一确认源MDL hash未变。
只在已完成且经远端进程检查确认不再渲染的MV7J6NIKTKJZ2AABAAAAADQ8_usd实验副本内，
将524个Materials链接指向独立库。没有改源数据，没有改变材质数值或几何。
[绑定记录](../../paper/shared/evidence/raw/cviu_formal/v1/mdl_library_probe_binding.json)。

新增prepare_mdl_library.py和audit_capture_logs.py；源不可变、CRLF保持、复制与纹理链接、
错误日志识别及已有导入修复测试共8项通过：
`python -m pytest -q tests/test_cviu_runtime_material_log.py tests/test_cviu_mdl_library.py tests/test_fix_mdl_absolute_imports.py`。

修复仍待运行时验证：控制进程3154714等待旧候选controller3086078退出和GPU0空闲，
再执行3个原始视角重渲染。输出formal_mdl_repair_probe_v1，控制日志
/tmp/cviu-material-repair-probe-controller.log。不能仅凭文本修复或测试通过认定渲染成功。
下一步检查probe的MDL日志和RGB，通过后再对其余受影响实验副本应用同一修复并重新采集。

同时按已冻结pilot manifest逐一定位12张原始图的实际捕获日志，均找到日志且未匹配
上述材质错误模式。记录[pilot日志复核](../../paper/shared/evidence/raw/cviu_formal/v1/pilot_runtime_log_recheck.json)。
本次正式候选失败不能据此推定pilot也失败；该日志扫描本身也不替代pilot既有图像检查。

## 无材质编译错误场景的视角验收与候补补足

MVUHLWYKTKJ5EAABAAAAAAI8_usd的8份检查图已本地逐图打开，逐图hash复核。
7个目标提议14视角；所有选中对的相机方位间隔为30或60度，通过新增
check_view_selections.py的相机矩阵与捕获身份检查。洗手盆4个原始视角近乎全黑，
因此未选任何视角；有mask不代表目标可辨。完整8目标资格仍未通过。

保留原始候补次序，排除已经试过的目标，从剩余96个候补中生成首个可行目标shelf，
得到3个原始候选视角。prepare_views.py新增--target-count（默认仍8），允许局部补足，
不更换场景或扩大正式目标数。首次误用Isaac4.1裸Python缺pxr而失败；随后通过仓库
scripts/isaac_python.sh成功生成，失败路径保留。真实USD相机层测试1项通过，
方位角跨360度边界与up-axis测试2项通过。

候补捕获controller3181781等待原采集controller结束后使用GPU1，修复probe使用GPU0，
两者均先检查GPU空闲。候补输出formal_alternate_target_capture_v1；此时仍是待审候选，
不是补足完成。日志/tmp/cviu-alternate-target-probe-controller.log。

本轮核对32B下载缓存约37.07GB，下载进程仍存在，尚未取得完整模型资格。

MVUCSQAKTKJ5EAABAAAAAAY8_usd也已逐图检查8目标30候选图，提议16视角；
相机间隔30–120度、图像/掩码身份检查通过，原候选捕获exit0且未匹配材质编译错误。
记录original_visual_reviews同名JSON和_geometry.json。查询使用类别与稳定场景关系，
不用可能随材质变化的颜色，例如small microwave with two control dials。

prepare_selected_capture.py将这16对选择绑定到同顺序原始/转换job清单，保存审阅、
相机层和日志hash；只标记selected_not_final_image_qualified。run_selected_capture.py
分条件独立进程捕获。controller3199903已排队等待旧候选采集结束，使用GPU2。
输出formal_selected_captures_v1/MVUCSQAKTKJ5EAABAAAAAAY8_usd，控制日志
/tmp/cviu-first-selected-capture-controller.log。代码编译检查通过；尚无最终32张图验收。

## 正式本地推理入口准备

新增formal_inference.py，formal模式要求已冻结manifest、完全相同的30场景集合、
960条件输入/480对、每场景8目标×2视角、配对查询一致、原始可见与技术资格、图像mask哈希。
转换条件空mask保留；基础设施错误为runtime_error/hit=null，不当失败分数。
8B要求暴露1GPU，32B要求2GPU，BF16且拒绝CPU/disk offload和量化权重。
保存原回答、processor配置、image_grid_thw、模型设备映射及配置hash。提示词及text→image
顺序沿用pilot；qualification模式与formal分开标识，不计入5760正式预测。

3项结构/可见性契约测试通过；对真实pilot的24条输入运行qualification --validate-only通过。
这里只验证输入，尚未验证该新入口的真实模型加载/推理，更未完成32B加载资格。

GPU1分配的所有原候选场景已完成，核对ready_scenes队列与完成记录后，将尚未启动渲染的
probe等待进程3154714结束，改由3220591在空闲GPU1立即运行。没有中断正在渲染的任务，
也没有因轮询超时重启；新控制日志/tmp/cviu-material-repair-probe-controller-gpu1.log。

新增queue_model_qualification.py：等待旧候选controller退出和指定GPU空闲后，运行
新的推理入口处理held-out pilot输入。8B资格任务controller3224494排队使用GPU3，
输出raw/cviu_formal/v1/qualification_8b，仍不计入正式预测。32B仍等待完整下载。

## 第二份运行时审计与GlassUtils依赖补全

刷新224份目标检查图后扫描全部30份当前日志，14个场景匹配材质编译错误。
新增两例来自GlassWithVolume.mdl中的`import GlassUtils::symbol;`：此前扫描仅处理
带`::`的绝对导入及using形式，漏掉不带前缀的兄弟模块。fetch_material_closure.py
新增这种导入的解析；3项依赖解析测试通过。重新递归下载得到19个文件、0未解析项，
新增官方GlassUtils.mdl（2417字节，hash见material_closure_v2.json）。没有改已有MDL字节。
这只是静态闭包补全，运行时仍待验证。

GPU3原候选队列已全部完成，GlassUtils三视角probe控制任务已启动，输出
formal_glassutils_probe_v1，日志/tmp/cviu-glassutils-probe-controller.log。
KooPbr probe进程3037800仍在运行，约1072% CPU；不能凭尚无帧输出认定失败或重启。

MV5M25QKTKJZ2AABAAAAAAI8_usd已完成8目标30候选图审阅与16视角选择，
相机间隔30–60度通过；暗色物体保留可辨识性的WARN说明，边缘视角排除。
已生成同序O/C清单，controller3228583在第一场景正式捕获完成后使用GPU2，
输出formal_selected_captures_v1同名场景。仍待最终图像资格，不是正式模型结果。

## KooPbr运行时修复验证通过

formal_mdl_repair_probe_v1完成3/3视角，exit0，材质编译错误计数0；主会话逐张打开RGB，
原饱和红色家具/灶台恢复木纹、石材、金属等可辨材质。三张图的camera_parameters与
原失败捕获完全相同，mask文件hash亦逐一相同。源1677份MDL重新核对hash未变。
[结果回执](../../paper/shared/evidence/raw/cviu_formal/v1/mdl_repair_probe_result.json)。
这个结论仅证明一场景三视角修复有效，不能替代其余受影响场景重新捕获与QA。

新增bind_material_library.py，仅对审计中含KooPbr错误的已完成场景进行实验副本链接切换，
先核对远端无该场景渲染、源MDL hash及workspace边界，所有链接变更保存在
raw/cviu_formal/v1/home_material_rebinding/bindings.json；源数据不写入。

首轮候选采集现已终止：30/30场景、902/902候选帧，所有exit0。终止日志审计
runtime_material_log_audit_03_terminal.json仍标记14个材质错误场景，不能将exit0当作资格。
12个KooPbr场景共切换7949个剩余Materials链接（probe场景之前已切换），源hash再验证不变。
重采队列controller3235644等待候补目标捕获3181781结束后使用GPU0/1；输出
formal_original_candidates_repaired_v1，命令和状态保存在home_material_rebinding/capture_queue.json。
GlassUtils两场景运行时probe仍在运行；其依赖修复不能提前记为通过。

MV4AFHQKTKJZ2AABAAAAADY8_usd也完成8目标32候选视图审阅，选择16视角，
相机间隔30–180度通过。明确保留checkout monitor可辨后视图为WARN，排除极端侧视
及沙发被墙遮挡视角；展示架mask包含其上商品。已生成配对捕获清单，第三场景捕获
等待8B资格任务3224494结束后用GPU3；日志/tmp/cviu-third-selected-capture-controller.log。

## GlassUtils运行时通过与8B真实推理资格

GlassUtils probe完成3/3，exit0，材质错误计数0；逐张打开图像，篮筐与室内环境可辨，
窗口背景无红色回退。结果glassutils_probe_result.json。两个受影响场景另排重采队列
3238088，等待第三场景配对捕获3237036完成后使用GPU3，输出
formal_original_candidates_glass_repaired_v1。三个probe视角不能替代这两个场景全量验收。

8B首轮新入口资格失败：模型没有hf_device_map字段，旧检查把空映射判为CPU/offload。
修正为检查实际参数device，并在检查前保存placement_report.json。重新运行
qualification_8b_v2：全部参数cuda:0、torch.bfloat16，24条预测全部成功且格式有效，
原始11/12、转换11/12，24条原回答与既有pilot repeat0逐条完全一致。
因此新推理入口的8B held-out资格通过；首轮失败日志保留。32B尚未完成资格，
本批24条预测不计入正式5760条。结果qualification_8b_v2/qualification_result.json。

## 首个候补替换通过

MVUHLWYKTKJ5EAABAAAAAAI8_usd的候补`shelf`经实际RGB/mask审阅确认为wall-mounted
towel rack。v1/v2可辨，方位间隔30度；v0暗色边缘视角排除。候补capture exit0且无
材质错误。保留旧洗手盆失败记录，新增同名_replacement_v2.json及_geometry.json，
该场景恢复8目标16视角，未改场景或目标数，未使用模型输出来筛选。
prepare_selected_capture.py现核对每个所选视角的实际来源日志（含候补单独捕获），
避免只检查主场景日志而漏掉候补错误。已生成配对job清单并排队在第二场景捕获结束后
使用GPU2；日志/tmp/cviu-fourth-selected-capture-controller.log。
32B缓存本轮检查约44.22GB，仍未完成下载及加载资格。

## 首个正式场景输入通过验收

MVUCSQAKTKJ5EAABAAAAAAY8_usd的最终O/C各16张已完成。新增audit_selected_capture.py
核对两侧终止码、材质日志、输入job/hash、渲染脚本一致、单进程单场景加载、相机参数、
查询、配对顺序、RGB/mask哈希和尺寸；结果无错误，保留转换空mask而不删除样本。

主会话实际打开8份最终四面板检查图（16对/32张图），目标在两侧均可辨，轮廓与取景
一致；可见变化包括反射降低、透明壶身变不透明、地面/墙面材质外观变化。本场景无
转换目标可见性丢失。最终审阅记录final_visual_reviews/MVUCSQAKTKJ5EAABAAAAAAY8_usd.json，
这是本地视觉审阅，不是独立人工审阅。

新增assemble_scene_inputs.py，结合技术审计与最终逐对审阅生成32条输入，记录图片、
mask、receipt、相机层hash，计算中心点及均匀像素基线。实际32条均经formal_inference
的文件校验通过。输出qualified_scene_inputs同名JSON，状态仅qualified_scene_inputs；
仍需收齐30场景后统一冻结，不能用该单场景冒充全局480对或启动正式推理。
make_review_packets.py新增--label-condition用于最终O/C标签；默认旧候选检查图格式不变。

MVUCSQAKTKJ5EAABAAAAAAI8_usd候选8目标31图已逐图检查。7目标提议14视角，
相机间隔30–120度通过；花瓶4视角均过暗，不用轮廓掩码代替视觉可辨性。
新增prepare_replacement_pool.py，保留154个剩余候补的既定次序，生成首个可行cabinet
目标视角，等待第四场景捕获3242345后用GPU2捕获；输出formal_alternate_vase_capture_v1，
日志/tmp/cviu-alternate-vase-controller.log。旧花瓶候选及失败原因保留，场景ID和8目标
正式规模不变。此候补仍待真实图像验收。

MVUCSQAKTKJ5EAABAAAAABA8_usd完成8目标31候选图审阅，16个选中视角方位间隔
30–180度通过；保留果盘实例包含水果的mask定义。洗碗机源标签不能仅凭外观确定，
查询使用under-counter appliance below the window的明确空间指代；不使用可变化颜色。
已准备同序O/C清单，并在花瓶候补捕获3250392完成后使用GPU2。
日志/tmp/cviu-fifth-selected-capture-controller.log。仍待最终配对图验收。

第二个正式场景MV5M25QKTKJZ2AABAAAAAAI8_usd完成16对/32图技术审计和逐对视觉审阅，
组装输入后经formal_inference文件检查通过；暗色托盘、台灯、时钟、咖啡机的WARN说明
保留，未发现转换目标消失。现在2/30场景、32/480对已通过最终输入资格，尚无全局冻结。

首个修复重采场景MVUHL5YKTKJ5EAABAAAAAAI8_usd完成，exit0且无材质编译错误。
实际重新打开8份检查图，原先提议视角仍可用；黑色靠垫v0/v2仍排除。新增_repaired_v2
审阅与相机检查记录，16视角方位间隔30–120度通过，使用新捕获图hash和日志。
已准备第六个场景的配对捕获清单，在第五个场景3251980完成后使用GPU2；
日志/tmp/cviu-sixth-selected-capture-controller.log。旧失败图片及审阅未覆盖。

第三个正式场景MV4AFHQKTKJZ2AABAAAAADY8_usd完成16对32图技术与逐图验收，
最终输入组装及文件校验通过。时钟面颜色、玻璃透明度、反射变化较明显，目标与取景
仍可比，均作为干预结果保留。累计3/30场景、48/480对、96张图合格，尚未全局冻结。
新增report_progress.py，按全部30场景的选择、捕获、审计、审阅和输入清单生成
campaign_status.json；这是文件状态快照，不能替代hash检查或目标完成审计。

MVUCSQAKTKJ5EAABAAAAADI8_usd完成8目标31候选图审阅，7目标14视角可用。
一个目标mask仅选择笔筒里多支相似铅笔中的一支，RGB无法支持跨视角唯一指代，因此
保留失败原因并按既定候补次序从165个剩余目标生成chair替代视角。未用目标掩码轮廓
替代模型原始图中的身份信息。候补捕获等待第六场景3254355完成后用GPU2，输出
formal_alternate_pencil_capture_v1，日志/tmp/cviu-alternate-pencil-controller.log。

## 正式统计入口准备（尚无正式结果）

新增analyze_formal.py，严格要求完整5760条正式预测及960输入，拒绝缺失/重复/运行错误。
从原始回答重新解析点坐标并按真实mask重算hit、bbox、可见性，同时复核中心点/均匀像素
基线，避免只信任缓存分数。输出逐repeat gains/losses及按scene聚合的均值、flip、格式
有效率、同条件repeat差异、条件间/重复点位移、mask支持子集与条件成功/失败率。

10,000次scene-cluster bootstrap，seed20261114，同一scene的对象、视角和重复保留在一起；
模型差异使用同一组场景抽样。条件指标按分子/分母重新汇总，避免把不同支持数的场景
简单平均。零支持指标显式输出undefined，退化bootstrap标记不支持“普遍无效应”主张。
render-repeat控制仍需另外分析，不把cross-condition flips自动归因为材质。

统计/输入契约共7项测试通过，覆盖不等分母、零支持、配对模型抽样、平均抵消但方向翻转
保留、完整队列/错误输入约束。尚未运行正式分析，因为5760预测不存在；测试不是实验结论。

第四个正式场景MVUHLWYKTKJ5EAABAAAAAAI8_usd完成16对32图技术与逐图验收，包含
替换后的毛巾架；组装输入并通过文件校验。记录圆形座椅转换后的分面着色、窗面透明度
与地面外观变化，不将这些变化误作几何位姿变化。累计4/30场景、64/480对合格。

32B held-out资格任务已排队，等待修复候选controller3235644结束、并检查并行下载回执
确认为downloaded，再使用GPU0/1进行BF16加载与pilot推理。队列记录qualification_32b_queue.json，
日志/tmp/cviu-32b-qualification-controller.log。排队不等于权重下载或模型资格通过。

GlassUtils修复后的MVSYCXYKTKJ66AABAAAAACY8_usd完整候选重采exit0，无材质编译错误。
逐图审阅8目标32视角，并额外打开花枝瓶的两张原始全分辨率RGB，避免绿色轮廓掩盖
实际可辨性。7目标14视角可用；blanket源标签的mask同时覆盖地毯与分离茶几，不能当
单个rug目标计分，保留排除记录并按原候补次序从1038项中生成首个可行book候补。
候补捕获在玻璃修复重采3238088结束后使用GPU3，输出formal_alternate_rug_capture_v1；
日志/tmp/cviu-alternate-rug-controller.log。book仍须真实图像/唯一指代验收，不能凭类别通过。

MVUCSQAKTKJ5EAABAAAAAAI8_usd花瓶候补cabinet实际捕获4视角完成，逐张检查后确定为
空调下方高窄搁架。选v1/v2（方位间隔60度），排除只有侧板而看不到搁架结构的v0。
新_replacement_v2记录保留花瓶排除原因，合并原候选与候补job、核对两份来源日志后，
该场景补齐8目标16视角。第七场景配对捕获排队在book候补3265841完成后使用GPU3；
日志/tmp/cviu-seventh-selected-capture-controller.log。

MVSGSAIKTKJ66AABAAAAAEA8_usd（预定render-repeat控制场景）完成8目标30候选视角审阅。
6目标12视角可用，方位间隔30–120度；文件架四视角遮挡/过暗，单支铅笔两视角无法
与近似铅笔唯一对应，二者待替换。按剩余309候补既定次序生成两个pen目标，共8视角，
需实际RGB确认是否可唯一指代，不能因生成成功而验收。捕获等待第七场景3267317后
使用GPU3，输出formal_alternate_office_capture_v1，日志/tmp/cviu-alternate-office-controller.log。
原场景ID与render-repeat控制计划保留，不替换场景。

MWAX5JYKTKJZ2AABAAAAAAA8_usd修复重采候选8目标31视角已逐图检查。
7目标14视角可用；一个目标的四个相机只看到室外全景及漂浮场景块，target mask全空，
因此排除这些原始视角并从142项剩余候补中生成ceiling_light候选4视角。待捕获检查，
未预先认定其可用。捕获等待铅笔替代任务3257830后用GPU2，输出
formal_alternate_outdoor_capture_v1，日志/tmp/cviu-alternate-outdoor-controller.log。

第五个正式场景MVUCSQAKTKJ5EAABAAAAABA8_usd完成16对32图技术与逐图审阅，输入组装
及文件校验通过；玻璃/金属外观、反射和地面材质变化保留。累计5/30场景、80/480对合格。

MVSYCXYKTKJ66AABAAAAACY8_usd的book候补两视角已实际查看：均为上层可见搁板最右侧
直立书，虽同排有重复标题，空间位置可唯一指代。选定查询rightmost upright book on the
upper shelf，不依赖颜色或重复标题。方位间隔30度，补齐8目标16视角，并核对主捕获和
候补捕获两份日志。第八场景配对捕获等待办公候补3270387后用GPU3，日志
/tmp/cviu-eighth-selected-capture-controller.log。仍需最终配对图验收。

MWAX5JYKTKJZ2AABAAAAADA8_usd修复候选8目标31视角逐图检查完成，7目标14视角可用。
一个shelf目标四视角均拍到屋顶/室外结构，不能据绿色mask认定目标可辨；按剩余93项
既定候补次序生成chair四视角，等待室外视角替代任务3272574后用GPU2捕获，输出
formal_alternate_roof_capture_v1，日志/tmp/cviu-alternate-roof-controller.log。

显示设备最初被描述为open laptop；核对源category=monitor及背面视觉歧义后，保留旧记录，
新增该场景_label_corrected_v2.json，将查询更正为computer display on the desk。
后续合并候补必须读取这个修正版，不能沿用初版laptop描述。冰箱选两个不同方位但相同
构图bin的可辨正侧视；另一bin仅见无辨识信息的背面，未为平衡构图而接受无效视图。

第六个正式场景MVUCSQAKTKJ5EAABAAAAAAI8_usd完成16对32图技术与逐图验收，包含替换
花瓶的高窄搁架。保留动物形座凳转换后的高光/着色接缝、金属壶外观和地面变化；目标
轮廓与取景可比，未见转换目标消失。输入组装及文件校验通过，累计6/30场景、96/480对。
本轮32B缓存约52.55GiB，仍有8个incomplete文件；两个下载进程均经ps确认存活，
未取得downloaded回执，32B资格任务继续等待。

第七个正式场景MVUHL5YKTKJ5EAABAAAAAAI8_usd完成16对32图技术与逐图验收，使用修复后
原始材质与最终同序配对捕获。洗手盆转换后的三角形着色、电视反射变化、靠垫布料变化
均保留，目标轮廓和取景可比。输入组装及文件校验通过。累计7/30场景、112/480对合格；
旧材质编译失败捕获仅保留历史记录，不进入本次输入。

办公场景MVSGSAIKTKJ66AABAAAAAEA8_usd的两个pen候补8视角已实际查看。笔筒中那支仍
无唯一指代，排除；桌上两笔中的一支可用“pen lying closest to the closed notebook”
指代，额外打开全分辨率RGB并核对mask连通区域（y288:332、x255:350）对应靠近笔记本
那支，排除另一支。选v0/v1，间隔30度。新增_replacement_v2.json，现7目标可用、缺1。

为减少重复加载，同场景下一批按原候补次序生成8个候选目标、26张原始候选视角；
预先记录candidate_batch_policy.json：只取按顺序首个通过原始图像资格的目标补足1个，
其他候选不用，正式仍为8目标。候选类别chair/chair/pen/pen/pen/pen/table/pen。
捕获等待第八场景3275635结束后用GPU3，输出formal_alternate_office_batch_capture_v2，
日志/tmp/cviu-office-reserve-batch-v2-controller.log；尚未取得任何新增目标资格。

MVUCSQAKTKJ5EAABAAAAADI8_usd的chair候补四视角实际审阅后，选v1/v3（间隔60度）：
两图均为前景餐椅，与背景另一把椅子可区分，查询dining chair in the foreground。
保留原铅笔歧义排除记录，新增_replacement_v2及几何检查；合并两份来源job并核对日志后
补齐8目标16视角。第九场景配对捕获等待屋顶视角替代3278401后使用GPU2，日志
/tmp/cviu-ninth-selected-capture-controller.log。仍待最终配对图验收。

办公场景reserve batch首个chair已逐图查看：v1/v2前景转椅可唯一识别，方位间隔120度。
按事先policy选此首个合格目标，其余7个候选未参与选择。新增_replacement_v3.json，
记录未使用目标和历次歧义排除，补齐8目标16视角；三批来源日志及哈希检查通过。
第十场景配对捕获接续候补batch3303381使用GPU3，之后再独立进程重复同序全量O/C批次，
作为预先指定的render-noise控制之一。队列回执render_control_office_queue.json，
日志/tmp/cviu-tenth-selected-capture-controller.log及/tmp/cviu-office-render-repeat-controller.log。
重复捕获属于辅助诊断，不计入5760主预测；尚待运行、图像差异审计与模型读出比较。

12个KooPbr场景重采全部终止，repaired_material_audit_terminal.json显示0个材质错误场景；
2个GlassUtils场景重采终止日志也为0错误（glass_repaired_material_audit_terminal.json）。
这些是运行时技术资格，不替代目标可见性与最终O/C审阅。

MWAX5JYKTKJZ2AABAAAAAAA8_usd顶灯候补四个正仰角视图都在天花板上方，无法识别灯。
prepare_views.py新增可选--elevations与--view-prefix，默认行为保持原值；为同一顶灯
生成4个负仰角候选，前缀below_v避免与旧视角ID冲突。旧失败图保留。真实USD相机层
回归通过，下面视角仍需渲染确认，不能提前验收。

重采GPU0已释放而32B仍未下载完。核对模型任务无子进程、无输出目录、无下载完成回执后，
将纯等待任务3262134替换为先执行顶灯下方视角3328532、再由3328533等待下载并做32B资格。
未中断任何运行中的模型/渲染。调度记录qualification_32b_queue_v2.json，日志
/tmp/cviu-ceiling-below-view-controller.log与/tmp/cviu-32b-qualification-controller-v2.log。

第八个正式场景MVSYCXYKTKJ66AABAAAAACY8_usd通过16对32图技术与逐图验收，包含替代的
右端直立书。花枝瓶转换后不透明瓶身更明显，两视角可见mask面积增加；未见目标整体
消失。组装输入并通过文件校验。累计8/30场景、128/480对合格。

新增评分区域诊断（正式推理前登记，主指标不变）：同一预测坐标在两条件mask上分别
复算，报告固定原始/转换mask的flip，以及对称的坐标变化/掩码变化评分分量。分量仅为
算术分解，不作为因果机制归因。analyze_formal.py新增cross-mask重算与逐对mask IoU，
全部9项统计/输入契约测试通过，包含“坐标不变但mask变化产生翻转”的回归。
protocol旧版保存为protocol_before_mask_diagnostics.json；新protocol明确主指标仍为
各条件可见mask上的固定480对端到端成功率。没有修改主样本或根据模型结果选择指标。

对当前8个合格场景128对输入实算mask支持差异，只有2对非完全相同，对应上述花枝瓶。
证据mask_support_preinference_v1.json（含输入清单hash）；这是输入审计，不是模型效应。

第九个正式场景MVSGSAIKTKJ66AABAAAAAEA8_usd完成16对32图技术与逐图验收，包含替代的
桌面笔和前景转椅。笔为细小目标，仍可按与合上笔记本的相对位置指代，保留困难度说明。
人物姿态、家具取景与目标身份可比，隔板透明度/反射及服装外观变化保留。输入组装与
文件检查通过。累计9/30场景、144/480对；本场景独立重复渲染控制仍需另外验收。

首个正式render-repeat控制MVSGSAIKTKJ66AABAAAAAEA8_usd完成32张重复图，技术审计通过。
对齐pair_id/condition和camera后逐像素比较：32/32 mask相同，RGB平均MAE 0.517729，
最大1.025647；1张超过预设MAE<=1阈值（original首帧dish v0）。结果标记
REPEAT_DIFFERENCES_REQUIRE_ANALYSIS，不放宽阈值、不把该控制记为全部通过。证据
render_control_office_technical_audit.json与render_control_office_image_comparison.json。
仍须在重复图上进行两模型读出并与主预测比较；这是三场景控制中的一个。

MWAX5JYKTKJZ2AABAAAAAAA8_usd顶灯below_v0/v1实际图像可辨，间隔30度；四张从下方
候选均已打开检查。保留从上方失败的四张图，补齐场景8目标16视角。_replacement_v2
记录相机恢复与排除历史，job使用below_v前缀避免碰撞。第十一场景配对捕获排队在
第九场景3319382后用GPU2，日志/tmp/cviu-eleventh-selected-capture-controller.log。

MWAX5JYKTKJZ2AABAAAAADA8_usd的desk-chair候补四视角已实际检查，选v2/v3，间隔30度，
座面/靠背/椅腿可辨。合并时明确读取_label_corrected_v2，保留computer display而非
laptop描述。新增_replacement_v3，补齐8目标16视角，来源日志与hash检查通过。
第十二场景捕获等待第十一场景3349685后使用GPU2，日志
/tmp/cviu-twelfth-selected-capture-controller.log。候补资格不等于最终图像资格。

32B两个下载调用均返回downloaded；qualification_32b_v1已完成24条held-out预测，
无运行错误，24条坐标格式有效。实核参数分布cuda:0/cuda:1、BF16，无CPU/disk offload；
逐条重新解析回答并在实际mask计分，与存储结果一致，图像/mask hash检查通过。
24条image_grid_thw与8B一致，runner hash及processor图像配置一致；修订号与协议匹配。
结果qualification_32b_v1/qualification_result.json。此24条不计入5760正式预测，
不能据pilot小样本宣称模型容量改善或退化。两模型正式运行资格现已具备。

第十个正式场景MVUCSQAKTKJ5EAABAAAAADI8_usd完成16对32图技术与逐图验收，包含替代
铅笔的前景餐椅。堆叠电器、细口壶、果盘和餐椅在两条件均可指代，亮度/反射及玻璃
外观变化保留。输入组装及文件校验通过。累计10/30场景、160/480对，仍需完整队列冻结。

预定home render-control场景MWBGLKQKTKJZ2AABAAAAACA8_usd完成8目标32候选图审阅，
6目标12视角可用；一个目标仅见室外全景且mask为空，单支pen无法唯一指代。保留失败
记录，从138项候补按既定次序生成8目标批次，实际审阅时只取最先合格的2个补足，
其余不用。捕获使用已结束32B资格任务3328533之后的GPU0空闲时段，输出
formal_control_home_reserve_capture_v1，日志/tmp/cviu-control-home-reserves-controller.log。
本场景仍保留在原30场景及3个重复控制名单中，尚未完成目标补足。

第十一个正式场景MWAX5JYKTKJZ2AABAAAAAAA8_usd通过16对32图技术与逐图验收，包含
从下方观察的顶灯。转换后灯具仍有匹配非空mask，但发光提示消失、外观接近周围天花板。
两条顶灯pair记为mask_supported_emission_cue_lost，保留为有效转换结果，不将技术
通过等同于语义可辨，也不预先将潜在任务失败归为推理错误。
assemble_scene_inputs.py新增visual_target_assessment保存审阅原文分类，不改变评分规则；
早期输入仍可通过其关联final_visual_reviews读取相应记录。全部32输入文件校验通过。
累计11/30场景、176/480对合格。

另一个预定home render-control场景MV7J6NIKTKJZ2AABAAAAADY8_usd完成8目标28候选图审阅。
6目标12视角可用；一个目标全空mask，冰箱仅一张可辨，未用单视角降低正式要求。
从139项剩余候补按既定顺序生成8目标批次，只取前2个通过原始视觉资格的补足。
捕获使用已结束32B资格任务3328533之后GPU1空闲时段，输出
formal_control_home2_reserve_capture_v1，日志/tmp/cviu-control-home2-reserves-controller.log。
该场景及render-repeat控制身份保留，候补尚待真实图像验收。

第十二个正式场景MWAX5JYKTKJZ2AABAAAAADA8_usd完成16对32图技术与逐图验收，包含替换
屋顶错误视角目标的桌边椅。保留computer display的修正描述及背面可见性说明，冰箱
使用不同方位的可辨正侧视。输入组装及文件校验通过。累计12/30场景、192/480对合格。

home控制场景MWBGLKQKTKJZ2AABAAAAACA8_usd候补批次前两项faucet/electriccooker的8张
原始候选已实际打开，均取v0/v1，间隔分别30/90度。按预定顺序恰好补足2个，其余6个
未参与选择。新增_replacement_v2并检查来源日志/hash，补齐8目标16视角。
正式捕获及独立同序O/C重复捕获已排队GPU0，接续候补3365743；队列记录
render_control_home_queue.json，日志/tmp/cviu-home-control-primary-controller.log及
/tmp/cviu-home-control-repeat-controller.log。重复捕获仍需单独验收与模型读出比较。

home2控制场景MV7J6NIKTKJZ2AABAAAAADY8_usd候补前两项book/towel已逐图查看，书取v0/v1，
毛巾取v0/v2，均间隔30度。毛巾v1/v3虽然RGB出现毛巾，但目标mask为空，明确排除。
按预定顺序补足2个，其余6候补未参与选择；_replacement_v2及来源检查通过，8目标16视角齐备。
正式捕获与独立同序重复捕获接续3373455排队GPU1，回执render_control_home2_queue.json，
日志/tmp/cviu-home2-control-primary-controller.log与/tmp/cviu-home2-control-repeat-controller.log。
至此3个预定重复控制场景均有完整目标清单及控制捕获安排，但仍须完成结果验收与模型对照。

MWBGLKQKTKJZ2AABAAAAABI8_usd完成8目标26候选图逐图审阅，6目标12视角可用；一个
目标仅见室外全景，另一个近似结构面板而无法建立物体身份，二者排除并保留记录。
从283项剩余候补按既定顺序生成8目标批次，只取前2个合格目标补足；捕获接续已结束
第十二场景3353156使用GPU2，输出formal_remaining_reserves_abi_capture_v1，日志
/tmp/cviu-remaining-abi-reserves-controller.log。未替换正式场景，仍待候补图像验收。

第十三个正式场景MWBGLKQKTKJZ2AABAAAAACA8_usd通过16对32图技术与逐图验收，包含
替代的水龙头和电饭煲。记录托盘内容物透明度/反射变化、茶几和水龙头表面变化，目标
身份与取景可比。输入组装及文件校验通过。累计13/30场景、208/480对；本场景的独立
重复控制仍需单独比较，不由主捕获验收自动判定通过。

MWAX5JYKTKJZ2AABAAAAAEA8_usd完成8目标30候选图审阅，5目标10视角可用；一个目标
空mask/室外视图、冰箱不足两个可辨视角、单只拖鞋在近似拖鞋中不能唯一指代，三者
排除并保存原因。从77项剩余候补按固定顺序生成8目标批次，只取前3个合格补足；
捕获接续办公重复控制3322609后用GPU3，输出formal_remaining_reserves_aea_capture_v1，
日志/tmp/cviu-remaining-aea-reserves-controller.log。正式场景和8目标×2视角要求不变。

第十四个正式场景MV7J6NIKTKJZ2AABAAAAADY8_usd通过16对32图技术与逐图验收，包含
右端书籍与系带毛巾替代目标。香料罐和锅盖转换后不透明、mask支持面积增加；镜面
反射提示消失，记为mask_supported_reflection_cue_lost并保留，不等同于模型推理错误。
输入组装与文件校验通过。累计14/30场景、224/480对；重复控制需另行比较。

三个预定render-repeat控制的图像比较完成，96/96 mask逐像素相同；办公、home、home2
最大RGB MAE分别1.025647、1.596716、0.754626。总计2/96图超过固定阈值1，均保留为
REPEAT_DIFFERENCES_REQUIRE_ANALYSIS，不调整阈值。两个住宅控制技术审计无错误。
新增compare_render_repeat.py复核实际文件hash、相机/查询/目标和跨运行script/job hash，
按int16像素差避免uint8下溢；重新计算办公控制与原报告数值完全一致。
汇总render_control_image_summary.json。阶段仅IMAGE_COMPARISONS_COMPLETE_MODEL_READOUT_PENDING；
全局输入冻结后仍须在重复图上做两模型读出，不能仅凭像素差宣称模型稳定或不稳定。

纠正历史选择理由：MVSYCXYKTKJ66AABAAAAACY8_usd原blanket/rug候选曾因“mask包含茶几”
被排除。实际二值mask检查显示两张茶几台面中心均为False、地毯面为True；绿线描绘的是
遮挡孔洞，先前包含关系判断错误，现撤回该理由。证据selection_rationale_correction_rug.json
含mask hash、坐标与布尔值，旧记录保留并由该纠错明确覆盖其理由。已选书籍的原始资格与
最终配对资格独立有效，保留既定8目标；地毯改记为未选候选，不能再称为已证实标注无效。
此纠错在正式模型预测之前完成。点检查仅反驳此前包含关系，不声称整张mask完全认证。

MWBGLKQKTKJZ2AABAAAAABI8_usd候补前两项书柜/书籍的候选图已检查，均选v0/v1、间隔
30度。分别以桌后左侧书柜和该排最右直立书指代，补齐8目标16视角；其余6候补未参与
选择。来源日志/hash检查通过，配对捕获接续3402678使用GPU2，日志
/tmp/cviu-abi-selected-capture-controller.log，仍待最终配对图验收。

MWAX5JYKTKJZ2AABAAAAAEA8_usd候补批次前3项目标通过原始图检查：台面下电器v0/v2、
床头桌灯v0/v1、靠近拖鞋的运动鞋v0/v1。单只鞋借与旁边拖鞋的相对位置区分，不使用颜色。
第四把椅子的图已预览但未选，后4项未检查；按顺序前3合格补足，正式8目标16视角不变。
新增_replacement_v2，来源日志和hash检查通过，配对捕获接续3481097使用GPU3，日志
/tmp/cviu-aea-selected-capture-controller.log。尚待最终图像验收。

MVUHL5YKTKJ5EAABAAAAAAA8_usd完成8目标28候选图审阅，均找到2个有效视角，间隔30–120度。
额外打开手表全分辨率原始RGB确认小表盘与表带；blank picture使用framed panel描述，
不臆测画面内容。毛巾架黑色遮挡v0/v1排除，选择可见v2/v3。来源检查通过，直接准备
8目标16对正式捕获，无需候补；接续住宅控制重复3380155使用GPU0，日志
/tmp/cviu-uhl5aaa-selected-capture-controller.log。仍待最终配对图验收。

第十五个正式场景MWBGLKQKTKJZ2AABAAAAABI8_usd通过16对32图技术与逐图验收，包含
左书柜与最右书籍替代目标。烤箱转换后门面和控制细节显著变淡，记录为
mask_supported_appliance_cues_reduced，保留有效转换，不预先当模型推理缺陷。
输入组装与文件校验通过。累计15/30场景、240/480对合格，仍未做正式模型推理。

第十六个正式场景MWAX5JYKTKJZ2AABAAAAAEA8_usd通过16对32图技术与逐图验收，包含
台下电器、床头桌灯、靠近拖鞋的运动鞋三个替代目标。洗手盆低对比说明、灯罩透明度变化
保留；目标取景与身份可比。输入组装及文件检查通过。累计16/30场景、256/480对合格。

新增freeze_formal_inputs.py，要求恰好原冻结30场景，逐场验证最终审阅/技术审计/捕获回执/
相机层/图像mask的hash与身份链、原始与转换场景root对既有全buffer几何审计的hash链，
并绑定协议、场景清单和选择理由纠错sidecar。补齐早期行缺少的visual_target_assessment，
不改图像/查询。最后调用正式结构与文件校验，只有960条件输入齐全才写frozen_formal_inputs。

6项冻结与输入契约测试通过，覆盖缺场景、替换场景、重复/未资格输入及固定场景顺序。
对当前真实16个合格场景实际调用CLI，正确拒绝不完整队列且未生成冻结文件；证据
freeze_scope_validation_initial.json。此检查不把16场景当作正式全量，也不代表后续完整冻结已完成。

第十七个正式场景MVUHL5YKTKJ5EAABAAAAAAA8_usd通过16对32图技术与逐图验收。小手表
及高亮毛巾架的困难度说明保留，毛巾架转换图记录visible_low_contrast；水壶透明度和
反射变化仍作为有效干预结果。输入组装及文件校验通过。累计17/30场景、272/480对合格。

MWBGLKQKTKJZ2AABAAAAABA8_usd完成8目标29候选图审阅，各选2有效视角，间隔30–90度。
电视极端侧视及凳子被挡空mask视角排除；冰箱斜视类别提示弱，用tall appliance beside
 the glass doors作空间指代并保留WARN。无需候补，来源检查通过，配对捕获接续住宅2
重复3383468使用GPU1，日志/tmp/cviu-wbglaba-selected-capture-controller.log。

MV7J6NIKTKJZ2AABAAAAAEA8_usd完成8目标31候选图审阅，6目标12视角可用；两目标仅见
室外/遮挡场景或微小残余mask，均排除。从200项候补按固定顺序生成8目标批次，仅取
前2个合格补足。化妆用品使用cosmetics set指代整个安排，不误称单瓶；屏幕不依赖具体
时间数字作查询。捕获接续3634641使用GPU3，输出formal_remaining_reserves_v7aea_capture_v1，
日志/tmp/cviu-v7aea-reserves-controller.log。场景ID和8×2正式要求保持不变。

该候补生成尚在运行时，第一次排队尝试因jobs.json未生成而退出，没有启动渲染；随后等待
原生成进程明确exit0、8目标完整后再排队成功。未重启或覆盖仍在运行的生成任务。

正式推理入口新增render_control模式：仅接受完整30场景主manifest绑定的3个指定控制
场景、96条辅助输入，核对主文件hash、协议hash、pair/目标/视角/查询身份及独立捕获
路径，固定repeat0种子；主分析仍拒绝非formal行，辅助预测不进入5760计数。
新增assemble_render_controls.py从重复技术审计和冻结主输入构造辅助manifest，重算mask
统计和基线；即使像素MAE超阈值也保留控制图像，不按结果筛选。必须先有完整主冻结。

共14项输入契约、冻结及统计测试通过，覆盖控制身份漂移、错误主图绑定、复用主捕获和
不完整主队列；真实pilot的24条validate-only仍通过。生成模型调用路径未改，当前仅新增
前置验证及模式记录。尚未生成全局控制manifest或运行辅助模型预测，等待30场景冻结。


### MWBGLKQKTKJZ2AABAAAAABA8 final input qualification

- Completed technical audit of 16 final O/C pairs with no errors; locally opened all eight four-panel review sheets (Codex review, not independent human review).
- Television, lower oven, coffee table, cooktop, tall appliance, kettle, lidded frying pan and stool retained. Converted oven interior/display cue loss, reduced transparency/reflections, lost marble pattern and stool shading boundary remain intervention observations, not exclusion criteria. Narrow second appliance view retains its original qualification caveat.
- Evidence: `paper/shared/evidence/raw/cviu_formal/v1/final_visual_reviews/MWBGLKQKTKJZ2AABAAAAABA8_usd.json` and corresponding `qualified_scene_inputs` file. `audit_selected_capture.py`, `assemble_scene_inputs.py`, and independent `formal_inference.validate_files` checks passed (32 image/mask records).
- `report_progress.py` now reports 18/30 qualified scenes, 288/480 pairs. Global freeze and 5,760 primary predictions remain outstanding; no model-performance conclusion follows from input qualification.
- MV7J6NIKTKJZ2AABAAAAAEA8 reserve capture has all 28 records; original-only reserve review is the next pending selection task.


### MV7J6NIKTKJZ2AABAAAAAEA8 reserve qualification and paired dispatch

Reviewed the first three reserve candidates in frozen order. Curtain and leaning book each provide two identifiable original views; intervening toilet candidate has exterior views and no identifiable target (0/24/0/0 mask pixels). Remaining five candidates were not used after the two required replacements qualified. Pendant-light occlusion in curtain view is retained; query identifies the left dining-area window curtain.

Saved `_with_reserves.json`, `_reserve_decisions.json` and `_with_reserves_geometry.json` in `original_visual_reviews`. Eight-target identity/hash and minimum-30-degree checks passed; all selected candidate runtime logs passed material checks and exit markers. Prepared 16 matched O/C jobs. GPU 0 was verified at 0 MiB before dispatch; controller 3857108 runs final capture, log `/tmp/cviu-v7aea-selected-capture-controller.log`. Final visual qualification remains pending.


### MVUHLWYKTKJ5EAABAAAAACQ8 original qualification and dispatch

Opened all eight original candidate sheets (31 frames), using local Codex visual review, not independent human review. Original runtime log has zero matched material errors and terminal exit 0. All eight initial targets retained: television, countertop oven, wire fruit basket, round tray with tea set, wooden armchair, cooktop, dark glass vase and faucet. Selected television v1/v2, oven v0/v2, cooktop v1/v2, and v0/v1 for other targets. Vase low contrast/transparency and partial occlusion are documented caveats, not converted-image selection.

Original review and geometry report saved under `original_visual_reviews/MVUHLWYKTKJ5EAABAAAAACQ8_usd*.json`. Identity/hash and separation checks passed (30,90,30,120,60,30,90,180 degrees). `prepare_selected_capture.py` passed with 16 O/C pairs. GPU 1 dispatch controller 3858406; log `/tmp/cviu-uhlwacq-selected-capture-controller.log`. Final capture/visual acceptance still pending.


### MWAX5JYKTKJZ2AABAAAAADQ8 original qualification and paired dispatch

Opened all eight sheets from the repaired original capture (31 frames), local Codex review, not independent human review. Repaired capture exit 0 and zero matched material errors. All eight initial targets retained. Microwave v0/v2 are occluded by wall with empty masks; selected v1/v3 have a 30-degree azimuth difference. Cooktop v1/v2 avoid foreground microwave occlusion. Other targets use v0/v1: coffee table, grey wingback armchair, refrigerator, tall potted plant, electric kettle and under-counter appliance. Query aliases correct the source oven/pot labels; under-counter appliance described by visible ribbed front rather than asserting an uncertain functional category.

Review and geometry saved to `original_visual_reviews/MWAX5JYKTKJZ2AABAAAAADQ8_usd*.json`; separation, source image/hash and runtime-log checks passed. Prepared 16 matched O/C pairs. GPU 2 was at 1 MiB before dispatch, with vacancy rechecked by runner. Controller 3859760, log `/tmp/cviu-axadq-selected-capture-controller.log`; final capture and visual acceptance remain pending.


### MVUHLWYKTKJ5EAABAAAAAAY8 original qualification and dispatch

Locally inspected eight original sheets (28 frames), not independent human review. Source log has zero matched material errors and exit 0. Retained television, lower stacked oven, two-drawer bedside cabinet, desk lamp, cooktop, refrigerator, dark vase and open-frame wall clock. Cabinet uses v1/v2 to avoid curtain occlusion; remaining targets v0/v1. Low-contrast vase/clock and reflective refrigerator caveats retained. Source category aliases refined using visible object identity.

Review and geometry JSON saved under `original_visual_reviews/MVUHLWYKTKJ5EAABAAAAAAY8_usd*.json`. Hash/identity, eight-target and camera-separation checks passed. Prepared 16 O/C pairs; GPU 3 was 1 MiB before dispatch, controller 3861218 logs to `/tmp/cviu-uhlwaay-selected-capture-controller.log`. The three preceding capture controllers were verified live and their original logs showed Simulation App Startup Complete; no restart was attempted merely because no progress.json existed yet. Final QA remains pending.


### MVUHLWYKTKJ5EAABAAAAADA8 original qualification and queued dispatch

Opened all eight original sheets (29 frames), local Codex review, not independent human review. Original log has zero matched material errors and exit 0. All initial targets retained: television, lower stacked oven, brown armchair, cooktop, refrigerator, bathroom washbasin, white electric kettle and two-handled pan. Cooktop v0/v2 avoid cabinet-edge occlusion; others v0/v1. Query aliases distinguish kettle from source pot label. Narrow refrigerator view retained as identifiable.

Review/geometry records saved under `original_visual_reviews/MVUHLWYKTKJ5EAABAAAAADA8_usd*.json`; all eight target hash/identity and minimum-30-degree checks passed. Prepared sixteen O/C pairs. Queued controller 3862504 for GPU 0 after controller 3857108, followed by memory vacancy check; log `/tmp/cviu-uhlwada-selected-capture-controller.log`. Queue creation does not imply image capture has started. Final capture and visual acceptance remain pending.


### MWF4WLIKTIFZIAABAAAAACI8 original review and reserve queue

Opened eight original candidate sheets (31 frames), local Codex review, not independent human review. Original capture exited 0; runtime log has zero matched material errors. Seven targets have two qualified, geometrically separated views: turquoise oven v2/v3, refrigerator v0/v1, clock v1/v2, tan sofa v0/v1, speckled bowl v0/v1, tissue box v0/v1, black microwave v0/v2. The book candidate is a thin slab beneath mugs and its book identity cannot be established visually; no two views selected. This is category ambiguity, not a claim of mask contamination.

Saved review and geometry (expected incomplete eight-target gate). Prepared first eight remaining reserves in frozen order: chair, cup, pen, plant, trashcan, pen, chair, curtain. Policy fixed before render review: take first qualifying target only; others unused. `prepare_views.py` completed successfully. Original-only batch has 30 frames; controller 3864274 queues GPU 1 behind paired-capture controller 3858406, log `/tmp/cviu-f4aci-reserves-controller.log`. This scene is not counted as fully selected or final-qualified.


### MWF4WLIKTIFZIAABAAAAADI8 original qualification and queued dispatch

Opened all eight original sheets (32 frames), local Codex review, not independent human review. Original log has zero matched material errors and exit 0. Retained mouse, keyboard, telephone, transparent drinking glass, microwave, white vase, wristwatch and seated woman. Microwave uses v0/v2 to retain front cues; others v0/v1. Small mouse/watch and transparent-glass visibility caveats retained without model-guided filtering. Source clock label corrected to wristwatch in query; seated person distinguished from standing figures.

Saved original review and geometry JSON. Eight-target image/hash/identity and minimum-30-degree checks passed; prepared 16 O/C pairs. Controller 3865732 queued on GPU 2 behind 3859760, followed by vacancy check; log `/tmp/cviu-f4adi-selected-capture-controller.log`. Final image capture and QA remain pending.


### MWF4WLIKTIFZIAABAAAAADQ8 original review and reserve queue

Opened eight original sheets (29 frames), local Codex review, not independent human review. Source log: zero matched material errors, exit 0. Six targets qualified: faucet, wall time screen, beverage display cabinet, checkout sign, shopping cart and pedal bin, each v0/v1. Source picture query corrected to checkout sign. Microwave has only one clearly identifiable front view; bottle heavily occluded among similar products in one of only two candidates. Both require replacements; decisions use originals only.

Saved review/geometry (expected incomplete eight-target gate). Prepared first eight eligible reserves in frozen order, all bottles; no category substitution to accelerate success. Policy fixed before RGB review: first two qualifying targets, others unused. `prepare_views.py` completed. Original batch 23 frames queued via controller 3867924 on GPU 3 after 3861218; log `/tmp/cviu-f4adq-reserves-controller.log`.

Also audited completed final captures MV7J6NIKTKJZ2AABAAAAAEA8 and MWAX5JYKTKJZ2AABAAAAADQ8: sixteen pairs each, errors empty. Their final visual acceptance remains pending; not yet added to qualified count.


### MV7J6NIKTKJZ2AABAAAAAEA8 final input qualification

Opened all eight final O/C four-panel sheets (six initial targets plus reserve curtain/book), local Codex review, not independent human review. All original views remain qualified and O/C framing comparable. Converted desk/table/cooktop surfaces lose dark reflective appearance; cooktop low contrast against counter retained. Window exterior cues disappear, monitor reflections diminish, and cosmetics/mouse background contrast changes. No full target disappearance observed.

Saved `final_visual_reviews/MV7J6NIKTKJZ2AABAAAAAEA8_usd.json` and corresponding 32-row `qualified_scene_inputs` manifest. Technical audit previously passed; `assemble_scene_inputs.py` and independent `formal_inference.validate_files` both passed. Final sheets stored in `formal_v7aea_final_review_packets_v1` and bound by hashes. Nineteen scenes / 304 pairs now qualified; global freeze and model inference remain outstanding.


### MWAX5JYKTKJZ2AABAAAAADQ8 final input qualification

Opened all eight final four-panel sheets (16 pairs), local Codex review, not independent human review. Original qualification preserved and paired framing comparable. Converted adjacent glass doors become opaque; table marble pattern, metal reflections and kettle transparency reduced. Under-counter appliance loses the ribbed-front cue named in the original-fixed query: explicitly retain this cue-loss case, without query rewriting or C-based exclusion. Plant remains dark/low-contrast. No full target disappearance observed.

Saved final visual review with packet/image hashes and 32-row scene-input manifest. Technical audit, `assemble_scene_inputs.py` and independent `formal_inference.validate_files` passed. Sheets in `formal_axadq_final_review_packets_v1`. Twenty scenes / 320 pairs now qualified; global freeze and model predictions remain outstanding.


### MV5M25QKTKJZ2AABAAAAAAY8 repaired original qualification and queue

Opened all eight sheets (30 original frames) from GlassUtils-repaired capture; local Codex review, not independent human review. Repaired source runtime log: zero matched material errors, exit 0. Retained basket, dome desk lamp, white pitcher, waiting-area sofa, toilet, curved reception counter, information screen and consultation monitor. Sofa v1/v2 avoid stronger foreground-chair occlusion; monitor v1/v3 cover recognizable back and front with 180-degree separation. Other targets v0/v1. Partial person/foreground occlusions retained.

Saved original review and geometry JSON. Eight-target identities/image hashes and camera separation checks passed; prepared 16 O/C pairs. Controller 3872673 queued on GPU 0 behind 3862504, with vacancy check after dependency; log `/tmp/cviu-v5aay-selected-capture-controller.log`. Scene is selected but not final-qualified.


### MWF4WLIKTIFZIAABAAAAAEA8 original qualification and queue

Locally inspected all eight original sheets (31 frames) plus raw RGB frame 028 to identify the small brown writing implement without green contour. Not independent human review. Original runtime log has zero matched material errors and exit 0. Retained arched desk clock v1/v2 (dark face without readable markings), kettle v0/v2, microwave v0/v2, pedal bin v0/v1, wire file organizer v1/v2, laptop v0/v1, potted plant v0/v1 and small brown pencil v0/v1. Small-object/partial-occlusion caveats retained.

Saved review and geometry JSON; eight-target identity/image hash and azimuth separation checks passed. Prepared 16 O/C pairs. Controller 3874960 queued GPU 2 behind 3865732 with vacancy check; log `/tmp/cviu-f4aea-selected-capture-controller.log`. Selected only, pending final recapture and QA.


### MWF4WLIKTIFZIAABAAAAACY8 original review and reserve queue

Opened eight original sheets (30 frames), local Codex review, not independent human review. Source exit 0 and zero matched material errors. Six targets qualified: kettle v0/v1, microwave v0/v2, display refrigerator v0/v2, two-tier table v0/v1, right-hand wall time screen v0/v1, metal bin v0/v2. Keyboard is invisible with empty masks in all three candidate frames. Checkout counter has only one identifiable view; other views are severely occluded among repeated bases. Original-only replacements required for these two targets.

Review/geometry saved (expected incomplete gate). `prepare_views.py` completed first eight eligible reserves in fixed order: bottle, bottle, bottle, bottle, box, bottle, bottle, bottle. Policy fixed before RGB review: take first two qualifying targets. Batch 30 original frames queued via controller 3878853 on GPU 1 after 3864274; log `/tmp/cviu-f4acy-reserves-controller.log`.

Four completed final captures technically audited with empty errors: MVUHLWYKTKJ5EAABAAAAACQ8, MVUHLWYKTKJ5EAABAAAAAAY8, MVUHLWYKTKJ5EAABAAAAADA8 and MWF4WLIKTIFZIAABAAAAADI8 (64 pairs total). Preparing final sheets under `formal_pending4_final_review_packets_v1`; visual review pending, no increase to qualified count yet.


### MVUHLWYKTKJ5EAABAAAAACQ8 final input qualification

Opened all eight final four-panel sheets (16 pairs), local Codex review, not independent human review. Original qualification and matched framing retained. Converted vase loses transparency and becomes striped grey; original-fixed dark-glass query unchanged. Faucet remains visible while neighboring sink displays repeated stripe-like appearance and window becomes opaque. Television/oven/tray reflections diminish; basket remains low-contrast on darker converted background. All retained as intervention appearances, not C-based exclusions.

Saved final review with packet/image hashes and 32-row scene-input manifest. Technical audit, `assemble_scene_inputs.py`, and independent `formal_inference.validate_files` passed. Sheets bound from `formal_pending4_final_review_packets_v1`. Twenty-one scenes / 336 pairs now qualified; full model inference still pending global freeze.


### MVUHLWYKTKJ5EAABAAAAAAY8 final input qualification

Opened eight final four-panel sheets (16 pairs), local Codex review, not independent human review. Original target qualification retained; paired framing comparable. TV/oven/refrigerator reflections diminish, windows become opaque, cabinet shading and neighboring bedding change, vase gains visible stripes. Thin open-frame clock and dark vase remain low-contrast cases; no C-based exclusion and no full target disappearance observed.

Saved final review and 32-row qualified scene manifest; technical audit, assembly and independent `formal_inference.validate_files` passed. Packet hashes bind `formal_pending4_final_review_packets_v1`. Twenty-two scenes / 352 pairs qualified; full 30-scene freeze and all formal model runs remain outstanding.


### MVUHLWYKTKJ5EAABAAAAADA8 final input qualification

Opened eight final four-panel sheets (16 pairs), local Codex review, not independent human review. Original target qualification and paired framing retained. Converted white kettle becomes grey-speckled with pale rectangular patch; original white-kettle query unchanged. Pan lid becomes opaque light grey. Oven/refrigerator control and reflection details change; washbasin highlights and wall reflections diminish. No full target disappearance observed and no converted-appearance filtering.

Saved final review with packet/image hashes and 32-row scene-input manifest. Technical audit, assembly and independent `formal_inference.validate_files` passed. Twenty-three scenes / 368 pairs qualified; full model inference remains pending global freeze.


### MWF4WLIKTIFZIAABAAAAADI8 final input qualification

Opened all eight final four-panel sheets (16 pairs), local Codex review, not independent human review. Original qualification and matched framing retained. Transparent glass becomes opaque grey; microwave door loses interior cues; background screen contents disappear. Small mouse/watch remain visible. Seated figure pose is retained while clothing/skin shading and neighboring plant/table appearance change. No full target disappearance observed; converted cue losses remain in evaluation.

Saved final review and 32-row scene-input manifest. Technical audit, assembly and independent `formal_inference.validate_files` passed. Twenty-four scenes / 384 pairs now qualified; full cohort freeze and model predictions remain outstanding.


### MV7J6NIKTKJZ2AABAAAAADQ8 repaired original review and reserve queue

Opened eight repaired-original sheets (30 frames), local Codex review, not independent human review. Repaired runtime log has zero matched material errors and exit 0. New `_repaired.json` review supersedes pre-repair qualification without overwriting historical review. Seven targets qualify with v0/v1: wall screen, woven basket, coffee table, mouse, monitor, cooktop, refrigerator. Under-counter appliance has empty masks in v0/v1 and only v2 identifiable, requiring one replacement. Refrigerator v2 is also empty and remains unselected.

Saved repaired review/geometry (expected incomplete gate). Prepared eight reserves in fixed order: trashcan, towel, chair, trashcan, picture, towel, chair, shoe. Policy fixed before RGB review: take first qualifying target. `prepare_views.py` completed, 32 original frames queued via controller 3890663 on GPU 3 after 3867924; log `/tmp/cviu-v7adq-reserves-controller.log`.

Checked prior reserve batches: f4aci 30/30, f4adq 23/23 and f4acy 30/30 records, each terminal exit 0. Their original-only visual reviews are pending; no rerenders requested.


### MWF4WLIKTIFZIAABAAAAACI8 reserve selection and paired dispatch

Inspected first reserve chair sheet, local Codex review, not independent human review. Selected v0/v1 show the near-end meeting-table swivel chair with back, arms and wheel base; positional query distinguishes neighboring chairs. Remaining seven reserves unused per fixed first-qualified policy. Original reserve log has zero matched material errors and terminal exit 0.

Saved `_with_reserves.json`, `_reserve_decisions.json` and `_with_reserves_geometry.json`. Eight-target identity/hash and minimum-30-degree checks passed. Merged original/replacement jobs and prepared sixteen matched O/C pairs. Controller 3892708 queued GPU 1 behind 3878853 with vacancy check; log `/tmp/cviu-f4aci-selected-capture-controller.log`. Twenty-seven scenes now selected, pending final paired recapture/QA for this scene.


### MWF4WLIKTIFZIAABAAAAADQ8 reserve selection and paired dispatch

First two reserves qualify: rightmost wine bottle on wooden shelf and leftmost cylindrical container on lower shelf, each v1/v2 (30 degrees). Queries identify spatial endpoints, without claiming product identity from blurred labels. Second target dimness retained. First four sheets opened in batch, but candidates 3/4 were not used in selection and all six candidates after the first two remain unused per fixed policy. Review local Codex, not independent human review. Reserve log: zero matched material errors, exit 0.

Saved `_with_reserves.json`, `_reserve_decisions.json`, geometry report and merged jobs. Eight-target identity/hash and separation checks passed; prepared sixteen O/C pairs. Controller 3895480 queued GPU 3 behind 3890663, with vacancy check; log `/tmp/cviu-f4adq-selected-capture-controller.log`. Twenty-eight scenes selected; final capture/QA pending for this scene.


### MWF4WLIKTIFZIAABAAAAACY8 reserve selection and paired dispatch

Reviewed reserve sequence locally (Codex, not independent human review). First bottle qualifies with v1/v2 using second-from-left position in pale-labelled front row; low contrast retained. Second red-labelled repeated bottle lacks unambiguous row-end reference across views; third bottle nearly merges with dark background. Fourth candidate qualifies as third can from left in top front row, v0/v1. Fifth sheet opened incidentally but unused; remaining four candidates unused per first-two-qualified rule. Source reserve log zero matched material errors, exit 0.

Saved combined review, reserve decisions, merged jobs and geometry report. Eight-target identity/hash and minimum-30-degree checks passed; prepared sixteen paired views. Controller 3897896 queues GPU 1 behind 3892708 with vacancy check; log `/tmp/cviu-f4acy-selected-capture-controller.log`. Twenty-nine scenes selected; this scene still requires final capture and QA.


### MV7J6NIKTKJZ2AABAAAAADQ8 final reserve selection; all scenes selected

Reserve capture completed 32 frames, exit 0, zero matched material errors. Opened first reserve bin sheet locally (Codex, not independent human review); v0/v1 show identifiable bin beside desk chair, 30-degree separation. Remaining seven candidates unused per fixed first-qualified rule.

Saved combined repaired-plus-reserve review, reserve decisions, merged jobs and geometry report. All eight target identity/hash and azimuth checks passed; sixteen paired final views prepared. Controller 3900316 queues GPU 3 behind 3895480 with vacancy check; log `/tmp/cviu-v7adq-selected-capture-controller.log`. All 30 frozen cohort scenes now have eight original-qualified targets and sixteen selected pairs. This is selection completion only: remaining final recaptures/QA, global freeze, 5,760 primary predictions, auxiliary render controls and statistical/claim reports are still required.


### MV5M25QKTKJZ2AABAAAAAAY8 final input qualification

Completed technical audit (16 pairs, errors empty) and locally opened all eight final four-panel sheets; Codex review, not independent human review. Original qualification and framing retained. Dome lamp becomes dark matte, countertop/reception counter lose reflections, curtain becomes opaque blue, and glass cabinet surfaces become grey. Existing person/foreground occlusions retained, no full target disappearance observed.

Saved final review with image/packet hashes and 32-row scene-input manifest. `audit_selected_capture.py`, assembly, and independent `formal_inference.validate_files` passed. Sheets under `formal_v5aay_final_review_packets_v1`. Twenty-five scenes / 400 pairs qualified; all 30 selected but global freeze and formal model runs remain outstanding.


### MWF4WLIKTIFZIAABAAAAAEA8 final input qualification

Technical audit passed (16 pairs, errors empty); locally opened all eight final four-panel sheets, not independent human review. Original qualification retained with comparable O/C framing. Converted kettle becomes speckled, microwave gains linear side patterns and opaque door, laptop screen becomes white, desk clock housing darkens. Small writing implement remains visible with partial occlusion and changed organizer contrast. All converted appearance changes retained; original queries unchanged.

Saved final visual review and 32-row scene manifest, bound to sheets in `formal_f4aea_final_review_packets_v1`. Assembly and independent `formal_inference.validate_files` passed. Twenty-six scenes / 416 pairs qualified; all thirty scenes selected. Remaining final capture/QA, freeze, model runs and analysis remain outstanding.


### MWF4WLIKTIFZIAABAAAAACI8 final input qualification

Technical audit passed (16 pairs, no errors); all eight final sheets locally inspected (Codex, not independent human review). Original qualification and paired framing retained. Reserve near-end chair remains identifiable by table position/wheel base, with shell changing dark reflective to light matte. Oven/microwave fronts become opaque, water bottle turns light blue, windows/wall reflections change. Bowl pattern and tissue-box grid persist. Converted appearance changes retained with fixed original queries.

Saved final review and 32-row scene-input manifest bound to `formal_f4aci_final_review_packets_v1`. Assembly and independent file/mask validation passed. Twenty-seven scenes / 432 pairs qualified; all thirty selected. Three final scene acceptances plus global freeze/model runs/analysis remain outstanding.


### MWF4WLIKTIFZIAABAAAAADQ8 final input qualification

Technical audit passed for sixteen pairs; locally opened eight final sheets (Codex, not independent human review). Original target qualification and framing retained, including two reserves identified by shelf endpoints. Converted beverage cabinet panes become opaque and sign emission diminishes; checkout counter becomes opaque; faucet/sink/wall reflections reduce. Rightmost wine bottle remains clear, leftmost cylindrical container stays dim with blurred label. No converted-driven exclusion.

Saved final review and 32-row manifest with packet/image hashes. Assembly and independent file/mask validation passed. Twenty-eight scenes / 448 pairs qualified. Last two scene acceptances, global freeze, formal/auxiliary inference and analysis remain required.


### MWF4WLIKTIFZIAABAAAAACY8 final input qualification

Technical audit passed (sixteen pairs, no errors). Opened all eight final four-panel sheets, local Codex review, not independent human review. Confirmed ordinal reserve queries: second bottle from visible left front-row end and third can from left in top front row. Original qualification and paired framing retained. Converted metal bin nearly black, bottle gains grey shoulder/base, display refrigerator panes become opaque, kettle level window loses transparency; table/floor darken. No converted-based exclusion or full target disappearance.

Saved final review and 32-row input manifest, with packet/image hashes. Assembly and independent file/mask checks passed. Twenty-nine scenes / 464 pairs qualified; last residential capture/QA and global freeze/model runs/analysis remain outstanding.


### Final residential acceptance and full-cohort freeze

MV7J6NIKTKJZ2AABAAAAADQ8 final capture terminated successfully with 16 original and 16 converted frames. Technical audit errors empty. Opened all eight final sheets locally (Codex, not independent human review); original qualification and paired framing retained. Screen image disappears, coffee-table marble pattern lost, basket/towel shading changes and metal reflections diminish. Reserve bin remains identifiable. Saved final visual review and qualified scene manifest.

`freeze_formal_inputs.py --raw paper/shared/evidence/raw/cviu_formal/v1 --out paper/shared/evidence/raw/cviu_formal/v1/manifest.json` completed successfully: all 30 frozen scenes, 480 pairs, 960 condition inputs. Freeze checks bind source geometry/root hashes, current RGB/masks, capture receipts, final audits/reviews, protocol and correction sidecars. Primary manifest SHA256: `1efcbeb7cc37f1d29ccb38eae7ff5607d222d23cd051f878e0c91a1231dc8854`. This completes input preparation, not the active research goal. 5,760 primary predictions and 192 auxiliary render-control predictions, statistical analysis, old-protocol comparison and CVIU claim report remain outstanding.


### Frozen auxiliary controls and formal campaign dispatch

`assemble_render_controls.py` bound all 96 auxiliary repeated-render images to the frozen primary manifest and three preselected repeat audits. All repeats retained, including previously documented two RGB-MAE threshold exceedances. Auxiliary predictions remain separate from the 5,760 primary predictions.

Added `run_formal_campaign.py`: each model runs three independent formal inference processes (repeat 0/1/2, 960 records each), followed by one repeat-0 auxiliary process (96 records). Controller binds runner/manifest/protocol/cohort hashes, uses exclusive output directories, stops on subprocess or completion failure and preserves partial outputs. Controller syntax check passed; existing freeze, inference-contract and clustered-statistics tests: 14 passed.

Verified all four GPUs idle before dispatch. Remote durable controllers on dsw-4090: 8B PID 3471792 on GPU 0; 32B PID 3471805 on GPUs 1,2. Both verified live after dispatch and campaign receipts show formal_repeat0 running. Outputs under `formal_model_runs_v1/{8b,32b}`, durable dispatch record `raw/cviu_formal/v1/formal_campaign_dispatch.json`. Frozen checkpoint revisions, BF16, greedy decoding, no offload and identical prompt/preprocessing contract preserved. No formal result claimed before complete outputs and analysis.


### Live formal inference prefix validation

Verified remote controllers 3471792 and 3471805 live. First repeat outputs checked against frozen identities/query/image/mask hashes; raw point parsing and mask hits recomputed for all complete lines captured in this snapshot: {'8b': 360, '32b': 112}. Shared image preprocessing grids agree on 112 common inputs. Both runners and manifest hashes agree; actual floating parameters BF16, 8B on cuda:0 and 32B on cuda:0/cuda:1 (physical GPU 0 versus 1,2 by process visibility). No runtime errors in checked prefixes.

Durable evidence: `raw/cviu_formal/v1/formal_early_prefix_audit.json`. This is a live-prefix contract check, not a completion/performance result; remaining formal and auxiliary runs continue unchanged.


### Render-control analysis implementation while inference continues

Added `analyze_render_controls.py` to compare 96 repeated-render inputs per model against the corresponding primary repeat-0 predictions. Requires complete successful primary and control outputs, frozen input/protocol identity, matching seed/revision/runner/processor/generation configuration and image grids. Recomputes raw response parsing, mask hit, bounding-box hit and visibility from actual masks. Reports per-scene and per-condition render-repeat flips, gains/losses, validity changes, raw response changes and displacement with explicit valid-point denominator; reports material O/C changes in primary and repeated renders on the same three scenes. Descriptive three-scene scope only, no inference to all 30 scenes or causal subtraction.

`tests/test_cviu_render_control_analysis.py`: 3 passed, covering canceling gains/losses, invalid-coordinate displacement denominators and rejection of runtime-failed runs. CLI help also checked. No analysis results generated yet because live inference is incomplete. Bound inference runner and frozen protocol were not edited. Remote controllers 3471792/3471805 verified live at turn start.


### Legacy ICLR protocol comparison prepared during inference

Read actual ICLR grounding/method/mechanisms/navigation sections and corrected `analysis_v1/results.json`. Saved `legacy_protocol_comparison.md` and `.json` under formal raw evidence, with source hashes and frozen-input baseline counts. Distinguishes 16-query two-view boards, 30-pair readout/raster experiments, stochastic decoding repetitions and 99 navigation pairs from current 480-pair single-view scene-clustered greedy 8B/32B experiment. Documents changed-image caveats already present in historical analysis. No numerical cross-protocol model improvement claim made.

Verified controllers live. 8B repeat0 has 960 rows and repeat1 is underway; 32B repeat0 continues. Full statistics and evidence-supported claims remain pending.


### Full frozen-mask support audit and first complete run validation

Checked actual hashes/binary masks for all 480 frozen O/C pairs. `mask_support_full_frozen.json`: 7 changed-support pairs in 3 scenes; no empty original or converted masks. Minimum mask IoU 0.6113753019323671. Remaining 473 pairs have identical binary support, which does not imply unchanged visual evidence. Planned fixed-mask cross-scoring and symmetric arithmetic decomposition must retain all seven changed cases rather than treat their scoring changes automatically as prediction changes.

Fully validated 8B formal repeat0: 960 successful records, exact expected identities/input hashes, completion marker, protocol/manifest metadata; independently recomputed raw point parsing, mask hits, bbox hits and visibility. Receipt: `formal_8b_repeat0_integrity.json`. This verifies one primary run only. Both remote controllers 3471792/3471805 verified live; 8B repeat1 and 32B repeat0 continue. No final capacity or significance conclusion yet.


### Formal statistical entry now verifies run provenance

Added `verify_run_metadata` to `analyze_formal.py`: require six distinct complete 960-row runs, exact frozen manifest/protocol, specified revisions/seeds, BF16 and GPU placement, matching runner snapshots/software/processor configurations, checkpoint config snapshot hashes and prediction model/repeat identities. This closes the gap where row-level scores alone could pass despite a mismatched run configuration. No bound inference files or protocol changed.

Statistics/control tests: 10 passed, including new seed/precision drift rejection. Actual completed 8B repeat0/repeat1 pass all metadata checks and are correctly rejected as an incomplete six-run cohort. Remote controllers 3471792/3471805 confirmed live; no partial model comparison emitted.


### Reviewer tracker synchronized with formal evidence

Updated CVIU `REVIEW_RESPONSE_TRACKER.md` current status and added E9 links for frozen primary/control inputs, dispatch, full mask audit, legacy protocol comparison and implementation record. Z04/G04/G06/H03/H04/H06/H12 remain partially complete with explicit pending model statistics/navigation/mechanism/cross-family scope. Preserved all 25 review items and historical update entries; all local links resolve and table column counts checked. Explicitly distinguishes local Codex visual QA from independent human review and retains the two render RGB-threshold exceedances.

Both remote controllers verified live. Snapshot: 8B repeat0/1 complete, repeat2 432 rows; 32B repeat0 735 rows; zero runtime-error rows in the inspected complete-line prefixes. This snapshot is not a final performance claim.


### Complete-output analysis queued

Added `analyze_when_complete.py`, a durable local waiter that requires both campaign receipts complete, stops on upstream failure, and then runs full six-file primary and separate auxiliary analyses with their existing strict validators. Exclusive output directories/logs preserve failures. Syntax checked; no numerical results generated while runs incomplete. Controller PID 3935464, log `/tmp/cviu-formal-analysis-controller.log`, output `raw/cviu_formal/v1/analysis_v1`; dispatch saved as `analysis_dispatch.json`. Initial status verified waiting_for_complete_campaigns. Experiment README documents the campaign and analysis commands.

Remote controllers 3471792/3471805 confirmed live. Snapshot before queue: 8B repeat2 915/960, earlier two repeats complete; 32B repeat0 871/960. Analysis will still require subsequent interpretation, legacy comparison integration and full goal completion audit.
