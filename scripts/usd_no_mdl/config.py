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
