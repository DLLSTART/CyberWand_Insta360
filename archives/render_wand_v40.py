"""
CyberWand v4.0 - 回归简洁美感
基于 v3.1/v3.3 的简洁风格，只做比例优化
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# 创建画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (245, 245, 240, 255))
draw = ImageDraw.Draw(img)

# 中心参数
center_x, center_y = width // 2, height // 2
angle = -35
rad = math.radians(angle)
scale = 12

# 魔杖参数（简洁美感）
wand_length = 400 * scale
shaft_start_diameter = 5.5 * scale
shaft_end_diameter = 1.5 * scale

# 圆球节点参数（简洁规则，比例协调）
# 圆球直径 = 杖身直径 × 1.5-1.7 倍（美观比例）
node_data = [
    {"pos": 24, "shaft_dia": 5.0, "node_dia": 8.0},   # 1.6 倍
    {"pos": 18, "shaft_dia": 4.5, "node_dia": 7.2},   # 1.6 倍
    {"pos": 12, "shaft_dia": 4.0, "node_dia": 6.4},   # 1.6 倍
    {"pos": 7, "shaft_dia": 3.5, "node_dia": 5.6},    # 1.6 倍
    {"pos": 2, "shaft_dia": 3.0, "node_dia": 4.8},    # 1.6 倍
    {"pos": -2, "shaft_dia": 2.5, "node_dia": 4.0},   # 1.6 倍
]

# 绘制简洁圆球节点（规则球形，蜂窝纹理）
def draw_simple_node(cx, cy, shaft_radius, node_radius):
    """绘制简洁规则的圆球节点"""
    
    # 圆球主体（3D 球体效果）
    for r in range(int(node_radius * 2.5), 0, -1):
        t = r / (node_radius * 2.5)
        brightness = int(160 * t + 30)
        r_val = int(brightness * 0.5)
        g_val = int(brightness * 0.35)
        b_val = int(brightness * 0.25)
        
        offset = int(node_radius * (1 - t) * 0.25)
        draw.ellipse([
            int(cx - r), int(cy - r + offset),
            int(cx + r), int(cy + r + offset)
        ], fill=(r_val, g_val, b_val, 255))
    
    # 蜂窝纹理（简洁凹坑）
    num_rings = 2
    num_per_ring = 6
    for ring in range(1, num_rings + 1):
        ring_radius = node_radius * 0.4 * ring
        for i in range(num_per_ring):
            angle_i = i * 2 * math.pi / num_per_ring + ring * math.pi / num_per_ring
            hx = cx + math.cos(angle_i) * ring_radius
            hy = cy + math.sin(angle_i) * ring_radius - node_radius * 0.2
            pit_size = int(node_radius * 0.12 * (num_rings - ring + 1))
            
            for ps in range(pit_size, 0, -1):
                shadow_offset = int(pit_size - ps)
                pit_brightness = int(50 * (ps / pit_size))
                draw.ellipse([
                    int(hx - ps), int(hy - ps + shadow_offset),
                    int(hx + ps), int(hy + ps + shadow_offset)
                ], fill=(pit_brightness, int(pit_brightness*0.7), int(pit_brightness*0.5), 200))
    
    # 高光（左上角）
    highlight_x = cx - node_radius * 0.35
    highlight_y = cy - node_radius * 0.35
    draw.ellipse([
        int(highlight_x - node_radius*0.15), int(highlight_y - node_radius*0.15),
        int(highlight_x + node_radius*0.15), int(highlight_y + node_radius*0.15)
    ], fill=(200, 170, 150, 180))

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 300
    start_y = center_y + 300
    end_x = start_x + wand_length * math.cos(rad)
    end_y = start_y + wand_length * math.sin(rad)
    
    # 绘制主杖身（红木色渐变）
    segments = 300
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        diameter = shaft_start_diameter * (1 - t) + shaft_end_diameter * t
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
    
    # 绘制 6 个简洁圆球节点（中心在杖身轴线上）
    for i, node in enumerate(node_data):
        t = (20 - node["pos"]) / 42
        node_x = start_x + t * (end_x - start_x)
        node_y = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        node_radius = node["node_dia"] * scale / 2
        
        draw_simple_node(node_x, node_y, shaft_radius, node_radius)
    
    # 手柄底部（球形设计）
    handle_x = start_x - 30
    handle_y = start_y - 30
    handle_radius = 7 * scale
    
    for r in range(int(handle_radius * 2.5), 0, -1):
        t = r / (handle_radius * 2.5)
        brightness = int(160 * t + 30)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 手柄底部装饰
    bottom_x = handle_x + int(30 * scale)
    bottom_y = handle_y + int(30 * scale)
    bottom_radius = 5 * scale
    
    for r in range(int(bottom_radius * 2.5), 0, -1):
        t = r / (bottom_radius * 2.5)
        brightness = int(160 * t + 30)
        draw.ellipse([
            int(bottom_x - r), int(bottom_y - r),
            int(bottom_x + r), int(bottom_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 杖尖（细长锥形）
    tip_x = end_x
    tip_y = end_y
    cone_length = 70 * scale
    
    for i in range(int(cone_length)):
        t = i / cone_length
        cone_x = tip_x - i * math.cos(rad)
        cone_y = tip_y - i * math.sin(rad)
        cone_radius = (0.3 + t * 1.8) * scale
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        draw.line([
            (cone_x + nx * cone_radius, cone_y + ny * cone_radius),
            (cone_x - nx * cone_radius, cone_y - ny * cone_radius)
        ], fill=(90, 55, 35), width=int(cone_radius * 2))
    
    # LED 发光效果（杖尖蓝色）
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
    
    title = "CyberWand v4.0 - 回归简洁美感"
    subtitle = "简洁规则圆球 + 协调比例 + 人类审美"
    
    title_bg = Image.new('RGBA', (1400, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 700, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing simple elegant wand...")
draw_wand()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v40_simple_elegant.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
