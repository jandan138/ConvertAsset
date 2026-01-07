# -*- coding: utf-8 -*-
"""
纹理处理工具模块。
使用 PIL (Pillow) 库进行图像加载、格式转换和通道打包。
"""
import os
from io import BytesIO
from PIL import Image

def process_texture(file_path):
    """
    读取图像文件并转换为 PNG 字节流。
    
    Args:
        file_path: 图像文件的绝对路径。
        
    Returns:
        tuple(bytes, str): (图片字节数据, MIME类型)
        None: 如果加载失败。
    """
    if not file_path:
        return None
        
    if not os.path.exists(file_path):
        print(f"[WARN] Texture not found: {file_path}")
        return None
        
    try:
        with Image.open(file_path) as img:
            # 确保图像格式兼容 (转换为 RGB 或 RGBA)
            if img.mode != 'RGBA' and img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 导出为内存中的 PNG 文件
            buf = BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            
            return img_bytes, "image/png"
    except Exception as e:
        print(f"[ERROR] Failed to process texture {file_path}: {e}")
        return None

def pack_metallic_roughness(metal_path, rough_path):
    """
    将金属度 (Metallic) 和粗糙度 (Roughness) 打包到同一张纹理中。
    glTF PBR 标准要求：
    - 绿色通道 (G) = 粗糙度 (Roughness)
    - 蓝色通道 (B) = 金属度 (Metallic)
    
    Args:
        metal_path: 金属度贴图路径。
        rough_path: 粗糙度贴图路径。
        
    Returns:
        tuple(bytes, str): (打包后的 PNG 字节数据, MIME类型)
        None: 如果处理失败。
    """
    try:
        # 加载图像或创建默认值
        metal_img = None
        rough_img = None
        size = (1, 1)
        
        # 加载金属度贴图并转为灰度 (L)
        if metal_path and os.path.exists(metal_path):
            metal_img = Image.open(metal_path).convert('L') 
            size = metal_img.size
        
        # 加载粗糙度贴图并转为灰度 (L)
        if rough_path and os.path.exists(rough_path):
            rough_img = Image.open(rough_path).convert('L')
            size = rough_img.size
            
        # 处理尺寸不一致的情况
        # 简单策略：如果有金属度贴图，以其尺寸为准缩放粗糙度贴图
        if metal_img and rough_img and metal_img.size != rough_img.size:
            size = metal_img.size 
            rough_img = rough_img.resize(size)
            
        # 构造通道
        # 红色通道 (R): 未使用，填充白色 (255)
        r_ch = Image.new('L', size, 255) 
        
        # 绿色通道 (G): 粗糙度。如果没图，默认 1.0 (255)
        g_ch = rough_img if rough_img else Image.new('L', size, 255)
        
        # 蓝色通道 (B): 金属度。如果没图，默认 0.0 (0)
        b_ch = metal_img if metal_img else Image.new('L', size, 0)
        
        # 合并通道生成新图像
        packed = Image.merge('RGB', (r_ch, g_ch, b_ch))
        
        # 导出为 PNG 字节流
        buf = BytesIO()
        packed.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        
        return img_bytes, "image/png"
        
    except Exception as e:
        print(f"[ERROR] Failed to pack MetallicRoughness: {e}")
        return None
