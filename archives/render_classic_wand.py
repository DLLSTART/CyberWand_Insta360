"""
CyberWand 经典魔杖风格 - 高清渲染脚本
参考皇上发的新图片（6 个装饰节点）
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# 创建超高清画布
width, height = 2560, 1440
img = Image.new('RGB', (width, height), color='#f5f5f5')
draw = ImageDraw.Draw(img)

# 中心点和角度
cx, cy = width // 2, height // 2
angle = 45  # 45 度斜放
rad = math.radians(angle)

# 魔杖参数
wand_length = 35
scale = 25  # 放大比例

# 绘制背景（简洁白色）
for y in range(height):
    r = int(245 + (y / height) * 10)
    g = int(245 + (y / height) * 10)
    b = int(245 + (y / height) * 10)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# 绘制装饰节点（蜂窝纹理）
def draw_node(x, y, radius):
    # 节点主体
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                 fill='#4A3728', outline='#2C1810', width=2)
    
    # 高光
    highlight_x = x - radius * 0.3
    highlight_y = y - radius * 0.3
    draw.ellipse([highlight_x - radius//4, highlight_y - radius//4, 
                 highlight_x + radius//4, highlight_y + radius//4], 
                 fill='#6B3E1F')
    
    # 蜂窝纹理（凹坑）
    for i in range(8):
        angle_i = i * math.pi / 4
        hx = x + math.cos(angle_i) * radius * 0.6
        hy = y + math.sin(angle_i) * radius * 0.6
        pit_radius = radius * 0.15
        draw.ellipse([hx - pit_radius, hy - pit_radius, 
                     hx + pit_radius, hy + pit_radius], 
                     fill='#2C1810')

# 绘制经典魔杖（参考新图片）
def draw_classic_wand():
    # 魔杖起点和终点
    start_x = cx - 400
    start_y = cy + 300
    end_x = start_x + 900 * math.cos(rad)
    end_y = start_y - 900 * math.sin(rad)
    
    # 绘制主杖身（细圆柱，渐变）
    wand_radius_start = 20
    wand_radius_end = 12
    
    for i in range(100):
        t = i / 99
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        current_radius = wand_radius_start - t * (wand_radius_start - wand_radius_end)
        
        # 法线方向
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        # 绘制杖身段（深红木色）
        color_val = int(107 - t * 20)  # 渐变
        draw.line([
            (x + nx * current_radius, y + ny * current_radius),
            (x - nx * current_radius, y - ny * current_radius)
        ], fill=(color_val, 62, 31), width=3)
    
    # 绘制 6 个装饰节点（从手柄到杖尖递减）
    node_positions = [0.85, 0.70, 0.55, 0.40, 0.25, 0.10]
    node_radii = [35, 32, 29, 26, 23, 20]
    
    for pos, radius in zip(node_positions, node_radii):
        nx = start_x + pos * (end_x - start_x)
        ny = start_y + pos * (end_y - start_y)
        draw_node(nx, ny, radius)
    
    # 手柄底部（特殊球形设计）
    handle_x = start_x - 30
    handle_y = start_y + 30
    draw.ellipse([handle_x - 45, handle_y - 45, handle_x + 45, handle_y + 45], 
                 fill='#6B3E1F', outline='#2C1810', width=3)
    
    # 手柄底部装饰
    draw.ellipse([handle_x - 35, handle_y - 35, handle_x + 35, handle_y + 35], 
                 fill='#4A3728', outline='#2C1810', width=2)
    
    # 杖尖（细长锥形）
    tip_x = end_x
    tip_y = end_y
    cone_base_x = end_x - 100 * math.cos(rad)
    cone_base_y = end_y + 100 * math.sin(rad)
    
    cone_points = [
        (tip_x, tip_y),
        (cone_base_x, cone_base_y - 12),
        (cone_base_x, cone_base_y + 12)
    ]
    draw.polygon(cone_points, fill='#6B3E1F', outline='#2C1810')
    
    # LED 发光效果（杖尖蓝色）
    for i in range(15, 0, -1):
        alpha = i * 8
        glow_radius = i * 2.5
        glow_color = f'rgba(100, 180, 255, {alpha})'
        draw.ellipse([tip_x - glow_radius, tip_y - glow_radius, 
                     tip_x + glow_radius, tip_y + glow_radius], 
                     fill=glow_color)
    
    # 按键（手柄顶部，隐藏式）
    button_x = handle_x - 15
    button_y = handle_y - 40
    draw.ellipse([button_x - 15, button_y - 15, button_x + 15, button_y + 15], 
                 fill='#2a2a2a', outline='#000000', width=2)
    
    # USB-C 开口（手柄底部）
    usb_x = handle_x + 40
    usb_y = handle_y + 35
    draw.rectangle([usb_x - 18, usb_y - 10, usb_x + 18, usb_y + 10], 
                   fill='#1a1a1a', outline='#333333')

# 绘制尺寸标注
def draw_dimensions():
    try:
        font_dim = ImageFont.truetype("simhei.ttf", 24)
    except:
        font_dim = ImageFont.load_default()
    
    # 长度标注
    dim_start = (cx - 450, cy + 400)
    dim_end = (cx + 500, cy + 400)
    
    draw.line([dim_start, dim_end], fill='#00aa00', width=3)
    draw.line([dim_start, (dim_start[0], dim_start[1] + 20)], fill='#00aa00', width=3)
    draw.line([dim_end, (dim_end[0], dim_end[1] + 20)], fill='#00aa00', width=3)
    
    draw.text((cx - 40, cy + 410), "35mm", fill='#00aa00', font=font_dim)

# 绘制标题
def draw_title():
    try:
        font_large = ImageFont.truetype("simhei.ttf", 42)
        font_medium = ImageFont.truetype("simhei.ttf", 28)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    title = "CyberWand v3.2 - 哈利波特经典魔杖"
    subtitle = "赛博魔杖 3D 设计图（6 节点蜂窝纹理版）"
    
    # 标题背景
    draw.rectangle([(cx - 400, 50), (cx + 400, 140)], fill='#00000060')
    
    draw.text((cx - 320, 65), title, fill='#2C1810', font=font_large)
    draw.text((cx - 260, 105), subtitle, fill='#6B3E1F', font=font_medium)

# 绘制图例
def draw_legend():
    legend_x = 100
    legend_y = height - 350
    
    try:
        font_small = ImageFont.truetype("simhei.ttf", 18)
    except:
        font_small = ImageFont.load_default()
    
    items = [
        ("🔵 LED 灯效（杖尖）", '#64b4ff'),
        ("🟤 深红木色杖身", '#6B3E1F'),
        ("⚫ 按键（手柄顶部）", '#2a2a2a'),
        ("🔌 USB-C（手柄底部）", '#1a1a1a'),
        ("✨ 装饰节点（6 个蜂窝纹理）", '#4A3728'),
    ]
    
    for i, (text, color) in enumerate(items):
        y = legend_y + i * 45
        draw.rectangle([legend_x, y, legend_x + 35, y + 35], fill=color)
        draw.text((legend_x + 50, y + 8), text, fill='#2C1810', font=font_small)

# 执行绘制
draw_title()
draw_classic_wand()
draw_dimensions()
draw_legend()

# 添加水印
draw.text((width - 350, height - 50), "CyberWand v3.2 | Classic Wand", fill='#999999', 
          font=ImageFont.load_default())

# 保存图像
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\classic_wand_render.png"
img.save(output_path, 'PNG', quality=95)
print(f"Classic wand render complete! Saved to: {output_path}")
