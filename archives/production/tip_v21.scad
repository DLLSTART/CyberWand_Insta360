// CyberWand v21.0 - 杖尖 LED 座 OpenSCAD 模型
// 用于 3D 打印的 STL 文件生成

// 参数设置
tip_length = 25;         // 杖尖长度 mm
tip_base_diameter = 10;  // 底部直径 mm（连接杖身）
tip_tip_diameter = 5;    // 顶端直径 mm
led_hole_diameter = 6;   // LED 开孔直径 mm（WS2812B 5x5mm）

// 螺纹参数（连接杖身）
thread_diameter = 6;
thread_length = 8;

// 透光设计
led_chamber_depth = 8;   // LED 腔体深度
led_chamber_diameter = 8; // LED 腔体直径

$fn = 64;  // 圆滑度

// 模块：锥形杖尖主体
module tip_body() {
    difference() {
        // 外锥体
        cylinder(h = tip_length, d1 = tip_base_diameter, d2 = tip_tip_diameter);
        // LED 腔体（中空）
        translate([0, 0, tip_length - led_chamber_depth])
            cylinder(h = led_chamber_depth + 1, d1 = led_chamber_diameter, d2 = led_hole_diameter);
    }
}

// 模块：内螺纹（连接杖身）
module internal_thread() {
    difference() {
        cylinder(h = thread_length + 2, d = thread_diameter + 2);
        cylinder(h = thread_length + 4, d = thread_diameter);
        // 简化螺纹
        for (i = [0:12]) {
            rotate([0, 0, i * 30])
                translate([thread_diameter/2 + 0.2, 0, i * 0.6])
                    cube([1, 1.5, 0.5]);
        }
    }
}

// 模块：导线孔（内部通道）
module wire_channel() {
    translate([0, 0, -1])
        cylinder(h = tip_length + 2, d = 3);  // Φ3mm 通道
}

// 模块：表面纹理（螺旋纹）
module surface_texture() {
    for (i = [0:8]) {
        rotate([0, 0, i * 45])
            translate([tip_base_diameter/2 - 0.3, 0, i * 2])
                rotate([90, 0, 0])
                    cylinder(h = tip_base_diameter, d = 0.8);
    }
}

// 主模型：杖尖 LED 座
module tip_v21() {
    difference() {
        union() {
            // 杖尖主体
            tip_body();
            // 底部内螺纹
            translate([0, 0, -1])
                internal_thread();
        }
        union() {
            // 导线通道
            wire_channel();
            // 表面纹理（凹陷）
            surface_texture();
        }
    }
}

// 生成模型
tip_v21();

// 注释：导出 STL 命令
// openscad -o tip_v21.stl tip_v21.scad
