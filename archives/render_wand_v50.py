"""
CyberWand v5.0 - 黄金比例版
应用黄金比例 φ = 1.618 进行专业设计
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# 黄金比例
PHI = 1.618

# 创建画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (245, 245, 240, 255))
draw = ImageDraw.Draw(img)

# 中心参数
center_x, center_y = width // 2, height // 2
angle = -35
rad = math.radians(angle)
scale = 12

# 魔杖参数（应用黄金比例）
wand_length = 450 * scale
shaft_base_diameter = 5.5 * scale
shaft_tip_diameter = shaft_base_diameter / (PHI * PHI)  # 1/φ² ≈ 0.382

# 圆球节点参数（黄金比例）
# 圆球直径 = 杖身直径 × φ
# 节点间距 = 圆球直径 × φ
node_data = [
    {"pos": 28, "shaft_dia": 5.0, "node_dia": 5.0 * PHI},  # 8.09mm
    {"pos": 28 - 8.09*PHI, "shaft_dia": 4.5, "node_dia": 4.5 * PHI},  # 7.28mm
    {"pos": 28 - 8.09*PHI - 7.28*PHI, "shaft_dia": 4.0, "node_dia": 4.0 * PHI},  # 6.47mm
    {"pos": 10, "shaft_dia": 3.5, "node_dia": 3.5 * PHI},  # 5.66mm
    {"pos": 5, "shaft_dia": 3.0, "node_dia": 3.0 * PHI},  # 4.85mm
    {"pos": 0, "shaft_dia": 2.5, "node_dia": 2.5 * PHI},  # 4.05mm
]

# 简化节点位置（黄金比例分布）
node_positions = [28, 19, 11, 7, 3, 0]  # 近似黄金比例分布
node_shaft_dias = [5.0, 4.5, 4.0, 3.5, 3.0, 2.5]

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 350
    start_y = center_y + 350
    end_x = start_x + wand_length * math.cos(rad)
    end_y = start_y + wand_length * math.sin(rad)
    
    # 1. 绘制主杖身（黄金比例渐变）
    segments = 350
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        # 黄金比例渐变
        diameter = shaft_base_diameter * (1 - t) + shaft_tip_diameter * t
        radius = diameter / 2
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        color_base = int(139 - t * 35)
        color_green = int(69 - t * 18)
        color_blue = int(19 - t * 5)
        
        draw.line([
            (x + nx * radius, y + ny * radius),
            (x - nx * radius, y - ny * radius)
        ], fill=(color_base, color_green, color_blue), width=int(diameter))
    
    # 2. 绘制圆球节点（黄金比例）
    for i, (pos, shaft_dia) in enumerate(zip(node_positions, node_shaft_dias)):
        t = (28 - pos) / 28
        node_x = start_x + t * (end_x - start_x)
        node_y = start_y + t * (end_y - start_y)
        
        shaft_radius = shaft_dia * scale / 2
        node_radius = shaft_dia * PHI * scale / 2  # 黄金比例
        
        # 圆球主体
        for r in range(int(node_radius * 2.5), 0, -1):
            layer_t = r / (node_radius * 2.5)
            brightness = int(160 * layer_t + 30)
            r_val = int(brightness * 0.5)
            g_val = int(brightness * 0.35)
            b_val = int(brightness * 0.25)
            
            offset = int(node_radius * (1 - layer_t) * 0.25)
            draw.ellipse([
                int(node_x - r), int(node_y - r + offset),
                int(node_x + r), int(node_y + r + offset)
            ], fill=(r_val, g_val, b_val, 255))
        
        # 蜂窝纹理（黄金比例分布）
        num_rings = 2
        for ring in range(1, num_rings + 1):
            ring_radius = node_radius * 0.4 * ring
            num_per_ring = int(6 * PHI)  # 约 10 个
            for j in range(num_per_ring):
                angle_j = j * 2 * math.pi / num_per_ring
                hx = node_x + math.cos(angle_j) * ring_radius
                hy = node_y + math.sin(angle_j) * ring_radius
                pit_size = int(node_radius * 0.1)
                
                draw.ellipse([
                    int(hx - pit_size), int(hy - pit_size),
                    int(hx + pit_size), int(hy + pit_size)
                ], fill=(50, 35, 25, 180))
        
        # 高光
        highlight_x = node_x - node_radius * 0.35
        highlight_y = node_y - node_radius * 0.35
        draw.ellipse([
            int(highlight_x - node_radius*0.12), int(highlight_y - node_radius*0.12),
            int(highlight_x + node_radius*0.12), int(highlight_y + node_radius*0.12)
        ], fill=(200, 170, 150, 180))
    
    # 3. 手柄（黄金比例）
    handle_x = start_x - 40
    handle_y = start_y - 40
    handle_radius = shaft_base_diameter * PHI * scale / 2  # 约 8.9mm
    
    for r in range(int(handle_radius * 2.5), 0, -1):
        t = r / (handle_radius * 2.5)
        brightness = int(160 * t + 30)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 4. 杖尖
    tip_x = end_x
    tip_y = end_y
    cone_length = 80 * scale
    
    for i in range(int(cone_length)):
        t = i / cone_length
        cone_x = tip_x - i * math.cos(rad)
        cone_y = tip_y - i * math.sin(rad)
        cone_radius = (shaft_tip_diameter/2 + t * shaft_base_diameter) * scale
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        draw.line([
            (cone_x + nx * cone_radius, cone_y + ny * cone_radius),
            (cone_x - nx * cone_radius, cone_y - ny * cone_radius)
        ], fill=(90, 55, 35), width=int(cone_radius * 2))
    
    # LED 发光
    for i in range(18, 0, -1):
        alpha = i * 10
        glow_radius = i * 2.2
        draw.ellipse([
            int(tip_x - glow_radius), int(tip_y - glow_radius),
            int(tip_x + glow_radius), int(tip_y + glow_radius)
        ], fill=(100, 180, 255, alpha))

# 添加标题
def draw_title():
    try:
        font_large = ImageFont.truetype("msyh.ttc", 48)
        font_medium = ImageFont.truetype("msyh.ttc", 32)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    title = f"CyberWand v5.0 - 黄金比例版 (φ = {PHI})"
    subtitle = "专业工业设计美学 - 黄金比例统一性/节奏/平衡"
    
    title_bg = Image.new('RGBA', (1600, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 800, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing wand with Golden Ratio (φ = 1.618)...")
draw_wand()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v50_golden_ratio.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
