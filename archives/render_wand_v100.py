"""
CyberWand v10.0 - 正确渐进版
修正：
1. 渐进方向：底部粗短 → 顶端细长
2. 底部（手柄端）：瘤体粗 + 间隔短
3. 顶端（杖尖端）：瘤体细 + 间隔长
4. 尾部瘤体形状：接近圆柱形（拉长）
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

# 瘤体参数（正确渐进方向）
# 底部（手柄端）：粗 + 短间隔
# 顶端（杖尖端）：细 + 长间隔
num_nodes = 10
# 底部瘤体直径大，顶端小
max_bump_dia = 12.0  # 底部最大
min_bump_dia = max_bump_dia * (1 - 3/7)  # 6.86mm 顶端最小
# 底部间隔短，顶端间隔长
min_spacing = 30  # 底部最短间隔
max_spacing = 55  # 顶端最长间隔

# 生成渐进变化的瘤体数据
node_data = []
for i in range(num_nodes):
    t = i / (num_nodes - 1)  # 0=手柄端（底部），1=杖尖端（顶端）
    
    # 二次渐进（变化更明显）
    progress = t * t
    
    # 直径渐进：底部大 → 顶端小
    bump_dia = max_bump_dia * (1 - progress) + min_bump_dia * progress
    
    # 间隔渐进：底部短 → 顶端长
    spacing = min_spacing * (1 - progress) + max_spacing * progress
    
    # 杖身直径：底部粗 → 顶端细
    shaft_dia = shaft_base_diameter * (1 - t) + shaft_tip_diameter * t
    
    # 瘤体长度：底部短粗 → 顶端细长（圆柱形）
    bump_len = bump_dia * (1.1 + t * 0.4)  # 底部 1.1 倍，顶端 1.5 倍（圆柱形）
    
    # 位置计算（从手柄端开始累积）
    if i == 0:
        pos = 80  # 第一个瘤体距手柄 80mm
    else:
        prev_spacing = node_data[i-1]["spacing"]
        pos = node_data[i-1]["pos"] + prev_spacing
    
    node_data.append({
        "pos": pos,
        "shaft_dia": shaft_dia,
        "bump_dia": bump_dia,
        "bump_len": bump_len,
        "spacing": spacing,
        "is_tail": i >= num_nodes - 3  # 最后 3 个是尾部瘤体
    })

# 绘制瘤体（尾部接近圆柱形）
def draw_bump(cx, cy, shaft_radius, bump_radius, bump_length, is_tail, wand_angle_rad):
    random.seed(42)
    
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    # 尾部瘤体更接近圆柱形（拉长）
    if is_tail:
        elongation = 1.6  # 圆柱形拉长
    else:
        elongation = 1.3  # 正常椭球
    
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
            
            # 沿杖身方向拉长（尾部更明显）
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
    
    # 表面纹理（纵向沟壑）
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
    
    # 1. 绘制主杖身（底部粗 → 顶端细）
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
    
    # 2. 绘制渐进瘤体（底部粗短 → 顶端细长）
    for i, node in enumerate(node_data):
        # 从手柄端开始计算位置
        t = node["pos"] / wand_total_length
        node_x = start_x + t * (end_x - start_x)
        node_y = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        bump_radius = node["bump_dia"] * scale / 2
        bump_length = node["bump_len"] * scale
        
        draw_bump(node_x, node_y, shaft_radius, bump_radius, bump_length, node["is_tail"], rad)
    
    # 3. 手柄（底部）
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
    
    # 4. 杖尖（顶端）
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
        ("总长度：500mm", center_x - 250, center_y + 450),
        ("底部（手柄端）：瘤体粗 12mm + 间隔短 30mm", center_x - 250, center_y + 485),
        ("顶端（杖尖端）：瘤体细 6.9mm + 间隔长 55mm", center_x - 250, center_y + 520),
        ("尾部瘤体：圆柱形（拉长 1.6 倍）", center_x - 250, center_y + 555),
        ("渐进方向：底部粗短 → 顶端细长 ✅", center_x - 250, center_y + 590),
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
    
    title = "CyberWand v10.0 - 正确渐进版"
    subtitle = "底部粗短 → 顶端细长 | 尾部圆柱形"
    
    title_bg = Image.new('RGBA', (1600, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 800, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing correct progressive wand v10.0...")
draw_wand()
draw_annotations()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v100_correct_progressive.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
