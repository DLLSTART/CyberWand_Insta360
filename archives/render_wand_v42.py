"""
CyberWand v4.2 - 无圆球简洁版
删除所有悬浮圆球，只要简洁杖身
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

# 魔杖参数（拉长杖身，无圆球）
wand_length = 450 * scale
shaft_start_diameter = 5.5 * scale
shaft_end_diameter = 1.5 * scale

# 绘制魔杖主体（无圆球）
def draw_wand():
    start_x = center_x - 350
    start_y = center_y + 350
    end_x = start_x + wand_length * math.cos(rad)
    end_y = start_y + wand_length * math.sin(rad)
    
    # 1. 绘制主杖身（拉长版，无圆球）
    segments = 350
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
    
    # 2. 手柄底部（球形设计）
    handle_x = start_x - 40
    handle_y = start_y - 40
    handle_radius = 7.5 * scale
    
    for r in range(int(handle_radius * 2.5), 0, -1):
        t = r / (handle_radius * 2.5)
        brightness = int(160 * t + 30)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 手柄底部装饰
    bottom_x = handle_x + int(35 * scale)
    bottom_y = handle_y + int(35 * scale)
    bottom_radius = 5.5 * scale
    
    for r in range(int(bottom_radius * 2.5), 0, -1):
        t = r / (bottom_radius * 2.5)
        brightness = int(160 * t + 30)
        draw.ellipse([
            int(bottom_x - r), int(bottom_y - r),
            int(bottom_x + r), int(bottom_y + r)
        ], fill=(int(brightness*0.5), int(brightness*0.35), int(brightness*0.25), 255))
    
    # 3. 杖尖（细长锥形）
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
    
    title = "CyberWand v4.2 - 无圆球简洁版"
    subtitle = "删除所有悬浮圆球 + 简洁杖身"
    
    title_bg = Image.new('RGBA', (1400, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 700, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing wand without nodes (clean shaft)...")
draw_wand()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v42_no_nodes.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
