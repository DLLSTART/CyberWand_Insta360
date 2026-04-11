"""
CyberWand v16.0 - 参考图片精确还原版
基于皇上提供的参考图片设计

关键特征：
1. 手柄：长约 120mm，深色树瘤纹理，复杂凹凸雕刻
2. 杖身：细长直杆约 8-10mm，金属色/木色
3. 杖尖：LED 发光（蓝白色）
4. 整体：哈利波特风格魔杖
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math
import random

# 创建画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (20, 20, 20, 255))  # 深色背景
draw = ImageDraw.Draw(img)

# 中心参数
center_x, center_y = width // 2, height // 2
angle = -35
rad = math.radians(angle)
scale = 6

# 魔杖参数（参考图片比例）
wand_total_length = 500
handle_length = 120  # 手柄长约 120mm（占 1/4）
handle_diameter = 28  # 手柄直径 28mm（容纳 PCB）
shaft_diameter = 9  # 杖身直径 9mm（细长）

# 绘制树瘤纹理手柄（复杂凹凸雕刻）
def draw_wooden_handle(start_x, start_y, handle_length, handle_radius, wand_angle_rad):
    """绘制树瘤纹理手柄 - 复杂凹凸雕刻"""
    
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    end_x = start_x + handle_length * wand_dir_x
    end_y = start_y + handle_length * wand_dir_y
    
    # 手柄主体（深棕色，复杂树瘤纹理）
    num_segments = int(handle_length / 2)
    for i in range(num_segments):
        t = i / num_segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        # 手柄半径有微小变化（树瘤不规则）
        radius_var = handle_radius * (1 + 0.15 * math.sin(t * 20) + 0.1 * math.cos(t * 13))
        
        for r in range(int(radius_var * 2.2), 0, -2):
            layer_t = r / (radius_var * 2.2)
            
            # 深棕色渐变（树瘤颜色）
            base_brightness = int(80 * layer_t + 30)
            
            # 添加不规则纹理
            texture = int(20 * math.sin(t * 30 + r * 0.5) * math.cos(r * 0.3))
            
            r_val = min(255, max(0, base_brightness + texture))
            g_val = min(255, max(0, int((base_brightness + texture) * 0.5)))
            b_val = min(255, max(0, int((base_brightness + texture) * 0.3)))
            
            cx = x - perp_dir_x * radius_var * 0.3
            cy = y - perp_dir_y * radius_var * 0.3
            
            draw.ellipse([
                int(cx - r), int(cy - r),
                int(cx + r), int(cy + r)
            ], fill=(r_val, g_val, b_val, 255))
    
    # 树瘤凹凸纹理（纵向沟壑 + 不规则凸起）
    random.seed(42)
    num_bumps = 25
    for i in range(num_bumps):
        bump_t = i / num_bumps
        bump_x = start_x + bump_t * handle_length * wand_dir_x
        bump_y = start_y + bump_t * handle_length * wand_dir_y
        
        # 随机凹凸
        bump_angle = random.uniform(0, 2 * math.pi)
        bump_radius = random.uniform(3, 8) * scale
        bump_depth = random.uniform(0.3, 0.8)
        
        # 凸起
        for r in range(int(bump_radius), 0, -1):
            t = r / bump_radius
            brightness = int(100 * t + 40 * bump_depth)
            texture = int(15 * math.sin(r * 0.8) * math.cos(bump_angle * 3))
            
            bx = bump_x + math.cos(bump_angle) * r * perp_dir_x * 0.5
            by = bump_y + math.cos(bump_angle) * r * perp_dir_y * 0.5
            
            draw.ellipse([
                int(bx - r * 0.8), int(by - r * 0.8),
                int(bx + r * 0.8), int(by + r * 0.8)
            ], fill=(brightness + texture, int((brightness + texture) * 0.5), 
                    int((brightness + texture) * 0.3), 255))
    
    # 纵向沟壑（树纹）
    num_grooves = 8
    for i in range(num_grooves):
        groove_angle = i * 2 * math.pi / num_grooves
        groove_x = start_x + 30 * math.cos(groove_angle) * perp_dir_x
        groove_y = start_y + 30 * math.sin(groove_angle) * perp_dir_y
        
        for j in range(int(handle_length / 3)):
            gx = groove_x + j * 3 * wand_dir_x
            gy = groove_y + j * 3 * wand_dir_y
            groove_radius = random.uniform(2, 4) * scale
            
            draw.ellipse([
                int(gx - groove_radius), int(gy - groove_radius),
                int(gx + groove_radius), int(gy + groove_radius)
            ], fill=(40, 25, 15, 200))
    
    # 手柄底部（平整）
    for r in range(int(handle_radius * 2.3), 0, -2):
        t = r / (handle_radius * 2.3)
        brightness = int(90 * t + 40)
        draw.ellipse([
            int(start_x - r), int(start_y - r),
            int(start_x + r), int(start_y + r)
        ], fill=(brightness, int(brightness * 0.5), int(brightness * 0.3), 255))

# 绘制细长杖身
def draw_wand_shaft(shaft_start_x, shaft_start_y, shaft_end_x, shaft_end_y, shaft_radius, wand_angle_rad):
    """绘制细长杖身 - 直杆无渐变"""
    
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    # 计算杖身长度
    shaft_length = math.sqrt((shaft_end_x - shaft_start_x)**2 + (shaft_end_y - shaft_start_y)**2)
    segments = int(shaft_length / 2)
    
    for i in range(segments):
        t = i / segments
        x = shaft_start_x + t * (shaft_end_x - shaft_start_x)
        y = shaft_start_y + t * (shaft_end_y - shaft_start_y)
        
        # 木色/金属色渐变
        color_base = int(160 - t * 40)
        color_green = int(110 - t * 30)
        color_blue = int(70 - t * 20)
        
        radius = shaft_radius
        
        nx = -math.sin(wand_angle_rad)
        ny = -math.cos(wand_angle_rad)
        
        draw.line([
            (x + nx * radius, y + ny * radius),
            (x - nx * radius, y - ny * radius)
        ], fill=(color_base, color_green, color_blue), width=int(shaft_radius * 2))
    
    # 杖身纹理（细木纹）
    random.seed(43)
    for i in range(50):
        t = random.uniform(0, 1)
        texture_x = shaft_start_x + t * (shaft_end_x - shaft_start_x)
        texture_y = shaft_start_y + t * (shaft_end_y - shaft_start_y)
        texture_len = random.uniform(10, 30) * scale
        
        tx_end = texture_x + texture_len * math.cos(wand_angle_rad)
        ty_end = texture_y + texture_len * math.sin(wand_angle_rad)
        
        draw.line([
            (texture_x, texture_y),
            (tx_end, ty_end)
        ], fill=(100, 70, 45), width=2)

# 绘制杖尖 LED
def draw_tip_with_led(tip_x, tip_y, tip_radius, wand_angle_rad):
    """绘制杖尖 LED 发光"""
    
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    
    cone_length = 40 * scale
    
    # 锥形杖尖
    for i in range(int(cone_length)):
        t = i / cone_length
        cone_x = tip_x - i * wand_dir_x
        cone_y = tip_y - i * wand_dir_y
        cone_radius = (tip_radius + t * 2) * scale
        
        nx = -math.sin(wand_angle_rad)
        ny = -math.cos(wand_angle_rad)
        
        draw.line([
            (cone_x + nx * cone_radius, cone_y + ny * cone_radius),
            (cone_x - nx * cone_radius, cone_y - ny * cone_radius)
        ], fill=(120, 80, 50), width=int(cone_radius * 2))
    
    # LED 发光（蓝白色）
    for i in range(20, 0, -1):
        alpha = i * 12
        glow_radius = i * 2.5
        draw.ellipse([
            int(tip_x - glow_radius), int(tip_y - glow_radius),
            int(tip_x + glow_radius), int(tip_y + glow_radius)
        ], fill=(150, 200, 255, alpha))
    
    # LED 核心（亮白色）
    draw.ellipse([
        int(tip_x - 3), int(tip_y - 3),
        int(tip_x + 3), int(tip_y + 3)
    ], fill=(255, 255, 255, 255))

# 绘制魔杖主体
def draw_wand():
    handle_start_x = center_x - 350
    handle_start_y = center_y + 350
    end_x = handle_start_x + wand_total_length * scale * math.cos(rad)
    end_y = handle_start_y + wand_total_length * scale * math.sin(rad)
    
    # 1. 绘制树瘤纹理手柄（120mm 长）
    handle_length_scaled = handle_length * scale
    handle_radius = handle_diameter * scale / 2
    draw_wooden_handle(handle_start_x, handle_start_y, handle_length_scaled, handle_radius, rad)
    
    # 手柄末端位置
    handle_end_x = handle_start_x + handle_length_scaled * math.cos(rad)
    handle_end_y = handle_start_y + handle_length_scaled * math.sin(rad)
    
    # 2. 绘制细长杖身
    shaft_start_x = handle_end_x
    shaft_start_y = handle_end_y
    shaft_radius = shaft_diameter * scale / 2
    
    draw_wand_shaft(shaft_start_x, shaft_start_y, end_x, end_y, shaft_radius, rad)
    
    # 3. 绘制杖尖 LED
    draw_tip_with_led(end_x, end_y, shaft_radius, rad)

# 添加标注
def draw_annotations():
    try:
        font_medium = ImageFont.truetype("msyh.ttc", 24)
    except:
        font_medium = ImageFont.load_default()
    
    annotations = [
        ("总长度：500mm（手柄 120mm + 杖身 380mm）", center_x - 280, center_y + 450),
        ("手柄：28mm 树瘤纹理（深色雕刻）", center_x - 280, center_y + 480),
        ("杖身：9mm 细长直杆（木色/金属色）", center_x - 280, center_y + 510),
        ("杖尖：WS2812B LED（蓝白色发光）", center_x - 280, center_y + 540),
        ("风格：哈利波特魔杖参考", center_x - 280, center_y + 570),
    ]
    
    for text, x, y in annotations:
        draw.text((x, y), text, fill='#CCCCCC', font=font_medium)

# 添加标题
def draw_title():
    try:
        font_large = ImageFont.truetype("msyh.ttc", 48)
        font_medium = ImageFont.truetype("msyh.ttc", 32)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    title = "CyberWand v16.0 - 参考图片精确还原"
    subtitle = "树瘤纹理手柄 120mm | 细长杖身 9mm | LED 发光"
    
    title_bg = Image.new('RGBA', (1800, 150), (0, 0, 0, 150))
    img.paste(title_bg, (center_x - 900, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#FFFFFF', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#AAAAAA', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing reference photo accurate wand v16.0...")
draw_wand()
draw_annotations()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v160_reference_accurate.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
