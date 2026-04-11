"""
CyberWand v3.9 - 精确还原图片圆球特征
- 扁椭圆形状（沿杖身方向拉长）
- 纵向沟壑纹理（不是蜂窝）
- 自然过渡到杖身
- 深色有光泽
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math
import random

# 创建画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# 中心参数
center_x, center_y = width // 2, height // 2
angle = -35
rad = math.radians(angle)
scale = 15

# 魔杖参数
wand_length = 400 * scale
shaft_start_diameter = 6 * scale
shaft_end_diameter = 2 * scale

# 圆球节点参数
node_data = [
    {"pos": 25, "shaft_dia": 5.5, "node_dia": 7.5, "node_len": 10},
    {"pos": 18, "shaft_dia": 4.5, "node_dia": 6.8, "node_len": 9},
    {"pos": 12, "shaft_dia": 4.0, "node_dia": 6.0, "node_len": 8},
    {"pos": 7, "shaft_dia": 3.5, "node_dia": 5.2, "node_len": 7},
    {"pos": 3, "shaft_dia": 3.0, "node_dia": 4.5, "node_len": 6},
    {"pos": 0, "shaft_dia": 2.5, "node_dia": 3.8, "node_len": 5},
]

# 绘制扁椭圆圆球（沿杖身方向拉长）
def draw_ellipsoid_node(cx, cy, shaft_radius, node_radius, node_length, wand_angle_rad):
    """绘制扁椭圆状圆球（沿杖身方向拉长，纵向沟壑纹理）"""
    
    random.seed(42)
    
    # 计算杖身方向向量
    wand_dir_x = math.cos(wand_angle_rad)
    wand_dir_y = math.sin(wand_angle_rad)
    # 垂直方向向量
    perp_dir_x = -math.sin(wand_angle_rad)
    perp_dir_y = math.cos(wand_angle_rad)
    
    # 绘制多层椭圆（从外到内）
    for layer in range(int(node_radius * 2.5), 0, -2):
        t = layer / (node_radius * 2.5)
        brightness = int(80 * t + 20)
        r_val = int(brightness * 0.6)
        g_val = int(brightness * 0.4)
        b_val = int(brightness * 0.3)
        
        # 生成椭圆轮廓点（沿杖身方向拉长）
        num_points = 48
        points = []
        for i in range(num_points):
            theta = i * 2 * math.pi / num_points
            # 椭圆参数：长轴沿杖身方向，短轴垂直杖身
            major_radius = node_length * scale / 2 * (layer / (node_radius * 2.5))
            minor_radius = node_radius * (layer / (node_radius * 2.5))
            
            # 椭圆上的点（未旋转）
            ellipse_x = major_radius * math.cos(theta)
            ellipse_y = minor_radius * math.sin(theta)
            
            # 旋转到杖身方向
            rot_x = ellipse_x * wand_dir_x - ellipse_y * perp_dir_x
            rot_y = ellipse_x * wand_dir_y - ellipse_y * perp_dir_y
            
            points.append((cx + rot_x, cy + rot_y))
        
        if len(points) >= 3:
            draw.polygon([(int(x), int(y)) for x, y in points], 
                        fill=(r_val, g_val, b_val, 255))
    
    # 纵向沟壑纹理（沿杖身方向的凹槽）
    num_grooves = 8
    for i in range(num_grooves):
        groove_angle = i * 2 * math.pi / num_grooves
        groove_radius = node_radius * 0.6
        
        # 沟壑起点和终点（沿杖身方向）
        start_x = cx + math.cos(groove_angle) * groove_radius * 1.2
        start_y = cy + math.sin(groove_angle) * groove_radius * 0.9
        
        # 绘制沟壑（多个小凹坑连成线）
        num_pits = int(node_length * 1.5)
        for j in range(num_pits):
            t = j / num_pits
            # 沿杖身方向分布
            pit_x = start_x + (t - 0.5) * node_length * scale * 0.5 * wand_dir_x
            pit_y = start_y + (t - 0.5) * node_length * scale * 0.5 * wand_dir_y
            
            pit_size = int(node_radius * 0.12 * (1 - abs(t - 0.5) * 2))
            
            if pit_size > 0:
                for ps in range(pit_size, 0, -1):
                    pit_brightness = int(30 * (ps / pit_size))
                    draw.ellipse([
                        int(pit_x - ps), int(pit_y - ps),
                        int(pit_x + ps), int(pit_y + ps)
                    ], fill=(pit_brightness, pit_brightness//2, pit_brightness//3, 180))
    
    # 高光（左上角，沿杖身方向）
    highlight_x = cx - node_radius * 0.3 * perp_dir_x
    highlight_y = cy - node_radius * 0.3 * perp_dir_y
    for hr in range(int(node_radius * 0.2), 0, -1):
        highlight_points = []
        for j in range(8):
            hl_angle = j * 2 * math.pi / 8
            hl_r = hr * (1 + 0.1 * math.sin(hl_angle * 3))
            highlight_points.append((
                highlight_x + math.cos(hl_angle) * hl_r,
                highlight_y + math.sin(hl_angle) * hl_r
            ))
        if len(highlight_points) >= 3:
            draw.polygon([(int(x), int(y)) for x, y in highlight_points],
                        fill=(160, 130, 110, int(140 * hr / (node_radius * 0.2))))

# 绘制魔杖主体
def draw_wand():
    start_x = center_x - 300
    start_y = center_y + 300
    end_x = start_x + wand_length * math.cos(rad)
    end_y = start_y + wand_length * math.sin(rad)
    
    # 先绘制主杖身
    segments = 300
    for i in range(segments):
        t = i / segments
        x = start_x + t * (end_x - start_x)
        y = start_y + t * (end_y - start_y)
        
        diameter = shaft_start_diameter * (1 - t) + shaft_end_diameter * t
        radius = diameter / 2
        
        nx = -math.sin(rad)
        ny = -math.cos(rad)
        
        color_base = int(139 - t * 40)
        color_green = int(69 - t * 20)
        color_blue = int(19 - t * 5)
        
        draw.line([
            (x + nx * radius, y + ny * radius),
            (x - nx * radius, y - ny * radius)
        ], fill=(color_base, color_green, color_blue), width=int(diameter))
    
    # 绘制 6 个扁椭圆圆球节点
    for i, node in enumerate(node_data):
        t = (20 - node["pos"]) / 40
        node_x = start_x + t * (end_x - start_x)
        node_y = start_y + t * (end_y - start_y)
        
        shaft_radius = node["shaft_dia"] * scale / 2
        node_radius = node["node_dia"] * scale / 2
        node_length = node["node_len"]
        
        draw_ellipsoid_node(node_x, node_y, shaft_radius, node_radius, node_length, rad)
    
    # 手柄底部
    handle_x = start_x - 30
    handle_y = start_y - 30
    handle_radius = 7 * scale
    
    for r in range(int(handle_radius * 3), 0, -1):
        t = r / (handle_radius * 3)
        brightness = int(80 * t + 20)
        draw.ellipse([
            int(handle_x - r), int(handle_y - r),
            int(handle_x + r), int(handle_y + r)
        ], fill=(int(brightness * 0.6), int(brightness * 0.4), int(brightness * 0.3), 255))
    
    # 杖尖
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
        ], fill=(100, 60, 40), width=int(cone_radius * 2))

# 添加标题
def draw_title():
    try:
        font_large = ImageFont.truetype("msyh.ttc", 48)
        font_medium = ImageFont.truetype("msyh.ttc", 32)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    title = "CyberWand v3.9 - 扁椭圆圆球 + 纵向沟壑"
    subtitle = "沿杖身拉长 + 纵向纹理 + 自然过渡"
    
    title_bg = Image.new('RGBA', (1600, 150), (0, 0, 0, 100))
    img.paste(title_bg, (center_x - 800, 80), title_bg)
    
    draw.text((center_x, 100), title, fill='#2C1810', font=font_large, anchor="mm")
    draw.text((center_x, 140), subtitle, fill='#6B3E1F', font=font_medium, anchor="mm")

# 执行绘制
print("Drawing ellipsoid nodes with longitudinal grooves...")
draw_wand()
draw_title()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_v39_ellipsoid.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
