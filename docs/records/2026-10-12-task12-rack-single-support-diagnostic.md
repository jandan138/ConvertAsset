# task12：架底单通道支撑诊断

状态：静态差异与原网格覆盖实测通过；动态接触、保液和完整机器人回放尚在验证，不是合格交付头。

## 来源与问题

接收方隔离源为`/mnt/data/zhuzihou/GenManip-Sim/saved/repair_20261010/task12_liquid_color_20261012/receiver_runtime`，原mixed5在6495条有效观察后出现GPU articulation/CUDA700错误，末段试管处于夹爪与架口附近。
不能据此把原因归为试管SDF；默认凸分解内腔偏差失败，shrinkWrap凸分解初始化发生GPU错误，二者均未发布。

本轮先检查实际架子碰撞：原`obj_tube_rack/Cube_015`静态三角网格启用，同时18片`__aan_collision_proxy/slot_15ml_rXX_cXX`圆柱支撑也启用。
Isaac4.1场景查询对18片各采65条射线，1170个采样均有原网格朝上的承托面；原网格位于补充片顶部同高或上方，差值约0–4.29mm。依据hit.position而非受raycast膨胀影响的distance。该采样不等于证明重复碰撞导致CUDA错误。

## 候选与变化

输出：`outputs/sciben_waterbath_120hz_20261010/task12_rack_seat_single_support_20261012`。
可移植delta仅覆盖18片支撑的`physics:collisionEnabled=False`；原架网格及全部孔壁、试管SDF、PBD边界、种子、质量、速度、过滤关系和材质保持源值。
组合前后逐属性和关系比较通过，允许差异恰为18个enabled值。源场景不写回。
`qualification_package`为测量专用，使用绝对源引用并重新声明物理场景owner，不当作可移植交付入口。

作者及调度脚本保存在上述个人GenManip工作根`tools/author_rack_single_support.py`、`run_rack_qualification.py`，不进入Scenario Forge核心或接收方运行依赖。
动态测量是既有生产者probe的外部仪表副本，只添加真实rack mesh接触数与试管位姿统计，保留逐120Hz步粒数及1mm内腔门槛。原生产者代码不修改。

## 验证与后续

静态作者执行成功；证据`evidence/rack_single_support_candidate.json`绑定来源、delta、1170点覆盖报告哈希和严格允许差异。
动态队列`evidence/rack_qualification.json`：两次10s冷态、两次17s规定120mm升降。冷态要求末120步至少100步真实接触原rack mesh且位姿范围小于1mm；全部要求无引擎错误、粒数一致、逐步内腔保留。
首错或600s超时按自有进程组停止。限定夹具通过后仍需原版核心7000步mixed5、其余四条坏例、最终实际反应/重置视频及独立安装验证。

本记录不宣布机器人成功或LeRobot可用。原任务成功示范仍待重采，7000步和原加热时长不放宽。
未修改通用物理默认或API；这是绑定task12/Isaac4.1来源的生产者诊断，遵循Scenario Forge ASSET-001/003/005和VAL-001/002/003。
