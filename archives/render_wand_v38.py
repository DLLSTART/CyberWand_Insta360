"""
CyberWand v3.8 - 圆球正确定位在杖身上
圆球中心 = 杖身轴线中心
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math
import random

# 创建画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# 中心参数
center_x, center_y = width // 2, height // 2
angle = -35
rad = math.radians(angle)
scale = 15

# 魔杖参数
wand_length = 400 * scale
handle_diameter = 14 * scale
shaft_start_diameter = 6 * scale
shaft_end_diameter = 2 * scale

# 圆球节点参数（圆球直径 = 杖身直径 × 1.3-1.6 倍）
node_data = [
    {"pos": 25, "shaft_dia": 5.5, "node_dia": 7.5, "spacing": 8},
    {"pos": 18, "shaft_dia": 4.5, "node_dia": 6.8, "spacing": 7},
    {"pos": 12, "shaft_dia": 4.0, "node_dia": 6.0, "spacing": 6},
    {"pos": 7, "shaft_dia": 3.5, "node_dia": 5.2, "spacing": 5},
    {"pos": 3, "shaft_dia": 3.0, "node_dia": 4.5, "spacing": 4},
    {"pos": 0, "shaft_dia": 2.5, "node_dia": 3.8, "spacing": 3},
]

# 绘制不规则圆球节点（树瘤状）
def draw_irregular_node(cx, cy, shaft_radius, node_radius):
    """绘制不规则树瘤状圆球（中心在杖身轴线上）"""
    
    random.seed(42)
    
    # 生成不规则轮廓点
    num_points = 36
    for layer in range(int(node_radius * 2.5), 0, -2):
        t = layer / (node_radius * 2.5)
        brightness = int(80 * t + 20)
        r_val = int(brightness * 0.6)
        g_val = int(brightness * 0.4)
        b_val = int(brightness * 0.3)
        
        layer_points = []
        for i in range(num_points):
            angle_i = i * 2 * math.pi / num_points
            layer_radius = layer * (1 + 0.15 * math.sin(angle_i * 3) + 0.1 * math.cos(angle_i * 5))
            # 圆球中心 = 杖身轴线中心 (cx, cy)
            x = cx + math.cos(angle_i) * layer_radius * 1.2
            y = cy + math.sin(angle_i) * layer_radius * 0.9
            layer_points.append((x, y))
        
        if len(layer_points) >= 3:
            draw.polygon([(int(x), int(y)) for x, y in layer_points], 
                        fill=(r_val, g_val, b_val, 255))
    
    # 表面凹凸纹理
    num_pits = 15
    for i in range(num_pits):
        pit_angle = random.uniform(0, 2 * math.pi)
        pit_radius = random.uniform(node_radius * 0.2, node_radius * 0.5)
        
        hx = cx + math.cos(pit_angle) * pit_radius * 1.2
        hy = cy + math.sin(pit_angle) * pit_radius * 0.9
        
        pit_size = int(random.uniform(node_radius * 0.08, node_radius * 0.15))
        
        for ps in range(pit_size, 0, -1):
            shadow_offset = int(pit_size - ps)
            pit_brightness = int(40 * (ps / pit_size))
            
            pit_points = []
            for j in range(8):
                pit_angle_j = j * 2 * math.pi / 8
                pit_r = ps * (1 + 0.2 * math.sin(pit_angle_j * 3))
                pit_points.append((
                    hx + math.cos(pit_angle_j) * pit_r,
                    hy + math.sin(pit_angle_j) * pit_r + shadow_offset
                ))
            
            if len(pit_points) >= 3:
                draw.polygon([(int(x), int(y)) for x, y in pit_points],
                           fill=(int(pit_brightness), int(pit_brightness//2), int(pit_brightness//3), 200))
    
    # 高光
    highlight_x = cx - node_radius * 0.4 * 1.2
    highlight_y = cy - node_radius * 0.4 * 0.9
    for hr in range(int(node_radius * 0.25), 0, -1):
        highlight_points = []
        for j in range(8):
            hl_angle = j * 2 * math.pi / 8
            hl_r = hr * (1 + 0.15 * math.sin(hl_angle * 3))
            highlight_points.append((
                highlight_x + math.cos(hl_angle) * hl_r,
                highlight_y + math.sin(hl_angle) * hl_r * 0.8
            ))
        if len(highlight_points) >= 3:
            draw.polygon([(int(x), int(y)) for x, y in highlight_points],
                        fill=(150, 120, 100, int(150 * hr / (node_radius * 0.25))))

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 300
    start_y = center_y + 300
    end_x = start_x + wand_length * math.cos(rad)
    end_y = start_y + wand_length * math.sin(rad)
    
    # 先绘制主杖身（作为背景）
    segments = 300
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        diameter = shaft_start_diameter * (1 - t) + shaft_end_diameter * t
        radius = diameter / 2
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        color_base = int(139 - t * 40)
        color_green = int(69 - t * 20)
        color_blue = int(19 - t * 5)
        
        draw.line([
            (x + nx * radius, y + ny * radius),
            (x - nx * radius, y - ny * radius)
        ], fill=(color_base, color_green, color_blue), width=int(diameter))
    
    # 绘制 6 个不规则圆球节点（圆球中心 = 杖身轴线中心）
    for i, node in enumerate(node_data):
        t = (20 - node["pos"]) / 40
        # 计算杖身轴线上的位置（圆球中心）
        node_x = start_x + t * (end_x - start_x)
        node_y = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        node_radius = node["node_dia"] * scale / 2
        
        # 圆球中心就是杖身轴线中心 (node_x, node_y)
        draw_irregular_node(node_x, node_y, shaft_radius, node_radius)
    
    # 手柄底部（特殊球形收尾）
    handle_x = start_x - 30
    handle_y = start_y - 30
    handle_radius = handle_diameter / 2
    
    for r in range(int(handle_radius * 3), 0, -1):
        t = r / (handle_radius * 3)
        brightness = int(80 * t + 20)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness * 0.6), int(brightness * 0.4), int(brightness * 0.3), 255))
    
    # 手柄底部装饰
    bottom_x = handle_x + int(35 * scale)
    bottom_y = handle_y + int(35 * scale)
    bottom_radius = 5 * scale
    
    for r in range(int(bottom_radius * 3), 0, -1):
        t = r / (bottom_radius * 3)
        brightness = int(80 * t + 20)
        draw.ellipse([
            int(bottom_x - r), int(bottom_y - r),
            int(bottom_x + r), int(bottom_y + r)
        ], fill=(int(brightness * 0.6), int(brightness * 0.4), int(brightness * 0.3), 255))
    
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
    
    title = "CyberWand v3.8 - 圆球正确定位"
    subtitle = "圆球中心 = 杖身轴线中心（圆球包裹杖身）"
    
    title_bg = Image.new('RGBA', (1400, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 700, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing wand with nodes centered on shaft...")
draw_wand()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v38_centered.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
