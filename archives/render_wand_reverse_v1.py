"""
魔杖 v1.0 渲染脚本 - 基于图片逆向设计
风格：哈利波特风格装饰魔杖
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

# 创建画布
width, height = 3840, 2160
img = Image.new('RGBA', (width, height), (245, 240, 230, 255))  # 米色背景
draw = ImageDraw.Draw(img)

# 中心参数
center_x, center_y = width // 2, height // 2

# 魔杖参数（逆向工程结果）
total_length = 350  # mm
handle_dia = 22     # mm
tip_dia = 5         # mm

# 节点参数 [位置，直径，长度]
nodes = [
    [35,  26, 22],   # 节点 1
    [80,  23, 19],   # 节点 2
    [120, 21, 17],   # 节点 3
    [160, 19, 15],   # 节点 4
    [195, 16, 13],   # 节点 5
    [225, 13, 11]    # 节点 6
]

# 渲染比例
scale = 3.5  # 放大比例

# 魔杖倾斜角度
angle = -25  # 逆时针倾斜 25 度
angle_rad = math.radians(angle)

def rotate_point(x, y, angle_rad):
    """旋转点"""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return (
        x * cos_a - y * sin_a,
        x * sin_a + y * cos_a
    )

def get_rod_diameter(z):
    """计算杆身直径（线性锥度）"""
    return handle_dia - (handle_dia - tip_dia) * (z / total_length)

def draw_hexagon(cx, cy, radius, rotation=0):
    """绘制六边形（蜂窝单元）"""
    points = []
    for i in range(6):
        a = rotation + i * math.pi / 3
        points.append((
            cx + radius * math.cos(a),
            cy + radius * math.sin(a)
        ))
    return points

def draw_wand():
    """绘制魔杖主体"""
    # 魔杖基线（从手柄到顶端）
    wand_start_x = center_x - 400
    wand_start_y = center_y + 100
    wand_length_px = total_length * scale * 0.8  # 80% 比例用于渲染
    
    # 计算顶端位置
    wand_end_x = wand_start_x + wand_length_px * math.cos(angle_rad)
    wand_end_y = wand_start_y + wand_length_px * math.sin(angle_rad)
    
    # 绘制杆身（分段绘制锥度）
    num_segments = 100
    for i in range(num_segments):
        z1 = (i / num_segments) * total_length
        z2 = ((i + 1) / num_segments) * total_length
        
        dia1 = get_rod_diameter(z1)
        dia2 = get_rod_diameter(z2)
        
        pos1_x = wand_start_x + (z1 / total_length) * wand_length_px * math.cos(angle_rad)
        pos1_y = wand_start_y + (z1 / total_length) * wand_length_px * math.sin(angle_rad)
        
        pos2_x = wand_start_x + (z2 / total_length) * wand_length_px * math.cos(angle_rad)
        pos2_y = wand_start_y + (z2 / total_length) * wand_length_px * math.sin(angle_rad)
        
        # 杆身颜色（深棕色渐变）
        color_val = 101 - int((i / num_segments) * 30)
        rod_color = (color_val, 61, 41, 255)
        
        # 绘制杆身段
        seg_width1 = dia1 * scale * 0.5
        seg_width2 = dia2 * scale * 0.5
        
        # 计算垂直方向
        perp_angle = angle_rad + math.pi / 2
        perp_x = math.cos(perp_angle)
        perp_y = math.sin(perp_angle)
        
        # 绘制四边形
        poly_points = [
            (pos1_x - perp_x * seg_width1, pos1_y - perp_y * seg_width1),
            (pos1_x + perp_x * seg_width1, pos1_y + perp_y * seg_width1),
            (pos2_x + perp_x * seg_width2, pos2_y + perp_y * seg_width2),
            (pos2_x - perp_x * seg_width2, pos2_y - perp_y * seg_width2),
        ]
        draw.polygon(poly_points, fill=rod_color)
    
    # 绘制节点（蜂窝纹理）
    for node_idx, (node_pos, node_dia, node_len) in enumerate(nodes):
        # 计算节点中心位置
        node_center_x = wand_start_x + (node_pos / total_length) * wand_length_px * math.cos(angle_rad)
        node_center_y = wand_start_y + (node_pos / total_length) * wand_length_px * math.sin(angle_rad)
        
        # 节点颜色（比杆身略深）
        node_color = (71, 41, 31, 255)
        
        # 节点半径
        node_radius = node_dia * scale * 0.5
        
        # 节点长度（沿魔杖方向）
        node_len_px = node_len * scale * 0.8
        
        # 绘制节点椭圆轮廓
        node_points = []
        for t in range(0, 360, 5):
            t_rad = math.radians(t)
            # 椭圆参数
            rx = node_radius
            ry = node_len_px * 0.5
            
            # 旋转后坐标
            px = rx * math.cos(t_rad)
            py = ry * math.sin(t_rad)
            
            # 旋转到魔杖角度
            px, py = rotate_point(px, py, angle_rad)
            
            node_points.append((node_center_x + px, node_center_y + py))
        
        draw.polygon(node_points, fill=node_color)
        
        # 绘制蜂窝纹理
        # 计算蜂窝单元
        circumference = math.pi * node_dia
        num_cells_round = max(6, int(circumference / 3))
        num_cells_height = max(3, int(node_len / 3))
        
        for i in range(num_cells_height):
            for j in range(num_cells_round):
                # 蜂窝单元位置
                z_offset = (i / num_cells_height) * node_len_px - node_len_px * 0.5
                angle_offset = (j / num_cells_round) * 2 * math.pi
                
                # 错位排列
                if i % 2 == 0:
                    angle_offset += math.pi / num_cells_round
                
                # 计算世界坐标
                cell_z = node_center_x + z_offset * math.cos(angle_rad)
                cell_y = node_center_y + z_offset * math.sin(angle_rad)
                
                # 径向偏移
                radial_offset = node_radius * 0.7
                cell_x = cell_z + radial_offset * math.cos(angle_offset) * math.cos(angle_rad)
                cell_y_adj = cell_y + radial_offset * math.cos(angle_offset) * math.sin(angle_rad)
                
                # 绘制蜂窝凹陷（深色六边形）
                hex_radius = 2.5 * scale
                hex_points = draw_hexagon(cell_x, cell_y_adj, hex_radius, angle_offset)
                draw.polygon(hex_points, fill=(51, 31, 21, 200))
    
    # 绘制手柄（加粗部分）
    handle_end_x = wand_start_x
    handle_end_y = wand_start_y
    handle_len_px = 40 * scale * 0.8
    
    handle_start_x = wand_start_x - handle_len_px * math.cos(angle_rad)
    handle_start_y = wand_start_y - handle_len_px * math.sin(angle_rad)
    
    # 手柄颜色（更深）
    handle_color = (61, 31, 21, 255)
    
    handle_width = handle_dia * scale * 0.55
    handle_poly = [
        (handle_start_x - perp_x * handle_width, handle_start_y - perp_y * handle_width),
        (handle_start_x + perp_x * handle_width, handle_start_y + perp_y * handle_width),
        (handle_end_x + perp_x * handle_width, handle_end_y + perp_y * handle_width),
        (handle_end_x - perp_x * handle_width, handle_end_y - perp_y * handle_width),
    ]
    draw.polygon(handle_poly, fill=handle_color)
    
    # 手柄底部装饰环
    ring_x = handle_start_x
    ring_y = handle_start_y
    ring_radius = handle_width * 1.2
    draw.ellipse([
        ring_x - ring_radius, ring_y - ring_radius,
        ring_x + ring_radius, ring_y + ring_radius
    ], outline=(41, 21, 11, 255), width=int(3 * scale))
    
    # 绘制顶端（尖端）
    tip_x = wand_end_x
    tip_y = wand_end_y
    tip_radius = tip_dia * scale * 0.5
    
    # 顶端渐变
    for i in range(10, 0, -1):
        alpha = i * 25
        tip_color = (101 - i*5, 61 - i*3, 41 - i*2, alpha)
        tip_r = tip_radius * (i / 10)
        draw.ellipse([
            tip_x - tip_r, tip_y - tip_r,
            tip_x + tip_r, tip_y + tip_r
        ], fill=tip_color)

def draw_dimensions():
    """添加尺寸标注"""
    try:
        font = ImageFont.truetype("msyh.ttc", 36)
        font_small = ImageFont.truetype("msyh.ttc", 28)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 标题
    title = "魔杖 v1.0 - 逆向工程设计"
    subtitle = "基于图片分析 | 蜂窝纹理 | 6 节点 | 350mm"
    
    title_bg = Image.new('RGBA', (1800, 160), (0, 0, 0, 120))
    img.paste(title_bg, (center_x - 900, 80), title_bg)
    
    draw.text((center_x, 130), title, fill='#FFFFFF', font=font, anchor="mm")
    draw.text((center_x, 180), subtitle, fill='#D4C4B0', font=font_small, anchor="mm")
    
    # 参数表（左下角）
    params = [
        "总长度：350mm",
        "手柄直径：Φ22mm",
        "顶端直径：Φ5mm",
        "节点数量：6 个",
        "节点纹理：蜂窝状",
        "杆身锥度：线性渐变",
    ]
    
    param_bg = Image.new('RGBA', (500, 300), (0, 0, 0, 100))
    img.paste(param_bg, (100, height - 400), param_bg)
    
    for i, text in enumerate(params):
        draw.text((150, height - 350 + i*45), text, fill='#D4C4B0', font=font_small)
    
    # 对比信息（右下角）
    comparison = [
        "vs CyberWand v21.0:",
        "✓ 长度相同 (350mm)",
        "✓ 节点数相同 (6 个)",
        "★ 新增蜂窝纹理",
        "★ 更明显锥度",
        "★ 装饰性设计",
    ]
    
    comp_bg = Image.new('RGBA', (500, 300), (0, 0, 0, 100))
    img.paste(comp_bg, (width - 600, height - 400), comp_bg)
    
    for i, text in enumerate(comparison):
        draw.text((width - 550, height - 350 + i*45), text, fill='#D4C4B0', font=font_small)

def draw_scale_bar():
    """添加比例尺"""
    scale_length = 100 * scale * 0.8  # 100mm 在图中的长度
    scale_y = height - 100
    
    # 比例尺线条
    draw.line([
        (center_x - scale_length/2, scale_y),
        (center_x + scale_length/2, scale_y)
    ], fill='#3C2415', width=5)
    
    # 两端垂直线
    draw.line([
        (center_x - scale_length/2, scale_y - 15),
        (center_x - scale_length/2, scale_y + 15)
    ], fill='#3C2415', width=3)
    
    draw.line([
        (center_x + scale_length/2, scale_y - 15),
        (center_x + scale_length/2, scale_y + 15)
    ], fill='#3C2415', width=3)
    
    # 标注文字
    try:
        font = ImageFont.truetype("msyh.ttc", 32)
    except:
        font = ImageFont.load_default()
    
    draw.text((center_x, scale_y + 30), "100mm", fill='#3C2415', font=font, anchor="mt")

# 执行绘制
print("Drawing wand reverse design v1.0...")
draw_wand()
draw_dimensions()
draw_scale_bar()

# 保存
output_path = r"D:\workspace\CyberWand_Insta360\enclosure\wand_reverse_v1_render.png"
img.save(output_path, 'PNG', quality=95)
print(f"Render complete! Saved to: {output_path}")
