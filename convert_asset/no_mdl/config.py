# -*- coding: utf-8 -*-
"""
User-tunable settings and constants extracted from the monolithic script.
"""
import time

SUFFIX = "_noMDL"          # 兄弟文件后缀：bed.usd -> bed_noMDL.usd
ALLOW_OVERWRITE = False    # 若已存在 *_noMDL.usd，是否直接覆盖（否则自动加时间戳）
MATERIAL_ROOT_HINTS = ("/Root/Looks", "/World/Looks")  # 常见 Looks 根，找不到就全局扫描
GROUP  = "PreviewNetwork"
UVSET  = "st"

# BaseColor 行为
BAKE_TINT_WHEN_WHITE = True
ALWAYS_BAKE_TINT     = False

# 遍历变体时，是否恢复原 variant selection（建议 True）
RESTORE_VARIANT_SELECTION = True

# MDL 文本解析设置（保持与你旧脚本一致）
MDL_BASECOLOR_CONST_KEYS = [
    "BaseColor_Color","BaseColor","baseColor","base_color",
    "diffuse_color","albedo_color","tint_color","base_color_constant"
]

_TEX_EXTS = (".png",".jpg",".jpeg",".tga",".bmp",".exr",".tif",".tiff",".ktx",".dds",".hdr",".psd",".gif",".webp")

# ================= Diagnostics / Verification Enhancements =================
# When adding richer reporting we keep old behaviour by default (strict).

# 是否打印详细诊断（缺失引用、残留 MDL 分布等）。
PRINT_DIAGNOSTICS = True

# 严格验证：True = 任何残留 MDL（无论来自外部引用还是本层）都令 noMDL=False。
# 设为 False 时，如果“本 root layer 自己”已经没有 MDL，而残留全部来自无法递归处理的外部文件，
# 则整体返回 True，并打印 WARNING（便于在资源不完整场景先产出预览版本）。
STRICT_VERIFY = True

# 如果有缺失的子 USD（打不开的引用）并且 STRICT_VERIFY=True，本来会直接失败。
# 将此项设为 True 可以在存在缺失引用的情况下忽略这些缺失文件里的潜在 MDL，
# 行为等价于：缺失引用导致的外部残留不阻止成功；仍然严格检查当前 root layer。
IGNORE_EXTERNAL_MDL_IF_MISSING_CHILDREN = False

# （预留）尝试对外部引用的 Material 做本层 override 来移除 MDL 输出。
# 高风险：可能污染共享资产的期望表现，仅在确有需求并理解 USD 组合覆盖机制时开启。
TRY_OVERRIDE_EXTERNAL_MATERIALS = False

# 若设为 True，则忽略 MATERIAL_ROOT_HINTS，扫描整个 Stage 下所有 Material。
ALWAYS_SCAN_ALL_MATERIALS = True

# 若某些 Material 处在实例化（instancing）层次里，属性来自 instance master，直接 Block 可能失败。
# 开启后：在 MDL 输出无法删除/Block 时，对该 Material prim 调用 SetInstanceable(False) 解除实例，再重试删除/Block。
# 代价：打破实例复用（内存略增）。建议仅在大量 MDL 输出无法 Block 时使用。
BREAK_INSTANCE_FOR_MDL = True

# 对变体（VariantSets）内部的 MDL（包括 outputs:mdl:surface 与 Shader prim）是否也尝试清理。
# False 时仅处理当前激活的 variant。
CLEAN_VARIANT_MDL = False

# 放宽验证：允许外部引用里残留 MDL Shader（未被本层 override）而仍视为成功。
# 仅在 STRICT_VERIFY=False 时才有意义；若 STRICT_VERIFY=True 则仍然严格失败。
ALLOW_EXTERNAL_MDL_SHADERS = False

# 放宽验证：允许外部引用里残留 MDL outputs（已断开或无法 Block）而仍视为成功。
# 同样仅在 STRICT_VERIFY=False 生效。
ALLOW_EXTERNAL_MDL_OUTPUTS = False

# ================= Run Summary Output =================
# 将顶层（用户直接执行的那个）USD 的处理结果写入一个简明 txt。
# 位置：与顶层 USD 同目录；文件名：<root_stem>_noMDL_summary.txt。
# 每次运行会覆盖（便于快速查看最新结果）。
WRITE_SUMMARY_TXT = True
# 限制在 summary 中列出的缺失子文件数量，避免过长。
SUMMARY_MISSING_CHILD_LIMIT = 20

# ================= Auto Preview Creation =================
# 若某个 Material 只有 MDL 输出/Shader，被移除后不再有任何通用 surface 输出，是否自动补一个简易 PreviewSurface。
# 目的：避免顶层查看 *_noMDL.usd 时出现大量空材质（完全黑/默认灰）。
CREATE_PREVIEW_FOR_EXTERNAL_MDL = True
# 自动补的 preview 若无原 baseColor 纹理或常量，可使用此灰度 (linear) 作为 baseColor。
AUTO_PREVIEW_BASECOLOR = (0.18, 0.18, 0.18)

# ================= External MDL Override (Visual Fidelity) =================
# 顶层仍然“全灰”常见原因：大量材质来自外部引用层；本策略在当前 *_noMDL.usd 层对这些外部材质创建
# override 规格并生成 PreviewSurface，尽量复用其 MDL Shader 上的贴图/常量（在还未删除 MDL 前抽取）。
# 开启后：
#   1) 在删除 MDL Shader 之前扫描所有非 root-owned Material；
#   2) 若其存在 MDL Shader，则：overridePrim -> ensure_preview -> copy_textures -> connect_preview；
#   3) 将其 primPath 记入 processed，避免后续 root-owned 转换重复统计；
#   4) 最终统一执行 remove_material_mdl_outputs / remove_all_mdl_shaders，清理残留。
# 风险：为大量外部材质写入本层 override，增加当前 layer 体积；但可显著改善顶层查看视觉。
OVERRIDE_EXTERNAL_MDL_PREVIEW = True

# ================= Result Pass Relaxation =================
# 当本层(root-owned)已经没有任何 MDL，只剩外部引用中的 MDL 时，是否直接判定为通过。
# 目的：在资源不完整或只需快速可视化的场景，避免一直 strict-fail。
ALLOW_EXTERNAL_ONLY_PASS = True
# 若为 True，则 external-only-pass 还要求没有 missing child USD；False 则忽略缺失子文件也判通过。
REQUIRE_NO_MISSING_FOR_EXTERNAL_PASS = False

# 当仅需要通过验证而不再关心外部 MDL Shader 的原貌时，可选择直接在本层对外部 MDL Shader 进行 SetActive(False)。
# 作用：使验证统计时 external MDL shader 数量归零（因为被标记 inactive 通常不会再被遍历/统计）。
# 风险：会改变后续在该 *_noMDL.usd 上游组合看到的活跃 prim 集。
DEACTIVATE_EXTERNAL_MDL_SHADERS = True

# 清洁删除模式：在主转换与失活之后，再额外扫描所有仍然 active 的外部 MDL Shader 并 RemovePrim。
# 让 strict 验证彻底归零；对 *_noMDL.usd* 内部不可逆（需重新生成才能恢复）。
CLEAN_DELETE_EXTERNAL_MDL_SHADERS = True


