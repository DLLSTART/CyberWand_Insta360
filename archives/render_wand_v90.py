"""
CyberWand v9.0 - 双渐进版
核心改进：
1. 尾端瘤体直径减少 3/7: 12mm → 6.9mm
2. 尾部瘤体间隔是杖身间隔的 2/3: 50mm → 33mm
3. 瘤体间隔渐进：50mm → 33mm
4. 瘤体直径渐进：12mm → 6.9mm
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
scale = 6

# 魔杖参数
wand_total_length = 500  # 500mm
handle_diameter = 16
shaft_base_diameter = 12
shaft_tip_diameter = 7

# 瘤体参数（双渐进）
# 直径渐进：12mm → 6.9mm（减少 3/7）
# 间隔渐进：50mm → 33mm（2/3）
num_nodes = 10
max_bump_dia = 12.0  # 最大瘤体直径
min_bump_dia = max_bump_dia * (1 - 3/7)  # 6.86mm（减少 3/7）
max_spacing = 50  # 最大间隔
min_spacing = max_spacing * 2/3  # 33.3mm（2/3）

# 生成渐进变化的瘤体数据
node_data = []
for i in range(num_nodes):
    t = i / (num_nodes - 1)  # 0=手柄端，1=杖尖端
    
    # 渐进变化（使用二次曲线，变化更明显）
    progress = t * t  # 二次渐进
    
    # 直径渐进
    bump_dia = max_bump_dia * (1 - progress) + min_bump_dia * progress
    
    # 间隔渐进
    spacing = max_spacing * (1 - progress) + min_spacing * progress
    
    # 杖身直径（随位置变化）
    shaft_dia = shaft_base_diameter * (1 - t) + shaft_tip_diameter * t
    
    # 位置（从杖尖开始累积间隔）
    if i == 0:
        pos = 50  # 第一个瘤体距杖尖 50mm
    else:
        prev_spacing = node_data[i-1]["spacing"]
        pos = node_data[i-1]["pos"] + prev_spacing
    
    node_data.append({
        "pos": pos,
        "shaft_dia": shaft_dia,
        "bump_dia": bump_dia,
        "bump_len": bump_dia * 1.2,
        "spacing": spacing
    })

# 绘制不规则瘤体
def draw_irregular_bump(cx, cy, shaft_radius, bump_radius, bump_length, wand_angle_rad):
    random.seed(42)
    
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
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
            radius_var = layer * (1 + 0.1 * math.sin(angle_i * 3) + 0.07 * math.cos(angle_i * 5))
            major_r = radius_var * 1.4
            minor_r = radius_var * 0.85
            
            local_x = math.cos(angle_i) * major_r
            local_y = math.sin(angle_i) * minor_r
            
            x = cx + local_x * wand_dir_x - local_y * perp_dir_x
            y = cy + local_x * wand_dir_y - local_y * perp_dir_y
            
            points.append((x, y))
        
        if len(points) >= 3:
            draw.polygon([(int(x), int(y)) for x, y in points], 
                        fill=(r_val, g_val, b_val, 255))
    
    # 表面纹理
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
    
    # 高光
    highlight_x = cx - bump_radius * 0.35 * perp_dir_x
    highlight_y = cy - bump_radius * 0.35 * perp_dir_y
    draw.ellipse([
        int(highlight_x - bump_radius*0.12), int(highlight_y - bump_radius*0.12),
        int(highlight_x + bump_radius*0.12), int(highlight_y + bump_radius*0.12)
    ], fill=(190, 160, 140, 170))

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 350
    start_y = center_y + 350
    end_x = start_x + wand_total_length * scale * math.cos(rad)
    end_y = start_y + wand_total_length * scale * math.sin(rad)
    
    # 1. 绘制主杖身
    segments = 500
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
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
    
    # 2. 绘制渐进变化的瘤体
    for i, node in enumerate(node_data):
        # 从杖尖开始计算位置
        t = (wand_total_length - node["pos"]) / wand_total_length
        node_x = start_x + t * (end_x - start_x)
        node_y = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        bump_radius = node["bump_dia"] * scale / 2
        bump_length = node["bump_len"] * scale
        
        draw_irregular_bump(node_x, node_y, shaft_radius, bump_radius, bump_length, rad)
    
    # 3. 手柄
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

# 添加标注
def draw_annotations():
    try:
        font_medium = ImageFont.truetype("msyh.ttc", 26)
    except:
        font_medium = ImageFont.load_default()
    
    # 标注前几个和后几个瘤体的参数
    first_node = node_data[0]
    last_node = node_data[-1]
    
    annotations = [
        (f"总长度：{wand_total_length}mm", center_x - 250, center_y + 450),
        (f"手柄直径：{handle_diameter}mm", center_x - 250, center_y + 485),
        (f"杖身直径：{shaft_tip_diameter}-{shaft_base_diameter}mm", center_x - 250, center_y + 520),
        (f"瘤体数量：{num_nodes}个", center_x - 250, center_y + 555),
        (f"瘤体直径渐进：{max_bump_dia:.1f}mm → {min_bump_dia:.1f}mm（减少 3/7）", center_x - 250, center_y + 590),
        (f"瘤体间隔渐进：{max_spacing}mm → {min_spacing:.0f}mm（2/3）", center_x - 250, center_y + 625),
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
    
    title = f"CyberWand v9.0 - 双渐进版（直径 -3/7 | 间隔 -2/3）"
    subtitle = f"瘤体直径渐进：{max_bump_dia:.1f}→{min_bump_dia:.1f}mm | 间隔渐进：{max_spacing}→{min_spacing:.0f}mm"
    
    title_bg = Image.new('RGBA', (1800, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 900, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing dual-progressive wand v9.0...")
draw_wand()
draw_annotations()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v90_dual_progressive.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
