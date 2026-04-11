"""
CyberWand v18.0 - 整体圆柱手柄版
修正：手柄是一整个大圆柱，不是多个圆球拼接

设计要点：
1. 手柄：完整圆柱体 30mm×110mm，无分段
2. 杖身：10mm 铝管，简洁直杆
3. 连接：手柄与杖身平滑过渡
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
scale = 6

# 魔杖参数
wand_total_length = 500
handle_length = 110  # 手柄长 110mm（完整圆柱）
handle_diameter = 30  # 手柄直径 30mm（完整圆柱）
shaft_diameter = 20  # 杖身直径 20mm（内径改为 20mm）

# 绘制完整圆柱手柄
def draw_solid_cylinder_handle(start_x, start_y, handle_length, handle_radius, wand_angle_rad):
    """绘制完整圆柱手柄 - 无分段"""
    
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    end_x = start_x + handle_length * wand_dir_x
    end_y = start_y + handle_length * wand_dir_y
    
    # 圆柱主体（金属渐变）
    num_segments = int(handle_length / 2)
    for i in range(num_segments):
        t = i / num_segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        # 金属色渐变（深灰→银灰）
        brightness = int(140 * t + 100)
        
        for r in range(int(handle_radius * 2.2), 0, -2):
            layer_t = r / (handle_radius * 2.2)
            layer_brightness = int(brightness * layer_t)
            
            # 圆柱中心偏移（3D 效果）
            cx = x - perp_dir_x * handle_radius * 0.3
            cy = y - perp_dir_y * handle_radius * 0.3
            
            # 金属质感（银灰色）
            draw.ellipse([
                int(cx - r), int(cy - r),
                int(cx + r), int(cy + r)
            ], fill=(layer_brightness, layer_brightness, layer_brightness + 20, 255))
    
    # 高光（金属反光）
    highlight_start_x = start_x - perp_dir_x * handle_radius * 0.4
    highlight_start_y = start_y - perp_dir_y * handle_radius * 0.4
    highlight_length = int(handle_length * 0.7)
    
    for i in range(highlight_length):
        t = i / highlight_length
        hx = highlight_start_x + t * handle_length * wand_dir_x
        hy = highlight_start_y + t * handle_length * wand_dir_y
        alpha = int(80 * (1 - t))
        
        highlight_width = handle_radius * 0.25
        draw.line([
            (hx - perp_dir_x * highlight_width, hy - perp_dir_y * highlight_width),
            (hx + perp_dir_x * highlight_width, hy + perp_dir_y * highlight_width)
        ], fill=(255, 255, 255, alpha), width=3)
    
    # 手柄底部（带 USB-C 开孔）
    for r in range(int(handle_radius * 2.3), 0, -2):
        t = r / (handle_radius * 2.3)
        brightness = int(130 * t + 95)
        draw.ellipse([
            int(start_x - r), int(start_y - r),
            int(start_x + r), int(start_y + r)
        ], fill=(brightness, brightness, brightness + 20, 255))
    
    # USB-C 开孔
    usb_hole_width = 8 * scale
    usb_hole_height = 4 * scale
    draw.rounded_rectangle([
        int(start_x - usb_hole_width), int(start_y - usb_hole_height),
        int(start_x + usb_hole_width), int(start_y + usb_hole_height)
    ], radius=2, fill=(35, 35, 35, 255))
    
    # 装饰环（手柄与杖身连接处）
    ring_x = end_x
    ring_y = end_y
    ring_radius = handle_radius * 1.05
    ring_width = 8 * scale
    
    for r in range(int(ring_radius * 2), 0, -1):
        t = r / (ring_radius * 2)
        brightness = int(110 * t + 85)
        draw.ellipse([
            int(ring_x - r), int(ring_y - r),
            int(ring_x + r), int(ring_y + r)
        ], fill=(brightness, brightness, brightness + 10, 255))

# 绘制杖身
def draw_wand_shaft(shaft_start_x, shaft_start_y, shaft_end_x, shaft_end_y, shaft_radius, wand_angle_rad):
    """绘制铝管杖身"""
    
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    shaft_length = math.sqrt((shaft_end_x - shaft_start_x)**2 + (shaft_end_y - shaft_start_y)**2)
    segments = int(shaft_length / 2)
    
    for i in range(segments):
        t = i / segments
        x = shaft_start_x + t * (shaft_end_x - shaft_start_x)
        y = shaft_start_y + t * (shaft_end_y - shaft_start_y)
        
        # 铝管金属色
        brightness = int(200 - t * 30)
        
        nx = -math.sin(wand_angle_rad)
        ny = -math.cos(wand_angle_rad)
        
        draw.line([
            (x + nx * shaft_radius, y + ny * shaft_radius),
            (x - nx * shaft_radius, y - ny * shaft_radius)
        ], fill=(brightness, brightness, brightness + 10), width=int(shaft_radius * 2))
    
    # 铝管高光
    highlight_x = shaft_start_x + (shaft_end_x - shaft_start_x) * 0.3
    highlight_y = shaft_start_y + (shaft_end_y - shaft_start_y) * 0.3
    highlight_width = shaft_radius * 0.4
    highlight_length = shaft_length * 0.4
    
    for i in range(int(highlight_length)):
        hx = highlight_x + i * math.cos(wand_angle_rad)
        hy = highlight_y + i * math.sin(wand_angle_rad)
        alpha = int(100 * (1 - i / highlight_length))
        
        draw.line([
            (hx - perp_dir_x * highlight_width, hy - perp_dir_y * highlight_width),
            (hx + perp_dir_x * highlight_width, hy + perp_dir_y * highlight_width)
        ], fill=(255, 255, 255, alpha), width=2)

# 绘制杖尖 LED
def draw_tip_with_led(tip_x, tip_y, shaft_radius, wand_angle_rad):
    """绘制 LED 组件"""
    
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    
    # LED 底座
    led_base_radius = shaft_radius * 1.3
    led_base_length = 25 * scale
    
    for i in range(int(led_base_length)):
        t = i / led_base_length
        cone_x = tip_x - i * wand_dir_x
        cone_y = tip_y - i * wand_dir_y
        cone_radius = led_base_radius - t * (led_base_radius - shaft_radius)
        
        nx = -math.sin(wand_angle_rad)
        ny = -math.cos(wand_angle_rad)
        
        draw.line([
            (cone_x + nx * cone_radius, cone_y + ny * cone_radius),
            (cone_x - nx * cone_radius, cone_y - ny * cone_radius)
        ], fill=(180, 180, 185), width=int(cone_radius * 2))
    
    # LED 发光
    for i in range(20, 0, -1):
        alpha = i * 12
        glow_radius = i * 2.5
        draw.ellipse([
            int(tip_x - glow_radius), int(tip_y - glow_radius),
            int(tip_x + glow_radius), int(tip_y + glow_radius)
        ], fill=(150, 200, 255, alpha))
    
    # LED 核心
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
    
    # 1. 绘制完整圆柱手柄
    handle_length_scaled = handle_length * scale
    handle_radius = handle_diameter * scale / 2
    draw_solid_cylinder_handle(handle_start_x, handle_start_y, handle_length_scaled, handle_radius, rad)
    
    # 手柄末端位置
    handle_end_x = handle_start_x + handle_length_scaled * math.cos(rad)
    handle_end_y = handle_start_y + handle_length_scaled * math.sin(rad)
    
    # 2. 绘制杖身
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
        ("总长度：500mm（手柄 110mm + 杖身 390mm）", center_x - 280, center_y + 450),
        ("手柄：Φ30mm 完整圆柱（无分段圆球）", center_x - 280, center_y + 480),
        ("杖身：Φ10mm 铝管（简洁直杆）", center_x - 280, center_y + 510),
        ("连接：平滑过渡 + 装饰环", center_x - 280, center_y + 540),
        ("制造：CNC 整体加工 / 3D 打印", center_x - 280, center_y + 570),
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
    
    title = "CyberWand v18.0 - 整体圆柱手柄版"
    subtitle = "手柄Φ30mm 完整圆柱 | 无分段圆球 | 简洁易制造"
    
    title_bg = Image.new('RGBA', (1800, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 900, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing solid cylinder handle wand v18.0...")
draw_wand()
draw_annotations()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v180_solid_cylinder.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
