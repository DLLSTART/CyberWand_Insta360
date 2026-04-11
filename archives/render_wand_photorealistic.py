"""
CyberWand v3.3 - 精确还原图片中的魔杖
使用 Python + Pillow 进行精确比例建模渲染
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

# 创建超高清画布（4K）
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 魔杖精确参数（根据图片比例测量）
# 特点：底部（手柄）粗，顶端（杖尖）细
scale = 10  # 放大比例
wand_visual_length = 350 * scale  # 视觉长度

# 直径参数（精确还原图片）
handle_diameter = 10.0    # 手柄直径（最粗）
shaft_start_diameter = 5.0  # 杖身起始直径（靠近手柄）
shaft_end_diameter = 1.2    # 杖尖直径（最细）
center_x = width // 2
center_y = height // 2
angle = -35  # 魔杖角度（度）
rad = math.radians(angle)

# 绘制背景（透明渐变）
for y in range(height):
    alpha = int(200 - (y / height) * 50)
    draw.line([(0, y), (width, y)], fill=(245, 245, 240, alpha))

# 绘制装饰节点（精确还原图片中的蜂窝纹理）
def draw_realistic_node(cx, cy, radius, detail=True):
    """绘制写实风格的装饰节点"""
    
    # 节点主体（3D 球体效果）
    for r in range(int(radius*3), 0, -1):
        # 计算颜色渐变（模拟 3D 球体）
        t = r / (radius*3)
        brightness = int(180 * t + 40)
        r_val = int(brightness * 0.42)
        g_val = int(brightness * 0.24)
        b_val = int(brightness * 0.12)
        
        # 绘制椭圆（模拟球体透视）
        offset = int(radius * (1 - t) * 0.3)
        draw.ellipse([
            cx - r, cy - r + offset,
            cx + r, cy + r + offset
        ], fill=(r_val, g_val, b_val, 255))
    
    # 蜂窝纹理（凹坑）
    if detail:
        for i in range(8):
            angle_i = i * math.pi / 4
            for ring in range(1, 3):
                hx = cx + math.cos(angle_i) * radius * 0.4 * ring
                hy = cy + math.sin(angle_i) * radius * 0.4 * ring - radius * 0.2
                pit_size = int(radius * 0.15 * (3-ring))
                
                # 凹坑阴影
                for ps in range(pit_size, 0, -1):
                    shadow_offset = int(pit_size - ps)
                    pit_brightness = int(60 * (ps / pit_size))
                    draw.ellipse([
                        int(hx - ps), int(hy - ps + shadow_offset),
                        int(hx + ps), int(hy + ps + shadow_offset)
                    ], fill=(int(pit_brightness), int(pit_brightness*0.6), int(pit_brightness*0.4), 200))

# 绘制魔杖主体（精确还原图片）
def draw_realistic_wand():
    # 魔杖起点和终点
    start_x = center_x - 400
    start_y = center_y + 250
    end_x = start_x + wand_visual_length * math.cos(rad)
    end_y = start_y + wand_visual_length * math.sin(rad)
    
    # 绘制主杖身（细圆柱，精确渐变：底部粗→顶端细）
    segments = 200
    for i in range(segments):
        t = i / segments  # 0=手柄端，1=杖尖端
        
        # 计算位置
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        # 直径渐变：从 5mm（手柄端）渐变到 1.2mm（杖尖端）
        # 使用非线性渐变，更符合真实魔杖比例
        diameter = shaft_start_diameter * (1 - t) + shaft_end_diameter * t
        radius = diameter / 2
        
        # 法线方向
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        # 颜色渐变（深红木色，手柄端更深）
        color_base = int(107 - t * 40)
        
        # 绘制杖身段
        points = [
            (x + nx * radius, y + ny * radius),
            (x - nx * radius, y - ny * radius)
        ]
        draw.line(points, fill=(color_base, 62, 31), width=int(diameter * scale))
    
    # 绘制 6 个装饰节点（精确位置，根据图片测量）
    # 节点规律：越靠近杖尖（末尾），节点越大、间距越近
    # 但节点直径仍然遵循"底部粗顶端细"的整体规律
    node_positions_mm = [-8, -3, 3, 9, 15, 21]  # 距离手柄中心的距离（mm），负数=靠近杖尖
    node_radii_mm = [2.0, 2.3, 2.6, 2.9, 3.1, 3.3]  # 节点半径（mm），越靠近杖尖越大（但整体仍从粗到细）
    node_spacings = [5, 5, 6, 6, 6, 6]  # 节点间距（mm），越靠近杖尖越近
    
    for i, (pos_mm, radius_mm) in enumerate(zip(node_positions_mm, node_radii_mm)):
        # 计算节点位置
        t = (17.5 - pos_mm) / 35  # 转换为比例
        nx = start_x + t * (end_x - start_x)
        ny = start_y + t * (end_y - start_y)
        
        # 绘制节点
        draw_realistic_node(nx, ny, radius_mm * scale * 1.5, detail=True)
    
    # 手柄（球形设计，精确还原图片 - 最粗部分）
    handle_x = start_x - 20
    handle_y = start_y - 20
    
    # 手柄主体（大球，直径 10mm）
    handle_radius = handle_diameter / 2 * scale
    for r in range(int(handle_radius*3), 0, -1):
        t = r / (handle_radius*3)
        brightness = int(180 * t + 40)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness*0.42), int(brightness*0.24), int(brightness*0.12), 255))
    
    # 手柄底部装饰（小球，直径 7mm）
    bottom_x = handle_x + int(25 * scale)
    bottom_y = handle_y + int(25 * scale)
    bottom_radius = 3.5 * scale
    for r in range(int(bottom_radius*3), 0, -1):
        t = r / (bottom_radius*3)
        brightness = int(180 * t + 40)
        draw.ellipse([
            int(bottom_x - r), int(bottom_y - r),
            int(bottom_x + r), int(bottom_y + r)
        ], fill=(int(brightness*0.42), int(brightness*0.24), int(brightness*0.12), 255))
    
    # 杖尖（细锥形，最细部分）
    tip_x = end_x
    tip_y = end_y
    cone_length = 60 * scale
    
    for i in range(int(cone_length)):
        t = i / cone_length
        cone_x = tip_x - i * math.cos(rad)
        cone_y = tip_y - i * math.sin(rad)
        # 杖尖从 0.3mm 渐变到 1.2mm
        cone_radius = (0.3 + t * 1.5) * scale
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        draw.line([
            (cone_x + nx * cone_radius, cone_y + ny * cone_radius),
            (cone_x - nx * cone_radius, cone_y - ny * cone_radius)
        ], fill=(80, 50, 30), width=int(cone_radius * 2))
    
    # LED 发光效果（杖尖蓝色）
    for i in range(20, 0, -1):
        alpha = i * 12
        glow_radius = i * 2.5
        draw.ellipse([
            tip_x - glow_radius, tip_y - glow_radius,
            tip_x + glow_radius, tip_y + glow_radius
        ], fill=(100, 180, 255, alpha))
    
    # 按键（手柄顶部，隐藏式）
    button_x = handle_x - 10
    button_y = handle_y - 35
    draw.ellipse([
        button_x - 15, button_y - 15,
        button_x + 15, button_y + 15
    ], fill=(30, 30, 30, 255))
    
    # USB-C 开口（手柄底部）
    usb_x = handle_x + 35
    usb_y = handle_y + 30
    draw.rectangle([
        usb_x - 18, usb_y - 10,
        usb_x + 18, usb_y + 10
    ], fill=(20, 20, 20, 255))

# 添加景深和光影效果
def add_lighting_effects():
    # 创建高光层
    highlight = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    highlight_draw = ImageDraw.Draw(highlight)
    
    # 主光源（左上角）
    gradient = Image.new('L', (width//2, height//2), color=0)
    for y in range(height//2):
        for x in range(width//2):
            dist = math.sqrt(x*x + y*y)
            alpha = max(0, 100 - int(dist * 0.1))
            gradient.putpixel((x, y), alpha)
    
    highlight.paste((255, 255, 255, 50), (0, 0, width//2, height//2), gradient)
    
    # 合并高光
    img.alpha_composite(highlight)

# 绘制标题和标注
def draw_annotations():
    try:
        font_large = ImageFont.truetype("msyh.ttc", 48)
        font_medium = ImageFont.truetype("msyh.ttc", 32)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # 标题背景
    title_bg = Image.new('RGBA', (1200, 150), (0, 0, 0, 128))
    img.paste(title_bg, (center_x - 600, 80), title_bg)
    
    title = "CyberWand v3.3 - 精确还原版"
    subtitle = "1:1 还原图片中的魔杖造型"
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("正在绘制魔杖主体...")
draw_realistic_wand()

print("正在添加光影效果...")
add_lighting_effects()

print("正在添加标注...")
draw_annotations()

# 保存图像
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_photorealistic.png"
img.save(output_path, 'PNG', quality=95)
print(f"Photorealistic render complete! Saved to: {output_path}")
