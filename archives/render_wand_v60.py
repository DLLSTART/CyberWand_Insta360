"""
CyberWand v6.0 - 人体工学版
分析参考图片后的关键发现：
1. 手柄直径：12-15mm（适合成人握持）
2. 杖身直径：8-10mm（可握持，不是装饰）
3. 瘤体突出：3-5mm（不影响握持）
4. 总长度：180-220mm（单手握持舒适）
5. 重量分布：手柄略重，平衡点在握持处
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
scale = 8  # 调整比例，适应实际尺寸

# 人体工学参数（基于参考图片分析）
wand_total_length = 200  # 200mm（实际握持舒适长度）
handle_diameter = 15  # 15mm（成人手柄直径）
shaft_diameter = 10  # 10mm（可握持杖身）
tip_diameter = 6  # 6mm（杖尖）

# 瘤体节点参数（不规则，突出 3-5mm，不影响握持）
# 关键：瘤体直径 = 杖身直径 + 2×突出高度
node_data = [
    {"pos": 160, "shaft_dia": 10, "bump_height": 4, "bump_len": 12},  # 手柄附近
    {"pos": 140, "shaft_dia": 9.5, "bump_height": 4, "bump_len": 11},
    {"pos": 120, "shaft_dia": 9, "bump_height": 3.5, "bump_len": 10},
    {"pos": 100, "shaft_dia": 8.5, "bump_height": 3.5, "bump_len": 10},
    {"pos": 80, "shaft_dia": 8, "bump_height": 3, "bump_len": 9},
    {"pos": 60, "shaft_dia": 7.5, "bump_height": 3, "bump_len": 9},
]

# 绘制不规则瘤体（树瘤状，突出 3-5mm）
def draw_irregular_bump(cx, cy, shaft_radius, bump_height, bump_length, wand_angle_rad):
    """绘制不规则瘤体 - 突出 3-5mm，不影响握持"""
    
    random.seed(42)
    
    # 瘤体半径 = 杖身半径 + 突出高度
    bump_radius = shaft_radius + bump_height
    
    # 计算杖身方向
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    
    # 瘤体主体（不规则形状，沿杖身方向拉长）
    num_points = 32
    for layer in range(int(bump_radius * 2), 0, -2):
        t = layer / (bump_radius * 2)
        brightness = int(140 * t + 40)
        r_val = int(brightness * 0.5)
        g_val = int(brightness * 0.35)
        b_val = int(brightness * 0.25)
        
        points = []
        for i in range(num_points):
            angle_i = i * 2 * math.pi / num_points
            # 不规则半径变化
            radius_var = layer * (1 + 0.12 * math.sin(angle_i * 3) + 0.08 * math.cos(angle_i * 5))
            
            # 沿杖身方向拉长
            major_r = radius_var * 1.3  # 长轴
            minor_r = radius_var * 0.9  # 短轴
            
            x = cx + math.cos(angle_i) * major_r * wand_dir_x - math.sin(angle_i) * minor_r * (-wand_dir_y)
            y = cy + math.cos(angle_i) * major_r * wand_dir_y - math.sin(angle_i) * minor_r * wand_dir_x
            
            points.append((x, y))
        
        if len(points) >= 3:
            draw.polygon([(int(x), int(y)) for x, y in points], 
                        fill=(r_val, g_val, b_val, 255))
    
    # 表面纹理（纵向沟壑 + 不规则凹坑）
    num_grooves = 6
    for i in range(num_grooves):
        groove_angle = i * 2 * math.pi / num_grooves
        for j in range(5):
            t = j / 5
            gx = cx + math.cos(groove_angle) * bump_radius * 0.5 * t
            gy = cy + math.sin(groove_angle) * bump_radius * 0.5 * t
            pit_size = int(bump_height * 0.15 * (1 - t))
            
            draw.ellipse([
                int(gx - pit_size), int(gy - pit_size),
                int(gx + pit_size), int(gy + pit_size)
            ], fill=(40, 28, 18, 200))
    
    # 高光
    highlight_x = cx - bump_radius * 0.3
    highlight_y = cy - bump_radius * 0.3
    draw.ellipse([
        int(highlight_x - bump_radius*0.1), int(highlight_y - bump_radius*0.1),
        int(highlight_x + bump_radius*0.1), int(highlight_y + bump_radius*0.1)
    ], fill=(180, 150, 130, 160))

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 200
    start_y = center_y + 200
    end_x = start_x + wand_total_length * scale * math.cos(rad)
    end_y = start_y + wand_total_length * scale * math.sin(rad)
    
    # 1. 绘制主杖身（可握持直径 8-10mm）
    segments = 200
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        # 直径渐变：手柄 10mm → 杖尖 6mm
        diameter = (shaft_diameter - t * (shaft_diameter - tip_diameter)) * scale
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
    
    # 2. 绘制不规则瘤体（突出 3-5mm，不影响握持）
    for i, node in enumerate(node_data):
        t = (wand_total_length - node["pos"]) / wand_total_length
        node_x = start_x + t * (end_x - start_x)
        node_y = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        bump_height = node["bump_height"] * scale
        bump_length = node["bump_len"] * scale
        
        draw_irregular_bump(node_x, node_y, shaft_radius, bump_height, bump_length, rad)
    
    # 3. 手柄（15mm 直径，适合握持）
    handle_x = start_x - 30
    handle_y = start_y - 30
    handle_radius = handle_diameter * scale / 2
    
    # 手柄主体
    for r in range(int(handle_radius * 2.5), 0, -1):
        t = r / (handle_radius * 2.5)
        brightness = int(140 * t + 40)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 手柄底部装饰
    bottom_x = handle_x + int(40 * scale)
    bottom_y = handle_y + int(40 * scale)
    bottom_radius = handle_radius * 0.7
    
    for r in range(int(bottom_radius * 2.5), 0, -1):
        t = r / (bottom_radius * 2.5)
        brightness = int(140 * t + 40)
        draw.ellipse([
            int(bottom_x - r), int(bottom_y - r),
            int(bottom_x + r), int(bottom_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 4. 杖尖
    tip_x = end_x
    tip_y = end_y
    cone_length = 50 * scale
    
    for i in range(int(cone_length)):
        t = i / cone_length
        cone_x = tip_x - i * math.cos(rad)
        cone_y = tip_y - i * math.sin(rad)
        cone_radius = (tip_diameter/2 + t * 3) * scale
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        draw.line([
            (cone_x + nx * cone_radius, cone_y + ny * cone_radius),
            (cone_x - nx * cone_radius, cone_y - ny * cone_radius)
        ], fill=(90, 55, 35), width=int(cone_radius * 2))
    
    # LED 发光
    for i in range(18, 0, -1):
        alpha = i * 10
        glow_radius = i * 2
        draw.ellipse([
            int(tip_x - glow_radius), int(tip_y - glow_radius),
            int(tip_x + glow_radius), int(tip_y + glow_radius)
        ], fill=(100, 180, 255, alpha))

# 添加人体工学标注
def draw_ergonomic_annotations():
    try:
        font_medium = ImageFont.truetype("msyh.ttc", 28)
    except:
        font_medium = ImageFont.load_default()
    
    # 标注尺寸
    annotations = [
        ("手柄直径：15mm", center_x - 250, center_y + 350),
        ("杖身直径：8-10mm", center_x - 100, center_y + 380),
        ("瘤体突出：3-5mm", center_x + 50, center_y + 410),
        ("总长度：200mm", center_x, center_y + 440),
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
    
    title = "CyberWand v6.0 - 人体工学版"
    subtitle = "可握持使用：手柄 15mm + 杖身 8-10mm + 瘤体突出 3-5mm"
    
    title_bg = Image.new('RGBA', (1600, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 800, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing ergonomic wand for comfortable grip...")
draw_wand()
draw_ergonomic_annotations()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v60_ergonomic.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
