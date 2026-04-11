"""
CyberWand v3.4 - 修正圆球与杖身比例
精确还原图片中的比例美感
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# 创建超高清画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 中心点和角度
center_x, center_y = width // 2, height // 2
angle = -35
rad = math.radians(angle)

# 魔杖精确参数（根据图片重新测量）
# 关键：圆球直径 ≈ 杖身直径的 1.3-1.5 倍（不是之前的 2-3 倍！）
scale = 12
wand_length = 350 * scale

# 直径参数（精确比例）
handle_diameter = 12 * scale      # 手柄直径
shaft_start_diameter = 4.5 * scale  # 杖身起始直径
shaft_end_diameter = 1.5 * scale    # 杖尖直径

# 圆球参数（关键修正：圆球直径 ≈ 杖身直径的 1.3-1.5 倍）
# 之前错误：圆球太大（2-3 倍），显得突兀
# 现在修正：圆球适度突出（1.3-1.5 倍），更美观
node_data = [
    {"pos": 22, "shaft_dia": 4.0, "node_dia": 5.2},   # 节点 1：杖身 4.0mm，圆球 5.2mm (1.3 倍)
    {"pos": 17, "shaft_dia": 3.5, "node_dia": 4.9},   # 节点 2：杖身 3.5mm，圆球 4.9mm (1.4 倍)
    {"pos": 12, "shaft_dia": 3.0, "node_dia": 4.2},   # 节点 3：杖身 3.0mm，圆球 4.2mm (1.4 倍)
    {"pos": 7, "shaft_dia": 2.5, "node_dia": 3.5},    # 节点 4：杖身 2.5mm，圆球 3.5mm (1.4 倍)
    {"pos": 2, "shaft_dia": 2.0, "node_dia": 2.8},    # 节点 5：杖身 2.0mm，圆球 2.8mm (1.4 倍)
    {"pos": -3, "shaft_dia": 1.8, "node_dia": 2.5},   # 节点 6：杖身 1.8mm，圆球 2.5mm (1.4 倍)
]

# 绘制背景
for y in range(height):
    alpha = int(200 - (y / height) * 50)
    draw.line([(0, y), (width, y)], fill=(245, 245, 240, alpha))

# 绘制圆球节点（修正后的比例）
def draw_node(cx, cy, shaft_radius, node_radius):
    """绘制圆球节点 - 比例协调版"""
    
    # 圆球主体（3D 球体效果）
    for r in range(int(node_radius*3), 0, -1):
        t = r / (node_radius*3)
        brightness = int(180 * t + 40)
        r_val = int(brightness * 0.42)
        g_val = int(brightness * 0.24)
        b_val = int(brightness * 0.12)
        
        offset = int(node_radius * (1 - t) * 0.3)
        draw.ellipse([
            int(cx - r), int(cy - r + offset),
            int(cx + r), int(cy + r + offset)
        ], fill=(r_val, g_val, b_val, 255))
    
    # 蜂窝纹理（凹坑）- 更细腻
    num_rings = 2
    num_per_ring = 6
    for ring in range(1, num_rings + 1):
        ring_radius = node_radius * 0.3 * ring
        for i in range(num_per_ring):
            angle_i = i * 2 * math.pi / num_per_ring + ring * math.pi / num_per_ring
            hx = cx + math.cos(angle_i) * ring_radius
            hy = cy + math.sin(angle_i) * ring_radius - node_radius * 0.2
            pit_size = int(node_radius * 0.12 * (num_rings - ring + 1))
            
            for ps in range(pit_size, 0, -1):
                shadow_offset = int(pit_size - ps)
                pit_brightness = int(60 * (ps / pit_size))
                draw.ellipse([
                    int(hx - ps), int(hy - ps + shadow_offset),
                    int(hx + ps), int(hy + ps + shadow_offset)
                ], fill=(int(pit_brightness), int(pit_brightness*0.6), int(pit_brightness*0.4), 200))

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 400
    start_y = center_y + 250
    end_x = start_x + wand_length * math.cos(rad)
    end_y = start_y + wand_length * math.sin(rad)
    
    # 绘制主杖身（细圆柱，渐变：底部粗→顶端细）
    segments = 300
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        # 直径渐变（从 4.5mm 到 1.5mm）
        diameter = shaft_start_diameter * (1 - t) + shaft_end_diameter * t
        radius = diameter / 2
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        color_base = int(107 - t * 40)
        
        draw.line([
            (x + nx * radius, y + ny * radius),
            (x - nx * radius, y - ny * radius)
        ], fill=(color_base, 62, 31), width=int(diameter))
    
    # 绘制 6 个圆球节点（修正后的比例）
    for node in node_data:
        t = (17.5 - node["pos"]) / 35
        nx = start_x + t * (end_x - start_x)
        ny = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        node_radius = node["node_dia"] * scale / 2
        
        draw_node(nx, ny, shaft_radius, node_radius)
    
    # 手柄（球形设计）
    handle_x = start_x - 20
    handle_y = start_y - 20
    handle_radius = handle_diameter / 2
    
    for r in range(int(handle_radius*3), 0, -1):
        t = r / (handle_radius*3)
        brightness = int(180 * t + 40)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness*0.42), int(brightness*0.24), int(brightness*0.12), 255))
    
    # 手柄底部装饰
    bottom_x = handle_x + int(30 * scale)
    bottom_y = handle_y + int(30 * scale)
    bottom_radius = 4 * scale
    
    for r in range(int(bottom_radius*3), 0, -1):
        t = r / (bottom_radius*3)
        brightness = int(180 * t + 40)
        draw.ellipse([
            int(bottom_x - r), int(bottom_y - r),
            int(bottom_x + r), int(bottom_y + r)
        ], fill=(int(brightness*0.42), int(brightness*0.24), int(brightness*0.12), 255))
    
    # 杖尖（细锥形）
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
        ], fill=(80, 50, 30), width=int(cone_radius * 2))
    
    # LED 发光效果
    for i in range(20, 0, -1):
        alpha = i * 12
        glow_radius = i * 2.5
        draw.ellipse([
            int(tip_x - glow_radius), int(tip_y - glow_radius),
            int(tip_x + glow_radius), int(tip_y + glow_radius)
        ], fill=(100, 180, 255, alpha))

# 添加光影效果
def add_lighting():
    highlight = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    highlight_draw = ImageDraw.Draw(highlight)
    
    gradient = Image.new('L', (width//2, height//2), color=0)
    for y in range(height//2):
        for x in range(width//2):
            dist = math.sqrt(x*x + y*y)
            alpha = max(0, 100 - int(dist * 0.1))
            gradient.putpixel((x, y), alpha)
    
    highlight.paste((255, 255, 255, 50), (0, 0, width//2, height//2), gradient)
    img.alpha_composite(highlight)

# 绘制标题
def draw_title():
    try:
        font_large = ImageFont.truetype("msyh.ttc", 48)
        font_medium = ImageFont.truetype("msyh.ttc", 32)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    title_bg = Image.new('RGBA', (1200, 150), (0, 0, 0, 128))
    img.paste(title_bg, (center_x - 600, 80), title_bg)
    
    draw.text((center_x, 100), "CyberWand v3.4 - 比例修正版", fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), "圆球与杖身比例协调（1.3-1.5 倍）", fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing wand body...")
draw_wand()

print("Adding lighting effects...")
add_lighting()

print("Adding title...")
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v34_proportions.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
