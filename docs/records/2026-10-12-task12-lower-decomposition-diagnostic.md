# task12 下半段刚体碰撞诊断：尚未合格

状态：诊断中，不是新合格资产，不替代已有候选或完整运行证据。

## 来源与问题

消费侧独立工作根为`/mnt/data/zhuzihou/GenManip-Sim/saved/repair_20261010/task12_liquid_color_20261012`。
原版GenManip及原始机器人上的mixed5回放保留6495条有效观察后发生GPU articulation/CUDA700错误；真实故障前视频显示试管回架末段倾斜至夹爪/架口附近。
该证据不证明SDF是唯一原因。完整报告为工作根的`evidence/first_native_failure_audit.json`；原始动作未改，绝对底座协议与未知原记录标志的区别保留。

## 生产者诊断

输出根为`outputs/sciben_waterbath_120hz_20261010/task12_lower_decomposition_20261012`。
只将`obj_sample_tube/RimPartition/LowerSDF`的刚体碰撞从SDF改为SDK的convexDecomposition，继续使用现成PhysX cooker，不实现新的USD/mesh转换管线。
原可见网格、质量、姿态、PBD边界及粒子库存不改；两套液体仍过滤该刚体表示，SDK凸分解仅负责刚体接触。
输出包含无外部依赖的portable delta及带绝对源引用的本地诊断/资格入口。后者不可冒充可移植交付。
一次性制作脚本在上述个人工作根的`tools/author_lower_decomposition_probe.py`，接收方不依赖它。

测量夹具初期缺GPU强制启用、scene-query启用及RaycastHit对象适配；原始失败日志均保留。这些工具设置失败不属于资产物理资格。
修正后原生120Hz测得凸分解内半径约6.727mm，而原液体语义内半径为8mm；内底存在约5.67mm偏差。既有严格门槛未通过，未运行后续冷态/升降或完整原生队列，不作几何保真或引擎修复声明。

## 有依据的下一候选

直接读取目标Isaac4.1的`extsPhysics/omni.usd.schema.physx/plugins/PhysxSchema/resources/generatedSchema.usda`：
该版本凸分解默认shrinkWrap=False、最大32个凸包、每包64顶点、voxelResolution=500000、minThickness=0.001。
schema说明shrinkWrap会尝试将凸包顶点投回原始图形网格表面。

第二个独立输出为`task12_lower_decomposition_shrinkwrap_20261012`，只在凸分解表示上应用对应API并启用shrinkWrap，其他默认值不变。
先用同源原SDF的实测做对照，再验证严格内腔、两次10秒冷态和两次17秒规定升降。尚未通过，不准入消费侧完整机器人测试或交付。
现有状态在个人工作根的`evidence/shrinkwrap_qualification.json`；任何局部PASS均不能替代完整原版回放。

## 边界与后续记录

GenManip核心、SDK、机器人源文件及建通目录未改；此次没有新成功示范或LeRobot。
消费侧另有统一样液材质重置修正和浴液不投影的任务可读性覆盖，它们属于USD任务呈现逻辑，与本次刚体诊断分开，不作为引擎因果证据。
源文件与失败产物保留。完成资格后由同一实现者更新本记录及消费侧说明；当前不修改任何通用物理默认、生产者核心API或模型转换契约。
