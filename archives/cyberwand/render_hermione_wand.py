"""
CyberWand 赫敏魔杖风格 - 高质量渲染脚本
使用 Python 生成 3D 渲染图
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# 创建高清画布
width, height = 1920, 1080
img = Image.new('RGB', (width, height), color='#1a1a2e')
draw = ImageDraw.Draw(img)

# 中心点
cx, cy = width // 2, height // 2

# 魔杖参数
wand_length = 35
wand_width = 25

# 缩放比例（放大以便展示细节）
scale = 15

# 绘制背景渐变
for y in range(height):
    r = int(26 + (y / height) * 20)
    g = int(26 + (y / height) * 20)
    b = int(46 + (y / height) * 30)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# 绘制赫敏魔杖（带装饰球）
def draw_hermione_wand():
    # 魔杖角度（45 度斜放，更有动感）
    angle = 30
    rad = math.radians(angle)
    
    # 魔杖起点
    start_x = cx - 200
    start_y = cy + 100
    
    # 魔杖终点
    end_x = start_x + 500 * math.cos(rad)
    end_y = start_y - 500 * math.sin(rad)
    
    # 绘制主杖身（细圆柱）
    wand_radius = 15
    # 使用多边形模拟圆柱
    points_top = []
    points_bottom = []
    
    for i in range(100):
        t = i / 99
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        # 法线方向
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        points_top.append((x + nx * wand_radius, y + ny * wand_radius))
        points_bottom.append((x - nx * wand_radius, y - ny * wand_radius))
    
    # 绘制杖身主体（深红木色）
    wand_body = points_top + points_bottom[::-1]
    draw.polygon(wand_body, fill='#8B4513', outline='#5D2906')
    
    # 绘制 5 个装饰球（赫敏风格特色）
    sphere_positions = [0.15, 0.30, 0.45, 0.60, 0.75]
    sphere_radii = [35, 32, 30, 28, 26]  # 从手柄到杖尖递减
    
    for i, (pos, radius) in enumerate(zip(sphere_positions, sphere_radii)):
        sx = start_x + pos * (end_x - start_x)
        sy = start_y + pos * (end_y - start_y)
        
        # 绘制球体（带蜂窝纹理）
        # 球体主体
        draw.ellipse([sx - radius, sy - radius, sx + radius, sy + radius], 
                     fill='#A0522D', outline='#5D2906', width=3)
        
        # 高光
        highlight_x = sx - radius * 0.3
        highlight_y = sy - radius * 0.3
        draw.ellipse([highlight_x - radius//4, highlight_y - radius//4, 
                     highlight_x + radius//4, highlight_y + radius//4], 
                     fill='#D2691E')
        
        # 蜂窝纹理（简化版）
        for j in range(6):
            angle_j = j * math.pi / 3
            hx = sx + math.cos(angle_j) * radius * 0.6
            hy = sy + math.sin(angle_j) * radius * 0.6
            draw.circle((hx, hy), radius=3, fill='#5D2906')
    
    # 手柄底部（大球）
    handle_x = start_x - 20
    handle_y = start_y + 20
    draw.ellipse([handle_x - 40, handle_y - 40, handle_x + 40, handle_y + 40], 
                 fill='#8B4513', outline='#5D2906', width=3)
    
    # 杖尖（细锥）
    tip_x = end_x
    tip_y = end_y
    # 锥形
    cone_points = [
        (tip_x, tip_y),
        (end_x - 80 * math.cos(rad), end_y + 80 * math.sin(rad) - 10),
        (end_x - 80 * math.cos(rad), end_y + 80 * math.sin(rad) + 10)
    ]
    draw.polygon(cone_points, fill='#A0522D', outline='#5D2906')
    
    # LED 发光效果（杖尖蓝色）
    for i in range(10, 0, -1):
        glow_color = f'rgba(100, 200, 255, {i*10})'
        glow_radius = i * 3
        draw.ellipse([tip_x - glow_radius, tip_y - glow_radius, 
                     tip_x + glow_radius, tip_y + glow_radius], 
                     fill=glow_color)
    
    # 按键（手柄顶部，隐藏式）
    button_x = handle_x - 10
    button_y = handle_y - 35
    draw.ellipse([button_x - 12, button_y - 12, button_x + 12, button_y + 12], 
                 fill='#2a2a2a', outline='#000000', width=2)
    
    # USB-C 开口（手柄底部）
    usb_x = handle_x + 30
    usb_y = handle_y + 30
    draw.rectangle([usb_x - 15, usb_y - 8, usb_x + 15, usb_y + 8], 
                   fill='#1a1a1a', outline='#333333')

# 绘制尺寸标注
def draw_dimensions():
    # 长度标注
    dim_start = (cx - 250, cy + 200)
    dim_end = (cx + 300, cy + 200)
    
    draw.line([dim_start, dim_end], fill='#00ff00', width=3)
    draw.line([dim_start, (dim_start[0], dim_start[1] + 15)], fill='#00ff00', width=3)
    draw.line([dim_end, (dim_end[0], dim_end[1] + 15)], fill='#00ff00', width=3)
    
    try:
        font_dim = ImageFont.truetype("simhei.ttf", 20)
    except:
        font_dim = ImageFont.load_default()
    
    draw.text((cx - 30, cy + 210), "35mm", fill='#00ff00', font=font_dim)

# 绘制标题
def draw_title():
    try:
        font_large = ImageFont.truetype("simhei.ttf", 36)
        font_medium = ImageFont.truetype("simhei.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    title = "CyberWand v3.1 - 赫敏魔杖风格"
    subtitle = "赛博魔杖 3D 设计图（哈利波特赫敏同款）"
    
    # 标题背景
    draw.rectangle([(cx - 350, 40), (cx + 350, 120)], fill='#00000080')
    
    draw.text((cx - 280, 55), title, fill='#ffffff', font=font_large)
    draw.text((cx - 220, 95), subtitle, fill='#aaaaaa', font=font_medium)

# 绘制图例
def draw_legend():
    legend_x = 80
    legend_y = height - 250
    
    try:
        font_small = ImageFont.truetype("simhei.ttf", 16)
    except:
        font_small = ImageFont.load_default()
    
    items = [
        ("🔵 LED 灯效（杖尖）", '#64c8ff'),
        ("🟤 深红木色杖身", '#8B4513'),
        ("⚫ 按键（手柄顶部）", '#2a2a2a'),
        ("🔌 USB-C（手柄底部）", '#1a1a1a'),
        ("✨ 装饰球（5 个蜂窝纹理）", '#A0522D'),
    ]
    
    for i, (text, color) in enumerate(items):
        y = legend_y + i * 40
        draw.rectangle([legend_x, y, legend_x + 30, y + 30], fill=color)
        draw.text((legend_x + 45, y + 5), text, fill='#ffffff', font=font_small)

# 执行绘制
draw_title()
draw_hermione_wand()
draw_dimensions()
draw_legend()

# 添加水印
draw.text((width - 300, height - 40), "CyberWand v3.1", fill='#666666', 
          font=ImageFont.load_default())

# 保存图像
output_path = r"D:\workspace\instafreelink\enclosure\cyberwand\hermione_wand_render.png"
img.save(output_path, 'PNG', quality=95)
print(f"Hermione wand render complete! Saved to: {output_path}")
