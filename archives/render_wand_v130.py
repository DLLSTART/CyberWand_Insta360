"""
CyberWand v13.0 - 尾部调整版
修正：
1. 尾部瘤体直径减少 1/5: 14.4mm → 11.5mm
2. 尾部瘤体间隔加大：28mm → 38mm
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
wand_total_length = 500
handle_diameter = 16
shaft_base_diameter = 12
shaft_tip_diameter = 7

# 瘤体参数（尾部调整）
num_nodes = 9
max_bump_dia = 12.0 * 0.8  # 9.6mm（减少 1/5，从 12mm 基准）
min_bump_dia = max_bump_dia * (1 - 3/7)  # 5.5mm 顶端最小
min_spacing = 38  # 底部最短间隔（加大到 38mm）
max_spacing = 55  # 顶端最长间隔

# 生成渐进变化的瘤体数据
node_data = []
for i in range(num_nodes):
    t = i / (num_nodes - 1)
    progress = t * t
    
    # 直径渐进：底部大 → 顶端小
    bump_dia = max_bump_dia * (1 - progress) + min_bump_dia * progress
    
    # 间隔渐进：底部短 → 顶端长（尾部 3 个之间保持 38mm 间隔）
    if i < 3:
        spacing = min_spacing  # 尾部 3 个之间保持 38mm
    else:
        spacing = min_spacing * (1 - progress) + max_spacing * progress
    
    # 杖身直径：底部粗 → 顶端细
    shaft_dia = shaft_base_diameter * (1 - t) + shaft_tip_diameter * t
    
    # 瘤体长度：底部圆柱形 → 顶端椭球形
    bump_len = bump_dia * (1.2 + t * 0.4)
    
    # 位置计算
    if i == 0:
        pos = 50  # 第一个瘤体距手柄末端 50mm
    else:
        prev_spacing = node_data[i-1]["spacing"]
        pos = node_data[i-1]["pos"] + prev_spacing
    
    node_data.append({
        "pos": pos,
        "shaft_dia": shaft_dia,
        "bump_dia": bump_dia,
        "bump_len": bump_len,
        "spacing": spacing,
        "is_tail": i < 3  # 前 3 个是尾部瘤体（圆柱形）
    })

# 绘制圆柱形手柄
def draw_cylindrical_handle(start_x, start_y, handle_length, handle_radius, wand_angle_rad):
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    end_x = start_x + handle_length * wand_dir_x
    end_y = start_y + handle_length * wand_dir_y
    
    num_segments = int(handle_length / 3)
    for i in range(num_segments):
        t = i / num_segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        for r in range(int(handle_radius * 2.2), 0, -2):
            layer_t = r / (handle_radius * 2.2)
            brightness = int(120 * layer_t + 50)
            
            cx = x - perp_dir_x * handle_radius * 0.3
            cy = y - perp_dir_y * handle_radius * 0.3
            
            draw.ellipse([
                int(cx - r), int(cy - r),
                int(cx + r), int(cy + r)
            ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    for r in range(int(handle_radius * 2.3), 0, -2):
        t = r / (handle_radius * 2.3)
        brightness = int(110 * t + 55)
        draw.ellipse([
            int(start_x - r), int(start_y - r),
            int(start_x + r), int(start_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    ring_x = start_x + 25 * wand_dir_x
    ring_y = start_y + 25 * wand_dir_y
    ring_radius = handle_radius * 1.05
    
    for r in range(int(ring_radius * 2), 0, -1):
        t = r / (ring_radius * 2)
        brightness = int(100 * t + 60)
        draw.ellipse([
            int(ring_x - r), int(ring_y - r),
            int(ring_x + r), int(ring_y + r)
        ], fill=(int(brightness*0.45), int(brightness*0.3), int(brightness*0.2), 255))

# 绘制瘤体
def draw_bump(cx, cy, shaft_radius, bump_radius, bump_length, is_tail, wand_angle_rad):
    random.seed(42)
    
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    if is_tail:
        elongation = 1.5
    else:
        elongation = 1.3
    
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
            radius_var = layer * (1 + 0.08 * math.sin(angle_i * 3))
            
            major_r = radius_var * elongation
            minor_r = radius_var * 0.9
            
            local_x = math.cos(angle_i) * major_r
            local_y = math.sin(angle_i) * minor_r
            
            x = cx + local_x * wand_dir_x - local_y * perp_dir_x
            y = cy + local_x * wand_dir_y - local_y * perp_dir_y
            
            points.append((x, y))
        
        if len(points) >= 3:
            draw.polygon([(int(x), int(y)) for x, y in points], 
                        fill=(r_val, g_val, b_val, 255))
    
    num_grooves = 6
    for i in range(num_grooves):
        groove_angle = i * 2 * math.pi / num_grooves
        for j in range(5):
            t = j / 5
            gx = cx + math.cos(groove_angle) * bump_radius * 0.4 * t
            gy = cy + math.sin(groove_angle) * bump_radius * 0.4 * t
            pit_size = int(bump_radius * 0.1 * (1 - t))
            
            draw.ellipse([
                int(gx - pit_size), int(gy - pit_size),
                int(gx + pit_size), int(gy + pit_size)
            ], fill=(45, 30, 20, 190))
    
    highlight_x = cx - bump_radius * 0.35 * perp_dir_x
    highlight_y = cy - bump_radius * 0.35 * perp_dir_y
    draw.ellipse([
        int(highlight_x - bump_radius*0.12), int(highlight_y - bump_radius*0.12),
        int(highlight_x + bump_radius*0.12), int(highlight_y + bump_radius*0.12)
    ], fill=(190, 160, 140, 170))

# 绘制魔杖主体
def draw_wand():
    handle_start_x = center_x - 400
    handle_start_y = center_y + 400
    end_x = handle_start_x + wand_total_length * scale * math.cos(rad)
    end_y = handle_start_y + wand_total_length * scale * math.sin(rad)
    
    # 1. 绘制圆柱形手柄（15mm 长）
    handle_length = 15 * scale
    handle_radius = handle_diameter * scale / 2
    draw_cylindrical_handle(handle_start_x, handle_start_y, handle_length, handle_radius, rad)
    
    handle_end_x = handle_start_x + handle_length * math.cos(rad)
    handle_end_y = handle_start_y + handle_length * math.sin(rad)
    
    # 2. 绘制主杖身
    shaft_start_x = handle_end_x
    shaft_start_y = handle_end_y
    shaft_length = (wand_total_length - 15) * scale
    
    segments = 485
    for i in range(segments):
        t = i / segments
        x = shaft_start_x + t * (end_x - shaft_start_x)
        y = shaft_start_y + t * (end_y - shaft_start_y)
        
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
    
    # 3. 绘制渐进瘤体
    for i, node in enumerate(node_data):
        t = node["pos"] / (wand_total_length - 15)
        node_x = shaft_start_x + t * (end_x - shaft_start_x)
        node_y = shaft_start_y + t * (end_y - shaft_start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        bump_radius = node["bump_dia"] * scale / 2
        bump_length = node["bump_len"] * scale
        
        draw_bump(node_x, node_y, shaft_radius, bump_radius, bump_length, node["is_tail"], rad)
    
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
    
    annotations = [
        ("总长度：500mm（手柄 15mm + 杖身 485mm）", center_x - 250, center_y + 450),
        ("手柄：圆柱形 16mm", center_x - 250, center_y + 485),
        ("尾部瘤体：9.6mm + 间隔 38mm（减少 1/5，加大间隔）", center_x - 250, center_y + 520),
        ("顶端瘤体：5.5mm + 间隔 55mm", center_x - 250, center_y + 555),
        ("渐进：底部粗短 → 顶端细长 ✅", center_x - 250, center_y + 590),
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
    
    title = "CyberWand v13.0 - 尾部调整版"
    subtitle = "尾部直径 -1/5(9.6mm) | 间隔 +38mm"
    
    title_bg = Image.new('RGBA', (1600, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 800, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing adjusted tail wand v13.0...")
draw_wand()
draw_annotations()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v130_adjusted_tail.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
