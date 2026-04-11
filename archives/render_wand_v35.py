"""
CyberWand v3.5 - 精确还原参考图片
深色圆球 + 红木杖身 + 渐变间距
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# 创建画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# 中心参数
center_x, center_y = width // 2, height // 2
angle = -35
rad = math.radians(angle)
scale = 15

# 魔杖参数（精确还原图片）
wand_length = 400 * scale

# 直径参数
handle_diameter = 14 * scale
shaft_start_diameter = 6 * scale
shaft_end_diameter = 2 * scale

# 圆球节点参数（深色，直径约杖身 1.5-2 倍）
# 间距：从底部到顶端逐渐变近
node_data = [
    {"pos": 25, "shaft_dia": 5.5, "node_dia": 9.0, "spacing": 8},   # 节点 1（底部）
    {"pos": 18, "shaft_dia": 4.5, "node_dia": 8.0, "spacing": 7},   # 节点 2
    {"pos": 12, "shaft_dia": 4.0, "node_dia": 7.0, "spacing": 6},   # 节点 3
    {"pos": 7, "shaft_dia": 3.5, "node_dia": 6.0, "spacing": 5},    # 节点 4
    {"pos": 3, "shaft_dia": 3.0, "node_dia": 5.0, "spacing": 4},    # 节点 5
    {"pos": 0, "shaft_dia": 2.5, "node_dia": 4.5, "spacing": 3},    # 节点 6（顶端）
]

# 绘制深色圆球节点
def draw_dark_node(cx, cy, shaft_radius, node_radius):
    """绘制深色圆球节点（参考图片风格）"""
    
    # 圆球主体（深棕色/接近黑色）
    base_color = (50, 30, 20)  # 深棕色
    
    for r in range(int(node_radius*3), 0, -1):
        t = r / (node_radius*3)
        # 3D 球体渐变
        brightness = int(80 * t + 20)
        r_val = int(brightness * 0.6)
        g_val = int(brightness * 0.4)
        b_val = int(brightness * 0.3)
        
        offset = int(node_radius * (1 - t) * 0.3)
        draw.ellipse([
            int(cx - r), int(cy - r + offset),
            int(cx + r), int(cy + r + offset)
        ], fill=(r_val, g_val, b_val, 255))
    
    # 蜂窝纹理（深色凹坑）
    num_rings = 3
    num_per_ring = 6
    for ring in range(1, num_rings + 1):
        ring_radius = node_radius * 0.35 * ring
        for i in range(num_per_ring):
            angle_i = i * 2 * math.pi / num_per_ring + ring * math.pi / num_per_ring
            hx = cx + math.cos(angle_i) * ring_radius
            hy = cy + math.sin(angle_i) * ring_radius - node_radius * 0.2
            pit_size = int(node_radius * 0.15 * (num_rings - ring + 1))
            
            for ps in range(pit_size, 0, -1):
                shadow_offset = int(pit_size - ps)
                pit_brightness = int(40 * (ps / pit_size))
                draw.ellipse([
                    int(hx - ps), int(hy - ps + shadow_offset),
                    int(hx + ps), int(hy + ps + shadow_offset)
                ], fill=(pit_brightness, pit_brightness//2, pit_brightness//3, 220))
    
    # 高光（左上角）
    highlight_x = cx - node_radius * 0.4
    highlight_y = cy - node_radius * 0.4
    draw.ellipse([
        int(highlight_x - node_radius*0.15), int(highlight_y - node_radius*0.15),
        int(highlight_x + node_radius*0.15), int(highlight_y + node_radius*0.15)
    ], fill=(180, 140, 120, 150))

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 300
    start_y = center_y + 300
    end_x = start_x + wand_length * math.cos(rad)
    end_y = start_y + wand_length * math.sin(rad)
    
    # 绘制主杖身（红木色，渐变）
    segments = 300
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        diameter = shaft_start_diameter * (1 - t) + shaft_end_diameter * t
        radius = diameter / 2
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        # 红木色渐变
        color_base = int(139 - t * 40)
        color_green = int(69 - t * 20)
        color_blue = int(19 - t * 5)
        
        draw.line([
            (x + nx * radius, y + ny * radius),
            (x - nx * radius, y - ny * radius)
        ], fill=(color_base, color_green, color_blue), width=int(diameter))
    
    # 绘制 6 个深色圆球节点
    for i, node in enumerate(node_data):
        t = (20 - node["pos"]) / 40
        nx = start_x + t * (end_x - start_x)
        ny = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        node_radius = node["node_dia"] * scale / 2
        
        draw_dark_node(nx, ny, shaft_radius, node_radius)
    
    # 手柄底部（特殊球形收尾）
    handle_x = start_x - 30
    handle_y = start_y - 30
    
    # 手柄主体（大球，深色）
    handle_radius = handle_diameter / 2
    for r in range(int(handle_radius*3), 0, -1):
        t = r / (handle_radius*3)
        brightness = int(80 * t + 20)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness*0.6), int(brightness*0.4), int(brightness*0.3), 255))
    
    # 手柄底部装饰（小球）
    bottom_x = handle_x + int(35 * scale)
    bottom_y = handle_y + int(35 * scale)
    bottom_radius = 5 * scale
    
    for r in range(int(bottom_radius*3), 0, -1):
        t = r / (bottom_radius*3)
        brightness = int(80 * t + 20)
        draw.ellipse([
            int(bottom_x - r), int(bottom_y - r),
            int(bottom_x + r), int(bottom_y + r)
        ], fill=(int(brightness*0.6), int(brightness*0.4), int(brightness*0.3), 255))
    
    # 杖尖（细长锥形）
    tip_x = end_x
    tip_y = end_y
    cone_length = 80 * scale
    
    for i in range(int(cone_length)):
        t = i / cone_length
        cone_x = tip_x - i * math.cos(rad)
        cone_y = tip_y - i * math.sin(rad)
        cone_radius = (0.3 + t * 2) * scale
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        draw.line([
            (cone_x + nx * cone_radius, cone_y + ny * cone_radius),
            (cone_x - nx * cone_radius, cone_y - ny * cone_radius)
        ], fill=(100, 60, 40), width=int(cone_radius * 2))

# 添加标题
def draw_title():
    try:
        font_large = ImageFont.truetype("msyh.ttc", 48)
        font_medium = ImageFont.truetype("msyh.ttc", 32)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    title = "CyberWand v3.5 - 精确还原参考图"
    subtitle = "深色圆球 + 红木杖身 + 渐变间距"
    
    title_bg = Image.new('RGBA', (1400, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 700, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing wand...")
draw_wand()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v35_reference.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
