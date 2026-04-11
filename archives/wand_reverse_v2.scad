// 魔杖参数化设计 v2.0 - 高保真逆向工程
// 分析时间：2026-04-07 23:30
// 参考图片：9bdb59b7-512d-4013-8f33-79ac7cdd3b03.jpg
// 改进：椭圆节点、密集尾部、不规则细节

// ==================== 核心参数 ====================

// 整体尺寸
total_length = 350;    // 总长度 mm
handle_dia = 22;       // 手柄直径 mm
tip_dia = 4;           // 顶端直径 mm（更细）

// 主节点参数 [位置，直径，长度，椭圆率]
// 椭圆率：1.0=球形，>1=拉长椭圆
// 位置：距手柄底部的距离
// 根据原图重新调整 - 尾部更密集
main_nodes = [
    [30,  27, 25, 1.3],   // 节点 1 - 手柄上方，最大直径，椭圆
    [70,  24, 21, 1.2],   // 节点 2 - 椭圆形
    [105, 22, 18, 1.2],   // 节点 3
    [140, 20, 16, 1.1],   // 节点 4
    [175, 18, 14, 1.1],   // 节点 5
    [205, 16, 12, 1.0],   // 节点 6
];

// 尾部小节点（密集区域）
// 原图特征：顶端有多个小凸起，不规则分布
tail_nodes = [
    [230, 13, 10, 1.0],   // 尾节点 1
    [248, 11, 8,  1.0],   // 尾节点 2
    [263, 9,  7,  1.0],   // 尾节点 3
    [276, 7,  6,  1.0],   // 尾节点 4
    [288, 6,  5,  1.0],   // 尾节点 5
];

// 杆身直径函数（非线性锥度 - 中间略粗）
function rod_diameter(z) = 
    z < 40 ? handle_dia - (handle_dia - 18) * (z / 40) :  // 手柄段
    z < 200 ? 18 - (18 - 10) * ((z - 40) / 160) :         // 中间段
    10 - (10 - tip_dia) * ((z - 200) / 150);              // 尾段

// ==================== 随机扰动函数 ====================
// 用于生成不规则细节

seed = 12345;  // 随机种子（固定以保证可重复性）

function random_n(seed_val, n) = [
    for (i = [0:n-1]) 
        (seed_val * (i + 1) * 997) % 1000 / 1000
];

// ==================== 椭圆节点模块 ====================

module ellipsoid_node(dia_x, dia_y, len, segments=60) {
    // 椭球体节点
    // dia_x: X 轴直径
    // dia_y: Y 轴直径（椭圆短轴）
    // len: 沿 Z 轴长度
    
    scale([1, dia_y/dia_x, 1])
    sphere(d=dia_x, $fn=segments);
}

// ==================== 不规则表面纹理 ====================

module irregular_bumps(dia, len, bump_count=20, bump_height=1.5) {
    // 不规则凸起纹理
    // 模拟原图中的随机小突起
    
    rand_vals = random_n(seed, bump_count);
    
    for (i = [0:bump_count-1]) {
        // 随机位置
        angle = rand_vals[i] * 360;
        z_pos = rand_vals[(i+7) % bump_count] * len;
        
        // 随机大小
        bump_size = 1.5 + rand_vals[(i+3) % bump_count] * 2;
        
        // 计算位置
        rad = angle * PI / 180;
        x = (dia/2 + 0.5) * cos(rad);
        y = (dia/2 + 0.5) * sin(rad);
        
        rotate([0, 0, angle])
        translate([dia/2, 0, z_pos - len/2])
        sphere(d=bump_size, $fn=20);
    }
}

// ==================== 螺旋缠绕纹理 ====================

module spiral_wrap(dia, len, turns=8, wrap_width=3, wrap_depth=1.2) {
    // 螺旋缠绕装饰（原图中的螺旋细节）
    
    for (t = [0:15:turns*360]) {
        angle = t;
        z_offset = (t / (turns*360)) * len;
        rad = angle * PI / 180;
        
        // 螺旋线位置
        x = (dia/2 - 0.3) * cos(rad);
        y = (dia/2 - 0.3) * sin(rad);
        
        rotate([0, 0, angle])
        translate([dia/2 - 0.5, 0, z_offset])
        cube([wrap_width, 2, wrap_depth+0.5], center=true);
    }
}

// ==================== 杆身段模块（非线性锥度） ====================

module rod_segment(z_start, z_end, dia_start, dia_end) {
    segment_len = z_end - z_start;
    translate([0, 0, z_start])
    cylinder(h=segment_len, d1=dia_start, d2=dia_end, $fn=60);
}

// ==================== 节点模块（椭圆 + 纹理） ====================

module node_v2(z_pos, dia, len, ellipse_ratio, with_bumps=true) {
    // 计算杆身在该位置的直径
    rod_dia = rod_diameter(z_pos);
    
    // 节点突出部分
    protrusion = (dia - rod_dia) / 2;
    
    translate([0, 0, z_pos]) {
        // 椭球节点主体
        rotate([90, 0, 0])  // 旋转使椭圆沿杆身方向
        scale([1, 1, ellipse_ratio])  // Z 轴拉长
        sphere(d=len > dia ? len : dia, $fn=60);
        
        // 表面不规则凸起（可选）
        if (with_bumps) {
            rotate([90, 0, 0])
            irregular_bumps(len > dia ? len : dia, len, bump_count=25, bump_height=1.2);
        }
    }
}

// ==================== 手柄模块（带装饰环） ====================

module handle_v2() {
    // 手柄主体
    handle_len = 35;
    
    // 手柄底部（加粗装饰）
    translate([0, 0, 0]) {
        // 底部球形装饰
        rotate([90, 0, 0])
        sphere(d=26, $fn=60);
    }
    
    // 手柄握持段（略锥度）
    translate([0, 0, 10])
    cylinder(h=handle_len-10, d1=24, d2=22, $fn=60);
    
    // 装饰环（靠近杆身）
    translate([0, 0, handle_len]) {
        rotate([90, 0, 0])
        torus(r_outer=13, r_inner=11, $fn=60);
    }
}

// ==================== 顶端模块（精细渐变） ====================

module tip_v2() {
    tip_start = 295;
    tip_len = total_length - tip_start;
    
    // 顶端分段渐变（更自然）
    translate([0, 0, tip_start]) {
        // 第一段：细锥
        cylinder(h=tip_len*0.6, d1=7, d2=5, $fn=60);
        // 第二段：尖顶
        translate([0, 0, tip_len*0.6])
        cylinder(h=tip_len*0.4, d1=5, d2=1.5, $fn=60);
    }
}

// ==================== 完整魔杖装配 ====================

module wand_assembly_v2() {
    color("brown") {
        // 1. 手柄
        handle_v2();
        
        // 2. 杆身段（主节点之间）
        // 手柄到节点 1
        rod_segment(35, main_nodes[0][0]-main_nodes[0][2]/2, 
                   rod_diameter(35), rod_diameter(main_nodes[0][0]-main_nodes[0][2]/2));
        
        // 主节点之间的杆身
        for (i = [0:len(main_nodes)-2]) {
            z_start = main_nodes[i][0] + main_nodes[i][2]/2;
            z_end = main_nodes[i+1][0] - main_nodes[i+1][2]/2;
            
            if (z_start < z_end) {
                rod_segment(z_start, z_end, 
                           rod_diameter(z_start), rod_diameter(z_end));
            }
        }
        
        // 最后一个主节点到尾段开始
        last_main = main_nodes[len(main_nodes)-1];
        first_tail = tail_nodes[0];
        z_start = last_main[0] + last_main[2]/2;
        z_end = first_tail[0] - first_tail[2]/2;
        
        if (z_start < z_end) {
            rod_segment(z_start, z_end, 
                       rod_diameter(z_start), rod_diameter(z_end));
        }
        
        // 尾部节点之间的杆身
        for (i = [0:len(tail_nodes)-2]) {
            z_start = tail_nodes[i][0] + tail_nodes[i][2]/2;
            z_end = tail_nodes[i+1][0] - tail_nodes[i+1][2]/2;
            
            if (z_start < z_end) {
                rod_segment(z_start, z_end, 
                           rod_diameter(z_start), rod_diameter(z_end));
            }
        }
        
        // 3. 主节点（椭圆 + 纹理）
        for (node_data = main_nodes) {
            node_v2(node_data[0], node_data[1], node_data[2], node_data[3], with_bumps=true);
        }
        
        // 4. 尾部小节点（密集区域）
        for (node_data = tail_nodes) {
            node_v2(node_data[0], node_data[1], node_data[2], node_data[3], with_bumps=false);
        }
        
        // 5. 顶端
        tip_v2();
    }
}

// ==================== 渲染输出 ====================

// 高质量渲染设置
$fa = 0.5;  // 角度精度（更高）
$fs = 0.05;  // 尺寸精度（更精细）

// 生成魔杖（水平放置便于查看）
rotate([90, 0, 0])
translate([0, 0, -total_length/2])
wand_assembly_v2();

// ==================== 单独组件预览（调试用） ====================

/*
// 查看单个椭圆节点
translate([-50, 0, 0])
node_v2(0, 24, 21, 1.2, with_bumps=true);

// 查看尾部节点群
translate([50, 0, 0])
for (i = [0:len(tail_nodes)-1]) {
    translate([0, 0, i*15])
    node_v2(0, tail_nodes[i][1], tail_nodes[i][2], tail_nodes[i][3], with_bumps=false);
}

// 查看不规则纹理
translate([100, 0, 0])
rotate([90, 0, 0])
irregular_bumps(30, 40, bump_count=30, bump_height=1.5);
*/
