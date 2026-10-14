# task12旧成功回归：刚体接触静态对比

本轮只读审计，没有新生产者资产发布或物理参数写入；计时诊断由消费者在独立工作树执行。
用户要求真实有效的旧成功保持兼容，允许在证实计时问题后统一校准反应节奏（可低于旧30–60秒），
但仍保留原加热门控、真实液体、120Hz、7000步和四项交付边界。

## 对比与证据

旧可获取入口：`/mnt/data/chenjiantong/GenManip-Sim/saved/assets/scene_usds/scientific_experiments/task_12_fehling_test/unseen_scene_5/scene.usda`。
新版入口位于消费者`task12_liquid_color_20261012/receiver_archive_install_20261013T031857Z`的同一相对路径。
旧入口未证明是2026-09-26历史运行的精确快照。
静态明细为消费者`evidence/grasp_contact_static_comparison_20261014.json`。

试管根质量18.008921g、COM/惯量、初始变换、38146点GlassShell可见几何相同。
这不排除新增8mL动态样液改变系统动力学；不能把根质量相同说成整体运动必然相同。
两侧机器人摩擦preprocess相同（静/动2.5、combine=max），未发现试管显式摩擦被改动。
旧整管SDF的contactOffset/restOffset为10/1mm，新LowerSDF+24rim为0.8/0mm；新版另有speculativeCCD。
SDF分辨率512/subgrid6相同；margin/narrowBand旧0.00035、新0.01，是AABB对角线比例，
相当于约53.425µm与1.504mm，不是0.35mm与1cm。依据已有source_sdf_audit及生产者记录，
只读agent旧地址SSH失败不构成重新核对远端schema的证据。

两套粒子系统的filteredPairs目标恰为这25项，且25项全部属RigidScene、不属Supplement；
因此恢复该组偏移不直接改变PBD接触边界，但会改变与夹爪/架/杯/桌等全部刚体的接触并间接影响液体。
120壁代理与353底部代理不随该建议修改。

## 最小对照建议

保持同一新版配置、液体、SDF几何与质量，只恢复25个刚体碰撞的contact/rest参数组到10/1mm。
如果逐标量隔离，先contact0.8→10mm，rest保持0，再rest0→1mm；不能出现rest1mm>contact0.8mm的无效状态。
该候选尚未作者/运行，需按资产冷态、抓取/搬运及回架范围重新验证后才可准入。

已有机器人状态比较显示前200帧新旧关节近乎相同，抓取后夹爪差从约0.977mm到4.52mm；
该数量级只是对照依据，不是偏移导致掉分的因果证明。原新YAML也新增Scene迭代上下限等，
消费者旧/新计时对照已统一使用新版配置，并另排旧配置控制，避免混杂。
旧场景首条诊断部分数据已测得同一物理步两次调用、有效加热增量2倍；这不解释全部抓取/回架差异。

主线程承担本记录及消费者文档同步。规范无需通用变化，ASSET-001/003、STATE-002与VAL-001/003已覆盖
单变量、来源身份与证据边界；不将上述偏移建议提升为通用默认。不修改同事目录、机器人源码或称量生产。
