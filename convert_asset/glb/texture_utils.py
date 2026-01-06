# -*- coding: utf-8 -*-
import os
from io import BytesIO
from PIL import Image

def process_texture(file_path):
    """
    Read image from path, convert to PNG bytes.
    Returns: (bytes, mime_type) or None
    """
    if not file_path:
        return None
        
    if not os.path.exists(file_path):
        print(f"[WARN] Texture not found: {file_path}")
        return None
        
    try:
        with Image.open(file_path) as img:
            # Convert to RGBA or RGB
            if img.mode != 'RGBA' and img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Export to PNG in memory
            buf = BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            
            return img_bytes, "image/png"
    except Exception as e:
        print(f"[ERROR] Failed to process texture {file_path}: {e}")
        return None

def pack_metallic_roughness(metal_path, rough_path):
    """
    Combine metallic (B) and roughness (G) into one texture.
    glTF expects: G=Roughness, B=Metallic.
    Returns: (bytes, mime_type) or None
    """
    try:
        # Load images or create defaults
        metal_img = None
        rough_img = None
        size = (1, 1)
        
        if metal_path and os.path.exists(metal_path):
            metal_img = Image.open(metal_path).convert('L') # Grayscale
            size = metal_img.size
        
        if rough_path and os.path.exists(rough_path):
            rough_img = Image.open(rough_path).convert('L') # Grayscale
            size = rough_img.size
            
        # If mismatch size, resize to larger? or just first one.
        # For simplicity, resize to match if both exist
        if metal_img and rough_img and metal_img.size != rough_img.size:
            size = metal_img.size # Prioritize metallic size
            rough_img = rough_img.resize(size)
            
        # Create packed image (R=0, G=Rough, B=Metal, A=1)
        # packed = Image.new('RGB', size, (255, 255, 255)) # Unused
        
        r_ch = Image.new('L', size, 255) # Unused R
        
        g_ch = rough_img if rough_img else Image.new('L', size, 255) # Default Roughness 1.0
        b_ch = metal_img if metal_img else Image.new('L', size, 0)   # Default Metallic 0.0
        
        packed = Image.merge('RGB', (r_ch, g_ch, b_ch))
        
        buf = BytesIO()
        packed.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        
        return img_bytes, "image/png"
        
    except Exception as e:
        print(f"[ERROR] Failed to pack MetallicRoughness: {e}")
        return None
