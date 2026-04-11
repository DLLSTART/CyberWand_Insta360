// CyberWand v21.0 - 杖身 OpenSCAD 模型
// 用于 3D 打印的 STL 文件生成（分段设计，便于打印）

// 参数设置
shaft_total_length = 338;  // 杖身总长度 mm（350-12 手柄）
shaft_segments = 4;        // 分段数量
segment_length = shaft_total_length / shaft_segments;  // 每段长度约 84.5mm

shaft_base_diameter = 14;   // 底部外径 mm
shaft_tip_diameter = 8;     // 顶端外径 mm
shaft_inner_diameter = 11;  // 底部内径 mm（容纳电池）
shaft_tip_inner_diameter = 5; // 顶端内径 mm

wall_thickness = 1.5;       // 壁厚 mm

// 螺纹连接参数
male_thread_diameter = 8;
female_thread_diameter = 8.5;
thread_length = 8;

$fn = 64;  // 圆滑度

// 模块：锥形中空管（杖身基本形状）
module tapered_tube(length, d_base_outer, d_base_inner, d_tip_outer, d_tip_inner) {
    difference() {
        // 外锥体
        cylinder(h = length, d1 = d_base_outer, d2 = d_tip_outer);
        // 内锥体（中空）
        translate([0, 0, -1])
            cylinder(h = length + 2, d1 = d_base_inner, d2 = d_tip_inner);
    }
}

// 模块：外螺纹（雄头）
module male_thread(diameter, length) {
    difference() {
        cylinder(h = length + 2, d = diameter);
        for (i = [0:15]) {
            rotate([0, 0, i * 24])
                translate([diameter/2 - 0.4, 0, i * 0.5])
                    cube([1, 2, 0.4]);
        }
    }
}

// 模块：内螺纹（雌头）
module female_thread(diameter, length) {
    difference() {
        cylinder(h = length + 2, d = diameter + 3);
        cylinder(h = length + 4, d = diameter);
        for (i = [0:15]) {
            rotate([0, 0, i * 24])
                translate([diameter/2 + 0.2, 0, i * 0.5])
                    cube([1, 2, 0.4]);
        }
    }
}

// 模块：杖身分段（第 n 段）
module shaft_segment(segment_num, total_segments) {
    t = (segment_num - 1) / (total_segments - 1);
    
    // 计算该段的直径
    d_base_outer = shaft_base_diameter - t * (shaft_base_diameter - shaft_tip_diameter);
    d_tip_outer = shaft_base_diameter - (t + 1/total_segments) * (shaft_base_diameter - shaft_tip_diameter);
    d_base_inner = shaft_inner_diameter - t * (shaft_inner_diameter - shaft_tip_inner_diameter);
    d_tip_inner = shaft_inner_diameter - (t + 1/total_segments) * (shaft_inner_diameter - shaft_tip_inner_diameter);
    
    // 第一段底部有内螺纹（连接手柄）
    if (segment_num == 1) {
        difference() {
            union() {
                tapered_tube(segment_length, d_base_outer, d_base_inner, d_tip_outer, d_tip_inner);
                // 底部内螺纹
                translate([0, 0, -1])
                    female_thread(male_thread_diameter, thread_length);
            }
            // 顶端外螺纹
            translate([0, 0, segment_length - thread_length])
                male_thread(male_thread_diameter - 1, thread_length);
        }
    }
    // 中间段
    else if (segment_num < total_segments) {
        difference() {
            union() {
                tapered_tube(segment_length, d_base_outer, d_base_inner, d_tip_outer, d_tip_inner);
                // 底部内螺纹
                translate([0, 0, -1])
                    female_thread(male_thread_diameter, thread_length);
            }
            // 顶端外螺纹
            translate([0, 0, segment_length - thread_length])
                male_thread(male_thread_diameter - 1, thread_length);
        }
    }
    // 最后一段顶端连接杖尖
    else {
        difference() {
            union() {
                tapered_tube(segment_length, d_base_outer, d_base_inner, d_tip_outer, d_tip_inner);
                // 底部内螺纹
                translate([0, 0, -1])
                    female_thread(male_thread_diameter, thread_length);
            }
            // 顶端外螺纹（连接杖尖）
            translate([0, 0, segment_length - thread_length])
                male_thread(6, thread_length);  // M6 螺纹
        }
    }
}

// 生成 4 个杖身分段
// 使用时分别导出每个分段：
// openscad -o shaft_v21_segment_1.stl -D segment_num=1 shaft_v21.scad
// openscad -o shaft_v21_segment_2.stl -D segment_num=2 shaft_v21.scad
// openscad -o shaft_v21_segment_3.stl -D segment_num=3 shaft_v21.scad
// openscad -o shaft_v21_segment_4.stl -D segment_num=4 shaft_v21.scad

segment_num = 1;  // 修改此值导出不同分段（1-4）
shaft_segment(segment_num, shaft_segments);

echo(str("导出杖身分段 ", segment_num, "/", shaft_segments));
