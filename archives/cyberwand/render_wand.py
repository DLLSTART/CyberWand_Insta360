"""
CyberWand 3D 设计渲染脚本
使用 Python 生成魔杖的 3D 渲染图
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# 创建画布
width, height = 800, 600
img = Image.new('RGB', (width, height), color='#1a1a2e')
draw = ImageDraw.Draw(img)

# 中心点
cx, cy = width // 2, height // 2 + 50

# 魔杖参数
wand_length = 35
wand_width = 25
wand_height = 8

# 缩放比例
scale = 8

# 绘制魔杖主体（侧视图）
def draw_wand_side():
    # 手柄部分（椭圆）
    handle_center_x = cx + 80
    handle_center_y = cy
    handle_rx = 60 * scale / 35  # 长度方向
    handle_ry = 25 * scale / 2   # 宽度方向
    
    # 绘制手柄
    bbox = [
        handle_center_x - handle_rx,
        handle_center_y - handle_ry,
        handle_center_x + handle_rx,
        handle_center_y + handle_ry
    ]
    draw.ellipse(bbox, fill='#8B4513', outline='#5D2906', width=3)
    
    # 杖身部分（渐变锥形）
    # 从手柄到杖尖的过渡
    points = []
    for i in range(100):
        t = i / 100
        x = handle_center_x + handle_rx - t * 180
        # 宽度渐变：从 25mm 到 4mm
        current_width = (25 - t * 21) * scale / 2
        points.append((x, handle_center_y - current_width))
    
    # 上边缘
    draw.line(points, fill='#8B4513', width=3)
    
    # 下边缘
    points_lower = [(p[0], 2 * handle_center_y - p[1]) for p in points]
    draw.line(points_lower, fill='#8B4513', width=3)
    
    # 填充杖身
    all_points = points + points_lower[::-1]
    draw.polygon(all_points, fill='#8B4513', outline='#5D2906')
    
    # 杖尖（细端）
    tip_x = handle_center_x + handle_rx - 180
    tip_width = 4 * scale / 2
    tip_bbox = [
        tip_x - 15,
        handle_center_y - tip_width,
        tip_x + 15,
        handle_center_y + tip_width
    ]
    draw.ellipse(tip_bbox, fill='#A0522D', outline='#5D2906')
    
    # LED 发光效果（杖尖）
    glow_radius = 20
    for i in range(5, 0, -1):
        glow_color = f'rgba(100, 200, 255, {i*15})'
        glow_bbox = [
            tip_x - i*4,
            handle_center_y - i*2,
            tip_x + i*4,
            handle_center_y + i*2
        ]
        draw.ellipse(glow_bbox, fill=glow_color)
    
    # 按键（手柄顶部）
    button_x = handle_center_x - 20
    button_y = handle_center_y - handle_ry + 5
    draw.ellipse([button_x - 8, button_y - 8, button_x + 8, button_y + 8], 
                 fill='#2a2a2a', outline='#000000', width=2)
    
    # USB-C 开口（手柄底部）
    usb_x = handle_center_x + handle_rx - 10
    usb_y = handle_center_y + handle_ry - 5
    draw.rectangle([usb_x - 12, usb_y - 6, usb_x + 12, usb_y + 6], 
                   fill='#1a1a1a', outline='#333333')

# 绘制俯视图
def draw_wand_top():
    top_cx, top_cy = cx, cy - 180
    
    # 手柄（矩形 + 圆角）
    handle_w = 80
    handle_h = 30
    draw.rounded_rectangle([
        top_cx - handle_w//2,
        top_cy - handle_h//2,
        top_cx + handle_w//2,
        top_cy + handle_h//2
    ], radius=15, fill='#8B4513', outline='#5D2906', width=3)
    
    # 杖身（渐变）
    for i in range(60):
        t = i / 60
        x = top_cx + handle_w//2 + t * 100
        current_h = handle_h * (1 - t * 0.7)
        draw.line([
            (x, top_cy - current_h//2),
            (x, top_cy + current_h//2)
        ], fill='#8B4513', width=2)
    
    # 杖尖
    tip_x = top_cx + handle_w//2 + 100
    draw.ellipse([
        tip_x - 10,
        top_cy - 5,
        tip_x + 10,
        top_cy + 5
    ], fill='#A0522D', outline='#5D2906')

# 绘制尺寸标注
def draw_dimensions():
    # 长度标注
    dim_y = cy + 80
    draw.line([(cx - 100, dim_y), (cx + 100, dim_y)], fill='#00ff00', width=2)
    draw.line([(cx - 100, dim_y - 5), (cx - 100, dim_y + 5)], fill='#00ff00', width=2)
    draw.line([(cx + 100, dim_y - 5), (cx + 100, dim_y + 5)], fill='#00ff00', width=2)
    draw.text((cx - 20, dim_y + 10), "35mm", fill='#00ff00', 
              font=ImageFont.load_default())
    
    # 宽度标注
    dim_x = cx - 150
    draw.line([(dim_x, cy - 50), (dim_x, cy + 50)], fill='#00ff00', width=2)
    draw.line([(dim_x - 5, cy - 50), (dim_x + 5, cy - 50)], fill='#00ff00', width=2)
    draw.line([(dim_x - 5, cy + 50), (dim_x + 5, cy + 50)], fill='#00ff00', width=2)
    draw.text((dim_x - 30, cy - 10), "25mm", fill='#00ff00',
              font=ImageFont.load_default())

# 绘制标题
def draw_title():
    title = "CyberWand v3.0 - 哈利波特风格魔杖"
    subtitle = "赛博魔杖 3D 设计图"
    
    try:
        font_large = ImageFont.truetype("simhei.ttf", 24)
        font_medium = ImageFont.truetype("simhei.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # 标题
    draw.text((width//2 - 200, 30), title, fill='#ffffff', font=font_large)
    # 副标题
    draw.text((width//2 - 100, 60), subtitle, fill='#aaaaaa', font=font_medium)

# 绘制图例
def draw_legend():
    legend_y = height - 80
    legend_x = 50
    
    try:
        font_small = ImageFont.truetype("simhei.ttf", 12)
    except:
        font_small = ImageFont.load_default()
    
    items = [
        ("🔴 LED 灯效（杖尖）", '#64c8ff'),
        ("🟤 手柄（深棕色）", '#8B4513'),
        ("⚫ 按键（顶部）", '#2a2a2a'),
        ("🔌 USB-C（底部）", '#1a1a1a'),
    ]
    
    for i, (text, color) in enumerate(items):
        y = legend_y + i * 25
        draw.rectangle([legend_x, y, legend_x + 15, y + 15], fill=color)
        draw.text((legend_x + 25, y), text, fill='#ffffff', font=font_small)

# 执行绘制
draw_title()
draw_wand_side()
draw_wand_top()
draw_dimensions()
draw_legend()

# 保存图像
output_path = r"D:\workspace\instafreelink\enclosure\cyberwand\render_preview.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
