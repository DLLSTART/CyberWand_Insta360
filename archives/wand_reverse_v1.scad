// 魔杖参数化设计 - 基于图片逆向工程
// 分析时间：2026-04-06
// 参考图片：9bdb59b7-512d-4013-8f33-79ac7cdd3b03.jpg
// 风格：哈利波特风格装饰魔杖

// ==================== 核心参数 ====================

// 整体尺寸
total_length = 350;    // 总长度 mm
handle_dia = 22;       // 手柄直径 mm
tip_dia = 5;           // 顶端直径 mm

// 节点参数 [位置，直径，长度]
// 位置：距手柄底部的距离
// 根据图片视觉分析优化
nodes = [
    [35,  26, 22],   // 节点 1 - 手柄上方，最大直径
    [80,  23, 19],   // 节点 2
    [120, 21, 17],   // 节点 3
    [160, 19, 15],   // 节点 4
    [195, 16, 13],   // 节点 5
    [225, 13, 11]    // 节点 6 - 最靠近顶端
];

// 杆身直径函数（线性锥度）
function rod_diameter(z) = handle_dia - (handle_dia - tip_dia) * (z / total_length);

// ==================== 蜂窝纹理模块 ====================

module honeycomb_pattern(dia, len, cell_size=3, depth=1.5) {
    // 计算蜂窝单元数量
    circumference = PI * dia;
    num_cells_round = floor(circumference / cell_size);
    num_cells_height = floor(len / cell_size);
    
    difference() {
        // 基础圆柱
        cylinder(h=len, d=dia, $fn=60);
        
        // 蜂窝凹陷
        for (i = [0:num_cells_height-1]) {
            for (j = [0:num_cells_round-1]) {
                z_pos = i * cell_size + cell_size/2;
                angle = j * 360 / num_cells_round;
                
                // 错位排列（蜂窝结构）
                offset = (i % 2 == 0) ? 0 : (180/num_cells_round);
                rotate([0, 0, angle + offset])
                translate([dia/2 - 0.3, 0, z_pos])
                cylinder(h=depth+0.5, d=cell_size*0.7, $fn=6);
            }
        }
    }
}

// ==================== 螺旋装饰纹理 ====================

module spiral_texture(dia, len, pitch=15, depth=0.8, width=2) {
    turns = floor(len / pitch);
    
    difference() {
        // 基础圆柱
        cylinder(h=len, d=dia, $fn=60);
        
        // 螺旋凹槽
        for (t = [0:turns-1]) {
            for (angle = [0:10:360]) {
                z_offset = t * pitch + (angle / 360) * pitch;
                rad = angle * PI / 180;
                x = (dia/2 - 0.2) * cos(rad);
                y = (dia/2 - 0.2) * sin(rad);
                
                rotate([0, 0, angle])
                translate([dia/2 - 0.5, 0, z_offset])
                cube([width, 1, depth+0.5], center=true);
            }
        }
    }
}

// ==================== 杆身段模块 ====================

module rod_segment(z_start, z_end, dia_start, dia_end) {
    segment_len = z_end - z_start;
    translate([0, 0, z_start])
    cylinder(h=segment_len, d1=dia_start, d2=dia_end, $fn=60);
}

// ==================== 节点模块 ====================

module node(z_pos, dia, len) {
    // 计算杆身在该位置的直径
    rod_dia = rod_diameter(z_pos);
    
    // 节点突出部分
    protrusion = (dia - rod_dia) / 2;
    
    translate([0, 0, z_pos - len/2]) {
        // 节点主体（带蜂窝纹理）
        honeycomb_pattern(dia, len, cell_size=3, depth=1.5);
    }
}

// ==================== 手柄模块 ====================

module handle() {
    // 手柄主体
    handle_len = 40;
    
    // 手柄底部装饰（加粗）
    translate([0, 0, 0]) {
        difference() {
            cylinder(h=15, d1=24, d2=22, $fn=60);
            // 底部凹槽装饰
            translate([0, 0, 5])
            cylinder(h=5, d=20, $fn=60);
        }
    }
    
    // 手柄握持段
    translate([0, 0, 15])
    cylinder(h=handle_len-15, d1=22, d2=20, $fn=60);
}

// ==================== 顶端模块 ====================

module tip() {
    tip_start = 280;
    tip_len = total_length - tip_start;
    
    translate([0, 0, tip_start])
    cylinder(h=tip_len, d1=8, d2=tip_dia, $fn=60);
}

// ==================== 完整魔杖装配 ====================

module wand_assembly() {
    // 1. 手柄
    handle();
    
    // 2. 杆身段（节点之间）
    // 手柄到节点 1
    rod_segment(40, nodes[0][0]-nodes[0][2]/2, rod_diameter(40), rod_diameter(nodes[0][0]-nodes[0][2]/2));
    
    // 节点之间的杆身
    for (i = [0:5]) {
        z_end = (i < 5) ? nodes[i+1][0] - nodes[i+1][2]/2 : 280;
        z_start = nodes[i][0] + nodes[i][2]/2;
        
        if (z_start < z_end) {
            rod_segment(z_start, z_end, rod_diameter(z_start), rod_diameter(z_end));
        }
    }
    
    // 3. 节点
    for (node_data = nodes) {
        node(node_data[0], node_data[1], node_data[2]);
    }
    
    // 4. 顶端
    tip();
}

// ==================== 渲染输出 ====================

// 高质量渲染
$fa = 1;  // 角度精度
$fs = 0.1;  // 尺寸精度

// 生成魔杖
rotate([90, 0, 0])  // 水平放置便于查看
wand_assembly();

// ==================== 单独组件预览（可选） ====================

// 取消注释以查看单独组件
/*
// 查看单个节点
translate([-50, 0, 0])
node(0, 25, 20);

// 查看蜂窝纹理细节
translate([50, 0, 0])
honeycomb_pattern(25, 20, cell_size=3, depth=1.5);
*/
