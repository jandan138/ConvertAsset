# CVIU 正式30场景资源闭包与渲染资格进展

## 场景资源

30个原冻结场景全部通过独立副本的转换及几何审计，未替换场景。25个直接通过，5个商业
场景因外部MDL引用失败，已单独修复。原始数据集入口SHA未变，修复只写独立副本。

- [30场景与240暂定目标索引](../../paper/shared/evidence/raw/cviu_formal/v1/ready_scenes.json)
- [外部材质完整下载闭包](../../paper/shared/evidence/raw/cviu_formal/v1/material_closure.json)

离线化18个官方资源文件，覆盖Tinted_Glass_R50/R75、Ash_Planks、Glass_Glazing_Spandrel、
Ground_Leaves及相对模板/纹理。已保留URL、文件hash、运行时模块路径/hash。
SDK中验证OmniPBR、OmniGlass、nvidia::core_definitions存在。实际着色仍需后续渲染验证，
不把静态闭包通过等同于图像可用。

localize_remote_materials.py仅修改独立USD层内已知官方URL的资源路径，保留每层前后hash
与替换明细。repair_remote_scenes.py在完整下载后恢复5场景转换、几何审计和目标池。
build_ready_manifest.py核对所有原冻结ID、源入口hash、几何/依赖报告和8个暂定目标。
目标尚待自然视角、关系指令、标签和图像验收，不是已经形成480对有效输入。

## 渲染优化资格

- 单进程、单scene加载、同render product切换A/B/A：mask全等；RGB MAE超过预设1级阈值。
- 每视角新render product：mask全等，RGB MAE约0.51/1.28/1.59，仍未准入。
- 单进程复用层缓存但重开USD context：mask全等，RGB MAE约0.57/1.28/1.58，仍未准入。
- FXAA批量与独立fresh基线尚未获得完整图像，不能宣称通过。
- 新增同步加载对照（sync_loads=True），比较batch与独立fresh A/B，以检验首次捕获时
  材质/纹理是否尚未稳定；不直接放宽阈值。运行中，输出formal_renderer_batch_sync_v1、
  fresh_a_sync_v1、fresh_b_sync_v1；日志/tmp/cviu-batch_sync.log等。

当前无正式渲染图像或5760条预测。32B revision固定下载仍进行中，尚无完成回执。

## 验证

- 场景索引生成：30场景、240暂定目标，全部几何一致且依赖无缺失。
- material URI/相对模块解析与target排序4项测试通过。
- 真实USD源目录逃逸保护测试此前通过；修复记录保留在各场景remote_material_repair目录。

下一步：完成批量捕获等价性资格、生成正式自然视角、通过图像/标签验收；下载32B后做
双GPU BF16加载和固定读出资格，再运行正式8B/32B容量对照。pilot零翻转结果保持原样。

正式可见性口径已在protocol.json明确：从原始有效视角冻结cohort，转换导致目标不可见
仍保留并单独统计；主分母固定，同时报告两条件均可见子集，不把信息丢失称为推理错误。
这与pilot双条件可见性资格集不同，两者不混合统计。此决策在正式预测前作出。

最新进程核对：同步加载三个资格任务2801602/3/4仍存活，尚无完整图像；32B下载2475480
仍存活，模型cache约14.2GB，未完成。没有把任何未通过资格的batch用于正式480对数据。

新增prepare_views.py及双CPU campaign：原始几何筛选、精确三角形遮挡、离中心目标位置
(0.3,0.4)/(0.7,0.6)、视角方位至少差30度、bbox完整入画，确定性候补直到8个不同目标。
不读模型输出；原始图QA后冻结最终视角，再按同顺序重新捕获O/C，不能把候选图混入正式数据。
输出formal_views_20261114_v1，controller2864842，日志/tmp/cviu-formal-view-campaign.log。
射线/平行AABB测试2 passed。候选不足会显式报告，不补重复对象凑数。

单张与batch不是已证实的像素等价成像协议，保留差异。新增同序batch独立重复资格，
仍使用mask相等/RGB MAE<=1阈值，输出formal_renderer_batch_repeat_v1（GPU3）。
正式采集需全程统一流程；另选3正式场景重复完整最终batch作为渲染噪声对照，
辅助调用单独计数，不混入5760主预测。资格未通过前不生成正式结果。
