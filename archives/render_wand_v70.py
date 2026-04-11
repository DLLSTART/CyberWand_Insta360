"""
CyberWand v7.0 - 参考图片精确还原版
关键修正：
1. 魔杖拉长到 250mm
2. 瘤体间距拉大到 25-35mm（方便握持）
3. 瘤体渐进变化明显（从大到小）
4. 握持的是杖体，不是瘤体
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math
import random

# 创建画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (245, 245, 240, 255))
draw = ImageDraw.Draw(img)

# 中心参数
center_x, center_y = width // 2, height // 2
angle = -35
rad = math.radians(angle)
scale = 7  # 调整比例

# 人体工学参数（参考图片精确测量）
wand_total_length = 250  # 250mm（更长）
handle_diameter = 16  # 16mm（手柄）
shaft_base_diameter = 12  # 12mm（靠近手柄的杖身）
shaft_tip_diameter = 7  # 7mm（杖尖）

# 瘤体节点参数（渐进变化 + 大间距）
# 关键：间距 25-35mm，方便握持杖体
# 渐进：从手柄到杖尖，瘤体逐渐变小
node_data = [
    {"pos": 210, "shaft_dia": 11.5, "bump_dia": 18, "bump_len": 18},  # 最大瘤体（靠近手柄）
    {"pos": 180, "shaft_dia": 11, "bump_dia": 17, "bump_len": 17},    # 间距 30mm
    {"pos": 150, "shaft_dia": 10.5, "bump_dia": 16, "bump_len": 16},  # 间距 30mm
    {"pos": 120, "shaft_dia": 10, "bump_dia": 15, "bump_len": 15},    # 间距 30mm
    {"pos": 90, "shaft_dia": 9.5, "bump_dia": 14, "bump_len": 14},    # 间距 30mm
    {"pos": 60, "shaft_dia": 9, "bump_dia": 13, "bump_len": 13},      # 间距 30mm
    {"pos": 30, "shaft_dia": 8.5, "bump_dia": 12, "bump_len": 12},    # 最小瘤体（靠近杖尖）
]

# 绘制不规则瘤体（渐进变化）
def draw_irregular_bump(cx, cy, shaft_radius, bump_radius, bump_length, wand_angle_rad):
    """绘制不规则瘤体 - 渐进变化，从大到小"""
    
    random.seed(42)
    
    # 计算杖身方向
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    # 瘤体主体（沿杖身方向拉长的椭球）
    num_points = 40
    for layer in range(int(bump_radius * 2.2), 0, -2):
        t = layer / (bump_radius * 2.2)
        brightness = int(130 * t + 45)
        r_val = int(brightness * 0.5)
        g_val = int(brightness * 0.35)
        b_val = int(brightness * 0.25)
        
        points = []
        for i in range(num_points):
            angle_i = i * 2 * math.pi / num_points
            # 不规则半径变化（更自然）
            radius_var = layer * (1 + 0.1 * math.sin(angle_i * 3) + 0.07 * math.cos(angle_i * 5))
            
            # 沿杖身方向拉长（椭球）
            major_r = radius_var * 1.4  # 长轴（沿杖身）
            minor_r = radius_var * 0.85  # 短轴（垂直杖身）
            
            # 旋转坐标到杖身方向
            local_x = math.cos(angle_i) * major_r
            local_y = math.sin(angle_i) * minor_r
            
            x = cx + local_x * wand_dir_x - local_y * perp_dir_x
            y = cy + local_x * wand_dir_y - local_y * perp_dir_y
            
            points.append((x, y))
        
        if len(points) >= 3:
            draw.polygon([(int(x), int(y)) for x, y in points], 
                        fill=(r_val, g_val, b_val, 255))
    
    # 表面纹理（纵向沟壑 + 不规则凹坑）
    num_grooves = 5
    for i in range(num_grooves):
        groove_angle = i * 2 * math.pi / num_grooves
        for j in range(6):
            t = j / 6
            gx = cx + math.cos(groove_angle) * bump_radius * 0.4 * t
            gy = cy + math.sin(groove_angle) * bump_radius * 0.4 * t
            pit_size = int(bump_radius * 0.12 * (1 - t))
            
            draw.ellipse([
                int(gx - pit_size), int(gy - pit_size),
                int(gx + pit_size), int(gy + pit_size)
            ], fill=(45, 30, 20, 190))
    
    # 高光（左上角）
    highlight_x = cx - bump_radius * 0.35 * perp_dir_x
    highlight_y = cy - bump_radius * 0.35 * perp_dir_y
    draw.ellipse([
        int(highlight_x - bump_radius*0.12), int(highlight_y - bump_radius*0.12),
        int(highlight_x + bump_radius*0.12), int(highlight_y + bump_radius*0.12)
    ], fill=(190, 160, 140, 170))

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 250
    start_y = center_y + 250
    end_x = start_x + wand_total_length * scale * math.cos(rad)
    end_y = start_y + wand_total_length * scale * math.sin(rad)
    
    # 1. 绘制主杖身（渐变：12mm → 7mm）
    segments = 250
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        # 直径渐变
        diameter = (shaft_base_diameter - t * (shaft_base_diameter - shaft_tip_diameter)) * scale
        radius = diameter / 2
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        color_base = int(139 - t * 30)
        color_green = int(69 - t * 15)
        color_blue = int(19 - t * 4)
        
        draw.line([
            (x + nx * radius, y + ny * radius),
            (x - nx * radius, y - ny * radius)
        ], fill=(color_base, color_green, color_blue), width=int(diameter))
    
    # 2. 绘制 7 个渐进变化的瘤体（间距 30mm）
    for i, node in enumerate(node_data):
        t = (wand_total_length - node["pos"]) / wand_total_length
        node_x = start_x + t * (end_x - start_x)
        node_y = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        bump_radius = node["bump_dia"] * scale / 2
        bump_length = node["bump_len"] * scale
        
        draw_irregular_bump(node_x, node_y, shaft_radius, bump_radius, bump_length, rad)
    
    # 3. 手柄（16mm 直径）
    handle_x = start_x - 40
    handle_y = start_y - 40
    handle_radius = handle_diameter * scale / 2
    
    for r in range(int(handle_radius * 2.5), 0, -1):
        t = r / (handle_radius * 2.5)
        brightness = int(130 * t + 45)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 手柄底部装饰
    bottom_x = handle_x + int(45 * scale)
    bottom_y = handle_y + int(45 * scale)
    bottom_radius = handle_radius * 0.75
    
    for r in range(int(bottom_radius * 2.5), 0, -1):
        t = r / (bottom_radius * 2.5)
        brightness = int(130 * t + 45)
        draw.ellipse([
            int(bottom_x - r), int(bottom_y - r),
            int(bottom_x + r), int(bottom_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 4. 杖尖
    tip_x = end_x
    tip_y = end_y
    cone_length = 60 * scale
    
    for i in range(int(cone_length)):
        t = i / cone_length
        cone_x = tip_x - i * math.cos(rad)
        cone_y = tip_y - i * math.sin(rad)
        cone_radius = (shaft_tip_diameter/2 + t * 3) * scale
        
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

# 添加尺寸标注
def draw_annotations():
    try:
        font_medium = ImageFont.truetype("msyh.ttc", 28)
    except:
        font_medium = ImageFont.load_default()
    
    annotations = [
        ("总长度：250mm", center_x - 150, center_y + 400),
        ("手柄直径：16mm", center_x - 150, center_y + 435),
        ("杖身直径：7-12mm", center_x - 150, center_y + 470),
        ("瘤体间距：30mm（方便握持）", center_x - 150, center_y + 505),
        ("瘤体渐进：18mm → 12mm", center_x - 150, center_y + 540),
    ]
    
    for text, x, y in annotations:
        draw.text((x, y), text, fill='#2C1810', font=font_medium)

# 添加标题
def draw_title():
    try:
        font_large = ImageFont.truetype("msyh.ttc", 48)
        font_medium = ImageFont.truetype("msyh.ttc", 32)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    title = "CyberWand v7.0 - 参考图片精确还原"
    subtitle = "250mm 长 + 瘤体间距 30mm + 渐进变化 18→12mm"
    
    title_bg = Image.new('RGBA', (1600, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 800, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing wand with reference photo accuracy...")
draw_wand()
draw_annotations()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v70_reference_accurate.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
