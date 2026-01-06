# 材质转换对视觉表征的影响分析

> 章节可用于论文“方法 / 表征分析”部分，并与 `convert_asset/no_mdl/materials.py` 中的实现逻辑互相引用。

## 1. 背景与目标
`materials.py` 在不打平 (no-flatten) 条件下，将依赖 MDL 的材质网络重建为最小 **UsdPreviewSurface** 子图 (BaseColor / Roughness / Metallic / Normal)，并执行：
1. MDL 输出剥离 (`remove_material_mdl_outputs`)
2. MDL Shader 删除 (`remove_all_mdl_shaders`)
3. 贴图复制与参数回填 (`copy_textures`)
4. Preview 网络骨架搭建 (`ensure_preview` / `connect_preview`)
5. 缺失 surface 的兜底 (`ensure_surface_output`, `post_process_material_surfaces`)

我们从 **AI 视觉特征稳定性** 角度研究：材质域规范化是否改变下游模型（CLIP / DINOv2 等）语义几何结构，是否引入系统偏差，及其通道层面的扰动主因。

## 2. 数据与符号
给定 N 个成对渲染：\((I_i^{pre}, I_i^{post})\), 其中 pre 为原始 MDL 渲染，post 为转换后的 Preview 渲染。

设 M 个特征模型（CLIP、DINOv2、自监督 ViT 等）：
\[
\mathcal{F} = \{ f^{(m)}: \mathbb{R}^{H\times W \times 3} \to \mathbb{R}^{d_m} \}_{m=1}^M
\]
归一化融合：
\[
\phi(I) = \operatorname{concat}\big( w_1 \tilde{f}^{(1)}(I), \ldots, w_M \tilde{f}^{(M)}(I) \big),\quad \tilde{f}^{(m)}(I)=\frac{f^{(m)}(I)-\mu^{(m)}}{\sigma^{(m)}}
\]

## 3. 成对差异与扰动统计
材质诱发位移：\(\Delta_i = \phi(I_i^{post}) - \phi(I_i^{pre})\)。

二阶统计：均值偏移 \(\bar{\Delta}\)，协方差 \(\Sigma_\Delta\)。若转换“语义无害”，期望 \(\|\bar{\Delta}\|_2\) 小，且 \(\Sigma_\Delta\) 无显著低秩异常集中。

## 4. 相似度结构保持 (SSPE)
特征拼接矩阵：
\[
\mathbf{X}^{pre}=[x_1^{pre},...,x_N^{pre}],\quad \mathbf{X}^{post}=[x_1^{post},...,x_N^{post}]
\]
余弦相似度矩阵：\(S^{pre}, S^{post}\)。

整体保持误差：
\[
\text{SSPE} = \frac{\| S^{post} - S^{pre} \|_F}{\| S^{pre} \|_F}
\]
对角/非对角分解：
\[
\text{SSPE}_{diag},\; \text{SSPE}_{off}
\]

## 5. 分布距离：FID 与 2-Wasserstein
高斯近似下：
\[
\text{FID} = \|\mu_{pre}-\mu_{post}\|_2^2 + \operatorname{Tr}\big( \Sigma_{pre}+\Sigma_{post}-2(\Sigma_{pre}^{1/2}\Sigma_{post}\Sigma_{pre}^{1/2})^{1/2} \big)
\]
与 2-Wasserstein 距离 \(W_2^2\) 在高斯假设下形式一致。

## 6. 材质敏感指数 (MSI)
定义样本距离：\(d_i=\|\Delta_i\|_2\)。构造随机重排基线：\(\tilde{d}_i=\|\phi(I_i^{pre})-\phi(I_{\pi(i)}^{pre})\|_2\)。
\[
\text{MSI} = \frac{\mathbb{E}[d_i]}{\mathbb{E}[\tilde{d}_i]}, \quad \text{MSI}_p = \frac{Q_p(d)}{Q_p(\tilde{d})}
\]
理想情况下 MSI≈1；显著大于 1 表示模型对材质替换敏感。

## 7. 扰动方向性 (PCA)
\(\Sigma_\Delta = U \Lambda U^\top\)，能量集中度：
\[
\text{CE}_k = \frac{\sum_{j=1}^k \lambda_j}{\sum_j \lambda_j}
\]
残差：\(r_i^{(k)}=\|\Delta_i-U_k U_k^\top \Delta_i\|_2\)。

## 8. 通道归因 (CAS)
四通道：BaseColor, Roughness, Metallic, Normal。对 post 结果仅恢复单通道为 pre 状态得 \(I_i^{(c)}\)。
\[
\text{CAS}_c = \frac{1}{N}\sum_i \frac{\|\phi(I_i^{(c)})-\phi(I_i^{post})\|_2}{\|\phi(I_i^{pre})-\phi(I_i^{post})\|_2+\varepsilon}
\]
若 \(\text{CAS}_{BC}\) 远高于其它，说明语义差异主要由 BaseColor（例如烘焙 / 白图判定策略）驱动。

## 9. 多模型权重自适应 (可选)
优化：
\[
\min_{w_m>0} \; \alpha\,\text{MSI}(w)+(1-\alpha)\,\text{SSPE}(w), \quad \sum_m w_m=M
\]
用于平衡“鲁棒性”与“结构保持”。

## 10. 降维可视化一致性
对 pre/post 分别 t-SNE 或 UMAP 得 \(Y^{pre},Y^{post}\)。用正交 Procrustes：
\[
R^* = \arg\min_{R\in O(2)} \|Y^{post}-RY^{pre}\|_F
\]
视觉失真：
\[
\text{VisDist} = \frac{\|Y^{post}-R^*Y^{pre}\|_F}{\|Y^{pre}\|_F}
\]

## 11. 统计检验
能量距离 (Energy Distance)：
\[
\text{ED}^2 = \frac{2}{N^2}\sum_{i,j}\|x_i^{pre}-x_j^{post}\| - \frac{1}{N^2}\sum_{i,j}\|x_i^{pre}-x_j^{pre}\| - \frac{1}{N^2}\sum_{i,j}\|x_i^{post}-x_j^{post}\|
\]
配合 KS 检验或置换检验获得显著性水平 (p 值)。

## 12. 实验管线摘要
1. 渲染采样：固定视角光照，生成配对 \((I^{pre}, I^{post})\)
2. 特征抽取：CLIP / DINOv2 / 其它 → 归一化拼接
3. 计算指标：MSI / FID / W2 / SSPE / PCA / CAS
4. 降维 & 对齐：t-SNE / UMAP + Procrustes → VisDist
5. 显著性：Energy Distance + 置换 / KS
6. 结果解读 + 通道定位

## 13. 结果解读建议
- 低 MSI + 低 FID + 低 SSPE：转换对语义保持稳定
- 高 MSI, CAS 基本集中在 BaseColor：需改进白图判定或 Tint 策略
- 高 SSPE_off：全局关系被扰动，检查 Roughness / Normal 贴图缺失逻辑
- PCA 低秩 + 高 CE_k：可通过低维补偿映射恢复一致性

## 14. 创新点总结
1. 定义 MSI / CAS / SSPE 组合指标剖析材质域扰动
2. 随机重排基线隔离对象语义差异
3. 通道级逆操作评估（局部恢复）定位主导材质参数
4. Procrustes 对齐的二维可视化失真量化 (VisDist)
5. 与 `materials.py` 操作阶段（复制贴图 / 常量烘焙 / Gloss→Roughness 反转 / Normal 缺省）逐一映射

## 15. 可扩展方向
- 引入 CLIP Text Prompt 相似度，检验材质变更对文本语义对齐的影响
- 使用 Diffusion 特征 (如 Stable Diffusion Encoder) 验证生成模型感知偏差
- 构建多尺度统计 (局部 patch 特征 vs 全局 token 汇聚)
- 在线回归预测：用 \(\Delta_i\) 预测通道改动类型（判别可解释性）

---
如需英文稿、伪代码或绘图脚本，请在后续提出。
